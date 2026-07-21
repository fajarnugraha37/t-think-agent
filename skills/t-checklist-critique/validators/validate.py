#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sys,warnings
from collections import Counter
from datetime import date,datetime
from pathlib import Path
from typing import Any,Iterable
import yaml
warnings.filterwarnings('ignore',category=DeprecationWarning)
from jsonschema import Draft202012Validator,FormatChecker,RefResolver
ROOT=Path(__file__).resolve().parents[1]
FILES={'input':'input.schema.json','output':'output.schema.json','critique':'critique-request.schema.json','assessment':'assessment.schema.json','revision':'revision-directive.schema.json','request':'evidence-request.schema.json','approval':'checklist-approval.schema.json','checklist_contract':'approved-checklist-contract.schema.json','builder_output':'upstream-checklist-builder-output.schema.json','checklist':'upstream-checklist-item.schema.json','dependency':'upstream-checklist-dependency.schema.json','coverage':'upstream-checklist-coverage-row.schema.json','batch':'upstream-execution-batch.schema.json','finding':'upstream-checklist-finding.schema.json','plan_contract':'upstream-approved-plan-contract.schema.json','plan_critique_output':'upstream-plan-critique-output.schema.json','evidence':'upstream-evidence-record.schema.json','element':'upstream-model-element.schema.json','relation':'upstream-model-relation.schema.json'}
SCHEMAS={k:ROOT/'schemas'/v for k,v in FILES.items()}
class Issue:
 def __init__(self,path,message): self.path,self.message=path,message
 def __str__(self): return f'{self.path}: {self.message}'
def norm(v):
 if isinstance(v,(date,datetime)): return v.isoformat()
 if isinstance(v,dict): return {k:norm(x) for k,x in v.items()}
 if isinstance(v,list): return [norm(x) for x in v]
 return v
def doc(path):
 p=Path(path); t=p.read_text(encoding='utf-8'); return json.loads(t) if p.suffix.lower()=='.json' else norm(yaml.safe_load(t))
def schema(kind): return json.loads(SCHEMAS[kind].read_text())
def store():
 out={}
 for p in (ROOT/'schemas').glob('*.json'):
  d=json.loads(p.read_text());
  if '$id' in d: out[d['$id']]=d
  out[p.name]=d; out[p.as_uri()]=d
 return out
STORE=store()
def pjoin(prefix,parts): return prefix+''.join(f'[{x}]' if isinstance(x,int) else f'.{x}' for x in parts)
def structural(obj,kind,prefix='$'):
 s=schema(kind); r=RefResolver.from_schema(s,store=STORE); out=[]
 for e in sorted(Draft202012Validator(s,resolver=r,format_checker=FormatChecker()).iter_errors(obj),key=lambda x:list(x.absolute_path)): out.append(Issue(pjoin(prefix,e.absolute_path),e.message))
 return out
def jsonl(path,kind,empty=False):
 rows=[]; issues=[]
 for n,line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(),1):
  if not line.strip(): continue
  try: x=json.loads(line)
  except Exception as e: issues.append(Issue(f'{path}:{n}',f'invalid JSON: {e}')); continue
  rows.append(x); issues+=structural(x,kind,f'{path}:{n}$')
 if not rows and not empty: issues.append(Issue(str(path),'must contain at least one record'))
 return rows,issues
def coverage_rows(path):
 fields=['coverage_id','plan_id','operation_sequence','coverage_status','checklist_ids','verification_ids','rollback_ids','rationale']; rows=[]; issues=[]
 with Path(path).open(encoding='utf-8',newline='') as f:
  rd=csv.DictReader(f)
  if (rd.fieldnames or [])!=fields: return [],[Issue(f'{path}:headers',f'expected exactly {fields}')]
  for n,r in enumerate(rd,2):
   x=dict(r); x['operation_sequence']=int(x['operation_sequence'])
   for k in ['checklist_ids','verification_ids','rollback_ids']: x[k]=[z.strip() for z in x[k].split('|') if z.strip()]
   rows.append(x); issues+=structural(x,'coverage',f'{path}:{n}$')
 return rows,issues
def dup(rows,key,label):
 c=Counter(x.get(key) for x in rows if x.get(key)); return [Issue('$',f'duplicate {label}: {x}') for x,n in c.items() if n>1]
def digest(x): return 'sha256:'+hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def bundle(builder,checks,deps,cov,batches,findings): return digest({'checklist_builder_output':builder,'checklist_items':checks,'dependencies':deps,'coverage':cov,'batches':batches,'findings':findings})
def target_set(kind,checks,deps,cov,batches,builder,plancon):
 if kind in ['CHECKLIST_ITEM','CHECKLIST_ACTION','CHECKLIST_SCOPE','CHECKLIST_PRECONDITION','CHECKLIST_EXPECTED_RESULT','CHECKLIST_VERIFICATION_MAPPING','CHECKLIST_ROLLBACK_MAPPING','EXECUTION_GUARD']: return {x['checklist_id'] for x in checks}
 if kind=='CHECKLIST_DEPENDENCY': return {x['dependency_id'] for x in deps}
 if kind in ['EXECUTION_BATCH','HUMAN_GATE']: return {x['batch_id'] for x in batches}
 if kind=='OPERATION_COVERAGE': return {x['coverage_id'] for x in cov}
 return {builder['metadata']['builder_run_id'],plancon['contract_id']}
def expected_gate(assessments,revisions,requests,all_assessed,approval,contract,digest_ok,hg_ok):
 routes=[x['route'] for x in revisions]+[x['route'] for x in requests if x['blocking']]+[x['recommended_route'] for x in assessments if x['resulting_status'] in ['INVESTIGATION_REQUIRED','UPSTREAM_DECISION_REQUIRED']]
 priority=[('PROBLEM_ALIGNMENT','RETURN_TO_PROBLEM_ALIGNMENT','PROBLEM_ALIGNMENT'),('INVESTIGATION','RETURN_TO_INVESTIGATION','INVESTIGATION'),('SYSTEM_MODEL','RETURN_TO_SYSTEM_MODEL','SYSTEM_MODEL'),('SOLUTION_DESIGN','RETURN_TO_SOLUTION_DESIGN','SOLUTION_DESIGN'),('SOLUTION_CRITIQUE','RETURN_TO_SOLUTION_CRITIQUE','SOLUTION_CRITIQUE'),('PLAN_CRITIQUE','RETURN_TO_PLAN_CRITIQUE','PLAN_CRITIQUE'),('IMPLEMENTATION_PLAN','RETURN_TO_IMPLEMENTATION_PLAN','IMPLEMENTATION_PLAN'),('IMPLEMENTATION_CHECKLIST','RETURN_TO_IMPLEMENTATION_CHECKLIST','IMPLEMENTATION_CHECKLIST')]
 for route,gate,state in priority:
  if route in routes: return gate,state
 if not all_assessed: return 'BLOCKED','CHECKLIST_CRITIQUE'
 if approval['status']=='APPROVED' and approval['execution_authorization'] and contract['status']=='APPROVED' and digest_ok and hg_ok and not revisions and not requests: return 'READY_FOR_BOUNDED_IMPLEMENTATION','BOUNDED_IMPLEMENTATION'
 return 'BLOCKED','CHECKLIST_CRITIQUE'
def validate(a):
 issues=[]
 docs={k:doc(getattr(a,k)) for k in ['input','output','builder_output','plan_contract','plan_critique_output','approval','checklist_contract']}
 for k,kind in [('input','input'),('output','output'),('builder_output','builder_output'),('plan_contract','plan_contract'),('plan_critique_output','plan_critique_output'),('approval','approval'),('checklist_contract','checklist_contract')]: issues+=structural(docs[k],kind,f'$.{k}')
 checks,e=jsonl(a.checklists,'checklist'); issues+=e
 deps,e=jsonl(a.dependencies,'dependency',True); issues+=e
 cov,e=coverage_rows(a.coverage); issues+=e
 batches,e=jsonl(a.batches,'batch'); issues+=e
 findings,e=jsonl(a.findings,'finding',True); issues+=e
 ledger,e=jsonl(a.ledger,'evidence'); issues+=e
 elements,e=jsonl(a.elements,'element'); issues+=e
 relations,e=jsonl(a.relations,'relation',True); issues+=e
 assessments,e=jsonl(a.assessments,'assessment'); issues+=e
 revisions,e=jsonl(a.revisions,'revision',True); issues+=e
 requests,e=jsonl(a.requests,'request',True); issues+=e
 if issues: return issues
 inp,out,builder,plancon,pcrit,approval,contract=[docs[k] for k in ['input','output','builder_output','plan_contract','plan_critique_output','approval','checklist_contract']]
 for rows,key,label in [(checks,'checklist_id','checklist id'),(deps,'dependency_id','dependency id'),(cov,'coverage_id','coverage id'),(batches,'batch_id','batch id'),(findings,'finding_id','finding id'),(ledger,'id','evidence id'),(elements,'id','model element id'),(relations,'id','model relation id'),(assessments,'assessment_id','assessment id'),(revisions,'directive_id','directive id'),(requests,'request_id','request id')]: issues+=dup(rows,key,label)
 check_ids={x['checklist_id'] for x in checks}; dep_ids={x['dependency_id'] for x in deps}; cov_ids={x['coverage_id'] for x in cov}; batch_ids={x['batch_id'] for x in batches}; evidence_ids={x['id'] for x in ledger}; model_ids={x['id'] for x in elements}; critique_ids={x['critique_id'] for x in inp['human_critiques']}
 # Source binding and readiness.
 if builder['gate_decision']['status']!='READY_FOR_CHECKLIST_CRITIQUE' or builder['gate_decision']['next_state']!='CHECKLIST_CRITIQUE' or builder['execution_readiness']['status']!='READY': issues.append(Issue('$.builder_output','source checklist package is not ready for critique'))
 src=inp['source_checklist']; outsrc=out['source_checklist']
 expected={'builder_run_id':builder['metadata']['builder_run_id'],'artifact_version':builder['metadata']['version'],'gate_status':'READY_FOR_CHECKLIST_CRITIQUE','repository_commit':plancon['repository_snapshot']['commit_sha']}
 for k,v in expected.items():
  if src[k]!=v: issues.append(Issue(f'$.input.source_checklist.{k}',f'expected {v}'))
  if outsrc[k]!=v: issues.append(Issue(f'$.output.source_checklist.{k}',f'expected {v}'))
 if builder['source_plan_contract']['contract_id']!=plancon['contract_id'] or builder['source_plan_contract']['plan_bundle_digest']!=plancon['plan_bundle_digest']: issues.append(Issue('$.builder_output.source_plan_contract','does not match approved plan contract'))
 if pcrit['gate_decision']['status']!='READY_FOR_IMPLEMENTATION_CHECKLIST' or pcrit['approval_readiness']['status']!='READY': issues.append(Issue('$.plan_critique_output','must be approved and ready for checklist construction'))
 if plancon['status']!='APPROVED' or plancon['approval']['approver_role']!='HUMAN': issues.append(Issue('$.plan_contract','must be approved by a human'))
 # Artifact counts.
 countmap={'checklist_builder_output':1,'checklist_items':len(checks),'dependency_edges':len(deps),'coverage_matrix':len(cov),'execution_batches':len(batches),'checklist_findings':len(findings),'approved_plan_contract':1,'plan_critique_output':1,'evidence_ledger':len(ledger),'model_elements':len(elements),'model_relations':len(relations)}
 for k,n in countmap.items():
  if inp['source_artifacts'][k]['record_count']!=n: issues.append(Issue(f'$.input.source_artifacts.{k}.record_count',f'expected {n}'))
 # Critique target and evidence closure.
 critique_by={x['critique_id']:x for x in inp['human_critiques']}; counts=Counter(x['critique_id'] for x in assessments)
 if len(critique_ids)!=len(inp['human_critiques']): issues.append(Issue('$.input.human_critiques','duplicate critique id'))
 target_errors=False
 for c in inp['human_critiques']:
  allowed=target_set(c['target_kind'],checks,deps,cov,batches,builder,plancon)
  for tid in c['target_ids']:
   if tid not in allowed: target_errors=True; issues.append(Issue(f'$.critique[{c["critique_id"]}].target_ids',f'unknown target for {c["target_kind"]}: {tid}'))
  for eid in c['claimed_evidence_ids']:
   if eid not in evidence_ids: issues.append(Issue(f'$.critique[{c["critique_id"]}].claimed_evidence_ids',f'unknown evidence: {eid}'))
 for arow in assessments:
  cid=arow['critique_id']
  if cid not in critique_by: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}].critique_id',f'unknown critique: {cid}')); continue
  c=critique_by[cid]
  if set(arow['target_ids'])!=set(c['target_ids']): issues.append(Issue(f'$.assessment[{arow["assessment_id"]}].target_ids','must exactly match critique targets'))
  for eid in arow['evidence_reviewed']:
   if eid not in evidence_ids: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}].evidence_reviewed',f'unknown evidence: {eid}'))
  for mid in arow['model_ids']:
   if mid not in model_ids: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}].model_ids',f'unknown model element: {mid}'))
  if not arow['evidence_reviewed'] and not arow['source_artifact_refs']: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}]','material assessment requires evidence or source artifact references'))
  cl,rs=arow['classification'],arow['resulting_status']
  if cl=='REJECTED_WITH_EVIDENCE' and (not arow['evidence_reviewed'] or not arow['contradicting_findings'] or rs!='NO_CHANGE'): issues.append(Issue(f'$.assessment[{arow["assessment_id"]}]','rejection requires evidence, contradicting findings, and NO_CHANGE'))
  if cl=='REQUIRES_INVESTIGATION' and (rs!='INVESTIGATION_REQUIRED' or not arow['evidence_request_ids']): issues.append(Issue(f'$.assessment[{arow["assessment_id"]}]','investigation classification requires request IDs and INVESTIGATION_REQUIRED'))
  if rs=='CHECKLIST_REVISION_REQUIRED' and not arow['revision_directive_ids']: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}]','checklist revision requires directive IDs'))
  if rs=='NO_CHANGE' and (arow['revision_directive_ids'] or arow['evidence_request_ids']): issues.append(Issue(f'$.assessment[{arow["assessment_id"]}]','NO_CHANGE cannot carry open directive or evidence request'))
 # Directive and request closure.
 rev_by={x['directive_id']:x for x in revisions}; req_by={x['request_id']:x for x in requests}
 for arow in assessments:
  for x in arow['revision_directive_ids']:
   if x not in rev_by: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}].revision_directive_ids',f'unknown directive: {x}'))
  for x in arow['evidence_request_ids']:
   if x not in req_by: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}].evidence_request_ids',f'unknown request: {x}'))
 for r in revisions:
  if r['source_critique_id'] not in critique_by: issues.append(Issue(f'$.revision[{r["directive_id"]}]','unknown source critique'))
  elif not set(r['target_ids']).issubset(set(critique_by[r['source_critique_id']]['target_ids'])): issues.append(Issue(f'$.revision[{r["directive_id"]}].target_ids','must be subset of source critique targets'))
  for eid in r['evidence_ids']:
   if eid not in evidence_ids: issues.append(Issue(f'$.revision[{r["directive_id"]}].evidence_ids',f'unknown evidence: {eid}'))
  for mid in r['model_ids']:
   if mid not in model_ids: issues.append(Issue(f'$.revision[{r["directive_id"]}].model_ids',f'unknown model: {mid}'))
  if r['semantic_change_required'] and r['route']=='IMPLEMENTATION_CHECKLIST': issues.append(Issue(f'$.revision[{r["directive_id"]}]','semantic change cannot be resolved by Checklist Builder'))
 for q in requests:
  if q['source_critique_id'] not in critique_by: issues.append(Issue(f'$.request[{q["request_id"]}]','unknown source critique'))
  elif not set(q['target_ids']).issubset(set(critique_by[q['source_critique_id']]['target_ids'])): issues.append(Issue(f'$.request[{q["request_id"]}].target_ids','must be subset of source critique targets'))
 # Output summaries.
 ccount=Counter(x['classification'] for x in assessments); all_assessed=len(assessments)==len(critique_ids) and all(counts[x]==1 for x in critique_ids)
 summary={'total_critiques':len(critique_ids),'accepted':ccount['ACCEPTED'],'partially_accepted':ccount['PARTIALLY_ACCEPTED'],'rejected_with_evidence':ccount['REJECTED_WITH_EVIDENCE'],'requires_investigation':ccount['REQUIRES_INVESTIGATION'],'unassessed':len(critique_ids)-sum(1 for x in critique_ids if counts[x]==1)}
 if out['review_summary']!=summary: issues.append(Issue('$.output.review_summary','does not match assessments'))
 evidence_backed=all((x['evidence_reviewed'] or x['source_artifact_refs']) and (x['classification']!='REJECTED_WITH_EVIDENCE' or x['contradicting_findings']) for x in assessments)
 refs_valid=not target_errors and not any('unknown evidence' in x.message or 'unknown model' in x.message or 'unknown directive' in x.message or 'unknown request' in x.message for x in issues)
 expcov={'all_critiques_assessed':all_assessed,'all_targets_resolved':not target_errors,'all_references_valid':refs_valid,'all_material_responses_evidence_backed':evidence_backed}
 if out['coverage']!=expcov: issues.append(Issue('$.output.coverage','does not match computed coverage'))
 affected=sorted({t for x in assessments if x['resulting_status']!='NO_CHANGE' for t in x['target_ids']}); retained=sorted({t for x in assessments if x['resulting_status']=='NO_CHANGE' for t in x['target_ids']})
 impact=out['checklist_impact']
 if impact['revision_required']!=bool(revisions) or impact['investigation_required']!=bool(requests): issues.append(Issue('$.output.checklist_impact','revision/investigation flags do not match artifacts'))
 upstream=any(x['route'] in ['PROBLEM_ALIGNMENT','SYSTEM_MODEL','SOLUTION_DESIGN','SOLUTION_CRITIQUE','PLAN_CRITIQUE','IMPLEMENTATION_PLAN'] for x in revisions)
 if impact['upstream_decision_required']!=upstream or sorted(impact['affected_ids'])!=affected or sorted(impact['retained_ids'])!=retained: issues.append(Issue('$.output.checklist_impact','does not match assessment impact'))
 # Approval.
 agents={inp['metadata']['author_agent'],out['metadata']['author_agent']}
 if approval['builder_run_id']!=builder['metadata']['builder_run_id'] or approval['approved_checklist_version']!=builder['metadata']['version']: issues.append(Issue('$.approval','does not bind exact checklist run/version'))
 risk_ids=sorted({r for c in checks for r in c['risk_ids']}); gate_batches=sorted(x['batch_id'] for x in batches if x['human_gate_required'])
 if approval['status']=='APPROVED':
  if approval['approver_role']!='HUMAN' or not approval['approved_by'] or not approval['approved_at'] or not approval['execution_authorization']: issues.append(Issue('$.approval','APPROVED requires named HUMAN, timestamp, and execution authorization'))
  if approval['approved_by'] in agents: issues.append(Issue('$.approval.approved_by','executing agent cannot approve its own checklist critique'))
  if set(approval['resolved_critique_ids'])!=critique_ids: issues.append(Issue('$.approval.resolved_critique_ids','must exactly contain all critique IDs'))
  if set(approval['accepted_residual_risk_ids'])!=set(risk_ids): issues.append(Issue('$.approval.accepted_residual_risk_ids',f'expected {risk_ids}'))
  if set(approval['accepted_human_gate_batch_ids'])!=set(gate_batches): issues.append(Issue('$.approval.accepted_human_gate_batch_ids',f'expected {gate_batches}'))
  if revisions or requests or any(x['resulting_status']!='NO_CHANGE' for x in assessments): issues.append(Issue('$.approval.status','cannot approve while critique action remains'))
 elif approval['execution_authorization']: issues.append(Issue('$.approval.execution_authorization','non-approved record cannot authorize execution'))
 # Contract exactness.
 computed=bundle(builder,checks,deps,cov,batches,findings); digest_ok=contract['checklist_bundle_digest']==computed
 if not digest_ok: issues.append(Issue('$.checklist_contract.checklist_bundle_digest',f'expected {computed}'))
 if contract['source_builder_run_id']!=builder['metadata']['builder_run_id'] or contract['source_plan_contract_id']!=plancon['contract_id'] or contract['checklist_approval_id']!=approval['approval_id']: issues.append(Issue('$.checklist_contract','source bindings do not match'))
 if contract['repository_snapshot']!=plancon['repository_snapshot']: issues.append(Issue('$.checklist_contract.repository_snapshot','must match approved plan contract'))
 if contract['artifact_versions']!={'checklist_builder_output_version':builder['metadata']['version'],'approved_plan_contract_id':plancon['contract_id']}: issues.append(Issue('$.checklist_contract.artifact_versions','version binding mismatch'))
 if contract['source_plan_bundle_digest']!=plancon['plan_bundle_digest']: issues.append(Issue('$.checklist_contract.source_plan_bundle_digest','must match approved plan bundle digest'))
 for field,expected in [('checklist_item_ids',check_ids),('dependency_edge_ids',dep_ids),('coverage_row_ids',cov_ids),('execution_batch_ids',batch_ids)]:
  if set(contract[field])!=expected: issues.append(Issue(f'$.checklist_contract.{field}',f'expected exact IDs {sorted(expected)}'))
 expbindings=[{'checklist_id':c['checklist_id'],'source_plan_id':c['source_plan_id'],'operation_sequence':c['source_operation']['sequence'],'source_operation_digest':c['source_operation']['digest'],'checklist_item_digest':digest(c)} for c in checks]
 if contract['operation_bindings']!=expbindings: issues.append(Issue('$.checklist_contract.operation_bindings','must exactly freeze checklist item and source operation digests in source order'))
 if contract['execution_order']!=builder['dependency_analysis']['topological_order'] or contract['parallel_levels']!=builder['dependency_analysis']['parallel_levels']: issues.append(Issue('$.checklist_contract.execution_order','must match validated dependency analysis'))
 if contract['change_surface']!=plancon['change_surface'] or contract['decision_envelope']!=plancon['decision_envelope'] or contract['failure_budget']!=plancon['failure_budget'] or contract['implementation_constraints']!=plancon['implementation_constraints']: issues.append(Issue('$.checklist_contract','must preserve plan change surface, decision envelope, failure budget, and constraints'))
 if set(contract['human_gate_batch_ids'])!=set(gate_batches): issues.append(Issue('$.checklist_contract.human_gate_batch_ids',f'expected {gate_batches}'))
 if contract['accepted_residual_risk_ids']!=approval['accepted_residual_risk_ids'] or contract['accepted_limitations']!=approval['accepted_limitations']: issues.append(Issue('$.checklist_contract','risk and limitation acceptance must mirror human approval'))
 if contract['status']=='APPROVED':
  if approval['status']!='APPROVED': issues.append(Issue('$.checklist_contract.status','cannot be approved without human approval'))
  ca=contract['approval']
  if ca!={'status':'APPROVED','approved_by':approval['approved_by'],'approver_role':'HUMAN','approved_at':approval['approved_at'],'execution_authorization':True}: issues.append(Issue('$.checklist_contract.approval','must exactly mirror approved human authorization'))
 # Artifact counts and route.
 af=out['artifact_files']; expected_counts={'assessments':len(assessments),'revision_directives':len(revisions),'evidence_requests':len(requests),'checklist_approval':1,'approved_checklist_contract':1,'report':1}
 for k,n in expected_counts.items():
  if af[k]['record_count']!=n: issues.append(Issue(f'$.output.artifact_files.{k}.record_count',f'expected {n}'))
 hg_ok=set(approval['accepted_human_gate_batch_ids'])==set(gate_batches)
 gate,state=expected_gate(assessments,revisions,requests,all_assessed,approval,contract,digest_ok,hg_ok)
 gd=out['gate_decision']
 if gd['status']!=gate or gd['next_state']!=state: issues.append(Issue('$.output.gate_decision',f'expected {gate} -> {state}'))
 blocking_critiques=sorted({x['critique_id'] for x in assessments if x['resulting_status']!='NO_CHANGE'}|{x for x in critique_ids if counts[x]!=1})
 blocking_requests=sorted({x['directive_id'] for x in revisions}|{x['request_id'] for x in requests if x['blocking']})
 if sorted(gd['blocking_critique_ids'])!=blocking_critiques or sorted(gd['blocking_request_ids'])!=blocking_requests: issues.append(Issue('$.output.gate_decision','blocking IDs do not match open actions'))
 readiness={'status':'READY' if gate=='READY_FOR_BOUNDED_IMPLEMENTATION' else 'NOT_READY','human_approval_status':approval['status'],'checklist_contract_status':contract['status'],'all_blocking_critiques_resolved':not blocking_critiques,'all_revision_directives_absent':not revisions,'all_evidence_requests_closed_or_routed':not requests,'bundle_digest_valid':digest_ok,'execution_authorized':approval['status']=='APPROVED' and approval['execution_authorization'],'human_gates_accepted':hg_ok}
 if out['execution_authorization_readiness']!=readiness: issues.append(Issue('$.output.execution_authorization_readiness','does not match computed readiness'))
 if a.require_transition_ready and gate!='READY_FOR_BOUNDED_IMPLEMENTATION': issues.append(Issue('$.transition',f'package is not transition-ready; got {gate}'))
 return issues
def main():
 p=argparse.ArgumentParser(); p.add_argument('--kind',choices=['schema','input','output','critique','assessment','revision','request','approval','checklist_contract','package'],required=True); p.add_argument('--file')
 for x in ['input','output','builder-output','checklists','dependencies','coverage','batches','findings','plan-contract','plan-critique-output','ledger','elements','relations','assessments','revisions','requests','approval','checklist-contract']: p.add_argument('--'+x,dest=x.replace('-','_'))
 p.add_argument('--require-transition-ready',action='store_true'); a=p.parse_args(); issues=[]
 try:
  if a.kind=='schema':
   for path in sorted((ROOT/'schemas').glob('*.json')): Draft202012Validator.check_schema(json.loads(path.read_text()))
  elif a.kind=='package':
   req=['input','output','builder_output','checklists','dependencies','coverage','batches','findings','plan_contract','plan_critique_output','ledger','elements','relations','assessments','revisions','requests','approval','checklist_contract']; miss=[x for x in req if not getattr(a,x)]
   issues=[Issue('$','missing package arguments: '+', '.join(miss))] if miss else validate(a)
  else:
   if not a.file: issues=[Issue('$','--file is required')]
   else: issues=structural(doc(a.file),a.kind)
 except Exception as e: issues=[Issue('$',f'validator failure: {type(e).__name__}: {e}')]
 if issues:
  for x in issues: print(x,file=sys.stderr)
  return 1
 print('VALID')
 if a.kind=='package' and a.require_transition_ready: print('Package is transition-ready for BOUNDED_IMPLEMENTATION')
 return 0
if __name__=='__main__': raise SystemExit(main())
