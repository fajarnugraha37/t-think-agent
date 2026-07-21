#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, warnings
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any
import yaml
warnings.filterwarnings('ignore',category=DeprecationWarning)
from jsonschema import Draft202012Validator, FormatChecker, RefResolver
ROOT=Path(__file__).resolve().parents[1]
MAP={'input':'input.schema.json','output':'output.schema.json','execution':'execution-record.schema.json','change':'change-record.schema.json','command':'command-result.schema.json','verification':'verification-result.schema.json','rollback':'rollback-result.schema.json','finding':'implementation-finding.schema.json','repository':'repository-state.schema.json','result_contract':'implementation-result-contract.schema.json','checklist_contract':'upstream-approved-checklist-contract.schema.json','critique_output':'upstream-checklist-critique-output.schema.json','plan_contract':'upstream-approved-plan-contract.schema.json','checklist':'upstream-checklist-item.schema.json','batch':'upstream-execution-batch.schema.json','evidence':'upstream-evidence-record.schema.json'}
SCHEMAS={k:ROOT/'schemas'/v for k,v in MAP.items()}
class Issue:
 def __init__(self,path,message): self.path,self.message=path,message
 def __str__(self): return f'{self.path}: {self.message}'
def norm(v):
 if isinstance(v,(date,datetime)): return v.isoformat()
 if isinstance(v,dict): return {k:norm(x) for k,x in v.items()}
 if isinstance(v,list): return [norm(x) for x in v]
 return v
def load(path):
 p=Path(path); t=p.read_text(encoding='utf-8'); return json.loads(t) if p.suffix=='.json' else norm(yaml.safe_load(t))
def store():
 out={}
 for p in (ROOT/'schemas').glob('*.json'):
  d=json.loads(p.read_text()); out[p.name]=d; out[p.as_uri()]=d
  if '$id' in d: out[d['$id']]=d
 return out
STORE=store()
def structural(obj,kind,prefix='$'):
 s=json.loads(SCHEMAS[kind].read_text()); r=RefResolver.from_schema(s,store=STORE); out=[]
 for e in sorted(Draft202012Validator(s,resolver=r,format_checker=FormatChecker()).iter_errors(obj),key=lambda z:list(z.absolute_path)):
  path=prefix+''.join(f'[{x}]' if isinstance(x,int) else f'.{x}' for x in e.absolute_path); out.append(Issue(path,e.message))
 return out
def jsonl(path,kind,empty=False):
 rows=[]; issues=[]
 for n,line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(),1):
  if not line.strip(): continue
  try:r=json.loads(line)
  except Exception as e: issues.append(Issue(f'{path}:{n}',f'invalid JSON: {e}')); continue
  rows.append(r); issues+=structural(r,kind,f'{path}:{n}$')
 if not rows and not empty: issues.append(Issue(str(path),'must contain at least one record'))
 return rows,issues
def dg(x): return 'sha256:'+hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def bundle(ex,ch,cmd,ver,rb,find,before,after): return dg({'executions':ex,'changes':ch,'commands':cmd,'verifications':ver,'rollbacks':rb,'findings':find,'repository_before':before,'repository_after':after})
def dup(rows,key,label):
 c=Counter(x.get(key) for x in rows); return [Issue('$',f'duplicate {label}: {k}') for k,n in c.items() if k and n>1]
def expected_route(findings,executions,contract):
 openf=[x for x in findings if x['status']=='OPEN' and x['blocking']]
 priority=[('PROBLEM_ALIGNMENT','RETURN_TO_PROBLEM_ALIGNMENT','PROBLEM_ALIGNMENT'),('INVESTIGATION','RETURN_TO_INVESTIGATION','INVESTIGATION'),('SYSTEM_MODEL','RETURN_TO_SYSTEM_MODEL','SYSTEM_MODEL'),('SOLUTION_DESIGN','RETURN_TO_SOLUTION_DESIGN','SOLUTION_DESIGN'),('SOLUTION_CRITIQUE','RETURN_TO_SOLUTION_CRITIQUE','SOLUTION_CRITIQUE'),('PLAN_CRITIQUE','RETURN_TO_PLAN_CRITIQUE','PLAN_CRITIQUE'),('IMPLEMENTATION_PLAN','RETURN_TO_IMPLEMENTATION_PLAN','IMPLEMENTATION_PLAN'),('CHECKLIST_CRITIQUE','RETURN_TO_CHECKLIST_CRITIQUE','CHECKLIST_CRITIQUE'),('IMPLEMENTATION_CHECKLIST','RETURN_TO_IMPLEMENTATION_CHECKLIST','IMPLEMENTATION_CHECKLIST')]
 routes=[x['route'] for x in openf]
 for r,g,s in priority:
  if r in routes:return g,s
 failed=[x for x in executions if x['status'] in ['FAILED','BLOCKED']]
 if failed:
  attempts=max((x['attempt_count'] for x in failed),default=0)
  if attempts < contract['failure_budget']['max_remediation_attempts']: return 'REMEDIATION_REQUIRED','BOUNDED_IMPLEMENTATION'
  return 'BLOCKED','BOUNDED_IMPLEMENTATION'
 if all(x['status']=='COMPLETED' for x in executions): return 'READY_FOR_SELF_REVIEW','SELF_REVIEW'
 return 'BLOCKED','BOUNDED_IMPLEMENTATION'
def validate_package(a):
 issues=[]
 docs={k:load(getattr(a,k)) for k in ['input','output','checklist_contract','critique_output','plan_contract','repository_before','repository_after','result_contract']}
 for k,kind in [('input','input'),('output','output'),('checklist_contract','checklist_contract'),('critique_output','critique_output'),('plan_contract','plan_contract'),('repository_before','repository'),('repository_after','repository'),('result_contract','result_contract')]: issues+=structural(docs[k],kind,f'$.{k}')
 checks,e=jsonl(a.checklists,'checklist'); issues+=e
 batches,e=jsonl(a.batches,'batch'); issues+=e
 ledger,e=jsonl(a.ledger,'evidence'); issues+=e
 executions,e=jsonl(a.executions,'execution'); issues+=e
 changes,e=jsonl(a.changes,'change',True); issues+=e
 commands,e=jsonl(a.commands,'command',True); issues+=e
 verifications,e=jsonl(a.verifications,'verification',True); issues+=e
 rollbacks,e=jsonl(a.rollbacks,'rollback',True); issues+=e
 findings,e=jsonl(a.findings,'finding',True); issues+=e
 if issues:return issues
 inp,out,cc,co,pc,before,after,rc=[docs[k] for k in ['input','output','checklist_contract','critique_output','plan_contract','repository_before','repository_after','result_contract']]
 for rows,key,label in [(checks,'checklist_id','checklist id'),(batches,'batch_id','batch id'),(ledger,'id','evidence id'),(executions,'execution_id','execution id'),(changes,'change_id','change id'),(commands,'command_id','command id'),(verifications,'result_id','verification result id'),(rollbacks,'rollback_result_id','rollback result id'),(findings,'finding_id','finding id')]: issues+=dup(rows,key,label)
 check={x['checklist_id']:x for x in checks}; exby={x['checklist_id']:x for x in executions}; chby={x['change_id']:x for x in changes}; cmdby={x['command_id']:x for x in commands}; vby={x['result_id']:x for x in verifications}; rbby={x['rollback_result_id']:x for x in rollbacks}; fby={x['finding_id']:x for x in findings}; batchby={x['batch_id']:x for x in batches}; evidence_ids={x['id'] for x in ledger}
 # Source gate and binding.
 if co['gate_decision']['status']!='READY_FOR_BOUNDED_IMPLEMENTATION' or co['gate_decision']['next_state']!='BOUNDED_IMPLEMENTATION': issues.append(Issue('$.critique_output','source is not ready for bounded implementation'))
 if co['execution_authorization_readiness']['status']!='READY' or not co['execution_authorization_readiness']['execution_authorized']: issues.append(Issue('$.critique_output.execution_authorization_readiness','execution is not authorized'))
 if cc['status']!='APPROVED' or cc['approval']['approver_role']!='HUMAN' or not cc['approval']['execution_authorization']: issues.append(Issue('$.checklist_contract','must be human-approved and execution-authorized'))
 if pc['status']!='APPROVED': issues.append(Issue('$.plan_contract','must be approved'))
 src=inp['source_authorization']; expected={'approved_checklist_contract_id':cc['contract_id'],'checklist_bundle_digest':cc['checklist_bundle_digest'],'checklist_critique_run_id':co['metadata']['critique_run_id'],'repository_commit':cc['repository_snapshot']['commit_sha']}
 for k,v in expected.items():
  if src[k]!=v: issues.append(Issue(f'$.input.source_authorization.{k}',f'expected {v}'))
  if out['source_binding'][k if k!='approved_checklist_contract_id' else 'approved_checklist_contract_id']!=v: issues.append(Issue(f'$.output.source_binding.{k}',f'expected {v}'))
 if inp['execution_controls']['max_remediation_attempts']!=cc['failure_budget']['max_remediation_attempts']: issues.append(Issue('$.input.execution_controls.max_remediation_attempts','must equal approved failure budget'))
 if before['commit_sha']!=cc['repository_snapshot']['commit_sha'] or before['working_tree_status']!=cc['repository_snapshot']['working_tree_status']: issues.append(Issue('$.repository_before','must match approved repository baseline'))
 if before['repository_id']!=cc['repository_snapshot']['repository_id'] or before['branch']!=cc['repository_snapshot']['branch']: issues.append(Issue('$.repository_before','repository identity must match approved contract'))
 if after['repository_id']!=before['repository_id'] or after['branch']!=before['branch']: issues.append(Issue('$.repository_after','repository identity changed'))
 # Source artifact counts and digests.
 count_expect={'approved_checklist_contract':1,'checklist_critique_output':1,'approved_plan_contract':1,'checklist_items':len(checks),'execution_batches':len(batches),'evidence_ledger':len(ledger)}
 path_attr={'approved_checklist_contract':'checklist_contract','checklist_critique_output':'critique_output','approved_plan_contract':'plan_contract','checklist_items':'checklists','execution_batches':'batches','evidence_ledger':'ledger'}
 for k,n in count_expect.items():
  ref=inp['source_artifacts'][k]
  if ref['record_count']!=n: issues.append(Issue(f'$.input.source_artifacts.{k}.record_count',f'expected {n}'))
  actual='sha256:'+hashlib.sha256(Path(getattr(a,path_attr[k])).read_bytes()).hexdigest()
  if ref.get('digest')!=actual: issues.append(Issue(f'$.input.source_artifacts.{k}.digest',f'expected {actual}'))
 # Checklist contract exactness.
 if set(check)!=set(cc['checklist_item_ids']): issues.append(Issue('$.checklists','IDs do not match approved checklist contract'))
 binding={x['checklist_id']:x for x in cc['operation_bindings']}
 for cid,c in check.items():
  b=binding.get(cid)
  if not b: issues.append(Issue(f'$.checklists.{cid}','missing operation binding')); continue
  if b['checklist_item_digest']!=dg(c) or b['source_operation_digest']!=c['source_operation']['digest'] or b['source_plan_id']!=c['source_plan_id']: issues.append(Issue(f'$.checklists.{cid}','operation binding or checklist digest drift'))
 if set(batchby)!=set(cc['execution_batch_ids']): issues.append(Issue('$.batches','batch IDs do not match approved contract'))
 # One execution per checklist and exact order.
 if set(exby)!=set(check): issues.append(Issue('$.executions','must contain exactly one execution record per approved checklist item'))
 ordered=[x['checklist_id'] for x in executions]
 # Completed prefix must preserve approved execution order; pending may follow.
 active=[cid for cid in ordered if exby[cid]['status']!='PENDING']
 expected_prefix=cc['execution_order'][:len(active)]
 if active!=expected_prefix: issues.append(Issue('$.executions','non-pending executions must preserve approved execution order'))
 # Check records.
 human_batches=set(cc['human_gate_batch_ids']); surface=set(cc['change_surface']['files_or_artifacts'])
 item_scope={cid:set(c['scope']['files_or_artifacts']) for cid,c in check.items()}
 for cid,e in exby.items():
  c=check[cid]; b=binding[cid]
  if e['implementation_run_id']!=inp['metadata']['implementation_run_id'] or e['source_plan_id']!=c['source_plan_id'] or e['source_operation_digest']!=b['source_operation_digest'] or e['checklist_item_digest']!=b['checklist_item_digest']: issues.append(Issue(f'$.executions.{cid}','source binding mismatch'))
  if e['attempt_count']>cc['failure_budget']['max_remediation_attempts']+1: issues.append(Issue(f'$.executions.{cid}.attempt_count','exceeds failure budget plus initial attempt'))
  if e['status']=='COMPLETED':
   if not e['started_at'] or not e['completed_at'] or e['failure'] is not None: issues.append(Issue(f'$.executions.{cid}','completed item requires timestamps and no failure'))
   if not e['command_result_ids'] or not e['verification_result_ids'] or not e['completion_evidence']: issues.append(Issue(f'$.executions.{cid}','completed item lacks command, verification, or completion evidence'))
  if e['status']=='PENDING' and (e['started_at'] or e['completed_at'] or e['attempt_count']!=0): issues.append(Issue(f'$.executions.{cid}','pending item must be untouched'))
  for x in e['change_ids']:
   if x not in chby: issues.append(Issue(f'$.executions.{cid}.change_ids',f'unknown change {x}'))
   elif chby[x]['checklist_id']!=cid: issues.append(Issue(f'$.executions.{cid}.change_ids',f'{x} belongs to another checklist item'))
  for x in e['command_result_ids']:
   if x not in cmdby or cid not in cmdby[x]['checklist_ids']: issues.append(Issue(f'$.executions.{cid}.command_result_ids',f'invalid command reference {x}'))
  for x in e['verification_result_ids']:
   if x not in vby or cid not in vby[x]['checklist_ids']: issues.append(Issue(f'$.executions.{cid}.verification_result_ids',f'invalid verification reference {x}'))
  for x in e['rollback_result_ids']:
   if x not in rbby or cid not in rbby[x]['checklist_ids']: issues.append(Issue(f'$.executions.{cid}.rollback_result_ids',f'invalid rollback reference {x}'))
  if e['failure']:
   for x in e['failure']['finding_ids']:
    if x not in fby: issues.append(Issue(f'$.executions.{cid}.failure.finding_ids',f'unknown finding {x}'))
  hb=[b for b in batches if cid in b['checklist_ids'] and b['batch_id'] in human_batches]
  if hb and e['status']!='PENDING':
   if not e['human_authorization'] or e['human_authorization']['authorizer_role']!='HUMAN' or e['human_authorization']['batch_id']!=hb[0]['batch_id'] or cid not in e['human_authorization']['scope']: issues.append(Issue(f'$.executions.{cid}.human_authorization','required human gate authorization missing or invalid'))
  elif e['human_authorization'] is not None: issues.append(Issue(f'$.executions.{cid}.human_authorization','authorization supplied for non-gated item'))
 # Dependencies complete before item starts.
 pos={cid:i for i,cid in enumerate(cc['execution_order'])}
 for cid,c in check.items():
  e=exby.get(cid)
  if not e or e['status']=='PENDING': continue
  for dep in c['dependency_checklist_ids']:
   if dep not in exby or exby[dep]['status']!='COMPLETED' or pos[dep]>=pos[cid]: issues.append(Issue(f'$.executions.{cid}','dependency not completed first: '+dep))
 # Changes and scope.
 for x in changes:
  cid=x['checklist_id']
  if cid not in check: issues.append(Issue(f'$.changes.{x["change_id"]}','unknown checklist id')); continue
  if x['path'] not in surface: issues.append(Issue(f'$.changes.{x["change_id"]}.path','outside approved change surface'))
  if x['path'] not in item_scope[cid]: issues.append(Issue(f'$.changes.{x["change_id"]}.path','outside checklist item scope'))
  if x['change_type']=='CREATE' and x['before_digest'] is not None: issues.append(Issue(f'$.changes.{x["change_id"]}','CREATE must have null before digest'))
  if x['change_type']=='DELETE' and x['after_digest'] is not None: issues.append(Issue(f'$.changes.{x["change_id"]}','DELETE must have null after digest'))
  if x['change_type'] not in ['CREATE','DELETE','NO_FILE_CHANGE'] and (not x['before_digest'] or not x['after_digest']): issues.append(Issue(f'$.changes.{x["change_id"]}','mutation requires before and after digests'))
 # Repository changed paths exact union.
 if set(after['changed_paths'])!=set(x['path'] for x in changes): issues.append(Issue('$.repository_after.changed_paths','must equal exact union of change record paths'))
 if not set(after['changed_paths']).issubset(surface): issues.append(Issue('$.repository_after.changed_paths','contains path outside approved surface'))
 # Command consistency.
 for x in commands:
  if any(cid not in check for cid in x['checklist_ids']): issues.append(Issue(f'$.commands.{x["command_id"]}','unknown checklist id'))
  if (x['status']=='PASS')!=(x['exit_code']==0): issues.append(Issue(f'$.commands.{x["command_id"]}','PASS must have exit_code 0 and non-PASS must not'))
 # Verification exact contract set only on successful completion; loopbacks may be partial.
 ver_ids=[x['verification_item_id'] for x in verifications]
 if len(ver_ids)!=len(set(ver_ids)): issues.append(Issue('$.verifications','duplicate verification_item_id'))
 for x in verifications:
  if x['verification_item_id'] not in pc['verification_item_ids']: issues.append(Issue(f'$.verifications.{x["result_id"]}','unknown verification item'))
  expected_cids={cid for cid,c in check.items() if x['verification_item_id'] in c['verification_item_ids']}
  if set(x['checklist_ids'])!=expected_cids: issues.append(Issue(f'$.verifications.{x["result_id"]}.checklist_ids',f'expected {sorted(expected_cids)}'))
  if any(c not in cmdby for c in x['command_result_ids']): issues.append(Issue(f'$.verifications.{x["result_id"]}.command_result_ids','unknown command'))
 # Rollbacks exact known ids and invocation semantics.
 for x in rollbacks:
  if x['rollback_item_id'] not in pc['rollback_item_ids']: issues.append(Issue(f'$.rollbacks.{x["rollback_result_id"]}','unknown rollback item'))
  if not x['invoked'] and x['outcome']!='NOT_INVOKED': issues.append(Issue(f'$.rollbacks.{x["rollback_result_id"]}','not invoked must have NOT_INVOKED outcome'))
  if x['invoked'] and x['outcome']=='NOT_INVOKED': issues.append(Issue(f'$.rollbacks.{x["rollback_result_id"]}','invoked rollback cannot be NOT_INVOKED'))
 # Findings evidence and routes.
 valid_targets=set(check)|set(chby)|set(cmdby)|set(vby)|set(rbby)
 for x in findings:
  if not set(x['target_ids']).issubset(valid_targets): issues.append(Issue(f'$.findings.{x["finding_id"]}.target_ids','contains unknown target'))
  if not x['evidence_refs']: issues.append(Issue(f'$.findings.{x["finding_id"]}.evidence_refs','must be evidence-backed'))
  if x['remediation_attempts']>cc['failure_budget']['max_remediation_attempts']: issues.append(Issue(f'$.findings.{x["finding_id"]}.remediation_attempts','exceeds approved failure budget'))
  if x['category'] in ['AMBIGUITY','SEMANTIC_DECISION_REQUIRED','OUT_OF_SCOPE_CHANGE'] and x['route']=='BOUNDED_IMPLEMENTATION': issues.append(Issue(f'$.findings.{x["finding_id"]}.route','semantic/scope ambiguity cannot be remediated silently in implementation'))
 # Derived summaries.
 statuses=Counter(x['status'] for x in executions)
 summary={'total':len(executions),'completed':statuses['COMPLETED'],'failed':statuses['FAILED'],'blocked':statuses['BLOCKED'],'rolled_back':statuses['ROLLED_BACK'],'pending':statuses['PENDING'],'skipped':statuses['SKIPPED'],'attempts_used':sum(x['attempt_count'] for x in executions)}
 if out['execution_summary']!=summary: issues.append(Issue('$.output.execution_summary','does not match execution records'))
 vc=Counter(x['outcome'] for x in verifications); vsummary={'total':len(verifications),'passed':vc['PASS'],'failed':vc['FAIL'],'blocked':vc['BLOCKED'],'not_run':vc['NOT_RUN'],'all_required_passed':set(ver_ids)==set(pc['verification_item_ids']) and all(x['outcome']=='PASS' for x in verifications)}
 if out['verification_summary']!=vsummary: issues.append(Issue('$.output.verification_summary','does not match verification records'))
 openf=sorted(x['finding_id'] for x in findings if x['status']=='OPEN' and x['blocking']); resolved=sorted(x['finding_id'] for x in findings if x['status']=='RESOLVED')
 route='NONE'
 if openf:
  routes=[fby[x]['route'] for x in openf]
  priority=['PROBLEM_ALIGNMENT','INVESTIGATION','SYSTEM_MODEL','SOLUTION_DESIGN','SOLUTION_CRITIQUE','PLAN_CRITIQUE','IMPLEMENTATION_PLAN','CHECKLIST_CRITIQUE','IMPLEMENTATION_CHECKLIST','BOUNDED_IMPLEMENTATION']
  route=next((r for r in priority if r in routes),'BOUNDED_IMPLEMENTATION')
 remediation=route=='BOUNDED_IMPLEMENTATION' and any(fby[x]['remediation_attempts']<cc['failure_budget']['max_remediation_attempts'] for x in openf)
 fs={'open_blocking_finding_ids':openf,'resolved_finding_ids':resolved,'remediation_available':remediation,'required_route':route}
 if out['failure_summary']!=fs: issues.append(Issue('$.output.failure_summary','does not match findings'))
 # Integrity flags.
 source_valid=not any('source' in i.path or 'checklist_contract' in i.path or 'critique_output' in i.path for i in issues)
 order_ok=not any('order' in i.message or 'dependency' in i.message for i in issues)
 human_ok=not any('human' in i.message for i in issues)
 scope_ok=not any('scope' in i.message or 'change surface' in i.message for i in issues)
 semantic_ok=not any('semantic' in i.message for i in issues)
 budget_ok=not any('failure budget' in i.message for i in issues)
 evidence_ok=not any('evidence' in i.message or 'reference' in i.message for i in issues)
 integ={'source_contract_valid':source_valid,'order_preserved':order_ok,'dependencies_honored':order_ok,'human_gates_honored':human_ok,'scope_preserved':scope_ok,'semantic_boundary_preserved':semantic_ok,'failure_budget_respected':budget_ok,'evidence_complete':evidence_ok}
 if out['integrity']!=integ: issues.append(Issue('$.output.integrity','does not match computed integrity'))
 # Result contract exactness.
 computed=bundle(executions,changes,commands,verifications,rollbacks,findings,before,after)
 if rc['implementation_bundle_digest']!=computed: issues.append(Issue('$.result_contract.implementation_bundle_digest',f'expected {computed}'))
 if rc['implementation_run_id']!=inp['metadata']['implementation_run_id'] or rc['source_checklist_contract_id']!=cc['contract_id'] or rc['source_checklist_bundle_digest']!=cc['checklist_bundle_digest'] or rc['source_plan_contract_id']!=cc['source_plan_contract_id']: issues.append(Issue('$.result_contract','source binding mismatch'))
 if rc['repository_before']!=before or rc['repository_after']!=after: issues.append(Issue('$.result_contract.repository','must exactly match repository state artifacts'))
 expected_completed=sorted(x['checklist_id'] for x in executions if x['status']=='COMPLETED'); expected_failed=sorted(x['checklist_id'] for x in executions if x['status'] in ['FAILED','BLOCKED'])
 if sorted(rc['completed_checklist_ids'])!=expected_completed or sorted(rc['failed_checklist_ids'])!=expected_failed: issues.append(Issue('$.result_contract','completed/failed checklist IDs mismatch'))
 for field,rows,key in [('change_ids',changes,'change_id'),('command_result_ids',commands,'command_id'),('verification_result_ids',verifications,'result_id'),('rollback_result_ids',rollbacks,'rollback_result_id'),('finding_ids',findings,'finding_id')]:
  if set(rc[field])!={x[key] for x in rows}: issues.append(Issue(f'$.result_contract.{field}','must exactly enumerate artifact IDs'))
 # Gate and status.
 gate,state=expected_route(findings,executions,cc)
 if gate=='READY_FOR_SELF_REVIEW' and not vsummary['all_required_passed']: gate,state='BLOCKED','BOUNDED_IMPLEMENTATION'
 if gate=='READY_FOR_SELF_REVIEW' and any(not x for x in integ.values()): gate,state='BLOCKED','BOUNDED_IMPLEMENTATION'
 if out['gate_decision']['status']!=gate or out['gate_decision']['next_state']!=state: issues.append(Issue('$.output.gate_decision',f'expected {gate} -> {state}'))
 expected_status='COMPLETE' if gate=='READY_FOR_SELF_REVIEW' else ('REMEDIATION_REQUIRED' if gate=='REMEDIATION_REQUIRED' else ('FAILED' if gate.startswith('RETURN_TO_') else 'BLOCKED'))
 if out['metadata']['status']!=expected_status: issues.append(Issue('$.output.metadata.status',f'expected {expected_status}'))
 if rc['status']!=('COMPLETE' if gate=='READY_FOR_SELF_REVIEW' else ('FAILED' if gate.startswith('RETURN_TO_') else 'BLOCKED')): issues.append(Issue('$.result_contract.status','does not match gate result'))
 if gate=='READY_FOR_SELF_REVIEW':
  if set(rc['completed_checklist_ids'])!=set(check): issues.append(Issue('$.result_contract.completed_checklist_ids','must contain every checklist item'))
  if rc['failed_checklist_ids'] or rc['finding_ids']: issues.append(Issue('$.result_contract','successful contract cannot contain failed items or findings'))
  if rc['scope_integrity']['status']!='PASS' or rc['semantic_integrity']['status']!='PASS' or not all(rc['execution_integrity'].values()): issues.append(Issue('$.result_contract','integrity must pass before self-review'))
 # Output artifact counts/digests.
 amap={'execution_records':(a.executions,len(executions)),'change_records':(a.changes,len(changes)),'command_results':(a.commands,len(commands)),'verification_results':(a.verifications,len(verifications)),'rollback_results':(a.rollbacks,len(rollbacks)),'findings':(a.findings,len(findings)),'repository_before':(a.repository_before,1),'repository_after':(a.repository_after,1),'implementation_result_contract':(a.result_contract,1)}
 for k,(p,n) in amap.items():
  ref=out['artifact_files'][k]
  if ref['record_count']!=n: issues.append(Issue(f'$.output.artifact_files.{k}.record_count',f'expected {n}'))
  actual='sha256:'+hashlib.sha256(Path(p).read_bytes()).hexdigest()
  if ref.get('digest')!=actual: issues.append(Issue(f'$.output.artifact_files.{k}.digest',f'expected {actual}'))
 if a.require_transition_ready and gate!='READY_FOR_SELF_REVIEW': issues.append(Issue('$.transition',f'package is not transition-ready; got {gate}'))
 return issues
def main():
 p=argparse.ArgumentParser(); p.add_argument('--kind',required=True,choices=['schema','input','output','execution','change','command','verification','rollback','finding','repository','result_contract','package']); p.add_argument('--file')
 for x in ['input','output','checklist-contract','critique-output','plan-contract','checklists','batches','ledger','executions','changes','commands','verifications','rollbacks','findings','repository-before','repository-after','result-contract']: p.add_argument('--'+x,dest=x.replace('-','_'))
 p.add_argument('--require-transition-ready',action='store_true'); a=p.parse_args(); issues=[]
 try:
  if a.kind=='schema':
   for q in sorted((ROOT/'schemas').glob('*.json')): Draft202012Validator.check_schema(json.loads(q.read_text()))
  elif a.kind=='package':
   req=['input','output','checklist_contract','critique_output','plan_contract','checklists','batches','ledger','executions','changes','commands','verifications','rollbacks','findings','repository_before','repository_after','result_contract']; miss=[x for x in req if not getattr(a,x)]
   issues=[Issue('$','missing package arguments: '+', '.join(miss))] if miss else validate_package(a)
  else:
   if not a.file: issues=[Issue('$','--file required')]
   else: issues=structural(load(a.file),a.kind)
 except Exception as e: issues=[Issue('$',f'validator failure: {type(e).__name__}: {e}')]
 if issues:
  for i in issues: print(i,file=sys.stderr)
  return 1
 print('VALID')
 if a.kind=='package' and a.require_transition_ready: print('Package is transition-ready for SELF_REVIEW')
 return 0
if __name__=='__main__': raise SystemExit(main())
