#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {k: ROOT/'schemas'/v for k,v in {
 'input':'input.schema.json','output':'output.schema.json','critique':'critique-request.schema.json','assessment':'assessment.schema.json','revision':'revision-directive.schema.json','request':'evidence-request.schema.json','element':'upstream-model-element.schema.json','relation':'upstream-model-relation.schema.json','trace':'upstream-traceability-row.schema.json','evidence':'upstream-evidence-record.schema.json','model_output':'upstream-system-model-output.schema.json','consistency':'upstream-consistency-decision.schema.json'}.items()}

class Issue:
 def __init__(self,path:str,message:str): self.path,self.message=path,message
 def __str__(self): return f"{self.path}: {self.message}"

def norm(v:Any)->Any:
 if isinstance(v,(datetime,date)): return v.isoformat()
 if isinstance(v,dict): return {k:norm(x) for k,x in v.items()}
 if isinstance(v,list): return [norm(x) for x in v]
 return v

def load_doc(path:Path)->Any:
 text=path.read_text(encoding='utf-8')
 return json.loads(text) if path.suffix=='.json' else norm(yaml.safe_load(text))

def schema(kind:str)->dict:
 s=json.loads(SCHEMAS[kind].read_text(encoding='utf-8'))
 if kind=='input':
  s['properties']['human_critiques']['items']=json.loads(SCHEMAS['critique'].read_text(encoding='utf-8'))
 if kind=='model_output':
  s['properties']['consistency_assessment']=json.loads(SCHEMAS['consistency'].read_text(encoding='utf-8'))
 return s

def fmt_path(p:Iterable[Any])->str:
 out='$'
 for x in p: out += f'[{x}]' if isinstance(x,int) else f'.{x}'
 return out

def structural(doc:Any,kind:str,prefix='$')->list[Issue]:
 s=schema(kind)
 v=Draft202012Validator(s,format_checker=FormatChecker())
 issues=[]
 for e in sorted(v.iter_errors(doc),key=lambda x:list(x.absolute_path)):
  p=fmt_path(e.absolute_path); p=prefix+(p[1:] if p.startswith('$') else p) if prefix!='$' else p
  issues.append(Issue(p,e.message))
 return issues

def load_jsonl(path:Path,kind:str,allow_empty=False):
 recs=[]; issues=[]
 for n,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
  if not line.strip(): continue
  try: r=json.loads(line)
  except json.JSONDecodeError as e: issues.append(Issue(f'$[line:{n}]',f'invalid JSON: {e.msg}')); continue
  recs.append(r); issues += structural(r,kind,f'$[line:{n}]')
 if not recs and not allow_empty: issues.append(Issue('$','JSONL file must contain at least one record'))
 return recs,issues

def split(v): return [x.strip() for x in (v or '').split('|') if x.strip()]
def load_trace(path:Path):
 rows=[]; issues=[]
 with path.open(encoding='utf-8',newline='') as h:
  rd=csv.DictReader(h)
  req={'trace_id','problem_id','evidence_ids','model_element_ids','model_relation_ids','coverage_status','summary','limitations'}
  if set(rd.fieldnames or [])!=req: return [],[Issue('$.headers',f'expected exactly {sorted(req)}')]
  for n,raw in enumerate(rd,2):
   r={'trace_id':raw['trace_id'].strip(),'problem_id':raw['problem_id'].strip(),'evidence_ids':split(raw['evidence_ids']),'model_element_ids':split(raw['model_element_ids']),'model_relation_ids':split(raw['model_relation_ids']),'coverage_status':raw['coverage_status'].strip(),'summary':raw['summary'].strip()}
   if raw['limitations'].strip(): r['limitations']=raw['limitations'].strip()
   rows.append(r); issues += structural(r,'trace',f'$[row:{n}]')
 return rows,issues

def dup(records,key,label):
 c=Counter(r.get(key) for r in records if r.get(key)); return [Issue('$',f'duplicate {label}: {x}') for x,n in c.items() if n>1]

def ids(records,key='id'): return {r.get(key) for r in records if r.get(key)}

def validate_package(args):
 issues=[]
 inp=load_doc(Path(args.input)); out=load_doc(Path(args.output)); model_out=load_doc(Path(args.model_output))
 issues += structural(inp,'input'); issues += structural(out,'output'); issues += structural(model_out,'model_output')
 ass,ix=load_jsonl(Path(args.assessments),'assessment'); issues+=ix
 rev,ix=load_jsonl(Path(args.revisions),'revision',allow_empty=True); issues+=ix
 reqs,ix=load_jsonl(Path(args.requests),'request',allow_empty=True); issues+=ix
 elems,ix=load_jsonl(Path(args.elements),'element'); issues+=ix
 rels,ix=load_jsonl(Path(args.relations),'relation'); issues+=ix
 ledger,ix=load_jsonl(Path(args.ledger),'evidence'); issues+=ix
 traces,ix=load_trace(Path(args.traceability)); issues+=ix
 if issues: return issues
 critiques=inp['human_critiques']; crit_ids=ids(critiques,'critique_id'); ass_ids=ids(ass,'assessment_id'); elem_ids=ids(elems); rel_ids=ids(rels); trace_ids=ids(traces,'trace_id'); evidence_ids=ids(ledger); rev_ids=ids(rev,'directive_id'); request_ids=ids(reqs,'request_id')
 issues += dup(critiques,'critique_id','critique id')+dup(ass,'assessment_id','assessment id')+dup(rev,'directive_id','revision id')+dup(reqs,'request_id','request id')
 critique_by_id={c['critique_id']:c for c in critiques}
 for c in critiques:
  cid=c['critique_id']
  for ref in c.get('target_ids',[]):
   if ref.startswith('MDL-') and ref not in elem_ids: issues.append(Issue(f'$.critique[{cid}].target_ids',f'unknown model element: {ref}'))
   if ref.startswith('REL-') and ref not in rel_ids: issues.append(Issue(f'$.critique[{cid}].target_ids',f'unknown relation: {ref}'))
   if ref.startswith('TRC-') and ref not in trace_ids: issues.append(Issue(f'$.critique[{cid}].target_ids',f'unknown traceability row: {ref}'))
   if ref.split('-')[0] in {'F','INF','ASM','UNK','CON','INV','RSK'} and ref not in evidence_ids: issues.append(Issue(f'$.critique[{cid}].target_ids',f'unknown evidence: {ref}'))
  for ref in c.get('claimed_evidence_ids',[]):
   if ref not in evidence_ids: issues.append(Issue(f'$.critique[{cid}].claimed_evidence_ids',f'unknown evidence id: {ref}'))
 # Every critique exactly once.
 assessed=[a.get('critique_id') for a in ass]
 for cid in crit_ids:
  n=assessed.count(cid)
  if n!=1: issues.append(Issue('$.assessments',f'critique {cid} must have exactly one assessment, found {n}'))
 for a in ass:
  cid=a['critique_id']
  if cid not in crit_ids: issues.append(Issue('$.assessments',f'unknown critique id: {cid}'))
  elif set(a['target_ids']) != set(critique_by_id[cid].get('target_ids',[])):
   issues.append(Issue(f'$.assessment[{a["assessment_id"]}].target_ids',f'must exactly match critique {cid} target_ids'))
  for ref in a['evidence_reviewed']:
   if ref not in evidence_ids: issues.append(Issue(f'$.assessment[{a["assessment_id"]}].evidence_reviewed',f'unknown evidence id: {ref}'))
  for ref in a['model_items_reviewed']:
   if ref.startswith('MDL-') and ref not in elem_ids: issues.append(Issue(f'$.assessment[{a["assessment_id"]}].model_items_reviewed',f'unknown model element: {ref}'))
   if ref.startswith('REL-') and ref not in rel_ids: issues.append(Issue(f'$.assessment[{a["assessment_id"]}].model_items_reviewed',f'unknown relation: {ref}'))
   if ref.startswith('TRC-') and ref not in trace_ids: issues.append(Issue(f'$.assessment[{a["assessment_id"]}].model_items_reviewed',f'unknown traceability row: {ref}'))
  for ref in a['target_ids']:
   if ref.startswith('MDL-') and ref not in elem_ids: issues.append(Issue(f'$.assessment[{a["assessment_id"]}].target_ids',f'unknown model element: {ref}'))
   if ref.startswith('REL-') and ref not in rel_ids: issues.append(Issue(f'$.assessment[{a["assessment_id"]}].target_ids',f'unknown relation: {ref}'))
   if ref.startswith('TRC-') and ref not in trace_ids: issues.append(Issue(f'$.assessment[{a["assessment_id"]}].target_ids',f'unknown traceability row: {ref}'))
   if ref.split('-')[0] in {'F','INF','ASM','UNK','CON','INV','RSK'} and ref not in evidence_ids: issues.append(Issue(f'$.assessment[{a["assessment_id"]}].target_ids',f'unknown evidence: {ref}'))
  for ref in a['revision_directive_ids']:
   if ref not in rev_ids: issues.append(Issue(f'$.assessment[{a["assessment_id"]}].revision_directive_ids',f'unknown revision directive: {ref}'))
  for ref in a['investigation_request_ids']:
   if ref not in request_ids: issues.append(Issue(f'$.assessment[{a["assessment_id"]}].investigation_request_ids',f'unknown evidence request: {ref}'))
  cl=a['classification']; status=a['resulting_status']
  if cl=='REJECTED_WITH_EVIDENCE':
   if not a['evidence_reviewed']: issues.append(Issue(f'$.assessment[{a["assessment_id"]}]','REJECTED_WITH_EVIDENCE requires evidence_reviewed'))
   if not a['contradicting_findings']: issues.append(Issue(f'$.assessment[{a["assessment_id"]}]','REJECTED_WITH_EVIDENCE requires contradicting_findings'))
  if cl=='REQUIRES_INVESTIGATION':
   if status!='INVESTIGATION_REQUIRED': issues.append(Issue(f'$.assessment[{a["assessment_id"]}].resulting_status','REQUIRES_INVESTIGATION requires INVESTIGATION_REQUIRED'))
   if not a['investigation_request_ids']: issues.append(Issue(f'$.assessment[{a["assessment_id"]}]','REQUIRES_INVESTIGATION requires an evidence request'))
  if status in {'WEAKENED','REVISED','RETRACTED'} and not a['revision_directive_ids']:
   issues.append(Issue(f'$.assessment[{a["assessment_id"]}]',f'{status} requires a revision directive'))
 # Revision refs and prohibition.
 for r in rev:
  for cid in r['trigger_critique_ids']:
   if cid not in crit_ids: issues.append(Issue(f'$.revision[{r["directive_id"]}]',f'unknown critique id: {cid}'))
  for eid in r['evidence_ids']:
   if eid not in evidence_ids: issues.append(Issue(f'$.revision[{r["directive_id"]}]',f'unknown evidence id: {eid}'))
  tid=r['target_id']
  if r['operation']!='ADD':
   if tid.startswith('MDL-') and tid not in elem_ids: issues.append(Issue(f'$.revision[{r["directive_id"]}]',f'unknown model element: {tid}'))
   if tid.startswith('REL-') and tid not in rel_ids: issues.append(Issue(f'$.revision[{r["directive_id"]}]',f'unknown relation: {tid}'))
   if tid.startswith('TRC-') and tid not in trace_ids: issues.append(Issue(f'$.revision[{r["directive_id"]}]',f'unknown trace row: {tid}'))
 # Request refs.
 for q in reqs:
  for cid in q['trigger_critique_ids']:
   if cid not in crit_ids: issues.append(Issue(f'$.request[{q["request_id"]}]',f'unknown critique id: {cid}'))
 # Counts and summaries.
 expected={'assessments':len(ass),'revision_directives':len(rev),'evidence_requests':len(reqs)}
 for k,n in expected.items():
  got=out['artifact_files'][k]['record_count']
  if got!=n: issues.append(Issue(f'$.artifact_files.{k}.record_count',f'expected {n}, got {got}'))
 cls=Counter(a['classification'] for a in ass)
 summary=out['review_summary']
 calc={'total_critiques':len(critiques),'accepted':cls['ACCEPTED'],'partially_accepted':cls['PARTIALLY_ACCEPTED'],'rejected_with_evidence':cls['REJECTED_WITH_EVIDENCE'],'requires_investigation':cls['REQUIRES_INVESTIGATION'],'unassessed':max(0,len(critiques)-len(ass))}
 for k,v in calc.items():
  if summary[k]!=v: issues.append(Issue(f'$.review_summary.{k}',f'expected {v}, got {summary[k]}'))
 # Cross source consistency.
 if inp['source_model']['modeling_id']!=model_out['metadata']['modeling_id']: issues.append(Issue('$.source_model.modeling_id','does not match source system model output'))
 if out['source_model']['modeling_id']!=inp['source_model']['modeling_id']: issues.append(Issue('$.output.source_model.modeling_id','does not match input'))
 # Gate consistency.
 gate=out['gate_decision']; open_block=[q['request_id'] for q in reqs if q['status']=='OPEN' and q['blocking']]
 revision_required=bool(rev)
 if out['model_impact']['revision_required']!=revision_required: issues.append(Issue('$.model_impact.revision_required',f'must be {revision_required} based on revision file'))
 if out['model_impact']['investigation_required']!=bool(open_block): issues.append(Issue('$.model_impact.investigation_required',f'must be {bool(open_block)} based on open blocking requests'))
 if gate['status']=='RETURN_TO_INVESTIGATION':
  if not open_block: issues.append(Issue('$.gate_decision','RETURN_TO_INVESTIGATION requires an OPEN blocking evidence request'))
  if gate['next_state']!='INVESTIGATION': issues.append(Issue('$.gate_decision.next_state','must be INVESTIGATION'))
 if gate['status']=='RETURN_TO_SYSTEM_MODEL':
  if not revision_required: issues.append(Issue('$.gate_decision','RETURN_TO_SYSTEM_MODEL requires revision directives'))
  if open_block: issues.append(Issue('$.gate_decision','cannot return to SYSTEM_MODEL while blocking evidence requests are open'))
  if gate['next_state']!='SYSTEM_MODEL': issues.append(Issue('$.gate_decision.next_state','must be SYSTEM_MODEL'))
 if gate['status']=='AWAITING_HUMAN_APPROVAL':
  if revision_required or open_block: issues.append(Issue('$.gate_decision','AWAITING_HUMAN_APPROVAL requires no revision or investigation'))
  if out['human_model_approval']['status']!='PENDING': issues.append(Issue('$.human_model_approval.status','must be PENDING'))
  if gate['next_state']!='MODEL_CRITIQUE': issues.append(Issue('$.gate_decision.next_state','must be MODEL_CRITIQUE'))
 if gate['status']=='READY_FOR_CHANGE_OPTIONS':
  if revision_required or open_block: issues.append(Issue('$.gate_decision','READY_FOR_CHANGE_OPTIONS requires no revision and no blocking request'))
  if out['human_model_approval']['status']!='APPROVED': issues.append(Issue('$.human_model_approval.status','READY_FOR_CHANGE_OPTIONS requires APPROVED human model approval'))
  if gate['next_state']!='SOLUTION_DESIGN': issues.append(Issue('$.gate_decision.next_state','must be SOLUTION_DESIGN'))
  if not all(out['coverage'].values()): issues.append(Issue('$.coverage','all coverage flags must be true for transition'))
  if out['metadata']['status']!='COMPLETE': issues.append(Issue('$.metadata.status','must be COMPLETE for transition'))
 if args.require_transition_ready and gate['status']!='READY_FOR_CHANGE_OPTIONS': issues.append(Issue('$.gate_decision.status','package is not transition-ready for SOLUTION_DESIGN'))
 return issues

def main():
 p=argparse.ArgumentParser(); p.add_argument('--kind',choices=['input','output','critique','assessment','revision','request','package'],required=True); p.add_argument('--file');
 for x in ['input','output','assessments','revisions','requests','model-output','elements','relations','traceability','ledger']: p.add_argument('--'+x)
 p.add_argument('--require-transition-ready',action='store_true'); a=p.parse_args()
 issues=[]
 if a.kind=='package':
  required=['input','output','assessments','revisions','requests','model_output','elements','relations','traceability','ledger']
  missing=[x for x in required if getattr(a,x,None) is None]
  if missing: p.error('missing package arguments: '+', '.join(missing))
  issues=validate_package(a)
 elif a.kind in {'assessment','revision','request'}:
  if not a.file: p.error('--file required')
  _,issues=load_jsonl(Path(a.file),a.kind,allow_empty=a.kind in {'revision','request'})
 else:
  if not a.file: p.error('--file required')
  issues=structural(load_doc(Path(a.file)),a.kind)
 if issues:
  print(f'INVALID ({len(issues)} issue(s))',file=sys.stderr)
  for i in issues: print('- '+str(i),file=sys.stderr)
  return 1
 print('VALID'+(' and transition-ready for SOLUTION_DESIGN' if a.kind=='package' and a.require_transition_ready else ''))
 return 0
if __name__=='__main__': raise SystemExit(main())
