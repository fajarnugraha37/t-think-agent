#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sys,warnings
from collections import Counter,defaultdict,deque
from datetime import date,datetime
from pathlib import Path
from typing import Any,Iterable
import yaml
warnings.filterwarnings('ignore',category=DeprecationWarning)
from jsonschema import Draft202012Validator,FormatChecker,RefResolver
ROOT=Path(__file__).resolve().parents[1]
SCHEMA_FILES={
 'input':'input.schema.json','output':'output.schema.json','checklist':'checklist-item.schema.json','dependency':'checklist-dependency.schema.json','coverage':'coverage-row.schema.json','batch':'execution-batch.schema.json','finding':'checklist-finding.schema.json',
 'plan_contract':'upstream-approved-plan-contract.schema.json','plan_critique_output':'upstream-plan-critique-output.schema.json','planning_output':'upstream-planning-output.schema.json','target':'upstream-planning-target.schema.json','plan':'upstream-plan-item.schema.json','plan_dependency':'upstream-plan-dependency.schema.json','plan_coverage':'upstream-plan-coverage-row.schema.json','verification':'upstream-verification-item.schema.json','rollback':'upstream-rollback-item.schema.json','planning_finding':'upstream-planning-finding.schema.json','solution_contract':'upstream-approved-solution-contract.schema.json','evidence':'upstream-evidence-record.schema.json','element':'upstream-model-element.schema.json','relation':'upstream-model-relation.schema.json'}
SCHEMAS={k:ROOT/'schemas'/v for k,v in SCHEMA_FILES.items()}
class Issue:
 def __init__(self,path,message): self.path,self.message=path,message
 def __str__(self): return f'{self.path}: {self.message}'
def normalize(v):
 if isinstance(v,(date,datetime)): return v.isoformat()
 if isinstance(v,dict): return {k:normalize(x) for k,x in v.items()}
 if isinstance(v,list): return [normalize(x) for x in v]
 return v
def load_doc(p):
 p=Path(p); t=p.read_text(encoding='utf-8'); return json.loads(t) if p.suffix.lower()=='.json' else normalize(yaml.safe_load(t))
def load_schema(k): return json.loads(SCHEMAS[k].read_text(encoding='utf-8'))
def schema_store():
 s={}
 for p in (ROOT/'schemas').glob('*.json'):
  d=json.loads(p.read_text());
  if '$id' in d: s[d['$id']]=d
  s[p.name]=d; s[p.as_uri()]=d
 return s
STORE=schema_store()
def pjoin(prefix,parts): return prefix+''.join(f'[{p}]' if isinstance(p,int) else f'.{p}' for p in parts)
def structural(obj,kind,prefix='$'):
 s=load_schema(kind); out=[]; resolver=RefResolver.from_schema(s,store=STORE)
 for e in sorted(Draft202012Validator(s,resolver=resolver,format_checker=FormatChecker()).iter_errors(obj),key=lambda x:list(x.absolute_path)): out.append(Issue(pjoin(prefix,e.absolute_path),e.message))
 return out
def load_jsonl(path,kind,allow_empty=False):
 path=Path(path); rows=[]; issues=[]
 for n,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
  if not line.strip(): continue
  try: obj=json.loads(line)
  except json.JSONDecodeError as e: issues.append(Issue(f'{path}:{n}',f'invalid JSON: {e.msg}')); continue
  rows.append(obj); issues+=structural(obj,kind,f'{path}:{n}$')
 if not rows and not allow_empty: issues.append(Issue(str(path),'must contain at least one record'))
 return rows,issues
def split_ids(v): return [x.strip() for x in (v or '').split('|') if x.strip()]
def load_coverage(path,kind,fields):
 rows=[]; issues=[]; path=Path(path)
 with path.open(encoding='utf-8',newline='') as f:
  r=csv.DictReader(f)
  if (r.fieldnames or [])!=fields: return [],[Issue(f'{path}:headers',f'expected exactly {fields}')]
  for n,row in enumerate(r,2):
   o=dict(row)
   if 'operation_sequence' in o and o['operation_sequence']!='': o['operation_sequence']=int(o['operation_sequence'])
   for k in [x for x in ['checklist_ids','verification_ids','rollback_ids','plan_ids'] if x in o]: o[k]=split_ids(o[k])
   rows.append(o); issues+=structural(o,kind,f'{path}:{n}$')
 return rows,issues
def dup(rows,key,label):
 c=Counter(x.get(key) for x in rows if x.get(key)); return [Issue('$',f'duplicate {label}: {k}') for k,n in c.items() if n>1]
def canonical_bundle_digest(pout,targets,plans,deps,cov,verifs,rollbacks,findings):
 payload={'planning_output':pout,'targets':targets,'plans':plans,'dependencies':deps,'coverage':cov,'verifications':verifs,'rollbacks':rollbacks,'findings':findings}
 return 'sha256:'+hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def op_digest(op):
 payload={k:op[k] for k in ['sequence','operation','expected_effect','non_goals']}
 return 'sha256:'+hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def graph(ids,edges):
 indeg={x:0 for x in ids}; adj={x:[] for x in ids}; incoming=defaultdict(list); refs=True
 for e in edges:
  a,b=e['from_checklist_id'],e['to_checklist_id']
  if a not in ids or b not in ids or a==b: refs=False; continue
  adj[a].append(b); indeg[b]+=1; incoming[b].append(a)
 rem=indeg.copy(); ready=sorted(x for x,d in rem.items() if d==0); levels=[]; topo=[]
 while ready:
  level=ready; levels.append(level); nxt=[]
  for x in level:
   topo.append(x)
   for z in sorted(adj[x]):
    rem[z]-=1
    if rem[z]==0: nxt.append(z)
  ready=sorted(set(nxt))
 return refs,len(topo)==len(ids),sorted(x for x,d in indeg.items() if d==0),sorted(x for x in ids if not adj[x]),topo,levels,incoming
def expected_gate(findings,intrinsic):
 routes={x['route'] for x in findings if x['blocking']}
 priority=[('PROBLEM_ALIGNMENT','RETURN_TO_PROBLEM_ALIGNMENT','PROBLEM_ALIGNMENT'),('INVESTIGATION','RETURN_TO_INVESTIGATION','INVESTIGATION'),('SYSTEM_MODEL','RETURN_TO_SYSTEM_MODEL','SYSTEM_MODEL'),('SOLUTION_DESIGN','RETURN_TO_SOLUTION_DESIGN','SOLUTION_DESIGN'),('SOLUTION_CRITIQUE','RETURN_TO_SOLUTION_CRITIQUE','SOLUTION_CRITIQUE'),('PLAN_CRITIQUE','RETURN_TO_PLAN_CRITIQUE','PLAN_CRITIQUE'),('IMPLEMENTATION_PLAN','RETURN_TO_IMPLEMENTATION_PLAN','IMPLEMENTATION_PLAN')]
 for route,gate,state in priority:
  if route in routes: return gate,state
 if routes or not intrinsic: return 'BLOCKED','IMPLEMENTATION_CHECKLIST'
 return 'READY_FOR_CHECKLIST_CRITIQUE','CHECKLIST_CRITIQUE'
def validate_package(a):
 issues=[]
 docs={k:load_doc(getattr(a,k)) for k in ['input','output','plan_contract','plan_critique_output','planning_output','solution_contract']}
 for k,kind in [('input','input'),('output','output'),('plan_contract','plan_contract'),('plan_critique_output','plan_critique_output'),('planning_output','planning_output'),('solution_contract','solution_contract')]: issues+=structural(docs[k],kind,f'$.{k}')
 targets,e=load_jsonl(a.targets,'target'); issues+=e
 plans,e=load_jsonl(a.plans,'plan'); issues+=e
 pdeps,e=load_jsonl(a.plan_dependencies,'plan_dependency',allow_empty=True); issues+=e
 pcov,e=load_coverage(a.plan_coverage,'plan_coverage',['coverage_id','planning_target_id','coverage_status','plan_ids','verification_ids','rollback_ids','rationale']); issues+=e
 verifs,e=load_jsonl(a.verifications,'verification'); issues+=e
 rollbacks,e=load_jsonl(a.rollbacks,'rollback',allow_empty=True); issues+=e
 pfind,e=load_jsonl(a.planning_findings,'planning_finding',allow_empty=True); issues+=e
 ledger,e=load_jsonl(a.ledger,'evidence'); issues+=e
 elements,e=load_jsonl(a.elements,'element'); issues+=e
 relations,e=load_jsonl(a.relations,'relation',allow_empty=True); issues+=e
 checks,e=load_jsonl(a.checklists,'checklist'); issues+=e
 deps,e=load_jsonl(a.dependencies,'dependency',allow_empty=True); issues+=e
 cov,e=load_coverage(a.coverage,'coverage',['coverage_id','plan_id','operation_sequence','coverage_status','checklist_ids','verification_ids','rollback_ids','rationale']); issues+=e
 batches,e=load_jsonl(a.batches,'batch'); issues+=e
 findings,e=load_jsonl(a.findings,'finding',allow_empty=True); issues+=e
 if issues: return issues
 inp,out,contract,crit,pout,solcon=[docs[k] for k in ['input','output','plan_contract','plan_critique_output','planning_output','solution_contract']]
 for rows,key,label in [(targets,'target_id','target id'),(plans,'plan_id','plan id'),(pdeps,'dependency_id','plan dependency id'),(verifs,'verification_id','verification id'),(rollbacks,'rollback_id','rollback id'),(ledger,'id','evidence id'),(elements,'id','model id'),(relations,'id','model relation id'),(checks,'checklist_id','checklist id'),(deps,'dependency_id','checklist dependency id'),(cov,'coverage_id','checklist coverage id'),(batches,'batch_id','batch id'),(findings,'finding_id','finding id')]: issues+=dup(rows,key,label)
 target_ids={x['target_id'] for x in targets}; plan_ids={x['plan_id'] for x in plans}; plan_by={x['plan_id']:x for x in plans}; pdep_ids={x['dependency_id'] for x in pdeps}; ver_ids={x['verification_id'] for x in verifs}; rb_ids={x['rollback_id'] for x in rollbacks}; ev_ids={x['id'] for x in ledger}; model_ids={x['id'] for x in elements}; check_ids={x['checklist_id'] for x in checks}; check_by={x['checklist_id']:x for x in checks}
 # Approval and source binding.
 approved=contract['status']=='APPROVED' and contract['approval']['status']=='APPROVED' and contract['approval']['approver_role']=='HUMAN' and bool(contract['approval']['approved_by'])
 if not approved: issues.append(Issue('$.plan_contract','must be APPROVED by a named HUMAN'))
 if crit['gate_decision']['status']!='READY_FOR_IMPLEMENTATION_CHECKLIST' or crit['approval_readiness']['status']!='READY': issues.append(Issue('$.plan_critique_output','must be READY_FOR_IMPLEMENTATION_CHECKLIST with approval readiness READY'))
 if crit['source_planning']['planning_run_id']!=contract['source_planning_run_id']: issues.append(Issue('$.plan_critique_output.source_planning','planning run does not match approved plan contract'))
 bindings={'contract_id':contract['contract_id'],'source_planning_run_id':contract['source_planning_run_id'],'source_solution_contract_id':contract['source_solution_contract_id'],'plan_bundle_digest':contract['plan_bundle_digest'],'repository_commit':contract['repository_snapshot']['commit_sha']}
 for f,v in bindings.items():
  if inp['source_plan_contract'][f]!=v: issues.append(Issue(f'$.input.source_plan_contract.{f}','does not match approved plan contract'))
  if out['source_plan_contract'][f]!=v: issues.append(Issue(f'$.output.source_plan_contract.{f}','does not match approved plan contract'))
 if inp['source_plan_critique']['critique_run_id']!=crit['metadata']['critique_run_id'] or inp['source_plan_critique']['artifact_version']!=crit['metadata']['version'] or inp['source_plan_critique']['approved_plan_contract_id']!=contract['contract_id']: issues.append(Issue('$.input.source_plan_critique','does not match source Plan Critique output'))
 if inp['repository_snapshot']['commit_sha']!=contract['repository_snapshot']['commit_sha']: issues.append(Issue('$.input.repository_snapshot.commit_sha','does not match approved repository snapshot'))
 # Planning bundle exactness.
 computed_digest=canonical_bundle_digest(pout,targets,plans,pdeps,pcov,verifs,rollbacks,pfind); digest_ok=computed_digest==contract['plan_bundle_digest']
 if not digest_ok: issues.append(Issue('$.plan_contract.plan_bundle_digest',f'expected {computed_digest}'))
 exact_pairs=[('planning_target_ids',target_ids),('plan_item_ids',plan_ids),('dependency_edge_ids',pdep_ids),('verification_item_ids',ver_ids),('rollback_item_ids',rb_ids)]
 for field,expected in exact_pairs:
  if set(contract[field])!=expected: issues.append(Issue(f'$.plan_contract.{field}',f'must exactly equal source IDs: {sorted(expected)}'))
 # Input descriptor counts.
 count_map={'approved_plan_contract':1,'plan_critique_output':1,'planning_output':1,'planning_targets':len(targets),'plan_items':len(plans),'plan_dependencies':len(pdeps),'plan_coverage':len(pcov),'verification_plan':len(verifs),'rollback_plan':len(rollbacks),'planning_findings':len(pfind),'approved_solution_contract':1,'evidence_ledger':len(ledger),'model_elements':len(elements),'model_relations':len(relations)}
 for k,n in count_map.items():
  if inp['source_artifacts'][k]['record_count']!=n: issues.append(Issue(f'$.input.source_artifacts.{k}.record_count',f'expected {n}'))
 # Checklist exact source mapping.
 op_map={(p['plan_id'],op['sequence']):(p,op) for p in plans for op in p['implementation_operations']}; seen=Counter(); scope_components=set(); scope_files=set(); union_ver=set(); union_rb=set(); semantic=[]; expanded=[]; non_atomic=[]
 for c in checks:
  key=(c['source_plan_id'],c['source_operation']['sequence']); seen[key]+=1
  if key not in op_map: issues.append(Issue(f'$.checklist[{c["checklist_id"]}].source_operation','unknown source plan operation')); continue
  p,op=op_map[key]
  if c['source_operation']['operation']!=op['operation'] or c['source_operation']['expected_effect']!=op['expected_effect'] or c['source_operation']['non_goals']!=op['non_goals'] or c['source_operation']['digest']!=op_digest(op): issues.append(Issue(f'$.checklist[{c["checklist_id"]}].source_operation','source operation text/effect/non-goals/digest drift'))
  exact=[('planning_target_ids',set(p['planning_target_ids'])),('problem_ids',set(p['problem_ids'])),('model_ids',set(p['model_ids'])),('evidence_ids',set(p['evidence_ids'])),('invariant_ids',set(p['invariant_ids'])),('verification_item_ids',set(p['verification_item_ids'])),('rollback_item_ids',set(p['rollback_item_ids'])),('risk_ids',set(p['risk_ids']))]
  for field,exp in exact:
   if set(c[field])!=exp: issues.append(Issue(f'$.checklist[{c["checklist_id"]}].{field}',f'must exactly match source plan item: {sorted(exp)}'))
  if set(c['scope']['components'])!=set(p['affected_components']) or set(c['scope']['files_or_artifacts'])!=set(p['affected_files_or_artifacts']): expanded.append(c['checklist_id']); issues.append(Issue(f'$.checklist[{c["checklist_id"]}].scope','scope expansion or loss relative to approved plan item'))
  if c['action']['exact_change']!=op['operation'] or c['expected_result']!=op['expected_effect']: issues.append(Issue(f'$.checklist[{c["checklist_id"]}].action','must preserve exact source operation and expected effect'))
  for x in c['evidence_ids']:
   if x not in ev_ids: issues.append(Issue(f'$.checklist[{c["checklist_id"]}].evidence_ids',f'unknown evidence: {x}'))
  for x in c['model_ids']:
   if x not in model_ids: issues.append(Issue(f'$.checklist[{c["checklist_id"]}].model_ids',f'unknown model element: {x}'))
  for x in c['verification_item_ids']:
   if x not in ver_ids: issues.append(Issue(f'$.checklist[{c["checklist_id"]}].verification_item_ids',f'unknown verification: {x}'))
  for x in c['rollback_item_ids']:
   if x not in rb_ids: issues.append(Issue(f'$.checklist[{c["checklist_id"]}].rollback_item_ids',f'unknown rollback: {x}'))
  if c['semantic_guard']['introduces_new_semantic_decision'] or not c['semantic_guard']['within_approved_plan'] or c['semantic_guard']['scope_expansion'] or c['semantic_guard']['deviations']: semantic.append(c['checklist_id']); issues.append(Issue(f'$.checklist[{c["checklist_id"]}].semantic_guard','new semantic decision or scope expansion is prohibited'))
  if not all([c['atomicity']['single_primary_action'],c['atomicity']['one_source_operation'],c['atomicity']['independently_verifiable']]): non_atomic.append(c['checklist_id'])
  if c['on_ambiguity']!='IMPLEMENTATION_FAILED' or c['on_unapproved_change']!='LOOPBACK_REQUIRED': issues.append(Issue(f'$.checklist[{c["checklist_id"]}]','execution guard is invalid'))
  scope_components.update(c['scope']['components']); scope_files.update(c['scope']['files_or_artifacts']); union_ver.update(c['verification_item_ids']); union_rb.update(c['rollback_item_ids'])
 missing=[k for k in op_map if seen[k]==0]; duplicate=[k for k,n in seen.items() if n>1]
 if missing: issues.append(Issue('$.checklists',f'uncovered plan operations: {missing}'))
 if duplicate: issues.append(Issue('$.checklists',f'duplicate-covered plan operations: {duplicate}'))
 if set(contract['change_surface']['components'])!=scope_components or set(contract['change_surface']['files_or_artifacts'])!=scope_files: issues.append(Issue('$.checklists.scope','checklist union must exactly equal approved change surface'))
 if union_ver!=ver_ids: issues.append(Issue('$.checklists.verification_item_ids',f'union must equal approved verification set: {sorted(ver_ids)}'))
 if union_rb!=rb_ids: issues.append(Issue('$.checklists.rollback_item_ids',f'union must equal approved rollback set: {sorted(rb_ids)}'))
 # Required dependency edges.
 expected_edges=set(); plan_cids=defaultdict(list)
 for c in checks: plan_cids[c['source_plan_id']].append((c['source_operation']['sequence'],c['checklist_id']))
 for pid,vals in plan_cids.items():
  vals=sorted(vals)
  for (_,from_cid),(_,to_cid) in zip(vals,vals[1:]): expected_edges.add((from_cid,to_cid,'WITHIN_PLAN_SEQUENCE',None))
 for e in pdeps:
  from_cid=sorted(plan_cids[e['from_plan_id']])[-1][1]; to_cid=sorted(plan_cids[e['to_plan_id']])[0][1]; expected_edges.add((from_cid,to_cid,'PLAN_DEPENDENCY',e['dependency_id']))
 actual_edges={(e['from_checklist_id'],e['to_checklist_id'],e['dependency_type'],e['source_plan_dependency_id']) for e in deps}
 if actual_edges!=expected_edges: issues.append(Issue('$.dependencies',f'must exactly preserve required checklist dependencies; missing={sorted(expected_edges-actual_edges)}, extra={sorted(actual_edges-expected_edges)}'))
 refs,acyclic,roots,leaves,topo,levels,incoming=graph(check_ids,deps)
 if not refs: issues.append(Issue('$.dependencies','contains dangling or self reference'))
 if not acyclic: issues.append(Issue('$.dependencies','dependency graph contains a cycle'))
 if acyclic:
  for i,cid in enumerate(topo,1):
   c=check_by[cid]; level=next(n for n,l in enumerate(levels,1) if cid in l)
   if sorted(c['dependency_checklist_ids'])!=sorted(incoming[cid]): issues.append(Issue(f'$.checklist[{cid}].dependency_checklist_ids','must equal incoming hard dependency edges'))
   if c['execution']['global_sequence']!=i or c['execution']['parallel_group']!=f'LEVEL-{level:03d}': issues.append(Issue(f'$.checklist[{cid}].execution','global sequence or parallel level drift'))
 # Batches exact levels.
 batch_ok=len(batches)==len(levels)
 if batch_ok:
  for n,(b,lvl) in enumerate(zip(sorted(batches,key=lambda x:x['sequence']),levels),1):
   human=any(check_by[x]['execution']['requires_human_action'] for x in lvl); rbs=sorted({r for x in lvl for r in check_by[x]['rollback_item_ids']})
   if b['sequence']!=n or b['parallel_level']!=f'LEVEL-{n:03d}' or b['checklist_ids']!=lvl or b['execution_mode']!=('PARALLEL' if len(lvl)>1 else 'SEQUENTIAL') or b['human_gate_required']!=human or sorted(b['rollback_item_ids'])!=rbs: batch_ok=False
 if not batch_ok: issues.append(Issue('$.batches','execution batches do not match computed dependency levels'))
 # Coverage exactness.
 cov_by={(r['plan_id'],r['operation_sequence']):r for r in cov}; full=partial=none=0; cov_dups=0
 if len(cov_by)!=len(cov): issues.append(Issue('$.coverage','duplicate plan-operation coverage row'))
 for key,(p,op) in op_map.items():
  r=cov_by.get(key)
  if not r: none+=1; issues.append(Issue('$.coverage',f'missing coverage row for {key}')); continue
  if r['coverage_status']=='FULL': full+=1
  elif r['coverage_status']=='PARTIAL': partial+=1
  else: none+=1
  matching=[c['checklist_id'] for c in checks if (c['source_plan_id'],c['source_operation']['sequence'])==key]
  if r['coverage_status']!='FULL' or r['checklist_ids']!=matching or set(r['verification_ids'])!=set(p['verification_item_ids']) or set(r['rollback_ids'])!=set(p['rollback_item_ids']): issues.append(Issue(f'$.coverage[{r["coverage_id"]}]','must be FULL with exact checklist, verification, and rollback mapping'))
  if len(r['checklist_ids'])!=1: cov_dups+=1
 # Findings refs.
 for f in findings:
  for eid in f['evidence_ids']:
   if eid not in ev_ids: issues.append(Issue(f'$.finding[{f["finding_id"]}].evidence_ids',f'unknown evidence: {eid}'))
 # Output summaries.
 af=out['artifact_files']; counts={'checklist_items':len(checks),'dependency_edges':len(deps),'coverage_matrix':len(cov),'execution_batches':len(batches),'findings':len(findings),'report':1}
 for k,n in counts.items():
  if af[k]['record_count']!=n: issues.append(Issue(f'$.output.artifact_files.{k}.record_count',f'expected {n}'))
 cs=out['checklist_summary']; acts=Counter(c['action_type'] for c in checks); exp_cs={'total_items':len(checks),'ready_for_review':sum(c['status']=='READY_FOR_REVIEW' for c in checks),'blocked':sum(c['status']=='BLOCKED' for c in checks),'action_type_counts':dict(acts),'human_action_items':sorted(c['checklist_id'] for c in checks if c['execution']['requires_human_action'])}
 if cs!=exp_cs: issues.append(Issue('$.output.checklist_summary','does not match checklist items'))
 exp_cov={'total_plan_operations':len(op_map),'fully_covered_operations':full,'partially_covered_operations':partial,'uncovered_operations':none,'duplicate_covered_operations':cov_dups,'all_plan_operations_exactly_once':full==len(op_map) and not partial and not none and not duplicate}
 if out['coverage_summary']!=exp_cov: issues.append(Issue('$.output.coverage_summary','does not match coverage'))
 exp_dep={'acyclic':acyclic,'all_references_valid':refs,'root_checklist_ids':roots,'leaf_checklist_ids':leaves,'topological_order':topo,'parallel_levels':levels}
 if out['dependency_analysis']!=exp_dep: issues.append(Issue('$.output.dependency_analysis','does not match dependency graph'))
 exp_atom={'all_single_primary_action':not non_atomic,'all_one_source_operation':not non_atomic,'all_independently_verifiable':not non_atomic,'semantic_decisions_detected':bool(semantic),'scope_expansions_detected':bool(expanded),'non_atomic_item_ids':sorted(non_atomic),'status':'PASS' if not non_atomic and not semantic and not expanded else 'FAIL'}
 if out['atomicity_assessment']!=exp_atom: issues.append(Issue('$.output.atomicity_assessment','does not match checklist semantics'))
 exact_plan_items={c['source_plan_id'] for c in checks}==plan_ids
 exact_ops=not missing and not duplicate and full==len(op_map) and partial==0 and none==0
 recon={'approved_contract_valid':approved,'plan_bundle_digest_valid':digest_ok,'exact_plan_item_set':exact_plan_items,'exact_operation_coverage':exact_ops,'exact_verification_set':union_ver==ver_ids,'exact_rollback_set':union_rb==rb_ids,'approved_change_surface_only':not expanded and set(contract['change_surface']['components'])==scope_components and set(contract['change_surface']['files_or_artifacts'])==scope_files,'status':'PASS' if approved and digest_ok and exact_plan_items and exact_ops and union_ver==ver_ids and union_rb==rb_ids and not expanded else 'FAIL'}
 if out['source_reconciliation']!=recon: issues.append(Issue('$.output.source_reconciliation','does not match source reconciliation'))
 pre=all(c['preconditions'] is not None for c in checks); allv=all(c['verification_item_ids'] for c in checks); allrb=all((not plan_by[c['source_plan_id']]['rollback_item_ids']) or c['rollback_item_ids'] for c in checks); hg=all((not c['execution']['requires_human_action']) or bool(c['execution']['human_action_reason']) for c in checks)
 ready=pre and allv and allrb and hg and batch_ok and acyclic and refs and recon['status']=='PASS' and exp_atom['status']=='PASS' and all(c['status']=='READY_FOR_REVIEW' for c in checks) and not any(f['blocking'] for f in findings)
 er={'all_preconditions_explicit':pre,'all_items_have_verification':allv,'all_planned_rollbacks_mapped':allrb,'human_gates_explicit':hg,'batch_plan_matches_dependency_levels':batch_ok,'status':'READY' if ready else 'NOT_READY'}
 if out['execution_readiness']!=er: issues.append(Issue('$.output.execution_readiness','does not match computed readiness'))
 bytype=Counter(f['type'] for f in findings); blocking=[f for f in findings if f['blocking']]; fs={'total':len(findings),'blocking':len(blocking),'by_type':dict(bytype),'blocking_finding_ids':sorted(f['finding_id'] for f in blocking)}
 if out['finding_summary']!=fs: issues.append(Issue('$.output.finding_summary','does not match findings'))
 gate,state=expected_gate(findings,ready); gd=out['gate_decision']
 if gd['status']!=gate or gd['next_state']!=state or sorted(gd['blocking_finding_ids'])!=fs['blocking_finding_ids']: issues.append(Issue('$.output.gate_decision',f'expected {gate} -> {state}'))
 if a.require_transition_ready and gate!='READY_FOR_CHECKLIST_CRITIQUE': issues.append(Issue('$.transition',f'package is not transition-ready; got {gate}'))
 return issues
def main():
 p=argparse.ArgumentParser(); p.add_argument('--kind',choices=['schema','input','output','checklist','dependency','coverage','batch','finding','package'],required=True); p.add_argument('--file')
 for x in ['input','output','plan-contract','plan-critique-output','planning-output','targets','plans','plan-dependencies','plan-coverage','verifications','rollbacks','planning-findings','solution-contract','ledger','elements','relations','checklists','dependencies','coverage','batches','findings']: p.add_argument('--'+x,dest=x.replace('-','_'))
 p.add_argument('--require-transition-ready',action='store_true'); a=p.parse_args(); issues=[]
 try:
  if a.kind=='schema':
   for path in sorted((ROOT/'schemas').glob('*.json')): Draft202012Validator.check_schema(json.loads(path.read_text()))
  elif a.kind=='package':
   req=['input','output','plan_contract','plan_critique_output','planning_output','targets','plans','plan_dependencies','plan_coverage','verifications','rollbacks','planning_findings','solution_contract','ledger','elements','relations','checklists','dependencies','coverage','batches','findings']; miss=[x for x in req if not getattr(a,x)]
   issues=[Issue('$','missing package arguments: '+', '.join(miss))] if miss else validate_package(a)
  else:
   if not a.file: issues=[Issue('$','--file is required')]
   elif a.kind=='coverage': _,issues=load_coverage(a.file,'coverage',['coverage_id','plan_id','operation_sequence','coverage_status','checklist_ids','verification_ids','rollback_ids','rationale'])
   else: issues=structural(load_doc(a.file),a.kind)
 except Exception as e: issues=[Issue('$',f'validator failure: {type(e).__name__}: {e}')]
 if issues:
  for i in issues: print(i,file=sys.stderr)
  return 1
 print('VALID')
 if a.kind=='package' and a.require_transition_ready: print('Package is transition-ready for CHECKLIST_CRITIQUE')
 return 0
if __name__=='__main__': raise SystemExit(main())
