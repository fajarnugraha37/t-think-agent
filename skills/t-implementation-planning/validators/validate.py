#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, sys
from collections import Counter, deque
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT=Path(__file__).resolve().parents[1]
SCHEMA_FILES={
 'input':'input.schema.json','output':'output.schema.json','target':'planning-target.schema.json','plan':'plan-item.schema.json',
 'dependency':'dependency-edge.schema.json','coverage':'coverage-row.schema.json','verification':'verification-item.schema.json',
 'rollback':'rollback-item.schema.json','finding':'planning-finding.schema.json','contract':'upstream-approved-solution-contract.schema.json',
 'critique_output':'upstream-solution-critique-output.schema.json','evidence':'upstream-evidence-record.schema.json',
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

def schema(kind:str)->dict: return json.loads(SCHEMAS[kind].read_text(encoding='utf-8'))
def pjoin(prefix:str,parts:Iterable[Any])->str: return prefix+''.join(f'[{p}]' if isinstance(p,int) else f'.{p}' for p in parts)
def structural(obj:Any,kind:str,prefix='$')->list[Issue]:
 out=[]
 for e in sorted(Draft202012Validator(schema(kind),format_checker=FormatChecker()).iter_errors(obj),key=lambda x:list(x.absolute_path)):
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

def duplicates(rows,key,label):
 c=Counter(r.get(key) for r in rows if r.get(key)); return [Issue('$',f'duplicate {label}: {x}') for x,n in c.items() if n>1]

def expected_source_refs(c:dict)->set[str]:
 refs=set(c['problem_ids'])|set(c['target_ids'])|set(c['model_ids'])|set(c['invariant_ids'])|set(c['accepted_assumption_ids'])|set(c['accepted_risk_ids'])
 refs.add('behavior_commitments.target_behavior')
 refs|={f'behavior_commitments.preserved_behavior[{i}]' for i,_ in enumerate(c['behavior_commitments']['preserved_behavior'])}
 refs|={f'behavior_commitments.intentionally_changed_behavior[{i}]' for i,_ in enumerate(c['behavior_commitments']['intentionally_changed_behavior'])}
 refs|={f'behavior_commitments.{x}' for x in ['failure_semantics','transaction_semantics','concurrency_semantics']}
 for field in ['components','files_or_artifacts','public_contract_changes','data_changes','configuration_changes','dependencies']:
  refs|={f'change_surface.{field}[{i}]' for i,_ in enumerate(c['change_surface'][field])}
 refs|={f'semantic_constraints[{i}]' for i,_ in enumerate(c['semantic_constraints'])}
 refs|={f'planning_constraints[{i}]' for i,_ in enumerate(c['planning_constraints'])}
 refs|={f'prohibited_changes[{i}]' for i,_ in enumerate(c['prohibited_changes'])}
 return refs

def graph_analysis(plan_ids:set[str],edges:list[dict]):
 indeg={x:0 for x in plan_ids}; adj={x:[] for x in plan_ids}; valid=True
 for e in edges:
  a,b=e['from_plan_id'],e['to_plan_id']
  if a not in plan_ids or b not in plan_ids or a==b: valid=False; continue
  adj[a].append(b); indeg[b]+=1
 roots=sorted([x for x,d in indeg.items() if d==0]); q=deque(roots); topo=[]
 while q:
  x=q.popleft(); topo.append(x)
  for z in sorted(adj[x]):
   indeg[z]-=1
   if indeg[z]==0:
    # maintain deterministic order
    q.append(z)
    q=deque(sorted(q))
 acyclic=len(topo)==len(plan_ids)
 leaves=sorted([x for x in plan_ids if not adj[x]])
 return valid,acyclic,roots,leaves,topo

def expected_gate(findings:list[dict],intrinsic_ready:bool,semantic_fail:bool,approval_bad:bool):
 if approval_bad: return 'RETURN_TO_SOLUTION_CRITIQUE','SOLUTION_CRITIQUE'
 blocking=[f for f in findings if f['blocking']]
 routes={f['route'] for f in blocking}
 if 'PROBLEM_ALIGNMENT' in routes: return 'BLOCKED','IMPLEMENTATION_PLAN'
 if 'INVESTIGATION' in routes: return 'RETURN_TO_INVESTIGATION','INVESTIGATION'
 if 'SYSTEM_MODEL' in routes: return 'RETURN_TO_SYSTEM_MODEL','SYSTEM_MODEL'
 if 'SOLUTION_DESIGN' in routes or semantic_fail: return 'RETURN_TO_SOLUTION_DESIGN','SOLUTION_DESIGN'
 if 'SOLUTION_CRITIQUE' in routes: return 'RETURN_TO_SOLUTION_CRITIQUE','SOLUTION_CRITIQUE'
 if blocking or not intrinsic_ready: return 'BLOCKED','IMPLEMENTATION_PLAN'
 return 'READY_FOR_PLAN_CRITIQUE','PLAN_CRITIQUE'

def validate_package(a)->list[Issue]:
 issues=[]
 inp=load_doc(Path(a.input)); out=load_doc(Path(a.output)); contract=load_doc(Path(a.contract)); crit=load_doc(Path(a.critique_output))
 for obj,kind,prefix in [(inp,'input','$.input'),(out,'output','$.output'),(contract,'contract','$.contract'),(crit,'critique_output','$.critique_output')]: issues+=structural(obj,kind,prefix)
 targets,e=load_jsonl(Path(a.targets),'target'); issues+=e
 plans,e=load_jsonl(Path(a.plans),'plan'); issues+=e
 deps,e=load_jsonl(Path(a.dependencies),'dependency',allow_empty=True); issues+=e
 coverage,e=load_coverage(Path(a.coverage)); issues+=e
 verifs,e=load_jsonl(Path(a.verifications),'verification'); issues+=e
 rollbacks,e=load_jsonl(Path(a.rollbacks),'rollback',allow_empty=True); issues+=e
 findings,e=load_jsonl(Path(a.findings),'finding',allow_empty=True); issues+=e
 ledger,e=load_jsonl(Path(a.ledger),'evidence'); issues+=e
 elements,e=load_jsonl(Path(a.elements),'element'); issues+=e
 relations,e=load_jsonl(Path(a.relations),'relation',allow_empty=True); issues+=e
 if issues: return issues

 # IDs and dictionaries.
 for rows,key,label in [(targets,'target_id','planning target id'),(plans,'plan_id','plan id'),(deps,'dependency_id','dependency id'),(coverage,'coverage_id','coverage id'),(verifs,'verification_id','verification id'),(rollbacks,'rollback_id','rollback id'),(findings,'finding_id','finding id'),(ledger,'id','evidence id'),(elements,'id','model element id'),(relations,'id','model relation id')]: issues+=duplicates(rows,key,label)
 target_ids={x['target_id'] for x in targets}; target_by={x['target_id']:x for x in targets}
 plan_ids={x['plan_id'] for x in plans}; plan_by={x['plan_id']:x for x in plans}
 ver_ids={x['verification_id'] for x in verifs}; rb_ids={x['rollback_id'] for x in rollbacks}; evidence_ids={x['id'] for x in ledger}; model_ids={x['id'] for x in elements}; relation_ids={x['id'] for x in relations}; finding_ids={x['finding_id'] for x in findings}

 # Upstream approval and binding.
 approval_bad=False
 if contract['status']!='APPROVED' or contract['approval']['approved_by_role']!='HUMAN': approval_bad=True; issues.append(Issue('$.contract','must be APPROVED by HUMAN'))
 if crit['gate_decision']['status']!='READY_FOR_IMPLEMENTATION_PLAN': approval_bad=True; issues.append(Issue('$.critique_output.gate_decision.status','must be READY_FOR_IMPLEMENTATION_PLAN'))
 if crit['human_solution_approval']['status']!='APPROVED': approval_bad=True; issues.append(Issue('$.critique_output.human_solution_approval.status','must be APPROVED'))
 if inp['source_solution_critique']['critique_run_id']!=crit['metadata']['critique_run_id']: issues.append(Issue('$.input.source_solution_critique.critique_run_id','does not match source critique output'))
 if inp['source_solution_critique']['artifact_version']!=crit['metadata']['version']: issues.append(Issue('$.input.source_solution_critique.artifact_version','does not match source critique output'))
 for field in ['contract_id','selected_option_id','approved_model_version']:
  if inp['source_solution_contract'][field]!=contract[field]: issues.append(Issue(f'$.input.source_solution_contract.{field}','does not match approved solution contract'))
  if out['source_solution_contract'][field]!=contract[field]: issues.append(Issue(f'$.output.source_solution_contract.{field}','does not match approved solution contract'))
 if crit['human_solution_approval']['solution_contract_id']!=contract['contract_id']: issues.append(Issue('$.critique_output.human_solution_approval.solution_contract_id','does not match contract'))

 # Actual source constraints.
 if not inp['repository_snapshot']['actual_code_reinspection_required']: issues.append(Issue('$.input.repository_snapshot.actual_code_reinspection_required','must be true'))
 if inp['repository_snapshot']['working_tree_status']=='UNKNOWN': issues.append(Issue('$.input.repository_snapshot.working_tree_status','must be known before transition readiness'))
 source_counts={'approved_solution_contract':1,'solution_critique_output':1,'evidence_ledger':len(ledger),'model_elements':len(elements),'model_relations':len(relations)}
 for k,n in source_counts.items():
  if inp['source_artifacts'][k]['record_count']!=n: issues.append(Issue(f'$.input.source_artifacts.{k}.record_count',f'expected {n}'))

 # Target normalization: exact source coverage.
 exp_refs=expected_source_refs(contract); got_refs=[t['source_ref'] for t in targets if t['status']=='ACTIVE']
 if set(got_refs)!=exp_refs:
  for x in sorted(exp_refs-set(got_refs)): issues.append(Issue('$.targets',f'missing normalized source_ref: {x}'))
  for x in sorted(set(got_refs)-exp_refs): issues.append(Issue('$.targets',f'unapproved source_ref: {x}'))
 for x,n in Counter(got_refs).items():
  if n!=1: issues.append(Issue('$.targets',f'source_ref must be normalized exactly once: {x} ({n})'))
 for t in targets:
  for eid in t.get('evidence_ids',[]):
   if eid not in evidence_ids: issues.append(Issue(f'$.target[{t["target_id"]}].evidence_ids',f'unknown evidence: {eid}'))

 # Plan refs and semantic guard.
 semantic_fail=False
 extra_files={x['path'] for x in out['change_surface_reconciliation']['discovered_supporting_files']}
 approved_files=set(contract['change_surface']['files_or_artifacts']); allowed_files=approved_files|extra_files
 approved_components=set(contract['change_surface']['components'])
 incoming={x:set() for x in plan_ids}
 for e in deps:
  if e['from_plan_id'] in plan_ids and e['to_plan_id'] in plan_ids: incoming[e['to_plan_id']].add(e['from_plan_id'])
 for p in plans:
  pid=p['plan_id']
  if p['source_contract_id']!=contract['contract_id']: issues.append(Issue(f'$.plan[{pid}].source_contract_id','does not match contract'))
  for ref in p['planning_target_ids']:
   if ref not in target_ids: issues.append(Issue(f'$.plan[{pid}].planning_target_ids',f'unknown target: {ref}'))
  for ref in p['problem_ids']:
   if ref not in contract['problem_ids']: issues.append(Issue(f'$.plan[{pid}].problem_ids',f'unapproved problem ref: {ref}'))
  for ref in p['model_ids']:
   if ref not in model_ids or ref not in contract['model_ids']: issues.append(Issue(f'$.plan[{pid}].model_ids',f'unknown or unapproved model ref: {ref}'))
  for ref in p['evidence_ids']:
   if ref not in evidence_ids or ref not in contract['evidence_ids']: issues.append(Issue(f'$.plan[{pid}].evidence_ids',f'unknown or unapproved evidence ref: {ref}'))
  for ref in p['invariant_ids']:
   if ref not in contract['invariant_ids'] and ref not in model_ids: issues.append(Issue(f'$.plan[{pid}].invariant_ids',f'unknown invariant ref: {ref}'))
  for ref in p['risk_ids']:
   if ref not in contract['accepted_risk_ids']: issues.append(Issue(f'$.plan[{pid}].risk_ids',f'unaccepted risk ref: {ref}'))
  for ref in p['verification_item_ids']:
   if ref not in ver_ids: issues.append(Issue(f'$.plan[{pid}].verification_item_ids',f'unknown verification: {ref}'))
  for ref in p['rollback_item_ids']:
   if ref not in rb_ids: issues.append(Issue(f'$.plan[{pid}].rollback_item_ids',f'unknown rollback: {ref}'))
  for ref in p['depends_on_plan_ids']:
   if ref not in plan_ids: issues.append(Issue(f'$.plan[{pid}].depends_on_plan_ids',f'unknown plan dependency: {ref}'))
  if set(p['depends_on_plan_ids'])!=incoming[pid]: issues.append(Issue(f'$.plan[{pid}].depends_on_plan_ids','must exactly match incoming dependency edges'))
  if not set(p['affected_components'])<=approved_components: issues.append(Issue(f'$.plan[{pid}].affected_components','contains component outside approved change surface'))
  for f in p['affected_files_or_artifacts']:
   if f not in allowed_files: issues.append(Issue(f'$.plan[{pid}].affected_files_or_artifacts',f'unreconciled artifact: {f}'))
  si=p['semantic_impact']
  if si['introduces_new_semantic_decision'] or not si['approved_by_contract'] or si['prohibited_change_conflicts']:
   semantic_fail=True
  seq=[x['sequence'] for x in p['implementation_operations']]
  if seq!=list(range(1,len(seq)+1)): issues.append(Issue(f'$.plan[{pid}].implementation_operations','sequence must be contiguous starting at 1'))

 # Discovered files must be evidence-backed and actually referenced.
 plan_files={f for p in plans for f in p['affected_files_or_artifacts']}
 for d in out['change_surface_reconciliation']['discovered_supporting_files']:
  if d['path'] not in plan_files: issues.append(Issue('$.output.change_surface_reconciliation.discovered_supporting_files',f'unused discovered file: {d["path"]}'))
  for eid in d['evidence_ids']:
   if eid not in evidence_ids: issues.append(Issue('$.output.change_surface_reconciliation.discovered_supporting_files',f'unknown evidence: {eid}'))
 if out['change_surface_reconciliation']['unapproved_scope_expansions']: semantic_fail=True
 if set(out['change_surface_reconciliation']['approved_components_covered'])!=approved_components: issues.append(Issue('$.output.change_surface_reconciliation.approved_components_covered','must exactly cover approved components'))
 if set(out['change_surface_reconciliation']['approved_artifacts_covered'])!=approved_files: issues.append(Issue('$.output.change_surface_reconciliation.approved_artifacts_covered','must exactly cover approved artifacts'))

 # Dependency graph.
 refs_valid,acyclic,roots,leaves,topo=graph_analysis(plan_ids,deps)
 for e in deps:
  if e['from_plan_id'] not in plan_ids: issues.append(Issue(f'$.dependency[{e["dependency_id"]}].from_plan_id','unknown plan'))
  if e['to_plan_id'] not in plan_ids: issues.append(Issue(f'$.dependency[{e["dependency_id"]}].to_plan_id','unknown plan'))
  if e['from_plan_id']==e['to_plan_id']: issues.append(Issue(f'$.dependency[{e["dependency_id"]}]','self dependency is prohibited'))
 if not acyclic: issues.append(Issue('$.dependencies','dependency graph contains a cycle'))
 da=out['dependency_analysis']
 if da['acyclic']!=acyclic or da['all_references_valid']!=refs_valid or set(da['root_plan_ids'])!=set(roots) or set(da['leaf_plan_ids'])!=set(leaves) or da['topological_order']!=topo:
  issues.append(Issue('$.output.dependency_analysis','does not match computed graph analysis'))

 # Coverage matrix exactly one row per target.
 cov_by=Counter(x['planning_target_id'] for x in coverage)
 for tid in target_ids:
  if cov_by[tid]!=1: issues.append(Issue('$.coverage',f'target {tid} must have exactly one coverage row, found {cov_by[tid]}'))
 for row in coverage:
  cid=row['coverage_id']; tid=row['planning_target_id']
  if tid not in target_ids: issues.append(Issue(f'$.coverage[{cid}].planning_target_id',f'unknown target: {tid}'))
  for ref in row['plan_ids']:
   if ref not in plan_ids: issues.append(Issue(f'$.coverage[{cid}].plan_ids',f'unknown plan: {ref}'))
  for ref in row['verification_ids']:
   if ref not in ver_ids: issues.append(Issue(f'$.coverage[{cid}].verification_ids',f'unknown verification: {ref}'))
  for ref in row['rollback_ids']:
   if ref not in rb_ids: issues.append(Issue(f'$.coverage[{cid}].rollback_ids',f'unknown rollback: {ref}'))
  if tid in target_by and target_by[tid]['mandatory'] and row['coverage_status']!='FULL': issues.append(Issue(f'$.coverage[{cid}].coverage_status','mandatory target must be FULL'))
  if row['coverage_status']=='FULL' and (not row['plan_ids'] or not row['verification_ids']): issues.append(Issue(f'$.coverage[{cid}]','FULL coverage requires plan and verification refs'))
 covered_plans={p for row in coverage for p in row['plan_ids']}
 for pid in plan_ids-covered_plans: issues.append(Issue('$.coverage',f'plan item is not represented in coverage: {pid}'))

 # Verification.
 categories={v['category'] for v in verifs}
 for v in verifs:
  vid=v['verification_id']
  for ref in v['plan_ids']:
   if ref not in plan_ids: issues.append(Issue(f'$.verification[{vid}].plan_ids',f'unknown plan: {ref}'))
  for ref in v['planning_target_ids']:
   if ref not in target_ids: issues.append(Issue(f'$.verification[{vid}].planning_target_ids',f'unknown target: {ref}'))
 for p in plans:
  for vid in p['verification_item_ids']:
   vv=next((x for x in verifs if x['verification_id']==vid),None)
   if vv and p['plan_id'] not in vv['plan_ids']: issues.append(Issue(f'$.plan[{p["plan_id"]}].verification_item_ids',f'{vid} does not map back to plan'))
 req_cats=set(inp['planning_configuration']['required_test_categories'])
 if not req_cats<=categories: issues.append(Issue('$.verifications',f'missing required categories: {sorted(req_cats-categories)}'))
 # Required planning dimensions may be satisfied by plan items, verification work, or rollback artifacts.
 change_types={p['change_type'] for p in plans}
 dimension_ok={
  'CODE':'CODE' in change_types,'DATABASE':'DATABASE_SCHEMA' in change_types,'DATA':'DATA_BACKFILL' in change_types,
  'CONFIGURATION':'CONFIGURATION' in change_types,'DEPLOYMENT':'DEPLOYMENT' in change_types,'MIGRATION':bool({'MIGRATION','DATABASE_SCHEMA','DATA_BACKFILL'} & change_types),
  'TESTING':'TEST' in change_types,'OBSERVABILITY':'OBSERVABILITY' in change_types,'SECURITY':('SECURITY_CONTROL' in change_types or 'SECURITY' in categories),
  'ROLLBACK':bool(rollbacks),'COMPATIBILITY':bool({'COMPATIBILITY','CONTRACT'} & categories),'OPERATIONS':bool({'OPERATIONS','DEPLOYMENT'} & change_types)}
 missing_dims=[d for d in inp['planning_configuration']['required_plan_dimensions'] if not dimension_ok.get(d,False)]
 if missing_dims: issues.append(Issue('$.plans',f'missing required planning dimensions: {missing_dims}'))
 flags={
  'pre_patch_regression_planned':'REGRESSION_REPRODUCTION' in categories,
  'negative_paths_planned':any(v['negative_path'] for v in verifs) and 'NEGATIVE_PATH' in categories,
  'invariants_planned':'INVARIANT' in categories,
  'compatibility_planned':bool({'COMPATIBILITY','CONTRACT'} & categories)}
 all_plans_verified=all(bool(p['verification_item_ids']) for p in plans)
 vr=out['verification_readiness']
 if vr['all_plan_items_have_verification']!=all_plans_verified: issues.append(Issue('$.output.verification_readiness.all_plan_items_have_verification','does not match plan items'))
 if set(vr['required_categories_covered'])!=categories: issues.append(Issue('$.output.verification_readiness.required_categories_covered','must exactly match present categories'))
 for k,val in flags.items():
  if vr[k]!=val: issues.append(Issue(f'$.output.verification_readiness.{k}','does not match verification plan'))
 verification_ready=all_plans_verified and req_cats<=categories and all(flags.values())
 if vr['status']!=('READY' if verification_ready else 'INCOMPLETE'): issues.append(Issue('$.output.verification_readiness.status','does not match computed readiness'))

 # Rollback.
 rb_required=set(inp['planning_configuration']['rollback_required_change_types'])
 all_rb=True
 for p in plans:
  if p['change_type'] in rb_required and not p['rollback_item_ids']:
   all_rb=False; issues.append(Issue(f'$.plan[{p["plan_id"]}].rollback_item_ids','rollback is required for this change type'))
 for r in rollbacks:
  rid=r['rollback_id']
  for ref in r['plan_ids']:
   if ref not in plan_ids: issues.append(Issue(f'$.rollback[{rid}].plan_ids',f'unknown plan: {ref}'))
  for ref in r['verification_item_ids']:
   if ref not in ver_ids: issues.append(Issue(f'$.rollback[{rid}].verification_item_ids',f'unknown verification: {ref}'))
  for pid in r['plan_ids']:
   if pid in plan_by and rid not in plan_by[pid]['rollback_item_ids']: issues.append(Issue(f'$.rollback[{rid}].plan_ids',f'{pid} does not map back to rollback'))
 data_addressed=all(bool(r['data_preservation']) for r in rollbacks)
 irreversible_explicit=all('irreversible_effects' in r for r in rollbacks)
 rr=out['rollback_readiness']; rollback_ready=all_rb and data_addressed and irreversible_explicit
 if rr['all_required_plan_items_have_rollback']!=all_rb or rr['data_preservation_addressed']!=data_addressed or rr['irreversible_effects_explicit']!=irreversible_explicit: issues.append(Issue('$.output.rollback_readiness','does not match rollback plan'))
 if rr['status']!=('READY' if rollback_ready else 'INCOMPLETE'): issues.append(Issue('$.output.rollback_readiness.status','does not match computed readiness'))

 # Findings and routing.
 for f in findings:
  for eid in f['evidence_ids']:
   if eid not in evidence_ids: issues.append(Issue(f'$.finding[{f["finding_id"]}].evidence_ids',f'unknown evidence: {eid}'))
 by_type=Counter(f['type'] for f in findings); blocking=[f for f in findings if f['blocking']]; fs=out['finding_summary']
 if fs['total']!=len(findings) or fs['blocking']!=len(blocking) or fs['by_type']!=dict(by_type) or set(fs['blocking_finding_ids'])!={f['finding_id'] for f in blocking}: issues.append(Issue('$.output.finding_summary','does not match findings'))

 # Summary and artifact counts.
 af=out['artifact_files']; expected_counts={'planning_targets':len(targets),'plan_items':len(plans),'dependency_edges':len(deps),'coverage_matrix':len(coverage),'verification_plan':len(verifs),'rollback_plan':len(rollbacks),'planning_findings':len(findings)}
 for k,n in expected_counts.items():
  if af[k]['record_count']!=n: issues.append(Issue(f'$.output.artifact_files.{k}.record_count',f'expected {n}'))
 cc=Counter(p['change_type'] for p in plans); ps=out['plan_summary']
 if ps['total_plan_items']!=len(plans) or ps['ready_for_review']!=sum(p['status']=='READY_FOR_REVIEW' for p in plans) or ps['blocked']!=sum(p['status']=='BLOCKED' for p in plans) or ps['change_type_counts']!=dict(cc): issues.append(Issue('$.output.plan_summary','does not match plan items'))
 mandatory=[t for t in targets if t['mandatory']]; cov_map={r['planning_target_id']:r for r in coverage}; full=sum(cov_map.get(t['target_id'],{}).get('coverage_status')=='FULL' for t in mandatory); partial=sum(r['coverage_status']=='PARTIAL' for r in coverage); none=sum(r['coverage_status']=='NONE' for r in coverage)
 cs=out['coverage_summary']; expected_cs={'total_targets':len(targets),'mandatory_targets':len(mandatory),'fully_covered_mandatory_targets':full,'partially_covered_targets':partial,'uncovered_targets':none,'all_mandatory_targets_fully_covered':full==len(mandatory)}
 if cs!=expected_cs: issues.append(Issue('$.output.coverage_summary','does not match coverage matrix'))

 # Semantic guard exactness.
 sg=out['semantic_decision_guard']; computed_semantic=semantic_fail or bool(out['change_surface_reconciliation']['unapproved_scope_expansions'])
 if sg['new_semantic_decisions_detected']!=any(p['semantic_impact']['introduces_new_semantic_decision'] for p in plans): issues.append(Issue('$.output.semantic_decision_guard.new_semantic_decisions_detected','does not match plan items'))
 if sg['unapproved_behavior_changes_detected']!=any(not p['semantic_impact']['approved_by_contract'] for p in plans): issues.append(Issue('$.output.semantic_decision_guard.unapproved_behavior_changes_detected','does not match plan items'))
 conflicts=[x for p in plans for x in p['semantic_impact']['prohibited_change_conflicts']]
 if sg['prohibited_change_conflicts']!=conflicts: issues.append(Issue('$.output.semantic_decision_guard.prohibited_change_conflicts','does not match plan items'))
 if sg['status']!=('FAIL' if computed_semantic else 'PASS'): issues.append(Issue('$.output.semantic_decision_guard.status','does not match computed semantic guard'))

 intrinsic_ready=(full==len(mandatory) and acyclic and refs_valid and verification_ready and rollback_ready and not computed_semantic and all(p['status']=='READY_FOR_REVIEW' for p in plans) and not out['change_surface_reconciliation']['unapproved_scope_expansions'])
 gate,next_state=expected_gate(findings,intrinsic_ready,computed_semantic,approval_bad)
 gd=out['gate_decision']
 if gd['status']!=gate or gd['next_state']!=next_state: issues.append(Issue('$.output.gate_decision',f'expected {gate} -> {next_state}'))
 if set(gd['blocking_finding_ids'])!={f['finding_id'] for f in blocking}: issues.append(Issue('$.output.gate_decision.blocking_finding_ids','does not match blocking findings'))
 expected_status='COMPLETE' if gate=='READY_FOR_PLAN_CRITIQUE' else 'BLOCKED'
 if out['metadata']['status']!=expected_status: issues.append(Issue('$.output.metadata.status',f'expected {expected_status} for gate {gate}'))
 if a.require_transition_ready and gate!='READY_FOR_PLAN_CRITIQUE': issues.append(Issue('$.output.gate_decision.status','package is not transition-ready for PLAN_CRITIQUE'))
 return issues

def main():
 p=argparse.ArgumentParser(description='Validate Implementation Planning artifacts')
 p.add_argument('--kind',required=True,choices=['input','output','target','plan','dependency','coverage','verification','rollback','finding','contract','critique_output','package'])
 p.add_argument('--file')
 for x in ['input','output','contract','critique-output','targets','plans','dependencies','coverage','verifications','rollbacks','findings','ledger','elements','relations']: p.add_argument('--'+x)
 p.add_argument('--require-transition-ready',action='store_true')
 a=p.parse_args()
 if a.kind=='package':
  needed=['input','output','contract','critique_output','targets','plans','dependencies','coverage','verifications','rollbacks','findings','ledger','elements','relations']
  miss=[x for x in needed if getattr(a,x,None) is None]
  if miss: p.error('missing package arguments: '+', '.join(miss))
  issues=validate_package(a)
 elif a.kind in {'target','plan','dependency','verification','rollback','finding'}:
  if not a.file: p.error('--file required')
  _,issues=load_jsonl(Path(a.file),a.kind,allow_empty=a.kind in {'dependency','rollback','finding'})
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
 print('VALID'+(' and transition-ready for PLAN_CRITIQUE' if a.kind=='package' and a.require_transition_ready else ''))
 return 0
if __name__=='__main__': raise SystemExit(main())
