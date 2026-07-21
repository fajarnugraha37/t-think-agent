#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT=Path(__file__).resolve().parents[1]
SCHEMA_FILES={
 'input':'input.schema.json','output':'output.schema.json','critique':'critique-request.schema.json','assessment':'assessment.schema.json',
 'revision':'revision-directive.schema.json','request':'evidence-request.schema.json','approval':'decision-approval.schema.json',
 'contract':'approved-solution-contract.schema.json','design_output':'upstream-solution-design-output.schema.json',
 'option':'upstream-solution-option.schema.json','coverage':'upstream-coverage-row.schema.json','decision':'upstream-decision-record.schema.json',
 'dominance':'upstream-dominance-proof.schema.json','evidence':'upstream-evidence-record.schema.json',
 'element':'upstream-model-element.schema.json','relation':'upstream-model-relation.schema.json'}
SCHEMAS={k:ROOT/'schemas'/v for k,v in SCHEMA_FILES.items()}

class Issue:
 def __init__(self,path:str,message:str): self.path,self.message=path,message
 def __str__(self): return f'{self.path}: {self.message}'

def normalize(v:Any)->Any:
 if isinstance(v,(date,datetime)): return v.isoformat()
 if isinstance(v,dict): return {k:normalize(x) for k,x in v.items()}
 if isinstance(v,list): return [normalize(x) for x in v]
 return v

def load_doc(path:Path)->Any:
 text=path.read_text(encoding='utf-8')
 return json.loads(text) if path.suffix.lower()=='.json' else normalize(yaml.safe_load(text))

def get_schema(kind:str)->dict:
 s=json.loads(SCHEMAS[kind].read_text(encoding='utf-8'))
 if kind=='input': s['properties']['human_critiques']['items']=json.loads(SCHEMAS['critique'].read_text(encoding='utf-8'))
 return s

def pjoin(prefix:str, parts:Iterable[Any])->str:
 return prefix+''.join(f'[{p}]' if isinstance(p,int) else f'.{p}' for p in parts)

def structural(obj:Any,kind:str,prefix='$')->list[Issue]:
 out=[]; v=Draft202012Validator(get_schema(kind),format_checker=FormatChecker())
 for e in sorted(v.iter_errors(obj),key=lambda x:list(x.absolute_path)):
  out.append(Issue(pjoin(prefix,e.absolute_path),e.message))
 return out

def load_jsonl(path:Path,kind:str,allow_empty=False):
 rows=[]; issues=[]
 for n,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
  if not line.strip(): continue
  try: obj=json.loads(line)
  except json.JSONDecodeError as e: issues.append(Issue(f'{path}:{n}',f'invalid JSON: {e.msg}')); continue
  rows.append(obj); issues.extend(structural(obj,kind,f'{path}:{n}$'))
 if not rows and not allow_empty: issues.append(Issue(str(path),'must contain at least one record'))
 return rows,issues

def split_ids(v:str)->list[str]: return [x.strip() for x in (v or '').split('|') if x.strip()]

def load_coverage(path:Path):
 rows=[]; issues=[]
 required={'coverage_id','option_id','target_id','coverage_status','mechanism','evidence_ids','model_ids','limitations','verification_ids'}
 with path.open(encoding='utf-8',newline='') as f:
  reader=csv.DictReader(f)
  if set(reader.fieldnames or [])!=required: return [],[Issue(f'{path}:headers',f'expected exactly {sorted(required)}')]
  for n,row in enumerate(reader,2):
   obj=dict(row)
   for k in ['evidence_ids','model_ids','verification_ids']: obj[k]=split_ids(obj.get(k,''))
   rows.append(obj); issues.extend(structural(obj,'coverage',f'{path}:{n}$'))
 return rows,issues

def duplicates(rows,key,label):
 c=Counter(r.get(key) for r in rows if r.get(key)); return [Issue('$',f'duplicate {label}: {x}') for x,n in c.items() if n>1]

def canonical_digest(obj:Any)->str:
 raw=json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
 return 'sha256:'+hashlib.sha256(raw).hexdigest()

def target_exists(ref:str,option_ids:set[str],coverage_ids:set[str],decision_id:str)->bool:
 if ref.startswith('OPT-'): return ref in option_ids
 if ref.startswith('SCOV-'): return ref in coverage_ids
 if ref.startswith('DEC-'): return ref==decision_id
 return ref in {'DOMINANCE-PROOF','SOLUTION-DESIGN-OUTPUT'}

def validate_package(a)->list[Issue]:
 issues=[]
 inp=load_doc(Path(a.input)); out=load_doc(Path(a.output)); approval=load_doc(Path(a.approval)); contract=load_doc(Path(a.contract))
 design_out=load_doc(Path(a.design_output)); decision=load_doc(Path(a.decision)); dominance=load_doc(Path(a.dominance))
 for obj,kind,prefix in [(inp,'input','$.input'),(out,'output','$.output'),(approval,'approval','$.approval'),(contract,'contract','$.contract'),(design_out,'design_output','$.design_output'),(decision,'decision','$.decision'),(dominance,'dominance','$.dominance')]: issues+=structural(obj,kind,prefix)
 assessments,e=load_jsonl(Path(a.assessments),'assessment'); issues+=e
 revisions,e=load_jsonl(Path(a.revisions),'revision',allow_empty=True); issues+=e
 requests,e=load_jsonl(Path(a.requests),'request',allow_empty=True); issues+=e
 options,e=load_jsonl(Path(a.options),'option'); issues+=e
 ledger,e=load_jsonl(Path(a.ledger),'evidence'); issues+=e
 elements,e=load_jsonl(Path(a.elements),'element'); issues+=e
 relations,e=load_jsonl(Path(a.relations),'relation',allow_empty=True); issues+=e
 coverage,e=load_coverage(Path(a.coverage)); issues+=e
 if issues: return issues

 critiques=inp['human_critiques']; critique_ids={x['critique_id'] for x in critiques}; critique_by={x['critique_id']:x for x in critiques}
 option_ids={x['option_id'] for x in options}; option_by={x['option_id']:x for x in options}; active_ids={x['option_id'] for x in options if x['status']=='ACTIVE'}
 viable_ids={x['option_id'] for x in options if x['status']=='ACTIVE' and x['viability'] in {'VIABLE','CONDITIONALLY_VIABLE'}}
 coverage_ids={x['coverage_id'] for x in coverage}; evidence_ids={x['id'] for x in ledger}; element_ids={x['id'] for x in elements}; relation_ids={x['id'] for x in relations}
 decision_id=decision['decision_id']; assessment_ids={x['assessment_id'] for x in assessments}; revision_ids={x['directive_id'] for x in revisions}; request_ids={x['request_id'] for x in requests}
 issues+=duplicates(critiques,'critique_id','critique id')+duplicates(assessments,'assessment_id','assessment id')+duplicates(revisions,'directive_id','revision id')+duplicates(requests,'request_id','request id')

 # Upstream binding and gate.
 if design_out['gate_decision']['status']!='READY_FOR_SOLUTION_CRITIQUE': issues.append(Issue('$.design_output.gate_decision.status','must be READY_FOR_SOLUTION_CRITIQUE'))
 if inp['source_solution_design']['design_id']!=design_out['metadata']['design_id']: issues.append(Issue('$.input.source_solution_design.design_id','does not match design output'))
 if inp['source_solution_design']['artifact_version']!=design_out['metadata']['version']: issues.append(Issue('$.input.source_solution_design.artifact_version','does not match design output'))
 if out['source_solution_design']['design_id']!=inp['source_solution_design']['design_id']: issues.append(Issue('$.output.source_solution_design.design_id','does not match input'))
 if out['source_solution_design']['artifact_version']!=inp['source_solution_design']['artifact_version']: issues.append(Issue('$.output.source_solution_design.artifact_version','does not match input'))
 if set(decision['candidate_option_ids'])!=active_ids: issues.append(Issue('$.decision.candidate_option_ids','must exactly match active option ids'))

 # Validate critique targets and evidence.
 for c in critiques:
  for ref in c['target_ids']:
   if not target_exists(ref,option_ids,coverage_ids,decision_id): issues.append(Issue(f'$.critique[{c["critique_id"]}].target_ids',f'unknown target: {ref}'))
  for ref in c['claimed_evidence_ids']:
   if ref not in evidence_ids: issues.append(Issue(f'$.critique[{c["critique_id"]}].claimed_evidence_ids',f'unknown evidence: {ref}'))

 # Every critique exactly once and assessment rules.
 assessed=[x['critique_id'] for x in assessments]
 for cid in critique_ids:
  n=assessed.count(cid)
  if n!=1: issues.append(Issue('$.assessments',f'critique {cid} must have exactly one assessment, found {n}'))
 unresolved_status={'SOLUTION_REVISION_REQUIRED','DECISION_REVISION_REQUIRED','DOMINANCE_REVISION_REQUIRED','INVESTIGATION_REQUIRED','MODEL_REVISION_REQUIRED','PROBLEM_REALIGNMENT_REQUIRED','CLARIFICATION_REQUIRED'}
 for s in assessments:
  sid=s['assessment_id']; cid=s['critique_id']
  if cid not in critique_ids: issues.append(Issue(f'$.assessment[{sid}].critique_id',f'unknown critique: {cid}')); continue
  if set(s['target_ids'])!=set(critique_by[cid]['target_ids']): issues.append(Issue(f'$.assessment[{sid}].target_ids',f'must exactly match critique {cid} targets'))
  for ref in s['target_ids']+s['solution_items_reviewed']:
   if not target_exists(ref,option_ids,coverage_ids,decision_id): issues.append(Issue(f'$.assessment[{sid}]',f'unknown solution item: {ref}'))
  for ref in s['evidence_reviewed']:
   if ref not in evidence_ids: issues.append(Issue(f'$.assessment[{sid}].evidence_reviewed',f'unknown evidence: {ref}'))
  for ref in s['revision_directive_ids']:
   if ref not in revision_ids: issues.append(Issue(f'$.assessment[{sid}].revision_directive_ids',f'unknown revision directive: {ref}'))
  for ref in s['investigation_request_ids']:
   if ref not in request_ids: issues.append(Issue(f'$.assessment[{sid}].investigation_request_ids',f'unknown evidence request: {ref}'))
  if s['classification']=='REJECTED_WITH_EVIDENCE':
   if not s['evidence_reviewed']: issues.append(Issue(f'$.assessment[{sid}]','REJECTED_WITH_EVIDENCE requires evidence_reviewed'))
   if not s['contradicting_findings']: issues.append(Issue(f'$.assessment[{sid}]','REJECTED_WITH_EVIDENCE requires contradicting_findings'))
  if s['classification']=='REQUIRES_INVESTIGATION':
   if s['resulting_status']!='INVESTIGATION_REQUIRED': issues.append(Issue(f'$.assessment[{sid}].resulting_status','REQUIRES_INVESTIGATION requires INVESTIGATION_REQUIRED'))
   if not s['investigation_request_ids']: issues.append(Issue(f'$.assessment[{sid}]','REQUIRES_INVESTIGATION requires an evidence request'))
  if s['resulting_status'] in {'SOLUTION_REVISION_REQUIRED','DECISION_REVISION_REQUIRED','DOMINANCE_REVISION_REQUIRED'} and not s['revision_directive_ids']:
   issues.append(Issue(f'$.assessment[{sid}]',f'{s["resulting_status"]} requires a revision directive'))
  if s['resulting_status'] in {'INVESTIGATION_REQUIRED','MODEL_REVISION_REQUIRED'} and not s['investigation_request_ids']:
   issues.append(Issue(f'$.assessment[{sid}]',f'{s["resulting_status"]} requires an evidence request'))

 # Revision and request references. Directives are proposals only.
 artifact_target={'OPTION':'OPT-','COVERAGE_MATRIX':'SCOV-','DECISION_RECORD':'DEC-','DOMINANCE_PROOF':'DOMINANCE-PROOF','SOLUTION_DESIGN_OUTPUT':'SOLUTION-DESIGN-OUTPUT'}
 for r in revisions:
  rid=r['directive_id']
  for cid in r['trigger_critique_ids']:
   if cid not in critique_ids: issues.append(Issue(f'$.revision[{rid}]',f'unknown critique: {cid}'))
  for eid in r['evidence_ids']:
   if eid not in evidence_ids: issues.append(Issue(f'$.revision[{rid}]',f'unknown evidence: {eid}'))
  if not target_exists(r['target_id'],option_ids,coverage_ids,decision_id) and r['operation']!='ADD': issues.append(Issue(f'$.revision[{rid}].target_id',f'unknown target: {r["target_id"]}'))
  expected=artifact_target[r['target_artifact']]
  if expected.endswith('-') and not r['target_id'].startswith(expected): issues.append(Issue(f'$.revision[{rid}].target_id',f'does not match target_artifact {r["target_artifact"]}'))
  if not expected.endswith('-') and r['target_id']!=expected: issues.append(Issue(f'$.revision[{rid}].target_id',f'must be {expected}'))
 for q in requests:
  qid=q['request_id']
  for cid in q['trigger_critique_ids']:
   if cid not in critique_ids: issues.append(Issue(f'$.request[{qid}]',f'unknown critique: {cid}'))

 # Decision approval.
 if approval['source_decision_id']!=decision_id: issues.append(Issue('$.approval.source_decision_id','does not match source decision'))
 if set(approval['candidate_option_ids'])!=active_ids: issues.append(Issue('$.approval.candidate_option_ids','must exactly match active option ids'))
 selected=approval['selected_option_id']; selected_opt=option_by.get(selected) if selected else None
 if inp['decision_context']['proposed_selected_option_id'] is not None and selected is not None and selected!=inp['decision_context']['proposed_selected_option_id']:
  issues.append(Issue('$.approval.selected_option_id','does not match human proposed selection in input'))
 if selected is not None and selected not in active_ids: issues.append(Issue('$.approval.selected_option_id','must reference an active option'))
 if selected is not None and selected not in viable_ids: issues.append(Issue('$.approval.selected_option_id','must reference a viable or conditionally viable option'))
 if selected in approval['rejected_option_ids']: issues.append(Issue('$.approval.rejected_option_ids','must not include selected option'))
 if set(approval['rejected_option_ids']) - active_ids: issues.append(Issue('$.approval.rejected_option_ids','contains unknown or inactive option'))
 if approval['status']=='APPROVED' and inp['decision_context']['requested_action']!='REVIEW_AND_SELECT': issues.append(Issue('$.approval.status','APPROVED requires REVIEW_AND_SELECT input action'))
 if approval['status']=='APPROVED' and approval['approved_by']==inp['metadata']['author_agent']: issues.append(Issue('$.approval.approved_by','human approver must not be the executing agent'))

 required_risks=set(); required_assumptions=set(); full_cover=False
 if selected_opt:
  required_risks={x['risk_id'] for x in selected_opt['residual_risks'] if x['acceptance_required']}
  required_assumptions=set(selected_opt['assumption_ids'])|{x['assumption_id'] for x in selected_opt['new_assumptions']}
  full_cover=all(any(r['option_id']==selected and r['target_id']==tid and r['coverage_status']=='FULL' for r in coverage) for tid in selected_opt['target_ids'])
  if not required_risks.issubset(set(approval['accepted_risk_ids'])): issues.append(Issue('$.approval.accepted_risk_ids',f'missing required risks: {sorted(required_risks-set(approval["accepted_risk_ids"]))}'))
  if not required_assumptions.issubset(set(approval['accepted_assumption_ids'])): issues.append(Issue('$.approval.accepted_assumption_ids',f'missing required assumptions: {sorted(required_assumptions-set(approval["accepted_assumption_ids"]))}'))
  if approval['status']=='APPROVED' and not full_cover: issues.append(Issue('$.approval.status','selected option must have FULL coverage for every target'))

 # Contract binding and exact semantic copy.
 if contract['source_design_id']!=design_out['metadata']['design_id']: issues.append(Issue('$.contract.source_design_id','does not match design output'))
 if contract['source_decision_id']!=decision_id: issues.append(Issue('$.contract.source_decision_id','does not match source decision'))
 if contract['decision_approval_id']!=approval['decision_approval_id']: issues.append(Issue('$.contract.decision_approval_id','does not match approval'))
 if selected and contract['selected_option_id']!=selected: issues.append(Issue('$.contract.selected_option_id','does not match approved selection'))
 if selected_opt:
  expected_digest=canonical_digest(selected_opt)
  if contract['selected_option_digest']!=expected_digest: issues.append(Issue('$.contract.selected_option_digest',f'expected {expected_digest}'))
  exact_lists={'problem_ids':selected_opt['problem_ids'],'target_ids':selected_opt['target_ids'],'model_ids':selected_opt['model_ids'],'evidence_ids':selected_opt['evidence_ids'],'invariant_ids':selected_opt['invariant_ids']}
  for k,v in exact_lists.items():
   if set(contract[k])!=set(v): issues.append(Issue(f'$.contract.{k}',f'must exactly match selected option {k}'))
  behavior=contract['behavior_commitments']; srcb=selected_opt['behavioral_effects']
  expected_behavior={'target_behavior':srcb['target_behavior'],'preserved_behavior':srcb['preserved_behavior'],'intentionally_changed_behavior':srcb['intentionally_changed_behavior'],'failure_semantics':selected_opt['failure_semantics'],'transaction_semantics':selected_opt['transaction_semantics'],'concurrency_semantics':selected_opt['concurrency_semantics']}
  for k,v in expected_behavior.items():
   if behavior[k]!=v: issues.append(Issue(f'$.contract.behavior_commitments.{k}','must exactly match selected option'))
  for k in ['components','files_or_artifacts','public_contract_changes','data_changes','configuration_changes','dependencies']:
   if contract['change_surface'][k]!=selected_opt['change_surface'][k]: issues.append(Issue(f'$.contract.change_surface.{k}','must exactly match selected option'))
 if set(contract['accepted_risk_ids'])!=set(approval['accepted_risk_ids']): issues.append(Issue('$.contract.accepted_risk_ids','must match approval'))
 if set(contract['accepted_assumption_ids'])!=set(approval['accepted_assumption_ids']): issues.append(Issue('$.contract.accepted_assumption_ids','must match approval'))
 if approval['status']=='APPROVED':
  if contract['status']!='APPROVED': issues.append(Issue('$.contract.status','must be APPROVED when human decision is approved'))
  if contract['approval']['approved_by']!=approval['approved_by'] or contract['approval']['approved_at']!=approval['approved_at'] or contract['approval']['approved_by_role']!=approval['approved_by_role']: issues.append(Issue('$.contract.approval','must match human approval'))

 # Summaries and file counts.
 cc=Counter(x['classification'] for x in assessments); summary=out['review_summary']
 expected_summary={'total_critiques':len(critiques),'accepted':cc['ACCEPTED'],'partially_accepted':cc['PARTIALLY_ACCEPTED'],'rejected_with_evidence':cc['REJECTED_WITH_EVIDENCE'],'requires_investigation':cc['REQUIRES_INVESTIGATION'],'unassessed':sum(1 for cid in critique_ids if cid not in assessed)}
 for k,v in expected_summary.items():
  if summary[k]!=v: issues.append(Issue(f'$.output.review_summary.{k}',f'expected {v}, got {summary[k]}'))
 expected_counts={'assessments':len(assessments),'revision_directives':len(revisions),'evidence_requests':len(requests),'decision_approval':1,'approved_solution_contract':1,'report':1}
 for k,v in expected_counts.items():
  if out['artifact_files'][k]['record_count']!=v: issues.append(Issue(f'$.output.artifact_files.{k}.record_count',f'expected {v}'))

 statuses={x['resulting_status'] for x in assessments}
 affected_opts=sorted({ref for x in assessments for ref in x['target_ids'] if ref.startswith('OPT-')})
 affected_cov=sorted({ref for x in assessments for ref in x['target_ids'] if ref.startswith('SCOV-')})
 affected_dec=sorted({ref for x in assessments for ref in x['target_ids'] if ref.startswith('DEC-')})
 impact=out['solution_impact']
 expected_impact={
  'solution_revision_required':bool(statuses & {'SOLUTION_REVISION_REQUIRED','DECISION_REVISION_REQUIRED','DOMINANCE_REVISION_REQUIRED'}),
  'investigation_required':'INVESTIGATION_REQUIRED' in statuses,
  'model_revision_required':'MODEL_REVISION_REQUIRED' in statuses,
  'problem_realignment_required':'PROBLEM_REALIGNMENT_REQUIRED' in statuses,
  'affected_option_ids':affected_opts,'affected_coverage_ids':affected_cov,'affected_decision_ids':affected_dec,
  'dominance_affected':any('DOMINANCE-PROOF' in x['target_ids'] for x in assessments),
  'retained_option_ids':sorted(active_ids)
 }
 for k,v in expected_impact.items():
  got=sorted(impact[k]) if isinstance(v,list) else impact[k]
  if got!=v: issues.append(Issue(f'$.output.solution_impact.{k}',f'expected {v}, got {got}'))

 unresolved=[x for x in assessments if x['resulting_status'] in unresolved_status]
 blocking_unresolved=[x['critique_id'] for x in assessments if x['resulting_status'] in unresolved_status or (critique_by[x['critique_id']]['severity']=='BLOCKING' and x['resulting_status']!='RETAINED')]
 all_risks=selected_opt is not None and required_risks.issubset(set(approval['accepted_risk_ids']))
 all_assumptions=selected_opt is not None and required_assumptions.issubset(set(approval['accepted_assumption_ids']))
 selection_permitted=not unresolved and selected_opt is not None and selected in viable_ids and full_cover
 dr=out['decision_readiness']
 expected_dr={'selection_permitted':selection_permitted,'selected_option_id':selected,'selected_option_active':selected in active_ids if selected else False,'selected_option_viable':selected in viable_ids if selected else False,'all_blocking_critiques_resolved':not blocking_unresolved,'all_required_risks_accepted':bool(all_risks),'all_required_assumptions_accepted':bool(all_assumptions),'selected_option_fully_covers_required_targets':bool(full_cover),'approved_solution_contract_ready':approval['status']=='APPROVED' and contract['status']=='APPROVED' and not unresolved and bool(full_cover) and bool(all_risks) and bool(all_assumptions)}
 for k,v in expected_dr.items():
  if dr[k]!=v: issues.append(Issue(f'$.output.decision_readiness.{k}',f'expected {v}, got {dr[k]}'))
 hs=out['human_solution_approval']
 if hs['status']!=approval['status'] or hs['decision_approval_id']!=approval['decision_approval_id'] or hs['selected_option_id']!=selected: issues.append(Issue('$.output.human_solution_approval','must summarize decision approval exactly'))
 if approval['status']=='APPROVED':
  if hs.get('solution_contract_id')!=contract['contract_id'] or hs.get('approved_by')!=approval['approved_by'] or hs.get('approved_at')!=approval['approved_at']: issues.append(Issue('$.output.human_solution_approval','approved summary must match contract and approval'))

 # Gate routing priority.
 gate=out['gate_decision']; expected_gate=None; expected_state=None
 if 'PROBLEM_REALIGNMENT_REQUIRED' in statuses: expected_gate,expected_state='RETURN_TO_PROBLEM_ALIGNMENT','PROBLEM_ALIGNMENT'
 elif 'INVESTIGATION_REQUIRED' in statuses: expected_gate,expected_state='RETURN_TO_INVESTIGATION','INVESTIGATION'
 elif 'MODEL_REVISION_REQUIRED' in statuses: expected_gate,expected_state='RETURN_TO_SYSTEM_MODEL','SYSTEM_MODEL'
 elif statuses & {'SOLUTION_REVISION_REQUIRED','DECISION_REVISION_REQUIRED','DOMINANCE_REVISION_REQUIRED'}: expected_gate,expected_state='RETURN_TO_SOLUTION_DESIGN','SOLUTION_DESIGN'
 elif selected is None: expected_gate,expected_state='AWAITING_HUMAN_SELECTION','SOLUTION_CRITIQUE'
 elif approval['status']!='APPROVED': expected_gate,expected_state='AWAITING_HUMAN_APPROVAL','SOLUTION_CRITIQUE'
 else: expected_gate,expected_state='READY_FOR_IMPLEMENTATION_PLAN','IMPLEMENTATION_PLAN'
 if gate['status']!=expected_gate: issues.append(Issue('$.output.gate_decision.status',f'expected {expected_gate}, got {gate["status"]}'))
 if gate['next_state']!=expected_state: issues.append(Issue('$.output.gate_decision.next_state',f'expected {expected_state}, got {gate["next_state"]}'))
 open_blocking_requests=sorted(x['request_id'] for x in requests if x['blocking'] and x['status']=='OPEN')
 if sorted(gate['blocking_request_ids'])!=open_blocking_requests: issues.append(Issue('$.output.gate_decision.blocking_request_ids',f'expected {open_blocking_requests}'))
 if sorted(gate['blocking_critique_ids'])!=sorted(blocking_unresolved): issues.append(Issue('$.output.gate_decision.blocking_critique_ids',f'expected {sorted(blocking_unresolved)}'))
 if expected_gate=='READY_FOR_IMPLEMENTATION_PLAN':
  if out['metadata']['status']!='COMPLETE': issues.append(Issue('$.output.metadata.status','must be COMPLETE for transition'))
  if not all(out['coverage'].values()): issues.append(Issue('$.output.coverage','all checks must be true for transition'))
  if not expected_dr['approved_solution_contract_ready']: issues.append(Issue('$.output.decision_readiness','approved solution contract is not ready'))
 if a.require_transition_ready and expected_gate!='READY_FOR_IMPLEMENTATION_PLAN': issues.append(Issue('$.output.gate_decision.status','package is not transition-ready for IMPLEMENTATION_PLAN'))
 return issues

def main():
 p=argparse.ArgumentParser(description='Validate Solution Critique artifacts')
 p.add_argument('--kind',required=True,choices=['input','output','critique','assessment','revision','request','approval','contract','option','coverage','decision','dominance','package'])
 p.add_argument('--file')
 for x in ['input','output','assessments','revisions','requests','approval','contract','design-output','options','coverage','decision','dominance','ledger','elements','relations']: p.add_argument('--'+x)
 p.add_argument('--require-transition-ready',action='store_true')
 a=p.parse_args()
 if a.kind=='package':
  needed=['input','output','assessments','revisions','requests','approval','contract','design_output','options','coverage','decision','dominance','ledger','elements','relations']
  miss=[x for x in needed if getattr(a,x,None) is None]
  if miss: p.error('missing package arguments: '+', '.join(miss))
  issues=validate_package(a)
 elif a.kind in {'assessment','revision','request','option'}:
  if not a.file: p.error('--file required')
  _,issues=load_jsonl(Path(a.file),a.kind,allow_empty=a.kind in {'revision','request'})
 elif a.kind=='coverage':
  if not a.file: p.error('--file required')
  _,issues=load_coverage(Path(a.file))
 else:
  if not a.file: p.error('--file required')
  issues=structural(load_doc(Path(a.file)),a.kind)
 if issues:
  print(f'INVALID ({len(issues)} issue(s))',file=sys.stderr)
  for i in issues: print('- '+str(i),file=sys.stderr)
  return 1
 print('VALID'+(' and transition-ready for IMPLEMENTATION_PLAN' if a.kind=='package' and a.require_transition_ready else ''))
 return 0
if __name__=='__main__': raise SystemExit(main())
