#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, sys, warnings
from collections import Counter, deque
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
import yaml
warnings.filterwarnings('ignore', category=DeprecationWarning)
from jsonschema import Draft202012Validator, FormatChecker, RefResolver

ROOT=Path(__file__).resolve().parents[1]
SCHEMA_FILES={
 'input':'input.schema.json','output':'output.schema.json','critique':'critique-request.schema.json','assessment':'assessment.schema.json',
 'revision':'revision-directive.schema.json','request':'evidence-request.schema.json','approval':'plan-approval.schema.json','plan_contract':'approved-plan-contract.schema.json',
 'planning_output':'upstream-planning-output.schema.json','target':'upstream-planning-target.schema.json','plan':'upstream-plan-item.schema.json','dependency':'upstream-dependency-edge.schema.json','coverage':'upstream-coverage-row.schema.json','verification':'upstream-verification-item.schema.json','rollback':'upstream-rollback-item.schema.json','finding':'upstream-planning-finding.schema.json','solution_contract':'upstream-approved-solution-contract.schema.json','evidence':'upstream-evidence-record.schema.json','element':'upstream-model-element.schema.json','relation':'upstream-model-relation.schema.json'}
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

def load_schema(kind:str)->dict: return json.loads(SCHEMAS[kind].read_text(encoding='utf-8'))

def schema_store()->dict:
 store={}
 for p in (ROOT/'schemas').glob('*.json'):
  d=json.loads(p.read_text(encoding='utf-8'))
  if '$id' in d: store[d['$id']]=d
  store[p.name]=d
  store[p.as_uri()]=d
 return store
STORE=schema_store()

def pjoin(prefix:str,parts:Iterable[Any])->str: return prefix+''.join(f'[{p}]' if isinstance(p,int) else f'.{p}' for p in parts)

def structural(obj:Any,kind:str,prefix='$')->list[Issue]:
 s=load_schema(kind); resolver=RefResolver.from_schema(s,store=STORE)
 out=[]
 for e in sorted(Draft202012Validator(s,resolver=resolver,format_checker=FormatChecker()).iter_errors(obj),key=lambda x:list(x.absolute_path)):
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
 fields=['coverage_id','planning_target_id','coverage_status','plan_ids','verification_ids','rollback_ids','rationale']
 rows=[]; issues=[]
 with path.open(encoding='utf-8',newline='') as f:
  reader=csv.DictReader(f)
  if (reader.fieldnames or [])!=fields: return [],[Issue(f'{path}:headers',f'expected exactly {fields}')]
  for n,row in enumerate(reader,2):
   obj=dict(row)
   for k in ['plan_ids','verification_ids','rollback_ids']: obj[k]=split_ids(obj[k])
   rows.append(obj); issues.extend(structural(obj,'coverage',f'{path}:{n}$'))
 return rows,issues

def duplicate_issues(rows,key,label):
 c=Counter(r.get(key) for r in rows if r.get(key)); return [Issue('$',f'duplicate {label}: {x}') for x,n in c.items() if n>1]

def canonical_bundle_digest(planning_output,targets,plans,deps,coverage,verifs,rollbacks,findings):
 payload={'planning_output':planning_output,'targets':targets,'plans':plans,'dependencies':deps,'coverage':coverage,'verifications':verifs,'rollbacks':rollbacks,'findings':findings}
 raw=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
 return 'sha256:'+hashlib.sha256(raw).hexdigest()

def graph_topology(plan_ids:set[str],edges:list[dict]):
 indeg={x:0 for x in plan_ids}; adj={x:[] for x in plan_ids}; refs_valid=True
 for e in edges:
  a,b=e['from_plan_id'],e['to_plan_id']
  if a not in plan_ids or b not in plan_ids or a==b: refs_valid=False; continue
  adj[a].append(b); indeg[b]+=1
 q=deque(sorted(x for x,d in indeg.items() if d==0)); order=[]
 while q:
  x=q.popleft(); order.append(x)
  for z in sorted(adj[x]):
   indeg[z]-=1
   if indeg[z]==0:
    q.append(z); q=deque(sorted(q))
 return refs_valid,len(order)==len(plan_ids),order

def expected_gate(assessments,revisions,requests,all_assessed,approval,contract,digest_valid):
 routes=[]
 routes += [r['route'] for r in revisions]
 routes += [r['route'] for r in requests if r['blocking']]
 routes += [a['recommended_route'] for a in assessments if a['resulting_status'] in ['INVESTIGATION_REQUIRED','UPSTREAM_DECISION_REQUIRED']]
 priority=[
  ('PROBLEM_ALIGNMENT','RETURN_TO_PROBLEM_ALIGNMENT','PROBLEM_ALIGNMENT'),
  ('INVESTIGATION','RETURN_TO_INVESTIGATION','INVESTIGATION'),
  ('SYSTEM_MODEL','RETURN_TO_SYSTEM_MODEL','SYSTEM_MODEL'),
  ('SOLUTION_DESIGN','RETURN_TO_SOLUTION_DESIGN','SOLUTION_DESIGN'),
  ('SOLUTION_CRITIQUE','RETURN_TO_SOLUTION_CRITIQUE','SOLUTION_CRITIQUE'),
  ('IMPLEMENTATION_PLAN','RETURN_TO_IMPLEMENTATION_PLAN','IMPLEMENTATION_PLAN')]
 for route,gate,state in priority:
  if route in routes: return gate,state
 if not all_assessed: return 'BLOCKED','PLAN_CRITIQUE'
 if approval['status']=='APPROVED' and contract['status']=='APPROVED' and digest_valid and not revisions and not requests:
  return 'READY_FOR_IMPLEMENTATION_CHECKLIST','IMPLEMENTATION_CHECKLIST'
 return 'BLOCKED','PLAN_CRITIQUE'

def validate_package(a)->list[Issue]:
 issues=[]
 paths={k:Path(getattr(a,k)) for k in ['input','output','planning_output','targets','plans','dependencies','coverage','verifications','rollbacks','findings','solution_contract','ledger','elements','relations','assessments','revisions','requests','approval','plan_contract']}
 inp=load_doc(paths['input']); out=load_doc(paths['output']); pout=load_doc(paths['planning_output']); solcon=load_doc(paths['solution_contract']); approval=load_doc(paths['approval']); pcontract=load_doc(paths['plan_contract'])
 for obj,kind,prefix in [(inp,'input','$.input'),(out,'output','$.output'),(pout,'planning_output','$.planning_output'),(solcon,'solution_contract','$.solution_contract'),(approval,'approval','$.approval'),(pcontract,'plan_contract','$.plan_contract')]: issues+=structural(obj,kind,prefix)
 targets,e=load_jsonl(paths['targets'],'target'); issues+=e
 plans,e=load_jsonl(paths['plans'],'plan'); issues+=e
 deps,e=load_jsonl(paths['dependencies'],'dependency',allow_empty=True); issues+=e
 coverage,e=load_coverage(paths['coverage']); issues+=e
 verifs,e=load_jsonl(paths['verifications'],'verification'); issues+=e
 rollbacks,e=load_jsonl(paths['rollbacks'],'rollback',allow_empty=True); issues+=e
 findings,e=load_jsonl(paths['findings'],'finding',allow_empty=True); issues+=e
 ledger,e=load_jsonl(paths['ledger'],'evidence'); issues+=e
 elements,e=load_jsonl(paths['elements'],'element'); issues+=e
 relations,e=load_jsonl(paths['relations'],'relation',allow_empty=True); issues+=e
 assessments,e=load_jsonl(paths['assessments'],'assessment'); issues+=e
 revisions,e=load_jsonl(paths['revisions'],'revision',allow_empty=True); issues+=e
 requests,e=load_jsonl(paths['requests'],'request',allow_empty=True); issues+=e
 if issues: return issues

 # Unique IDs.
 for rows,key,label in [(targets,'target_id','target id'),(plans,'plan_id','plan id'),(deps,'dependency_id','dependency id'),(coverage,'coverage_id','coverage id'),(verifs,'verification_id','verification id'),(rollbacks,'rollback_id','rollback id'),(findings,'finding_id','finding id'),(ledger,'id','evidence id'),(elements,'id','model element id'),(relations,'id','model relation id'),(assessments,'assessment_id','assessment id'),(revisions,'directive_id','revision directive id'),(requests,'request_id','evidence request id')]: issues+=duplicate_issues(rows,key,label)

 target_ids={x['target_id'] for x in targets}; plan_ids={x['plan_id'] for x in plans}; dep_ids={x['dependency_id'] for x in deps}; cov_ids={x['coverage_id'] for x in coverage}; verif_ids={x['verification_id'] for x in verifs}; rollback_ids={x['rollback_id'] for x in rollbacks}; finding_ids={x['finding_id'] for x in findings}; evidence_ids={x['id'] for x in ledger}; element_ids={x['id'] for x in elements}; relation_ids={x['id'] for x in relations}; all_target_ids=target_ids|plan_ids|dep_ids|cov_ids|verif_ids|rollback_ids|finding_ids
 critique_ids={x['critique_id'] for x in inp['human_critiques']}; asmt_ids={x['assessment_id'] for x in assessments}; rev_ids={x['directive_id'] for x in revisions}; req_ids={x['request_id'] for x in requests}

 # Exact upstream binding.
 if inp['source_planning']['planning_run_id']!=pout['metadata']['planning_run_id']: issues.append(Issue('$.input.source_planning.planning_run_id','does not match planning output'))
 if inp['source_planning']['artifact_version']!=pout['metadata']['version']: issues.append(Issue('$.input.source_planning.artifact_version','does not match planning output'))
 if pout['gate_decision']['status']!='READY_FOR_PLAN_CRITIQUE' or pout['gate_decision']['next_state']!='PLAN_CRITIQUE': issues.append(Issue('$.planning_output.gate_decision','source package is not transition-ready for PLAN_CRITIQUE'))
 if solcon['status']!='APPROVED' or solcon['approval'].get('approved_by_role')!='HUMAN' or not solcon['approval'].get('approved_by') or not solcon['approval'].get('approved_at'): issues.append(Issue('$.solution_contract','must be APPROVED by HUMAN'))
 if pout['source_solution_contract']['contract_id']!=solcon['contract_id']: issues.append(Issue('$.planning_output.source_solution_contract.contract_id','does not match supplied solution contract'))
 if pout['source_solution_contract']['status']!='APPROVED': issues.append(Issue('$.planning_output.source_solution_contract.status','must be APPROVED'))

 # Record counts in input and source output.
 actual_counts={'planning_output':1,'planning_targets':len(targets),'plan_items':len(plans),'dependency_edges':len(deps),'coverage_matrix':len(coverage),'verification_plan':len(verifs),'rollback_plan':len(rollbacks),'planning_findings':len(findings),'approved_solution_contract':1,'evidence_ledger':len(ledger),'model_elements':len(elements),'model_relations':len(relations)}
 for k,n in actual_counts.items():
  if inp['source_artifacts'][k]['record_count']!=n: issues.append(Issue(f'$.input.source_artifacts.{k}.record_count',f'expected {n}'))
 mapping={'planning_targets':'planning_targets','plan_items':'plan_items','dependency_edges':'dependency_edges','coverage_matrix':'coverage_matrix','verification_plan':'verification_plan','rollback_plan':'rollback_plan','planning_findings':'planning_findings'}
 for src_key,out_key in mapping.items():
  if pout['artifact_files'][out_key]['record_count']!=actual_counts[src_key]: issues.append(Issue(f'$.planning_output.artifact_files.{out_key}.record_count',f'expected {actual_counts[src_key]}'))

 # Source graph and references are still coherent.
 refs_valid,acyclic,computed_order=graph_topology(plan_ids,deps)
 if not refs_valid: issues.append(Issue('$.dependencies','contains invalid plan references'))
 if not acyclic: issues.append(Issue('$.dependencies','contains a dependency cycle'))
 if pout['dependency_analysis']['topological_order']!=computed_order: issues.append(Issue('$.planning_output.dependency_analysis.topological_order','does not match computed dependency order'))

 # Critique target and claimed evidence resolution.
 for c in inp['human_critiques']:
  for tid in c['target_ids']:
   if tid not in all_target_ids: issues.append(Issue(f'$.input.human_critiques[{c["critique_id"]}].target_ids',f'unknown target: {tid}'))
  for eid in c.get('claimed_evidence_ids',[]):
   if eid not in evidence_ids: issues.append(Issue(f'$.input.human_critiques[{c["critique_id"]}].claimed_evidence_ids',f'unknown evidence: {eid}'))

 # Exactly one assessment per critique.
 counts=Counter(x['critique_id'] for x in assessments)
 for cid in critique_ids:
  if counts[cid]!=1: issues.append(Issue('$.assessments',f'critique {cid} must be assessed exactly once; found {counts[cid]}'))
 for arow in assessments:
  if arow['critique_id'] not in critique_ids: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}].critique_id','unknown critique'))
  for tid in arow['target_ids']+arow['planning_items_reviewed']:
   if tid not in all_target_ids: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}]',f'unknown planning target: {tid}'))
  for eid in arow['evidence_reviewed']:
   if eid not in evidence_ids: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}].evidence_reviewed',f'unknown evidence: {eid}'))
  for rid in arow['revision_directive_ids']:
   if rid not in rev_ids: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}].revision_directive_ids',f'unknown directive: {rid}'))
  for rid in arow['evidence_request_ids']:
   if rid not in req_ids: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}].evidence_request_ids',f'unknown request: {rid}'))
  if arow['classification']=='REJECTED_WITH_EVIDENCE':
   if not arow['evidence_reviewed']: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}]','REJECTED_WITH_EVIDENCE requires evidence_reviewed'))
   if not arow['contradicting_findings']: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}]','REJECTED_WITH_EVIDENCE requires contradicting_findings'))
   if arow['resulting_status'] not in ['NO_CHANGE','WEAKENED']: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}].resulting_status','rejected critique cannot require revision'))
  if arow['classification']=='REQUIRES_INVESTIGATION':
   if arow['resulting_status']!='INVESTIGATION_REQUIRED' or not arow['evidence_request_ids']: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}]','REQUIRES_INVESTIGATION needs INVESTIGATION_REQUIRED and evidence request'))
  if arow['resulting_status'] in ['REVISION_REQUIRED','UPSTREAM_DECISION_REQUIRED'] and not arow['revision_directive_ids']: issues.append(Issue(f'$.assessment[{arow["assessment_id"]}]','revision/upstream decision status requires revision directive'))

 # Directives and evidence requests.
 for r in revisions:
  for cid in r['source_critique_ids']:
   if cid not in critique_ids: issues.append(Issue(f'$.revision[{r["directive_id"]}].source_critique_ids',f'unknown critique: {cid}'))
  for aid in r['source_assessment_ids']:
   if aid not in asmt_ids: issues.append(Issue(f'$.revision[{r["directive_id"]}].source_assessment_ids',f'unknown assessment: {aid}'))
  for tid in r['target_ids']:
   if tid not in all_target_ids: issues.append(Issue(f'$.revision[{r["directive_id"]}].target_ids',f'unknown target: {tid}'))
  for eid in r['evidence_ids']:
   if eid not in evidence_ids: issues.append(Issue(f'$.revision[{r["directive_id"]}].evidence_ids',f'unknown evidence: {eid}'))
  if r['semantic_change_required'] and r['route']=='IMPLEMENTATION_PLAN': issues.append(Issue(f'$.revision[{r["directive_id"]}].route','semantic change cannot route only to IMPLEMENTATION_PLAN'))
  if not r['semantic_change_required'] and r['route'] in ['SOLUTION_DESIGN','SOLUTION_CRITIQUE']:
   # allowed only if rationale states upstream contract conflict; don't force but flag weak mapping if no semantic change
   issues.append(Issue(f'$.revision[{r["directive_id"]}]','upstream solution route requires semantic_change_required=true'))
 for q in requests:
  for cid in q['source_critique_ids']:
   if cid not in critique_ids: issues.append(Issue(f'$.request[{q["request_id"]}].source_critique_ids',f'unknown critique: {cid}'))

 # Summary and artifact counts.
 class_counts=Counter(x['classification'] for x in assessments); rs=out['review_summary']
 expected_rs={'total_critiques':len(critique_ids),'accepted':class_counts['ACCEPTED'],'partially_accepted':class_counts['PARTIALLY_ACCEPTED'],'rejected_with_evidence':class_counts['REJECTED_WITH_EVIDENCE'],'requires_investigation':class_counts['REQUIRES_INVESTIGATION'],'unassessed':max(0,len(critique_ids)-len(assessments))}
 if rs!=expected_rs: issues.append(Issue('$.output.review_summary','does not match critiques and assessments'))
 af=out['artifact_files']; exp_counts={'assessments':len(assessments),'revision_directives':len(revisions),'evidence_requests':len(requests),'plan_approval':1,'approved_plan_contract':1,'report':1}
 for k,n in exp_counts.items():
  if af[k]['record_count']!=n: issues.append(Issue(f'$.output.artifact_files.{k}.record_count',f'expected {n}'))

 all_assessed=len(assessments)==len(critique_ids) and all(counts[c]==1 for c in critique_ids)
 all_targets_valid=not any('unknown target' in x.message or 'unknown planning target' in x.message for x in issues)
 evidence_backed=all(a['classification']!='REJECTED_WITH_EVIDENCE' or bool(a['evidence_reviewed'] and a['contradicting_findings']) for a in assessments)
 expected_cov={'all_critiques_assessed':all_assessed,'all_targets_resolved':all_targets_valid,'all_references_valid':all_targets_valid and not any('unknown evidence' in x.message or 'unknown directive' in x.message or 'unknown request' in x.message for x in issues),'all_material_responses_evidence_backed':evidence_backed}
 if out['coverage']!=expected_cov: issues.append(Issue('$.output.coverage','does not match computed critique coverage'))

 expected_affected=sorted({tid for arow in assessments if arow['resulting_status']!='NO_CHANGE' for tid in arow['target_ids']})
 expected_retained=sorted({tid for arow in assessments if arow['resulting_status']=='NO_CHANGE' for tid in arow['target_ids']})
 impact=out['plan_impact']
 if impact['revision_required']!=bool(revisions): issues.append(Issue('$.output.plan_impact.revision_required','does not match revision directives'))
 if impact['investigation_required']!=any(q['route']=='INVESTIGATION' for q in requests): issues.append(Issue('$.output.plan_impact.investigation_required','does not match evidence requests'))
 if impact['upstream_decision_required']!=any(r['route'] in ['SOLUTION_DESIGN','SOLUTION_CRITIQUE','SYSTEM_MODEL','PROBLEM_ALIGNMENT'] for r in revisions): issues.append(Issue('$.output.plan_impact.upstream_decision_required','does not match revision routes'))
 if sorted(impact['affected_ids'])!=expected_affected: issues.append(Issue('$.output.plan_impact.affected_ids',f'expected {expected_affected}'))
 if sorted(impact['retained_ids'])!=expected_retained: issues.append(Issue('$.output.plan_impact.retained_ids',f'expected {expected_retained}'))

 # Approval semantics.
 executing_agents={inp['metadata']['author_agent'],out['metadata']['author_agent']}
 if approval['planning_run_id']!=pout['metadata']['planning_run_id'] or approval['approved_plan_version']!=pout['metadata']['version']: issues.append(Issue('$.approval','does not bind exact planning run/version'))
 if approval['status']=='APPROVED':
  if approval['approver_role']!='HUMAN' or not approval['approved_by'] or not approval['approved_at']: issues.append(Issue('$.approval','APPROVED plan requires named HUMAN and approved_at'))
  if approval['approved_by'] in executing_agents: issues.append(Issue('$.approval.approved_by','executing agent cannot approve its own plan critique'))
  if set(approval['resolved_critique_ids'])!=critique_ids: issues.append(Issue('$.approval.resolved_critique_ids','must contain every critique id exactly once'))
 else:
  if approval['approver_role']=='HUMAN' and approval['approved_by'] and approval['status']=='PENDING': issues.append(Issue('$.approval','PENDING approval must not appear completed'))

 plan_risks=sorted({x for p in plans for x in p.get('risk_ids',[])})
 accepted_risks=set(approval['accepted_residual_risk_ids'])
 missing_risks=sorted(set(plan_risks)-accepted_risks)
 if approval['status']=='APPROVED' and missing_risks: issues.append(Issue('$.approval.accepted_residual_risk_ids',f'unaccepted plan risks: {missing_risks}'))

 # Approved plan contract exactness and digest.
 computed_digest=canonical_bundle_digest(pout,targets,plans,deps,coverage,verifs,rollbacks,findings)
 digest_valid=pcontract['plan_bundle_digest']==computed_digest
 if not digest_valid: issues.append(Issue('$.plan_contract.plan_bundle_digest',f'expected {computed_digest}'))
 if pcontract['source_planning_run_id']!=pout['metadata']['planning_run_id'] or pcontract['source_solution_contract_id']!=solcon['contract_id'] or pcontract['plan_approval_id']!=approval['approval_id']: issues.append(Issue('$.plan_contract','source bindings do not match'))
 if pcontract['repository_snapshot']['commit_sha']!=inp['source_planning']['repository_commit']: issues.append(Issue('$.plan_contract.repository_snapshot.commit_sha','does not match source planning commit'))
 if pcontract['artifact_versions']['planning_output_version']!=pout['metadata']['version'] or pcontract['artifact_versions']['solution_contract_id']!=solcon['contract_id']: issues.append(Issue('$.plan_contract.artifact_versions','does not match source versions'))
 exact_sets=[('planning_target_ids',target_ids),('plan_item_ids',plan_ids),('dependency_edge_ids',dep_ids),('verification_item_ids',verif_ids),('rollback_item_ids',rollback_ids)]
 for field,expected in exact_sets:
  if set(pcontract[field])!=expected: issues.append(Issue(f'$.plan_contract.{field}',f'must exactly equal source IDs; expected {sorted(expected)}'))
 if pcontract['execution_order']!=computed_order: issues.append(Issue('$.plan_contract.execution_order','must equal computed topological order'))
 exp_components=sorted({x for p in plans for x in p['affected_components']}); exp_files=sorted({x for p in plans for x in p['affected_files_or_artifacts']})
 if sorted(pcontract['change_surface']['components'])!=exp_components: issues.append(Issue('$.plan_contract.change_surface.components','does not match plan item union'))
 if sorted(pcontract['change_surface']['files_or_artifacts'])!=exp_files: issues.append(Issue('$.plan_contract.change_surface.files_or_artifacts','does not match plan item union'))
 if set(pcontract['accepted_residual_risk_ids'])!=accepted_risks: issues.append(Issue('$.plan_contract.accepted_residual_risk_ids',f'expected {sorted(accepted_risks)}'))
 if pcontract['accepted_limitations']!=approval['accepted_limitations']: issues.append(Issue('$.plan_contract.accepted_limitations','must match human approval'))
 if pcontract['status']=='APPROVED':
  if approval['status']!='APPROVED': issues.append(Issue('$.plan_contract.status','cannot be APPROVED without approved human plan approval'))
  pa=pcontract['approval']
  if pa['status']!='APPROVED' or pa['approver_role']!='HUMAN' or pa['approved_by']!=approval['approved_by'] or pa['approved_at']!=approval['approved_at']: issues.append(Issue('$.plan_contract.approval','must exactly mirror human plan approval'))
  if pcontract['decision_envelope']['no_silent_replanning'] is not True: issues.append(Issue('$.plan_contract.decision_envelope','silent replanning must be prohibited'))

 # Output readiness and route.
 expected_status,expected_state=expected_gate(assessments,revisions,requests,all_assessed,approval,pcontract,digest_valid)
 gate=out['gate_decision']
 if gate['status']!=expected_status or gate['next_state']!=expected_state: issues.append(Issue('$.output.gate_decision',f'expected {expected_status} -> {expected_state}'))
 blocking_critiques=sorted({a['critique_id'] for a in assessments if a['resulting_status']!='NO_CHANGE'} | ({c for c in critique_ids if counts[c]!=1}))
 blocking_requests=sorted(rev_ids|{q['request_id'] for q in requests if q['blocking']})
 if sorted(gate['blocking_critique_ids'])!=blocking_critiques: issues.append(Issue('$.output.gate_decision.blocking_critique_ids',f'expected {blocking_critiques}'))
 if sorted(gate['blocking_request_ids'])!=blocking_requests: issues.append(Issue('$.output.gate_decision.blocking_request_ids',f'expected {blocking_requests}'))
 ar=out['approval_readiness']
 expected_ar={'status':'READY' if expected_status=='READY_FOR_IMPLEMENTATION_CHECKLIST' else 'NOT_READY','human_approval_status':approval['status'],'plan_contract_status':pcontract['status'],'all_blocking_critiques_resolved':not blocking_critiques,'all_revision_directives_absent':not revisions,'all_evidence_requests_closed_or_routed':not requests,'bundle_digest_valid':digest_valid}
 if ar!=expected_ar: issues.append(Issue('$.output.approval_readiness','does not match computed approval readiness'))

 if a.require_transition_ready and expected_status!='READY_FOR_IMPLEMENTATION_CHECKLIST': issues.append(Issue('$.transition',f'package is not transition-ready; expected READY_FOR_IMPLEMENTATION_CHECKLIST, got {expected_status}'))
 return issues

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--kind',choices=['schema','input','output','critique','assessment','revision','request','approval','plan_contract','package'],required=True)
 p.add_argument('--file')
 for x in ['input','output','planning-output','targets','plans','dependencies','coverage','verifications','rollbacks','findings','solution-contract','ledger','elements','relations','assessments','revisions','requests','approval','plan-contract']:
  p.add_argument('--'+x,dest=x.replace('-','_'))
 p.add_argument('--require-transition-ready',action='store_true')
 a=p.parse_args()
 issues=[]
 try:
  if a.kind=='schema':
   for path in sorted((ROOT/'schemas').glob('*.json')): Draft202012Validator.check_schema(json.loads(path.read_text()))
  elif a.kind=='package':
   required=['input','output','planning_output','targets','plans','dependencies','coverage','verifications','rollbacks','findings','solution_contract','ledger','elements','relations','assessments','revisions','requests','approval','plan_contract']
   missing=[x for x in required if not getattr(a,x)]
   if missing: issues=[Issue('$','missing package arguments: '+', '.join(missing))]
   else: issues=validate_package(a)
  else:
   if not a.file: issues=[Issue('$','--file is required')]
   else:
    obj=load_doc(Path(a.file)); issues=structural(obj,a.kind)
 except Exception as e:
  issues=[Issue('$',f'validator failure: {type(e).__name__}: {e}')]
 if issues:
  for i in issues: print(i,file=sys.stderr)
  return 1
 print('VALID')
 if a.kind=='package' and a.require_transition_ready: print('Package is transition-ready for IMPLEMENTATION_CHECKLIST')
 return 0

if __name__=='__main__': raise SystemExit(main())
