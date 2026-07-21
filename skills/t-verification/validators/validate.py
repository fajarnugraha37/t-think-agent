#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, warnings
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import yaml
warnings.filterwarnings('ignore',category=DeprecationWarning)
from jsonschema import Draft202012Validator, FormatChecker, RefResolver
ROOT=Path(__file__).resolve().parents[1]
MAP={'input':'input.schema.json','output':'output.schema.json','assignment':'verifier-assignment.schema.json','environment':'environment.schema.json','obligation':'verification-obligation.schema.json','execution':'verification-execution.schema.json','falsification':'falsification-attempt.schema.json','evidence':'verification-evidence.schema.json','finding':'verification-finding.schema.json','directive':'remediation-directive.schema.json','result_contract':'verification-result-contract.schema.json','technical_review_output':'upstream-technical-review-output.schema.json','technical_review_contract':'upstream-technical-review-result-contract.schema.json','implementation_contract':'upstream-implementation-result-contract.schema.json','checklist_contract':'upstream-approved-checklist-contract.schema.json','checklist':'upstream-checklist-item.schema.json','source_verification':'upstream-verification-result.schema.json','repository':'upstream-repository-state.schema.json','change':'upstream-change-record.schema.json','source_evidence':'upstream-evidence-record.schema.json'}
SCHEMAS={k:ROOT/'schemas'/v for k,v in MAP.items()}
ROWS={'obligation','execution','falsification','evidence','finding','directive','checklist','source_verification','change','source_evidence'}
PRIORITY=['PROBLEM_ALIGNMENT','INVESTIGATION','SYSTEM_MODEL','SOLUTION_DESIGN','SOLUTION_CRITIQUE','IMPLEMENTATION_PLAN','PLAN_CRITIQUE','IMPLEMENTATION_CHECKLIST','CHECKLIST_CRITIQUE','BOUNDED_IMPLEMENTATION','SELF_REVIEW','TECHNICAL_REVIEW','VERIFICATION']
class Issue:
 def __init__(self,path,msg): self.path,self.message=path,msg
 def __str__(self): return f'{self.path}: {self.message}'
def load(path):
 p=Path(path); text=p.read_text()
 if p.suffix=='.jsonl': return [json.loads(x) for x in text.splitlines() if x.strip()]
 if p.suffix=='.json': return json.loads(text)
 return yaml.safe_load(text)
def validate_obj(obj,kind):
 schema=json.loads(SCHEMAS[kind].read_text()); base=SCHEMAS[kind].resolve().as_uri(); resolver=RefResolver(base_uri=base,referrer=schema)
 return [Issue('$'+''.join(f'[{x}]' if isinstance(x,int) else f'.{x}' for x in e.path),e.message) for e in Draft202012Validator(schema,resolver=resolver,format_checker=FormatChecker()).iter_errors(obj)]
def structural(obj,kind):
 if kind in ROWS:
  if not isinstance(obj,list): return [Issue('$','expected JSONL/list')]
  out=[]
  for i,x in enumerate(obj):
   for e in validate_obj(x,kind): e.path=f'$[{i}]'+e.path[1:]; out.append(e)
  return out
 return validate_obj(obj,kind)
def unique(rows,key,path,issues):
 vals=[x[key] for x in rows]; d=[x for x,c in Counter(vals).items() if c>1]
 if d: issues.append(Issue(path,'duplicate IDs: '+', '.join(d)))
def digest_file(path): return 'sha256:'+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canon(obj): return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def bundle(assignment,environment,obligations,executions,falsifications,evidence,findings,directives,source_binding):
 return 'sha256:'+hashlib.sha256(canon({'assignment':assignment,'environment':environment,'obligations':obligations,'executions':executions,'falsification_attempts':falsifications,'evidence':evidence,'findings':findings,'remediation_directives':directives,'source_binding':source_binding})).hexdigest()
def expected_route(findings):
 blocking=[x for x in findings if x['status']=='OPEN' and x['blocking']]
 if not blocking: return 'READY_FOR_RECONCILIATION','RECONCILIATION','NONE'
 routes={x['required_route'] for x in blocking}; route=next((r for r in PRIORITY if r in routes),'VERIFICATION')
 if route=='VERIFICATION': return 'BLOCKED','VERIFICATION','VERIFICATION'
 return 'RETURN_TO_'+route,route,route
def validate_package(a):
 issues=[]
 names=['input','output','assignment','environment','technical_review_output','technical_review_contract','implementation_contract','checklist_contract','checklists','source_verifications','repository_state','changes','source_ledger','obligations','executions','falsifications','evidence','findings','directives','result_contract']
 vals={n:load(getattr(a,n)) for n in names}
 kinds={'input':'input','output':'output','assignment':'assignment','environment':'environment','technical_review_output':'technical_review_output','technical_review_contract':'technical_review_contract','implementation_contract':'implementation_contract','checklist_contract':'checklist_contract','checklists':'checklist','source_verifications':'source_verification','repository_state':'repository','changes':'change','source_ledger':'source_evidence','obligations':'obligation','executions':'execution','falsifications':'falsification','evidence':'evidence','findings':'finding','directives':'directive','result_contract':'result_contract'}
 for n in names: issues+=structural(vals[n],kinds[n])
 if issues: return issues
 inp,out,assignment,env=vals['input'],vals['output'],vals['assignment'],vals['environment']; tro,trc,ic,cc=vals['technical_review_output'],vals['technical_review_contract'],vals['implementation_contract'],vals['checklist_contract']; checks,sv,repo,changes,sledger=vals['checklists'],vals['source_verifications'],vals['repository_state'],vals['changes'],vals['source_ledger']; obs,exe,fals,evid,finds,dirs,rc=vals['obligations'],vals['executions'],vals['falsifications'],vals['evidence'],vals['findings'],vals['directives'],vals['result_contract']
 for rows,key,name in [(checks,'checklist_id','checklists'),(sv,'result_id','source_verifications'),(changes,'change_id','changes'),(obs,'obligation_id','obligations'),(exe,'execution_id','executions'),(fals,'falsification_id','falsifications'),(evid,'evidence_id','evidence'),(finds,'finding_id','findings'),(dirs,'directive_id','directives')]: unique(rows,key,'$.'+name,issues)
 # Upstream readiness and exact binding.
 if tro['gate_decision']['status']!='READY_FOR_VERIFICATION' or tro['gate_decision']['next_state']!='VERIFICATION': issues.append(Issue('$.source.technical_review_output','must be READY_FOR_VERIFICATION -> VERIFICATION'))
 if trc['status']!='PASS' or trc['verdict']['status']!='READY_FOR_VERIFICATION': issues.append(Issue('$.source.technical_review_contract','must be PASS and READY_FOR_VERIFICATION'))
 sb={'technical_review_contract_id':trc['contract_id'],'technical_review_bundle_digest':trc['technical_review_bundle_digest'],'technical_review_run_id':trc['technical_review_run_id'],'implementation_result_contract_id':ic['contract_id'],'implementation_bundle_digest':ic['implementation_bundle_digest'],'source_checklist_contract_id':cc['contract_id'],'repository_tree_digest':repo['tree_digest']}
 ia=inp['source_authorization']; expected_input={'technical_review_contract_id':sb['technical_review_contract_id'],'technical_review_bundle_digest':sb['technical_review_bundle_digest'],'technical_review_run_id':sb['technical_review_run_id'],'implementation_result_contract_id':sb['implementation_result_contract_id'],'implementation_bundle_digest':sb['implementation_bundle_digest'],'approved_checklist_contract_id':sb['source_checklist_contract_id'],'repository_tree_digest':sb['repository_tree_digest']}
 for k,v in expected_input.items():
  if ia[k]!=v: issues.append(Issue('$.input.source_authorization.'+k,'does not match upstream source'))
 if out['source_binding']!=sb: issues.append(Issue('$.output.source_binding','does not match exact upstream source binding'))
 # Input source artifact descriptors.
 pathmap={'technical_review_output':a.technical_review_output,'technical_review_contract':a.technical_review_contract,'implementation_contract':a.implementation_contract,'approved_checklist_contract':a.checklist_contract,'checklist_items':a.checklists,'source_verification_results':a.source_verifications,'repository_state':a.repository_state,'change_records':a.changes,'evidence_ledger':a.source_ledger}
 for k,p in pathmap.items():
  d=inp['source_artifacts'][k]
  if d['digest']!=digest_file(p): issues.append(Issue('$.input.source_artifacts.'+k+'.digest','digest mismatch'))
  actual=len(load(p)) if Path(p).suffix=='.jsonl' else 1
  if d['record_count']!=actual: issues.append(Issue('$.input.source_artifacts.'+k+'.record_count','record count mismatch'))
 # Independent assignment.
 if assignment['verification_run_id']!=inp['metadata']['verification_run_id']: issues.append(Issue('$.assignment.verification_run_id','run mismatch'))
 if assignment['verifier_id'] in assignment['prohibited_identity_ids']: issues.append(Issue('$.assignment.verifier_id','verifier is a prohibited upstream identity'))
 if not set(assignment['required_competencies']).issubset(set(assignment['declared_competencies'])): issues.append(Issue('$.assignment.declared_competencies','missing required competency'))
 if not all(assignment['independence'].values()) or assignment['conflicts']: issues.append(Issue('$.assignment.independence','independence is not established'))
 if out['metadata']['verifier_id']!=assignment['verifier_id']: issues.append(Issue('$.output.metadata.verifier_id','must match assignment'))
 # Environment.
 if env['verification_run_id']!=inp['metadata']['verification_run_id']: issues.append(Issue('$.environment.verification_run_id','run mismatch'))
 if env['repository']['repository_id']!=repo['repository_id'] or env['repository']['commit_sha']!=repo['commit_sha'] or env['repository']['tree_digest']!=repo['tree_digest'] or sorted(env['repository']['changed_paths'])!=sorted(repo['changed_paths']): issues.append(Issue('$.environment.repository','must exactly match reviewed repository state'))
 if any(x['availability']=='UNAVAILABLE' for x in env['dependencies']): issues.append(Issue('$.environment.dependencies','required dependency unavailable'))
 # Source sets.
 check_by={x['checklist_id']:x for x in checks}; source_by={x['result_id']:x for x in sv}; source_test_by={x['verification_item_id']:x for x in sv}; ledger_ids={x['id'] for x in sledger}
 source_tests=set(source_test_by); ob_tests=[x['source_verification_item_id'] for x in obs]
 if set(ob_tests)!=source_tests or len(ob_tests)!=len(source_tests): issues.append(Issue('$.obligations','must cover every source verification item exactly once'))
 ob_by={x['obligation_id']:x for x in obs}; ex_by={x['execution_id']:x for x in exe}; fal_by={x['falsification_id']:x for x in fals}; ev_by={x['evidence_id']:x for x in evid}
 for o in obs:
  if o['verification_run_id']!=inp['metadata']['verification_run_id']: issues.append(Issue('$.obligations.'+o['obligation_id'],'run mismatch'))
  s=source_by.get(o['source_verification_result_id'])
  if not s: issues.append(Issue('$.obligations.'+o['obligation_id']+'.source_verification_result_id','dangling source result')); continue
  if o['source_verification_item_id']!=s['verification_item_id']: issues.append(Issue('$.obligations.'+o['obligation_id']+'.source_verification_item_id','source item mismatch'))
  if set(o['checklist_ids'])!=set(s['checklist_ids']): issues.append(Issue('$.obligations.'+o['obligation_id']+'.checklist_ids','must equal source verification checklist coverage'))
  if any(x not in check_by for x in o['checklist_ids']): issues.append(Issue('$.obligations.'+o['obligation_id']+'.checklist_ids','dangling checklist ID'))
  if any(x not in ledger_ids for x in o['source_evidence_ids']): issues.append(Issue('$.obligations.'+o['obligation_id']+'.source_evidence_ids','dangling source evidence ID'))
  if o['criticality'] in ['HIGH','CRITICAL'] and not o['falsification_required']: issues.append(Issue('$.obligations.'+o['obligation_id']+'.falsification_required','high-risk obligation must require falsification'))
 # Executions and exact terminal coverage.
 grouped=defaultdict(list)
 for x in exe:
  grouped[x['obligation_id']].append(x)
  if x['obligation_id'] not in ob_by: issues.append(Issue('$.executions.'+x['execution_id']+'.obligation_id','dangling obligation'))
  if x['environment_id']!=env['environment_id']: issues.append(Issue('$.executions.'+x['execution_id']+'.environment_id','environment mismatch'))
  if x['repository_tree_before']!=repo['tree_digest'] or x['repository_tree_after']!=repo['tree_digest']: issues.append(Issue('$.executions.'+x['execution_id'],'repository tree drift detected'))
  if x['outcome']=='PASS' and x['exit_code']!=0: issues.append(Issue('$.executions.'+x['execution_id'],'PASS requires exit_code 0'))
  if any(e not in ev_by for e in x['evidence_ids']): issues.append(Issue('$.executions.'+x['execution_id']+'.evidence_ids','dangling verification evidence'))
 for o in obs:
  xs=grouped.get(o['obligation_id'],[])
  if o['applicability']=='MANDATORY' and not xs: issues.append(Issue('$.executions','missing execution for '+o['obligation_id']))
  attempts=[x['attempt'] for x in xs]
  if len(attempts)!=len(set(attempts)): issues.append(Issue('$.executions.'+o['obligation_id'],'duplicate attempt number'))
  if xs and sorted(attempts)!=list(range(1,max(attempts)+1)): issues.append(Issue('$.executions.'+o['obligation_id'],'attempt sequence must be contiguous'))
 # Evidence backlinks.
 for e in evid:
  if e['verification_run_id']!=inp['metadata']['verification_run_id']: issues.append(Issue('$.evidence.'+e['evidence_id'],'run mismatch'))
  if any(x not in ex_by for x in e['source_execution_ids']): issues.append(Issue('$.evidence.'+e['evidence_id']+'.source_execution_ids','dangling execution'))
  if any(x not in fal_by for x in e['source_falsification_ids']): issues.append(Issue('$.evidence.'+e['evidence_id']+'.source_falsification_ids','dangling falsification'))
 # Falsification coverage.
 required={o['obligation_id'] for o in obs if o['falsification_required']}
 covered={f['obligation_id'] for f in fals}
 if not required.issubset(covered): issues.append(Issue('$.falsifications','missing required falsification attempts: '+', '.join(sorted(required-covered))))
 if len(fals)<inp['verification_policy']['minimum_falsification_attempts']: issues.append(Issue('$.falsifications','below minimum falsification attempts'))
 for f in fals:
  if f['obligation_id'] not in ob_by: issues.append(Issue('$.falsifications.'+f['falsification_id']+'.obligation_id','dangling obligation'))
  if any(x not in ex_by for x in f['execution_ids']): issues.append(Issue('$.falsifications.'+f['falsification_id']+'.execution_ids','dangling execution'))
  if any(x not in ev_by for x in f['evidence_ids']): issues.append(Issue('$.falsifications.'+f['falsification_id']+'.evidence_ids','dangling evidence'))
 # Findings and required findings.
 target_sets={'OBLIGATION':set(ob_by),'EXECUTION':set(ex_by),'FALSIFICATION':set(fal_by),'ENVIRONMENT':{env['environment_id']},'TECHNICAL_REVIEW_CONTRACT':{trc['contract_id']},'IMPLEMENTATION_CONTRACT':{ic['contract_id']},'CHECKLIST_ITEM':set(check_by)}
 find_by={x['finding_id']:x for x in finds}
 for f in finds:
  if f['target_id'] not in target_sets[f['target_type']]: issues.append(Issue('$.findings.'+f['finding_id']+'.target_id','dangling target'))
  if any(x not in ex_by for x in f['execution_ids']): issues.append(Issue('$.findings.'+f['finding_id']+'.execution_ids','dangling execution'))
  if any(x not in fal_by for x in f['falsification_ids']): issues.append(Issue('$.findings.'+f['finding_id']+'.falsification_ids','dangling falsification'))
  if any(x not in ev_by for x in f['evidence_ids']): issues.append(Issue('$.findings.'+f['finding_id']+'.evidence_ids','dangling evidence'))
  if f['status']=='OPEN' and not f['evidence_ids']: issues.append(Issue('$.findings.'+f['finding_id'],'open finding requires evidence'))
 for x in exe:
  if x['outcome'] in ['FAIL','BLOCKED','INCONCLUSIVE'] and not any(x['execution_id'] in f['execution_ids'] or x['obligation_id']==f['target_id'] for f in finds): issues.append(Issue('$.executions.'+x['execution_id'],'non-pass execution requires finding'))
 for f in fals:
  if f['resolution'] in ['REFUTED','INCONCLUSIVE'] and not any(f['falsification_id'] in z['falsification_ids'] or f['obligation_id']==z['target_id'] for z in finds): issues.append(Issue('$.falsifications.'+f['falsification_id'],'refuted/inconclusive falsification requires finding'))
 # Directives.
 dir_by_f=defaultdict(list)
 for d in dirs:
  dir_by_f[d['finding_id']].append(d)
  if d['finding_id'] not in find_by: issues.append(Issue('$.directives.'+d['directive_id']+'.finding_id','dangling finding'))
  elif d['target_state']!=find_by[d['finding_id']]['required_route']: issues.append(Issue('$.directives.'+d['directive_id']+'.target_state','must equal finding required route'))
 for f in finds:
  if f['status']=='OPEN' and f['blocking'] and len(dir_by_f[f['finding_id']])!=1: issues.append(Issue('$.directives','each open blocking finding requires exactly one directive: '+f['finding_id']))
 # Bundle and contract.
 bd=bundle(assignment,env,obs,exe,fals,evid,finds,dirs,sb)
 if rc['verification_bundle_digest']!=bd: issues.append(Issue('$.result_contract.verification_bundle_digest','bundle digest mismatch'))
 pairs=[('source_technical_review_contract_id',trc['contract_id']),('source_technical_review_bundle_digest',trc['technical_review_bundle_digest']),('source_implementation_contract_id',ic['contract_id']),('source_implementation_bundle_digest',ic['implementation_bundle_digest']),('source_checklist_contract_id',cc['contract_id']),('repository_tree_digest',repo['tree_digest']),('assignment_id',assignment['assignment_id']),('environment_id',env['environment_id'])]
 for k,v in pairs:
  if rc[k]!=v: issues.append(Issue('$.result_contract.'+k,'source binding mismatch'))
 for k,actual in [('obligation_ids',[x['obligation_id'] for x in obs]),('execution_ids',[x['execution_id'] for x in exe]),('falsification_ids',[x['falsification_id'] for x in fals]),('evidence_ids',[x['evidence_id'] for x in evid]),('finding_ids',[x['finding_id'] for x in finds]),('remediation_directive_ids',[x['directive_id'] for x in dirs])]:
  if rc[k]!=actual: issues.append(Issue('$.result_contract.'+k,'ID list/order mismatch'))
 # Artifact descriptors in output.
 amap={'verifier_assignment':a.assignment,'environment':a.environment,'obligations':a.obligations,'executions':a.executions,'falsification_attempts':a.falsifications,'evidence':a.evidence,'findings':a.findings,'remediation_directives':a.directives,'verification_result_contract':a.result_contract}
 for k,p in amap.items():
  d=out['artifact_files'][k]
  if d['digest']!=digest_file(p): issues.append(Issue('$.output.artifact_files.'+k+'.digest','digest mismatch'))
  actual=len(load(p)) if Path(p).suffix=='.jsonl' else 1
  if d['record_count']!=actual: issues.append(Issue('$.output.artifact_files.'+k+'.record_count','record count mismatch'))
 # Summaries and gate.
 latest={o['obligation_id']:sorted(grouped.get(o['obligation_id'],[]),key=lambda x:x['attempt'])[-1] for o in obs if grouped.get(o['obligation_id'])}
 counts=Counter(x['outcome'] for x in latest.values())
 os=out['obligation_summary']; exp={'total':len(obs),'mandatory':sum(o['applicability']=='MANDATORY' for o in obs),'not_applicable':sum(o['applicability']=='NOT_APPLICABLE' for o in obs),'passed':counts['PASS'],'failed':counts['FAIL'],'blocked':counts['BLOCKED'],'inconclusive':counts['INCONCLUSIVE'],'coverage_complete':set(ob_tests)==source_tests and len(ob_tests)==len(source_tests)}
 for k,v in exp.items():
  if os[k]!=v: issues.append(Issue('$.output.obligation_summary.'+k,f'expected {v!r}'))
 ec=Counter(x['outcome'] for x in exe); es=out['execution_summary']; exp2={'total':len(exe),'passed':ec['PASS'],'failed':ec['FAIL'],'blocked':ec['BLOCKED'],'inconclusive':ec['INCONCLUSIVE'],'not_run':ec['NOT_RUN'],'repository_unchanged':all(x['repository_tree_before']==repo['tree_digest']==x['repository_tree_after'] and not x['mutation_detected'] for x in exe)}
 for k,v in exp2.items():
  if es[k]!=v: issues.append(Issue('$.output.execution_summary.'+k,f'expected {v!r}'))
 fc=Counter(x['resolution'] for x in fals); fs=out['falsification_summary']; expected_f={'total':len(fals),'survived':fc['SURVIVED'],'refuted':fc['REFUTED'],'inconclusive':fc['INCONCLUSIVE'],'required_obligation_ids':sorted(required),'covered_obligation_ids':sorted(covered),'requirement_met':required.issubset(covered) and len(fals)>=inp['verification_policy']['minimum_falsification_attempts']}
 for k,v in expected_f.items():
  vv=sorted(fs[k]) if isinstance(v,list) else fs[k]
  if vv!=v: issues.append(Issue('$.output.falsification_summary.'+k,f'expected {v!r}'))
 openb=[x['finding_id'] for x in finds if x['status']=='OPEN' and x['blocking']]; openn=[x['finding_id'] for x in finds if x['status']=='OPEN' and not x['blocking']]; resolved=[x['finding_id'] for x in finds if x['status']=='RESOLVED']; accepted=[x['finding_id'] for x in finds if x['status']=='ACCEPTED_RISK']
 status,next_state,route=expected_route(finds); fsum=out['finding_summary']; expf={'total':len(finds),'open_blocking_finding_ids':openb,'open_nonblocking_finding_ids':openn,'resolved_finding_ids':resolved,'accepted_risk_finding_ids':accepted,'remediation_directive_ids':[x['directive_id'] for x in dirs],'required_route':route}
 for k,v in expf.items():
  if fsum[k]!=v: issues.append(Issue('$.output.finding_summary.'+k,f'expected {v!r}'))
 gate=out['gate_decision']
 if gate['status']!=status or gate['next_state']!=next_state or gate['blocking_ids']!=openb: issues.append(Issue('$.output.gate_decision','does not match findings and expected lifecycle route'))
 if rc['verdict']['status']!=status or rc['verdict']['next_state']!=next_state or rc['verdict']['blocking_finding_ids']!=openb: issues.append(Issue('$.result_contract.verdict','does not match findings and expected route'))
 ready=status=='READY_FOR_RECONCILIATION'
 if ready:
  if rc['status']!='PASS': issues.append(Issue('$.result_contract.status','ready result must PASS'))
  if any(x['applicability']=='MANDATORY' and latest.get(x['obligation_id'],{}).get('outcome')!='PASS' for x in obs): issues.append(Issue('$.executions','all mandatory obligations must PASS for reconciliation'))
  if not required.issubset(covered): issues.append(Issue('$.falsifications','required falsification coverage incomplete'))
  if not all(rc['integrity'].values()): issues.append(Issue('$.result_contract.integrity','all integrity flags must be true for reconciliation'))
 else:
  if rc['status']=='PASS': issues.append(Issue('$.result_contract.status','loopback/blocking result cannot PASS'))
 if a.require_transition_ready and not ready: issues.append(Issue('$.gate','transition-ready validation requested but result is not READY_FOR_RECONCILIATION'))
 return issues
def main():
 p=argparse.ArgumentParser(); p.add_argument('--kind',choices=['package','file'],default='package'); p.add_argument('--schema-kind',choices=sorted(MAP)); p.add_argument('--file')
 for n in ['input','output','assignment','environment','technical_review_output','technical_review_contract','implementation_contract','checklist_contract','checklists','source_verifications','repository_state','changes','source_ledger','obligations','executions','falsifications','evidence','findings','directives','result_contract']: p.add_argument('--'+n.replace('_','-'))
 p.add_argument('--require-transition-ready',action='store_true'); a=p.parse_args()
 if a.kind=='file':
  if not a.file or not a.schema_kind: p.error('--file and --schema-kind required')
  issues=structural(load(a.file),a.schema_kind)
 else:
  missing=[n for n in ['input','output','assignment','environment','technical_review_output','technical_review_contract','implementation_contract','checklist_contract','checklists','source_verifications','repository_state','changes','source_ledger','obligations','executions','falsifications','evidence','findings','directives','result_contract'] if not getattr(a,n)]
  if missing: p.error('missing: '+', '.join(missing))
  issues=validate_package(a)
 if issues:
  for i in issues: print(i,file=sys.stderr)
  print(f'INVALID ({len(issues)} issue(s))',file=sys.stderr); return 1
 print('VALID'); return 0
if __name__=='__main__': raise SystemExit(main())
