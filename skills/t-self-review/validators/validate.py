#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, warnings
from collections import Counter
from pathlib import Path
from typing import Any
import yaml
warnings.filterwarnings('ignore',category=DeprecationWarning)
from jsonschema import Draft202012Validator, FormatChecker, RefResolver
ROOT=Path(__file__).resolve().parents[1]
MAP={'input':'input.schema.json','output':'output.schema.json','review_check':'review-check.schema.json','conformance':'conformance-result.schema.json','audit':'evidence-audit.schema.json','finding':'review-finding.schema.json','directive':'remediation-directive.schema.json','result_contract':'self-review-result-contract.schema.json','bounded_output':'upstream-bounded-output.schema.json','implementation_contract':'upstream-implementation-result-contract.schema.json','checklist_contract':'upstream-approved-checklist-contract.schema.json','checklist':'upstream-checklist-item.schema.json','execution':'upstream-execution-record.schema.json','change':'upstream-change-record.schema.json','command':'upstream-command-result.schema.json','verification':'upstream-verification-result.schema.json','rollback':'upstream-rollback-result.schema.json','implementation_finding':'upstream-implementation-finding.schema.json','repository':'upstream-repository-state.schema.json','evidence':'upstream-evidence-record.schema.json'}
SCHEMAS={k:ROOT/'schemas'/v for k,v in MAP.items()}
DIMS=['CORRECTNESS','CHECKLIST_CONFORMANCE','SCOPE_INTEGRITY','SEMANTIC_CONFORMANCE','CHANGE_SURFACE','DEPENDENCY_ORDER','HUMAN_GATES','ERROR_HANDLING','SECURITY','DATA_INTEGRITY','CONCURRENCY','COMPATIBILITY','MIGRATION','OBSERVABILITY','TEST_ADEQUACY','ROLLBACK_READINESS','MAINTAINABILITY']
PRIORITY=['PROBLEM_ALIGNMENT','INVESTIGATION','SYSTEM_MODEL','SOLUTION_DESIGN','SOLUTION_CRITIQUE','PLAN_CRITIQUE','IMPLEMENTATION_PLAN','CHECKLIST_CRITIQUE','IMPLEMENTATION_CHECKLIST','BOUNDED_IMPLEMENTATION']
class Issue:
 def __init__(self,path,msg): self.path,self.message=path,msg
 def __str__(self): return f'{self.path}: {self.message}'
def load(path):
 p=Path(path); text=p.read_text()
 if p.suffix=='.jsonl': return [json.loads(x) for x in text.splitlines() if x.strip()]
 if p.suffix=='.json': return json.loads(text)
 return yaml.safe_load(text)
def unique(rows,key,path,issues):
 vals=[x[key] for x in rows]; dup=[x for x,c in Counter(vals).items() if c>1]
 if dup: issues.append(Issue(path,'duplicate IDs: '+', '.join(dup)))
def validate_obj(obj,kind):
 schema=json.loads(SCHEMAS[kind].read_text()); base=SCHEMAS[kind].resolve().as_uri(); resolver=RefResolver(base_uri=base,referrer=schema)
 return [Issue('$'+''.join(f'[{x}]' if isinstance(x,int) else f'.{x}' for x in e.path),e.message) for e in Draft202012Validator(schema,resolver=resolver,format_checker=FormatChecker()).iter_errors(obj)]
def structural(obj,kind):
 if kind in ['review_check','conformance','audit','finding','directive','checklist','execution','change','command','verification','rollback','implementation_finding','evidence']:
  if not isinstance(obj,list): return [Issue('$','expected JSONL/list')]
  out=[]
  for i,x in enumerate(obj):
   for e in validate_obj(x,kind): e.path=f'$[{i}]'+e.path[1:]; out.append(e)
  return out
 return validate_obj(obj,kind)
def digest_file(path): return 'sha256:'+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canon(obj): return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def bundle(checks,confs,audits,findings,directives,source_binding):
 return 'sha256:'+hashlib.sha256(canon({'review_checks':checks,'conformance_results':confs,'evidence_audits':audits,'findings':findings,'remediation_directives':directives,'source_binding':source_binding})).hexdigest()
def expected_route(findings):
 blocking=[x for x in findings if x['status']=='OPEN' and x['blocking']]
 if not blocking: return 'READY_FOR_TECHNICAL_REVIEW','TECHNICAL_REVIEW','NONE'
 routes={x['required_route'] for x in blocking}; route=next((r for r in PRIORITY if r in routes),'BOUNDED_IMPLEMENTATION')
 return 'RETURN_TO_'+route,route,route
def validate_package(a):
 issues=[]
 inp=load(a.input); out=load(a.output); bo=load(a.bounded_output); ic=load(a.implementation_contract); cc=load(a.checklist_contract); checkslist=load(a.checklists); executions=load(a.executions); changes=load(a.changes); commands=load(a.commands); verifications=load(a.verifications); rollbacks=load(a.rollbacks); ifinds=load(a.implementation_findings); before=load(a.repository_before); after=load(a.repository_after); ledger=load(a.ledger); checks=load(a.review_checks); confs=load(a.conformance_results); audits=load(a.evidence_audits); findings=load(a.findings); directives=load(a.directives); rc=load(a.result_contract)
 for obj,kind in [(inp,'input'),(out,'output'),(bo,'bounded_output'),(ic,'implementation_contract'),(cc,'checklist_contract'),(checkslist,'checklist'),(executions,'execution'),(changes,'change'),(commands,'command'),(verifications,'verification'),(rollbacks,'rollback'),(ifinds,'implementation_finding'),(before,'repository'),(after,'repository'),(ledger,'evidence'),(checks,'review_check'),(confs,'conformance'),(audits,'audit'),(findings,'finding'),(directives,'directive'),(rc,'result_contract')]: issues+=structural(obj,kind)
 if issues: return issues
 # Unique IDs
 for rows,key,name in [(checks,'review_check_id','checks'),(confs,'conformance_id','conformance'),(audits,'audit_id','audits'),(findings,'finding_id','findings'),(directives,'directive_id','directives')]: unique(rows,key,'$.'+name,issues)
 # Source authorization and binding
 if bo['gate_decision']['status']!='READY_FOR_SELF_REVIEW' or bo['gate_decision']['next_state']!='SELF_REVIEW': issues.append(Issue('$.bounded_output.gate_decision','source must be READY_FOR_SELF_REVIEW -> SELF_REVIEW'))
 if ic['status']!='COMPLETE': issues.append(Issue('$.implementation_contract.status','must be COMPLETE'))
 sa=inp['source_authorization']
 if sa['implementation_result_contract_id']!=ic['contract_id'] or sa['implementation_bundle_digest']!=ic['implementation_bundle_digest'] or sa['bounded_implementation_run_id']!=ic['implementation_run_id'] or sa['repository_after_tree_digest']!=ic['repository_after']['tree_digest']: issues.append(Issue('$.input.source_authorization','does not match implementation contract'))
 sb=out['source_binding']
 exp_sb={'implementation_result_contract_id':ic['contract_id'],'implementation_bundle_digest':ic['implementation_bundle_digest'],'bounded_implementation_run_id':ic['implementation_run_id'],'source_checklist_contract_id':ic['source_checklist_contract_id'],'repository_after_tree_digest':ic['repository_after']['tree_digest']}
 if sb!=exp_sb: issues.append(Issue('$.output.source_binding','does not exactly match source contracts'))
 if after!=ic['repository_after'] or before!=ic['repository_before']: issues.append(Issue('$.repository','repository state does not match implementation contract'))
 if ic['source_checklist_contract_id']!=cc['contract_id']: issues.append(Issue('$.checklist_contract.contract_id','does not match implementation contract'))
 # Input source artifact digests/counts
 argmap={'bounded_output':a.bounded_output,'implementation_result_contract':a.implementation_contract,'approved_checklist_contract':a.checklist_contract,'checklist_items':a.checklists,'execution_records':a.executions,'change_records':a.changes,'command_results':a.commands,'verification_results':a.verifications,'rollback_results':a.rollbacks,'implementation_findings':a.implementation_findings,'repository_before':a.repository_before,'repository_after':a.repository_after,'evidence_ledger':a.ledger}
 countmap={'bounded_output':1,'implementation_result_contract':1,'approved_checklist_contract':1,'checklist_items':len(checkslist),'execution_records':len(executions),'change_records':len(changes),'command_results':len(commands),'verification_results':len(verifications),'rollback_results':len(rollbacks),'implementation_findings':len(ifinds),'repository_before':1,'repository_after':1,'evidence_ledger':len(ledger)}
 for k,p in argmap.items():
  ref=inp['source_artifacts'][k]
  if ref['digest']!=digest_file(p): issues.append(Issue(f'$.input.source_artifacts.{k}.digest','digest mismatch'))
  if ref['record_count']!=countmap[k]: issues.append(Issue(f'$.input.source_artifacts.{k}.record_count',f'expected {countmap[k]}'))
 # Source ID universes
 chk={x['checklist_id']:x for x in checkslist}; exby={x['checklist_id']:x for x in executions}; chg={x['change_id'] for x in changes}; cmd={x['command_id'] for x in commands}; vres={x['result_id'] for x in verifications}; rres={x['rollback_result_id'] for x in rollbacks}
 if set(ic['completed_checklist_ids'])!=set(chk) or ic['failed_checklist_ids']: issues.append(Issue('$.implementation_contract.completed_checklist_ids','source implementation must complete every checklist item with no failures'))
 # Conformance exact one per checklist and exact binding
 counts=Counter(x['checklist_id'] for x in confs)
 for cid in chk:
  if counts[cid]!=1: issues.append(Issue(f'$.conformance.{cid}',f'expected exactly one conformance result, got {counts[cid]}'))
 for x in confs:
  cid=x['checklist_id']
  if cid not in chk: issues.append(Issue(f'$.conformance.{x["conformance_id"]}.checklist_id','unknown checklist')); continue
  e=exby.get(cid)
  if not e or x['execution_id']!=e['execution_id']: issues.append(Issue(f'$.conformance.{x["conformance_id"]}.execution_id','must match source execution'))
  binding=next((b for b in cc['operation_bindings'] if b['checklist_id']==cid),None)
  if not binding or x['source_operation_digest']!=binding['source_operation_digest'] or x['checklist_item_digest']!=binding['checklist_item_digest']: issues.append(Issue(f'$.conformance.{x["conformance_id"]}','source/checklist digest drift'))
  if set(x['implementation_change_ids'])!=set(e['change_ids']): issues.append(Issue(f'$.conformance.{x["conformance_id"]}.implementation_change_ids','must exactly match execution changes'))
  if set(x['verification_result_ids'])!=set(e['verification_result_ids']): issues.append(Issue(f'$.conformance.{x["conformance_id"]}.verification_result_ids','must exactly match execution verifications'))
  if not x['evidence_refs'] or any(not a['evidence_refs'] for a in x['assertions']): issues.append(Issue(f'$.conformance.{x["conformance_id"]}.evidence_refs','conformance must be evidence-backed'))
  derived='PASS' if all(z['status']=='PASS' for z in x['assertions']) and not x['deviations'] else ('FAIL' if any(z['status']=='FAIL' for z in x['assertions']) or x['deviations'] else 'INCONCLUSIVE')
  if x['outcome']!=derived: issues.append(Issue(f'$.conformance.{x["conformance_id"]}.outcome',f'expected {derived}'))
 # Dimensions exactly once
 dc=Counter(x['dimension'] for x in checks)
 for d in DIMS:
  if dc[d]!=1: issues.append(Issue(f'$.review_checks.dimension.{d}',f'expected exactly one check, got {dc[d]}'))
 valid_targets=set(chk)|{x['execution_id'] for x in executions}|chg|cmd|vres|rres|{ic['contract_id'],cc['contract_id'],bo['metadata']['implementation_run_id']}
 for x in checks:
  if not x['target_ids'] or not set(x['target_ids']).issubset(valid_targets): issues.append(Issue(f'$.review_checks.{x["review_check_id"]}.target_ids','contains unknown or empty targets'))
  if not x['evidence_refs']: issues.append(Issue(f'$.review_checks.{x["review_check_id"]}.evidence_refs','must be evidence-backed'))
  if x['outcome']=='NOT_APPLICABLE' and (not x['reviewer_reasoning'] or not x['evidence_refs']): issues.append(Issue(f'$.review_checks.{x["review_check_id"]}','NOT_APPLICABLE requires evidence-backed reasoning'))
 # Audits exact source artifacts and all pass for ready
 expected_paths={str(Path(p)) for p in argmap.values()}
 audit_paths={str(Path(x['source_path'])) for x in audits}
 # Accept relative example paths by basename matching
 exp_basenames={Path(p).name for p in argmap.values()}; got_basenames={Path(x['source_path']).name for x in audits}
 if got_basenames!=exp_basenames: issues.append(Issue('$.evidence_audits','must audit every source artifact exactly once'))
 for x in audits:
  p=next((p for p in argmap.values() if Path(p).name==Path(x['source_path']).name),None)
  if not p: continue
  actual=digest_file(p)
  if x['expected_digest']!=actual or x['actual_digest']!=actual or not x['digest_verified'] or not x['existence_verified'] or not x['content_inspected'] or x['outcome']!='PASS': issues.append(Issue(f'$.evidence_audits.{x["audit_id"]}','audit must verify actual digest, existence, content, and PASS'))
 # Findings and directives
 fby={x['finding_id']:x for x in findings}; dby={x['directive_id']:x for x in directives}
 all_targets=valid_targets|{x['review_check_id'] for x in checks}|{x['conformance_id'] for x in confs}|{x['audit_id'] for x in audits}
 failed_targets={x['review_check_id'] for x in checks if x['outcome'] in ['FAIL','INCONCLUSIVE']}|{x['conformance_id'] for x in confs if x['outcome'] in ['FAIL','INCONCLUSIVE']}
 for x in findings:
  if not x['target_ids'] or not set(x['target_ids']).issubset(all_targets): issues.append(Issue(f'$.findings.{x["finding_id"]}.target_ids','contains unknown or empty targets'))
  if not x['evidence_refs']: issues.append(Issue(f'$.findings.{x["finding_id"]}.evidence_refs','must be evidence-backed'))
  if x['status']=='OPEN' and x['required_route']=='NONE': issues.append(Issue(f'$.findings.{x["finding_id"]}.required_route','open finding requires a route'))
  if x['remediation_type']=='MECHANICAL' and x['required_route']!='BOUNDED_IMPLEMENTATION': issues.append(Issue(f'$.findings.{x["finding_id"]}.required_route','mechanical finding must route to BOUNDED_IMPLEMENTATION'))
  if x['category'] in ['SEMANTIC_DRIFT','MODEL_OR_SOLUTION_DEFECT'] and x['required_route'] in ['NONE','BOUNDED_IMPLEMENTATION']: issues.append(Issue(f'$.findings.{x["finding_id"]}.required_route','semantic/model defect must route upstream'))
 for tid in failed_targets:
  if not any(tid in x['target_ids'] and x['status']=='OPEN' for x in findings): issues.append(Issue(f'$.findings','failed/inconclusive target {tid} lacks open finding'))
 open_change=[x for x in findings if x['status']=='OPEN' and x['remediation_type']!='NONE']
 for f in open_change:
  ds=[d for d in directives if f['finding_id'] in d['finding_ids']]
  if len(ds)!=1: issues.append(Issue(f'$.directives.{f["finding_id"]}',f'expected exactly one directive, got {len(ds)}'))
 for x in directives:
  if not set(x['finding_ids']).issubset(fby): issues.append(Issue(f'$.directives.{x["directive_id"]}.finding_ids','unknown finding'))
  if not set(x['target_checklist_ids']).issubset(chk): issues.append(Issue(f'$.directives.{x["directive_id"]}.target_checklist_ids','unknown checklist'))
  if x['applied']: issues.append(Issue(f'$.directives.{x["directive_id"]}.applied','self-review directives must remain unapplied'))
  if x['status']!='OPEN' and any(fby[z]['status']=='OPEN' for z in x['finding_ids']): issues.append(Issue(f'$.directives.{x["directive_id"]}.status','directive for open finding must be OPEN'))
  if any(fby[z]['required_route']!=x['route'] for z in x['finding_ids']): issues.append(Issue(f'$.directives.{x["directive_id"]}.route','must match finding route'))
 # Summaries and integrity
 c=Counter(x['outcome'] for x in checks); cs={'total':len(checks),'passed':c['PASS'],'failed':c['FAIL'],'not_applicable':c['NOT_APPLICABLE'],'inconclusive':c['INCONCLUSIVE'],'required_dimensions':len(DIMS),'covered_dimensions':len(set(x['dimension'] for x in checks))}
 if out['review_summary']!=cs: issues.append(Issue('$.output.review_summary','does not match review checks'))
 c2=Counter(x['outcome'] for x in confs); complete=set(counts)==set(chk) and all(v==1 for v in counts.values()); csum={'total':len(confs),'passed':c2['PASS'],'failed':c2['FAIL'],'inconclusive':c2['INCONCLUSIVE'],'complete_coverage':complete}
 if out['conformance_summary']!=csum: issues.append(Issue('$.output.conformance_summary','does not match conformance results'))
 openb=sorted(x['finding_id'] for x in findings if x['status']=='OPEN' and x['blocking']); openn=sorted(x['finding_id'] for x in findings if x['status']=='OPEN' and not x['blocking']); resolved=sorted(x['finding_id'] for x in findings if x['status']=='RESOLVED'); accepted=sorted(x['finding_id'] for x in findings if x['status']=='ACCEPTED_RISK'); gate,state,route=expected_route(findings)
 fs={'total':len(findings),'open_blocking_finding_ids':openb,'open_nonblocking_finding_ids':openn,'resolved_finding_ids':resolved,'accepted_risk_finding_ids':accepted,'remediation_directive_ids':[x['directive_id'] for x in directives],'required_route':route}
 if out['finding_summary']!=fs: issues.append(Issue('$.output.finding_summary','does not match findings/directives'))
 source_ok=not any('source' in i.path or 'repository' in i.path or 'audit' in i.path for i in issues)
 dims_ok=all(dc[d]==1 for d in DIMS)
 coverage_ok=complete
 ev_ok=not any('evidence' in i.message.lower() or 'audit' in i.path for i in issues)
 scope_ok=not any(x['category'] in ['SCOPE_DRIFT','EXTRA_CHANGE'] and x['status']=='OPEN' for x in findings)
 sem_ok=not any(x['category'] in ['SEMANTIC_DRIFT','MODEL_OR_SOLUTION_DEFECT'] and x['status']=='OPEN' for x in findings)
 no_mut=all(not x['applied'] for x in directives)
 integ={'source_bundle_verified':source_ok,'checklist_coverage_complete':coverage_ok,'review_dimensions_complete':dims_ok,'evidence_complete':ev_ok,'scope_preserved':scope_ok,'semantic_boundary_preserved':sem_ok,'no_silent_mutation':no_mut}
 if out['integrity']!=integ: issues.append(Issue('$.output.integrity','does not match computed integrity'))
 # Gate requires all checks pass/NA, all conformance pass, no findings/directives, integrity all true
 ready=all(x['outcome'] in ['PASS','NOT_APPLICABLE'] for x in checks) and all(x['outcome']=='PASS' for x in confs) and not openb and not directives and all(integ.values())
 if not ready and gate=='READY_FOR_TECHNICAL_REVIEW': gate,state='BLOCKED','SELF_REVIEW'
 if out['gate_decision']['status']!=gate or out['gate_decision']['next_state']!=state: issues.append(Issue('$.output.gate_decision',f'expected {gate} -> {state}'))
 expected_status='COMPLETE' if gate=='READY_FOR_TECHNICAL_REVIEW' else ('FAILED' if gate.startswith('RETURN_TO_') else 'BLOCKED')
 if out['metadata']['status']!=expected_status: issues.append(Issue('$.output.metadata.status',f'expected {expected_status}'))
 # Result contract exactness
 bd=bundle(checks,confs,audits,findings,directives,sb)
 if rc['self_review_bundle_digest']!=bd: issues.append(Issue('$.result_contract.self_review_bundle_digest',f'expected {bd}'))
 if rc['self_review_run_id']!=inp['metadata']['self_review_run_id'] or rc['source_implementation_contract_id']!=ic['contract_id'] or rc['source_implementation_bundle_digest']!=ic['implementation_bundle_digest'] or rc['source_checklist_contract_id']!=cc['contract_id'] or rc['repository_after_tree_digest']!=after['tree_digest']: issues.append(Issue('$.result_contract','source binding mismatch'))
 exacts=[('reviewed_checklist_ids',set(chk)),('review_check_ids',{x['review_check_id'] for x in checks}),('conformance_ids',{x['conformance_id'] for x in confs}),('evidence_audit_ids',{x['audit_id'] for x in audits}),('finding_ids',set(fby)),('remediation_directive_ids',set(dby))]
 for field,expected in exacts:
  if set(rc[field])!=expected: issues.append(Issue(f'$.result_contract.{field}','must exactly enumerate source IDs'))
 if rc['integrity']!=integ: issues.append(Issue('$.result_contract.integrity','must equal computed integrity'))
 if rc['verdict']['status']!=gate or rc['verdict']['next_state']!=state or sorted(rc['verdict']['blocking_finding_ids'])!=openb: issues.append(Issue('$.result_contract.verdict','does not match computed gate'))
 exp_rc_status='PASS' if gate=='READY_FOR_TECHNICAL_REVIEW' else ('FAIL' if gate.startswith('RETURN_TO_') else 'BLOCKED')
 if rc['status']!=exp_rc_status: issues.append(Issue('$.result_contract.status',f'expected {exp_rc_status}'))
 # Output artifact counts/digests
 amap={'review_checks':(a.review_checks,len(checks)),'conformance_results':(a.conformance_results,len(confs)),'evidence_audits':(a.evidence_audits,len(audits)),'findings':(a.findings,len(findings)),'remediation_directives':(a.directives,len(directives)),'self_review_result_contract':(a.result_contract,1)}
 for k,(p,n) in amap.items():
  ref=out['artifact_files'][k]
  if ref['record_count']!=n: issues.append(Issue(f'$.output.artifact_files.{k}.record_count',f'expected {n}'))
  actual=digest_file(p)
  if ref['digest']!=actual: issues.append(Issue(f'$.output.artifact_files.{k}.digest',f'expected {actual}'))
 if a.require_transition_ready and gate!='READY_FOR_TECHNICAL_REVIEW': issues.append(Issue('$.transition',f'package is not transition-ready; got {gate}'))
 return issues
def main():
 p=argparse.ArgumentParser(); p.add_argument('--kind',required=True,choices=['schema','input','output','review_check','conformance','audit','finding','directive','result_contract','package']); p.add_argument('--file')
 for x in ['input','output','bounded-output','implementation-contract','checklist-contract','checklists','executions','changes','commands','verifications','rollbacks','implementation-findings','repository-before','repository-after','ledger','review-checks','conformance-results','evidence-audits','findings','directives','result-contract']: p.add_argument('--'+x,dest=x.replace('-','_'))
 p.add_argument('--require-transition-ready',action='store_true'); a=p.parse_args(); issues=[]
 try:
  if a.kind=='schema':
   for q in sorted((ROOT/'schemas').glob('*.json')): Draft202012Validator.check_schema(json.loads(q.read_text()))
  elif a.kind=='package':
   req=['input','output','bounded_output','implementation_contract','checklist_contract','checklists','executions','changes','commands','verifications','rollbacks','implementation_findings','repository_before','repository_after','ledger','review_checks','conformance_results','evidence_audits','findings','directives','result_contract']; miss=[x for x in req if not getattr(a,x)]
   issues=[Issue('$','missing package arguments: '+', '.join(miss))] if miss else validate_package(a)
  else:
   if not a.file: issues=[Issue('$','--file required')]
   else: issues=structural(load(a.file),a.kind)
 except Exception as e: issues=[Issue('$',f'validator failure: {type(e).__name__}: {e}')]
 if issues:
  for i in issues: print(i,file=sys.stderr)
  return 1
 print('VALID')
 if a.kind=='package' and a.require_transition_ready: print('Package is transition-ready for TECHNICAL_REVIEW')
 return 0
if __name__=='__main__': raise SystemExit(main())
