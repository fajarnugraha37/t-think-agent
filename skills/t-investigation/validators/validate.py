#!/usr/bin/env python3
"""Validate investigation skill inputs, outputs, evidence ledgers, critiques, and sufficiency decisions."""
from __future__ import annotations
import argparse, json, sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "input": ROOT / "schemas/input.schema.json",
    "output": ROOT / "schemas/output.schema.json",
    "evidence": ROOT / "schemas/evidence-record.schema.json",
    "critique": ROOT / "schemas/critique.schema.json",
    "sufficiency": ROOT / "schemas/sufficiency-decision.schema.json",
}

@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str
    def __str__(self) -> str:
        return f"{self.path}: {self.message}"

def normalize(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v) for v in value]
    return value

def load_document(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return normalize(yaml.safe_load(text))

def load_schema(kind: str) -> dict[str, Any]:
    return json.loads(SCHEMAS[kind].read_text(encoding="utf-8"))

def format_path(path: Iterable[Any]) -> str:
    result = "$"
    for part in path:
        result += f"[{part}]" if isinstance(part, int) else f".{part}"
    return result

def structural_issues(document: Any, schema: dict[str, Any], prefix: str = "$") -> list[ValidationIssue]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    issues=[]
    for error in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path)):
        p=format_path(error.absolute_path)
        if prefix != "$":
            p=prefix + (p[1:] if p.startswith("$") else p)
        issues.append(ValidationIssue(p,error.message))
    return issues

def load_ledger(path: Path) -> tuple[list[dict[str, Any]], list[ValidationIssue]]:
    records=[]; issues=[]
    schema=load_schema("evidence")
    for lineno,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip():
            continue
        try:
            rec=json.loads(line)
        except json.JSONDecodeError as exc:
            issues.append(ValidationIssue(f"$[line:{lineno}]",f"invalid JSON: {exc.msg}")); continue
        rec=normalize(rec); records.append(rec)
        issues.extend(structural_issues(rec,schema,f"$[line:{lineno}]"))
    if not records:
        issues.append(ValidationIssue("$","ledger must contain at least one record"))
    if not issues:
        issues.extend(ledger_semantic_issues(records))
    return records,issues

def ledger_semantic_issues(records: list[dict[str,Any]]) -> list[ValidationIssue]:
    issues=[]; by_id={}; source_ids=set()
    for i,r in enumerate(records):
        rid=r.get("id")
        if rid in by_id:
            issues.append(ValidationIssue(f"$[{i}].id",f"duplicate claim ID {rid!r}; first at record {by_id[rid]}"))
        else: by_id[rid]=i
        for j,s in enumerate(r.get("sources",[])):
            sid=s.get("source_id")
            if sid in source_ids: issues.append(ValidationIssue(f"$[{i}].sources[{j}].source_id",f"duplicate source ID {sid!r}"))
            source_ids.add(sid)
    ids=set(by_id)
    def refs(i:int,r:dict[str,Any],field:str):
        for j,x in enumerate(r.get(field,[]) or []):
            if x==r.get("id"): issues.append(ValidationIssue(f"$[{i}].{field}[{j}]","self-reference is prohibited"))
            elif x not in ids: issues.append(ValidationIssue(f"$[{i}].{field}[{j}]",f"references unknown claim ID {x!r}"))
    for i,r in enumerate(records):
        for field in ("supporting_claim_ids","contradicting_claim_ids","conflicting_claim_ids","supersedes"):
            refs(i,r,field)
        typ=r.get("type")
        if typ=="FACT":
            sources=r.get("sources",[])
            if r.get("fact_scope")=="SYSTEM_OBSERVED":
                direct=[s for s in sources if s.get("authority")=="DIRECT" and s.get("source_context")=="ACTUAL_SYSTEM" and s.get("source_type") not in {"DOCUMENTATION","COMMENT","HUMAN_REPORT","CONVERSATION_HINT"}]
                if not direct: issues.append(ValidationIssue(f"$[{i}].sources","SYSTEM_OBSERVED fact requires at least one DIRECT ACTUAL_SYSTEM source"))
            if r.get("fact_scope")=="HUMAN_REPORTED" and not any(s.get("source_type")=="HUMAN_REPORT" for s in sources):
                issues.append(ValidationIssue(f"$[{i}].sources","HUMAN_REPORTED fact requires HUMAN_REPORT source"))
        if typ=="INFERENCE":
            support=r.get("supporting_claim_ids",[])
            if not support: issues.append(ValidationIssue(f"$[{i}].supporting_claim_ids","inference requires supporting claims"))
            elif not any(by_id.get(x) is not None and records[by_id[x]].get("type")=="FACT" for x in support):
                issues.append(ValidationIssue(f"$[{i}].supporting_claim_ids","inference must directly cite at least one FACT"))
        if typ=="ASSUMPTION" and r.get("confidence")=="HIGH":
            issues.append(ValidationIssue(f"$[{i}].confidence","ASSUMPTION cannot have HIGH confidence"))
        if typ=="CONFLICT" and r.get("resolution_status")=="RESOLVED" and r.get("status") not in {"RESOLVED","SUPERSEDED"}:
            issues.append(ValidationIssue(f"$[{i}].status","resolved conflict should use RESOLVED or SUPERSEDED status"))
        if r.get("status")=="RETRACTED" and not r.get("supersedes") and not r.get("resolution_summary"):
            issues.append(ValidationIssue(f"$[{i}]","RETRACTED claim should explain resolution_summary or replacement relationship"))
        if r.get("negative_claim") is True:
            ss=r.get("search_scope",{})
            if not ss.get("queries") and not ss.get("paths"):
                issues.append(ValidationIssue(f"$[{i}].search_scope","negative claim requires queries or paths"))
    return issues

def output_semantic_issues(doc:dict[str,Any], records:list[dict[str,Any]]|None, transition:bool) -> list[ValidationIssue]:
    issues=[]
    # Unique IDs in output lists.
    for field,key in (("problem_coverage","problem_element_id"),("coverage_dimensions","dimension"),("snapshot.repositories","repository_id"),("operation_summary.operations","id")):
        cur=doc
        for part in field.split('.'): cur=cur.get(part,[]) if isinstance(cur,dict) else []
        seen=set()
        for i,item in enumerate(cur):
            val=item.get(key)
            if val in seen: issues.append(ValidationIssue(f"$.{field}[{i}].{key}",f"duplicate {key} {val!r}"))
            seen.add(val)
    ops=doc.get("operation_summary",{}).get("operations",[])
    actual=Counter(o.get("operation_class") for o in ops)
    count_fields={"READ_ONLY":"read_only_count","NON_MUTATING_TEST":"non_mutating_test_count","MUTATING":"mutating_count","DESTRUCTIVE":"destructive_count"}
    for klass,field in count_fields.items():
        if doc.get("operation_summary",{}).get(field,0)!=actual.get(klass,0):
            issues.append(ValidationIssue(f"$.operation_summary.{field}",f"does not match operations list count {actual.get(klass,0)}"))
    for i,o in enumerate(ops):
        if o.get("operation_class") in {"MUTATING","DESTRUCTIVE"} and o.get("authorized") is not True:
            issues.append(ValidationIssue(f"$.operation_summary.operations[{i}].authorized",f"{o.get('operation_class')} operation must be explicitly authorized"))
    if records is not None:
        by_id={r['id']:r for r in records if 'id' in r}; ids=set(by_id)
        ledger=doc.get("evidence_ledger",{})
        counts=Counter(r.get("type") for r in records)
        active=sum(1 for r in records if r.get("status") in {"ACTIVE","WEAKENED","RESOLVED"})
        if ledger.get("record_count")!=len(records): issues.append(ValidationIssue("$.evidence_ledger.record_count",f"expected {len(records)} from ledger"))
        if ledger.get("active_record_count")!=active: issues.append(ValidationIssue("$.evidence_ledger.active_record_count",f"expected {active} from ledger"))
        for typ,val in ledger.get("counts_by_type",{}).items():
            if val!=counts.get(typ,0): issues.append(ValidationIssue(f"$.evidence_ledger.counts_by_type.{typ}",f"expected {counts.get(typ,0)} from ledger"))
        def check_refs(path,arr):
            for j,x in enumerate(arr or []):
                if x not in ids: issues.append(ValidationIssue(f"{path}[{j}]",f"references unknown ledger claim {x!r}"))
        for i,x in enumerate(doc.get("problem_coverage",[])): check_refs(f"$.problem_coverage[{i}].supporting_claim_ids",x.get("supporting_claim_ids"))
        for i,x in enumerate(doc.get("coverage_dimensions",[])): check_refs(f"$.coverage_dimensions[{i}].supporting_claim_ids",x.get("supporting_claim_ids"))
        sa=doc.get("sufficiency_assessment",{})
        check_refs("$.sufficiency_assessment.blocking_unknown_ids",sa.get("blocking_unknown_ids"))
        check_refs("$.sufficiency_assessment.blocking_conflict_ids",sa.get("blocking_conflict_ids"))
        for j,x in enumerate(sa.get("blocking_unknown_ids",[])):
            r=by_id.get(x,{})
            if r.get("type")!="UNKNOWN" or r.get("blocking") is not True: issues.append(ValidationIssue(f"$.sufficiency_assessment.blocking_unknown_ids[{j}]",f"{x} is not a blocking UNKNOWN"))
        for j,x in enumerate(sa.get("blocking_conflict_ids",[])):
            r=by_id.get(x,{})
            if r.get("type")!="CONFLICT" or r.get("blocking") is not True or r.get("resolution_status")=="RESOLVED": issues.append(ValidationIssue(f"$.sufficiency_assessment.blocking_conflict_ids[{j}]",f"{x} is not a blocking unresolved CONFLICT"))
    gate=doc.get("gate",{}); sa=doc.get("sufficiency_assessment",{}); status=doc.get("metadata",{}).get("status")
    if gate.get("status")=="READY_FOR_SYSTEM_MODEL":
        if status!="COMPLETE": issues.append(ValidationIssue("$.metadata.status","must be COMPLETE for READY_FOR_SYSTEM_MODEL"))
        if sa.get("status")!="SUFFICIENT": issues.append(ValidationIssue("$.sufficiency_assessment.status","must be SUFFICIENT for READY_FOR_SYSTEM_MODEL"))
        if gate.get("next_state")!="SYSTEM_MODEL": issues.append(ValidationIssue("$.gate.next_state","must be SYSTEM_MODEL"))
        if gate.get("blocking_reasons"): issues.append(ValidationIssue("$.gate.blocking_reasons","must be empty"))
        if sa.get("blocking_unknown_ids"): issues.append(ValidationIssue("$.sufficiency_assessment.blocking_unknown_ids","must be empty"))
        if sa.get("blocking_conflict_ids"): issues.append(ValidationIssue("$.sufficiency_assessment.blocking_conflict_ids","must be empty"))
        for i,x in enumerate(doc.get("problem_coverage",[])):
            if x.get("status")=="UNEXPLAINED": issues.append(ValidationIssue(f"$.problem_coverage[{i}].status","required problem element remains UNEXPLAINED"))
            if not x.get("supporting_claim_ids"): issues.append(ValidationIssue(f"$.problem_coverage[{i}].supporting_claim_ids","transition-ready coverage needs evidence"))
        for i,x in enumerate(doc.get("coverage_dimensions",[])):
            if x.get("required") and x.get("status") not in {"COVERED","JUSTIFIED_NOT_APPLICABLE"}: issues.append(ValidationIssue(f"$.coverage_dimensions[{i}].status","required dimension is incomplete"))
            if x.get("status")=="JUSTIFIED_NOT_APPLICABLE" and not x.get("justification"): issues.append(ValidationIssue(f"$.coverage_dimensions[{i}].justification","required for JUSTIFIED_NOT_APPLICABLE"))
        if records is not None:
            direct_facts=0
            for r in records:
                if r.get("type")=="FACT" and r.get("status") in {"ACTIVE","WEAKENED"} and r.get("fact_scope")=="SYSTEM_OBSERVED":
                    if any(s.get("authority")=="DIRECT" and s.get("source_context")=="ACTUAL_SYSTEM" and s.get("source_type") not in {"DOCUMENTATION","COMMENT","HUMAN_REPORT","CONVERSATION_HINT"} for s in r.get("sources",[])): direct_facts+=1
            if direct_facts<1: issues.append(ValidationIssue("$.evidence_ledger","transition requires at least one active direct system FACT"))
    if gate.get("status")=="INVESTIGATION_INCOMPLETE":
        if gate.get("next_state")!="INVESTIGATION": issues.append(ValidationIssue("$.gate.next_state","must be INVESTIGATION"))
        if not gate.get("blocking_reasons"): issues.append(ValidationIssue("$.gate.blocking_reasons","must explain why investigation is incomplete"))
    if gate.get("status")=="BLOCKED" and status!="BLOCKED": issues.append(ValidationIssue("$.metadata.status","must be BLOCKED"))
    if transition and gate.get("status")!="READY_FOR_SYSTEM_MODEL": issues.append(ValidationIssue("$.gate.status","transition-ready validation requires READY_FOR_SYSTEM_MODEL"))
    if transition and records is None: issues.append(ValidationIssue("$","--require-transition-ready requires --ledger"))
    return issues

def validate(kind:str,path:Path,ledger_path:Path|None=None,transition:bool=False)->list[ValidationIssue]:
    if kind=="ledger":
        _,issues=load_ledger(path); return issues
    doc=load_document(path); issues=structural_issues(doc,load_schema(kind))
    records=None
    if ledger_path:
        records,lissues=load_ledger(ledger_path); issues.extend(ValidationIssue(f"ledger{e.path[1:] if e.path.startswith('$') else e.path}",e.message) for e in lissues)
    if not issues and kind=="output": issues.extend(output_semantic_issues(doc,records,transition))
    elif transition and kind!="output": issues.append(ValidationIssue("$","--require-transition-ready is valid only for output"))
    return issues

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kind",choices=["input","output","ledger","evidence","critique","sufficiency"],required=True)
    p.add_argument("--file",type=Path,required=True)
    p.add_argument("--ledger",type=Path)
    p.add_argument("--require-transition-ready",action="store_true")
    a=p.parse_args()
    kind="evidence" if a.kind=="evidence" else a.kind
    try: issues=validate(kind,a.file,a.ledger,a.require_transition_ready)
    except (OSError,ValueError,json.JSONDecodeError,yaml.YAMLError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr); return 2
    if issues:
        print(f"INVALID: {a.file}",file=sys.stderr)
        for issue in issues: print(f"- {issue}",file=sys.stderr)
        return 1
    suffix=" and transition-ready" if a.require_transition_ready else ""
    print(f"VALID{suffix}: {a.file}")
    return 0

if __name__=="__main__": raise SystemExit(main())
