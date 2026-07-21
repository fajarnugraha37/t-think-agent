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
MAP={'input':'input.schema.json','output':'output.schema.json','assignment':'review-assignment.schema.json','technical_check':'technical-review-check.schema.json','assessment':'change-assessment.schema.json','challenge':'evidence-challenge.schema.json','finding':'review-finding.schema.json','directive':'remediation-directive.schema.json','result_contract':'technical-review-result-contract.schema.json','self_review_output':'upstream-self-review-output.schema.json','self_review_contract':'upstream-self-review-result-contract.schema.json','bounded_output':'upstream-bounded-output.schema.json','implementation_contract':'upstream-implementation-result-contract.schema.json','checklist_contract':'upstream-approved-checklist-contract.schema.json','checklist':'upstream-checklist-item.schema.json','change':'upstream-change-record.schema.json','verification':'upstream-verification-result.schema.json','repository':'upstream-repository-state.schema.json','evidence':'upstream-evidence-record.schema.json','sr_check':'upstream-self-review-check.schema.json','sr_conformance':'upstream-self-review-conformance.schema.json','sr_audit':'upstream-self-review-audit.schema.json','sr_finding':'upstream-self-review-finding.schema.json','sr_directive':'upstream-self-review-directive.schema.json'}
SCHEMAS={k:ROOT/'schemas'/v for k,v in MAP.items()}
DIMS=['ARCHITECTURE_CONFORMANCE', 'FUNCTIONAL_CORRECTNESS', 'CHECKLIST_AND_SCOPE_CONFORMANCE', 'API_AND_CONTRACT_COMPATIBILITY', 'DATA_MODEL_AND_TRANSACTIONAL_INTEGRITY', 'CONCURRENCY_AND_IDEMPOTENCY', 'SECURITY_AND_PRIVACY', 'ERROR_HANDLING', 'RESILIENCE_AND_FAILURE_MODES', 'PERFORMANCE_AND_RESOURCE_USE', 'OBSERVABILITY', 'OPERABILITY', 'MIGRATION_AND_DEPLOYMENT', 'ROLLBACK_AND_RECOVERY', 'TEST_STRATEGY', 'DEPENDENCY_AND_SUPPLY_CHAIN', 'MAINTAINABILITY', 'CODE_QUALITY', 'EVIDENCE_QUALITY', 'SELF_REVIEW_CHALLENGE']
PRIORITY=['PROBLEM_ALIGNMENT','INVESTIGATION','SYSTEM_MODEL','SOLUTION_DESIGN','SOLUTION_CRITIQUE','IMPLEMENTATION_PLAN','PLAN_CRITIQUE','IMPLEMENTATION_CHECKLIST','CHECKLIST_CRITIQUE','BOUNDED_IMPLEMENTATION','SELF_REVIEW']
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
 if kind in ['technical_check','assessment','challenge','finding','directive','checklist','change','verification','evidence','sr_check','sr_conformance','sr_audit','sr_finding','sr_directive']:
  if not isinstance(obj,list): return [Issue('$','expected JSONL/list')]
  out=[]
  for i,x in enumerate(obj):
   for e in validate_obj(x,kind): e.path=f'$[{i}]'+e.path[1:]; out.append(e)
  return out
 return validate_obj(obj,kind)
def digest_file(path): return 'sha256:'+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canon(obj): return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def bundle(checks,assessments,challenges,findings,directives,assignment,source_binding):
 return 'sha256:'+hashlib.sha256(canon({'assignment':assignment,'technical_checks':checks,'change_assessments':assessments,'evidence_challenges':challenges,'findings':findings,'remediation_directives':directives,'source_binding':source_binding})).hexdigest()
def expected_route(findings):
 blocking=[x for x in findings if x['status']=='OPEN' and x['blocking']]
 if not blocking: return 'READY_FOR_VERIFICATION','VERIFICATION','NONE'
 routes={x['required_route'] for x in blocking}; route=next((r for r in PRIORITY if r in routes),'SELF_REVIEW')
 return 'RETURN_TO_'+route,route,route
def validate_package(a):
 issues=[]
 inp=load(a.input); out=load(a.output); assignment=load(a.assignment); sro=load(a.self_review_output); src=load(a.self_review_contract); bo=load(a.bounded_output); ic=load(a.implementation_contract); cc=load(a.checklist_contract); checklists=load(a.checklists); changes=load(a.changes); verifs=load(a.verifications); repo=load(a.repository_after); ledger=load(a.ledger); srchecks=load(a.self_review_checks); srconfs=load(a.self_review_conformance); sraudits=load(a.self_review_audits); srfinds=load(a.self_review_findings); srdirs=load(a.self_review_directives); checks=load(a.technical_checks); assessments=load(a.change_assessments); challenges=load(a.evidence_challenges); findings=load(a.findings); directives=load(a.directives); rc=load(a.result_contract)
 objs=[(inp,'input'),(out,'output'),(assignment,'assignment'),(sro,'self_review_output'),(src,'self_review_contract'),(bo,'bounded_output'),(ic,'implementation_contract'),(cc,'checklist_contract'),(checklists,'checklist'),(changes,'change'),(verifs,'verification'),(repo,'repository'),(ledger,'evidence'),(srchecks,'sr_check'),(srconfs,'sr_conformance'),(sraudits,'sr_audit'),(srfinds,'sr_finding'),(srdirs,'sr_directive'),(checks,'technical_check'),(assessments,'assessment'),(challenges,'challenge'),(findings,'finding'),(directives,'directive'),(rc,'result_contract')]
 for obj,kind in objs: issues+=structural(obj,kind)
 if issues: return issues
 for rows,key,name in [(checks,'technical_check_id','checks'),(assessments,'assessment_id','assessments'),(challenges,'challenge_id','challenges'),(findings,'finding_id','findings'),(directives,'directive_id','directives')]: unique(rows,key,'$.'+name,issues)
 # Source binding and readiness.
 if sro['gate_decision']['status']!='READY_FOR_TECHNICAL_REVIEW' or sro['gate_decision']['next_state']!='TECHNICAL_REVIEW': issues.append(Issue('$.source.self_review_output','must be READY_FOR_TECHNICAL_REVIEW -> TECHNICAL_REVIEW'))
 if src['status']!='PASS' or src['verdict']['status']!='READY_FOR_TECHNICAL_REVIEW': issues.append(Issue('$.source.self_review_contract','must be PASS and ready'))
 sb={'self_review_contract_id':src['contract_id'],'self_review_bundle_digest':src['self_review_bundle_digest'],'self_review_run_id':src['self_review_run_id'],'implementation_result_contract_id':ic['contract_id'],'implementation_bundle_digest':ic['implementation_bundle_digest'],'source_checklist_contract_id':cc['contract_id'],'repository_after_tree_digest':repo['tree_digest']}
 ia=inp['source_authorization']
 for k,v in [('self_review_contract_id',sb['self_review_contract_id']),('self_review_bundle_digest',sb['self_review_bundle_digest']),('self_review_run_id',sb['self_review_run_id']),('implementation_result_contract_id',sb['implementation_result_contract_id']),('implementation_bundle_digest',sb['implementation_bundle_digest']),('approved_checklist_contract_id',sb['source_checklist_contract_id']),('repository_after_tree_digest',sb['repository_after_tree_digest'])]:
  if ia[k]!=v: issues.append(Issue(f'$.input.source_authorization.{k}','source binding mismatch'))
 if out['source_binding']!=sb: issues.append(Issue('$.output.source_binding','must exactly match computed source binding'))
 if src['source_implementation_contract_id']!=ic['contract_id'] or src['source_implementation_bundle_digest']!=ic['implementation_bundle_digest'] or src['source_checklist_contract_id']!=cc['contract_id'] or src['repository_after_tree_digest']!=repo['tree_digest']: issues.append(Issue('$.source','upstream contracts are inconsistent'))
 # Source artifact descriptors.
 source_args={'self_review_output':a.self_review_output,'self_review_result_contract':a.self_review_contract,'bounded_output':a.bounded_output,'implementation_result_contract':a.implementation_contract,'approved_checklist_contract':a.checklist_contract,'checklist_items':a.checklists,'change_records':a.changes,'verification_results':a.verifications,'repository_after':a.repository_after,'evidence_ledger':a.ledger,'self_review_checks':a.self_review_checks,'self_review_conformance':a.self_review_conformance,'self_review_audits':a.self_review_audits,'self_review_findings':a.self_review_findings,'self_review_directives':a.self_review_directives}
 source_counts={'self_review_output':1,'self_review_result_contract':1,'bounded_output':1,'implementation_result_contract':1,'approved_checklist_contract':1,'checklist_items':len(checklists),'change_records':len(changes),'verification_results':len(verifs),'repository_after':1,'evidence_ledger':len(ledger),'self_review_checks':len(srchecks),'self_review_conformance':len(srconfs),'self_review_audits':len(sraudits),'self_review_findings':len(srfinds),'self_review_directives':len(srdirs)}
 source_verified=True
 for k,p in source_args.items():
  ref=inp['source_artifacts'][k]; actual=digest_file(p)
  if ref['digest']!=actual: issues.append(Issue(f'$.input.source_artifacts.{k}.digest',f'expected {actual}')); source_verified=False
  if ref['record_count']!=source_counts[k]: issues.append(Issue(f'$.input.source_artifacts.{k}.record_count',f'expected {source_counts[k]}')); source_verified=False
 # Assignment and independence.
 run=inp['metadata']['technical_review_run_id']; reviewer=assignment['reviewer_id']; implementer=bo['metadata']['author_agent']; selfrev=sro['metadata']['reviewer_agent']
 if assignment['technical_review_run_id']!=run: issues.append(Issue('$.assignment.technical_review_run_id','run mismatch'))
 independent=(reviewer not in [implementer,selfrev] and all([assignment['independence']['not_implementation_author'],assignment['independence']['not_self_reviewer'],assignment['independence']['no_unresolved_conflict']]) and not assignment['independence']['conflicting_identity_ids'])
 if not independent: issues.append(Issue('$.assignment.independence','reviewer must be independent from implementation author and self-reviewer'))
 competency=set(assignment['required_competencies']).issubset(set(assignment['declared_competencies']))
 if not competency: issues.append(Issue('$.assignment.declared_competencies','does not cover all required competencies'))
 if out['metadata']['reviewer_id']!=reviewer: issues.append(Issue('$.output.metadata.reviewer_id','must match assignment reviewer'))
 exp_ind={'reviewer_id':reviewer,'implementation_author_id':implementer,'self_reviewer_id':selfrev,'independent':independent,'competency_coverage_complete':competency,'conflict_ids':assignment['independence']['conflicting_identity_ids']}
 if out['independence']!=exp_ind: issues.append(Issue('$.output.independence','does not match assignment and source identities'))
 # ID sets.
 chk={x['checklist_id']:x for x in checklists}; chg={x['change_id']:x for x in changes}; vf={x['result_id']:x for x in verifs}; evid={x['id']:x for x in ledger}; srcchk={x['review_check_id']:x for x in srchecks}; srconf={x['conformance_id']:x for x in srconfs}; sraud={x['audit_id']:x for x in sraudits}; fby={x['finding_id']:x for x in findings}; dby={x['directive_id']:x for x in directives}
 source_targets=set(chk)|set(chg)|set(vf)|set(evid)|set(srcchk)|set(srconf)|set(sraud)|{src['contract_id'],ic['contract_id'],cc['contract_id']}
 # Mandatory checks and source self-review claim coverage.
 dc=Counter(x['dimension'] for x in checks)
 for d in DIMS:
  if dc[d]!=1: issues.append(Issue('$.technical_checks',f'dimension {d} expected exactly once, got {dc[d]}'))
 sr_cov=Counter()
 for x in checks:
  if x['technical_review_run_id']!=run or x['reviewer_id']!=reviewer: issues.append(Issue(f'$.technical_checks.{x["technical_check_id"]}','run/reviewer mismatch'))
  if not set(x['target_ids']).issubset(source_targets|{z['technical_check_id'] for z in checks}): issues.append(Issue(f'$.technical_checks.{x["technical_check_id"]}.target_ids','unknown target'))
  if not set(x['source_self_review_check_ids']).issubset(srcchk): issues.append(Issue(f'$.technical_checks.{x["technical_check_id"]}.source_self_review_check_ids','unknown self-review check'))
  for z in x['source_self_review_check_ids']: sr_cov[z]+=1
  if x['self_review_disposition'] in ['DISAGREE','PARTIAL'] and not any(x['technical_check_id'] in f['target_ids'] for f in findings): issues.append(Issue(f'$.technical_checks.{x["technical_check_id"]}','disagreement/partial disposition requires finding'))
 for sid in srcchk:
  if sr_cov[sid]<1: issues.append(Issue('$.technical_checks',f'self-review check {sid} is not covered'))
 # Change assessments exactly once and exact binding.
 ac=Counter(x['change_id'] for x in assessments)
 for cid in chg:
  if ac[cid]!=1: issues.append(Issue('$.change_assessments',f'change {cid} expected exactly once, got {ac[cid]}'))
 for x in assessments:
  if x['technical_review_run_id']!=run or x['reviewer_id']!=reviewer: issues.append(Issue(f'$.change_assessments.{x["assessment_id"]}','run/reviewer mismatch'))
  c=chg.get(x['change_id'])
  if not c: issues.append(Issue(f'$.change_assessments.{x["assessment_id"]}.change_id','unknown change')); continue
  if x['checklist_id']!=c['checklist_id'] or x['path']!=c['path'] or x['source_diff_digest']!=c['diff_digest']: issues.append(Issue(f'$.change_assessments.{x["assessment_id"]}','change binding drift'))
  if not set(x['self_review_conformance_ids']).issubset(srconf): issues.append(Issue(f'$.change_assessments.{x["assessment_id"]}.self_review_conformance_ids','unknown conformance result'))
  if any(srconf[z]['checklist_id']!=x['checklist_id'] for z in x['self_review_conformance_ids']): issues.append(Issue(f'$.change_assessments.{x["assessment_id"]}.self_review_conformance_ids','conformance checklist mismatch'))
  if x['outcome']=='APPROVE' and (not x['semantic_conformance'] or not x['scope_conformance'] or x['finding_ids']): issues.append(Issue(f'$.change_assessments.{x["assessment_id"]}','APPROVE requires semantic/scope conformance and no finding'))
  if x['outcome'] in ['REQUEST_CHANGES','INCONCLUSIVE'] and not x['finding_ids']: issues.append(Issue(f'$.change_assessments.{x["assessment_id"]}.finding_ids','non-approval requires finding'))
  if not set(x['finding_ids']).issubset(fby): issues.append(Issue(f'$.change_assessments.{x["assessment_id"]}.finding_ids','unknown finding'))
 # Challenges.
 if len(challenges)<inp['review_controls']['minimum_evidence_challenges']: issues.append(Issue('$.evidence_challenges','minimum challenge count not met'))
 target_maps={'SELF_REVIEW_CHECK':set(srcchk),'CONFORMANCE_RESULT':set(srconf),'EVIDENCE_AUDIT':set(sraud),'SELF_REVIEW_RESULT_CONTRACT':{src['contract_id']}}
 for x in challenges:
  if x['technical_review_run_id']!=run or x['reviewer_id']!=reviewer: issues.append(Issue(f'$.evidence_challenges.{x["challenge_id"]}','run/reviewer mismatch'))
  if x['target_id'] not in target_maps[x['target_type']]: issues.append(Issue(f'$.evidence_challenges.{x["challenge_id"]}.target_id','unknown target'))
  if x['resolution']=='CONFIRMED' and (x['impact']!='NONE' or x['finding_ids']): issues.append(Issue(f'$.evidence_challenges.{x["challenge_id"]}','CONFIRMED must have NONE impact and no finding'))
  if x['resolution'] in ['REFUTED','INCONCLUSIVE'] and (x['impact']=='NONE' or not x['finding_ids']): issues.append(Issue(f'$.evidence_challenges.{x["challenge_id"]}','refuted/inconclusive challenge requires impact and finding'))
  if not set(x['finding_ids']).issubset(fby): issues.append(Issue(f'$.evidence_challenges.{x["challenge_id"]}.finding_ids','unknown finding'))
 # Findings and directives.
 all_targets=source_targets|{x['technical_check_id'] for x in checks}|{x['assessment_id'] for x in assessments}|{x['challenge_id'] for x in challenges}
 failed={x['technical_check_id'] for x in checks if x['outcome'] in ['FAIL','INCONCLUSIVE']}|{x['assessment_id'] for x in assessments if x['outcome'] in ['REQUEST_CHANGES','INCONCLUSIVE']}|{x['challenge_id'] for x in challenges if x['resolution'] in ['REFUTED','INCONCLUSIVE']}
 for x in findings:
  if not set(x['target_ids']).issubset(all_targets): issues.append(Issue(f'$.findings.{x["finding_id"]}.target_ids','contains unknown target'))
  if x['status']=='OPEN' and x['required_route']=='NONE': issues.append(Issue(f'$.findings.{x["finding_id"]}.required_route','open finding requires route'))
  if x['remediation_type']=='MECHANICAL' and x['required_route']!='BOUNDED_IMPLEMENTATION': issues.append(Issue(f'$.findings.{x["finding_id"]}.required_route','mechanical finding must route to BOUNDED_IMPLEMENTATION'))
  if x['category']=='SELF_REVIEW_DEFECT' and x['required_route']!='SELF_REVIEW': issues.append(Issue(f'$.findings.{x["finding_id"]}.required_route','self-review defect must route to SELF_REVIEW'))
  if x['category'] in ['SEMANTIC_DRIFT','MODEL_OR_SOLUTION_DEFECT','PROBLEM_MISALIGNMENT'] and x['required_route'] in ['NONE','BOUNDED_IMPLEMENTATION','SELF_REVIEW']: issues.append(Issue(f'$.findings.{x["finding_id"]}.required_route','semantic/model/problem defect must route upstream'))
 for tid in failed:
  if not any(tid in f['target_ids'] and f['status']=='OPEN' for f in findings): issues.append(Issue('$.findings',f'failed/inconclusive target {tid} lacks open finding'))
 for f in [x for x in findings if x['status']=='OPEN' and x['remediation_type']!='NONE']:
  ds=[d for d in directives if f['finding_id'] in d['finding_ids']]
  if len(ds)!=1: issues.append(Issue(f'$.directives.{f["finding_id"]}',f'expected exactly one directive, got {len(ds)}'))
 for x in directives:
  if not set(x['finding_ids']).issubset(fby): issues.append(Issue(f'$.directives.{x["directive_id"]}.finding_ids','unknown finding'))
  if not set(x['target_checklist_ids']).issubset(chk): issues.append(Issue(f'$.directives.{x["directive_id"]}.target_checklist_ids','unknown checklist'))
  if x['applied']: issues.append(Issue(f'$.directives.{x["directive_id"]}.applied','directives must remain unapplied'))
  if any(fby[z]['required_route']!=x['route'] for z in x['finding_ids']): issues.append(Issue(f'$.directives.{x["directive_id"]}.route','must match finding route'))
 # Summaries.
 c=Counter(x['outcome'] for x in checks); rs={'total':len(checks),'passed':c['PASS'],'failed':c['FAIL'],'not_applicable':c['NOT_APPLICABLE'],'inconclusive':c['INCONCLUSIVE'],'required_dimensions':len(DIMS),'covered_dimensions':len(set(x['dimension'] for x in checks))}
 if out['review_summary']!=rs: issues.append(Issue('$.output.review_summary','does not match checks'))
 c2=Counter(x['outcome'] for x in assessments); complete=set(ac)==set(chg) and all(v==1 for v in ac.values()); asum={'total':len(assessments),'approved':c2['APPROVE'],'request_changes':c2['REQUEST_CHANGES'],'inconclusive':c2['INCONCLUSIVE'],'complete_coverage':complete}
 if out['change_assessment_summary']!=asum: issues.append(Issue('$.output.change_assessment_summary','does not match assessments'))
 c3=Counter(x['resolution'] for x in challenges); minc=inp['review_controls']['minimum_evidence_challenges']; chsum={'total':len(challenges),'confirmed':c3['CONFIRMED'],'refuted':c3['REFUTED'],'inconclusive':c3['INCONCLUSIVE'],'minimum_required':minc,'requirement_met':len(challenges)>=minc}
 if out['challenge_summary']!=chsum: issues.append(Issue('$.output.challenge_summary','does not match challenges'))
 openb=sorted(x['finding_id'] for x in findings if x['status']=='OPEN' and x['blocking']); openn=sorted(x['finding_id'] for x in findings if x['status']=='OPEN' and not x['blocking']); resolved=sorted(x['finding_id'] for x in findings if x['status']=='RESOLVED'); accepted=sorted(x['finding_id'] for x in findings if x['status']=='ACCEPTED_RISK'); gate,state,route=expected_route(findings)
 fs={'total':len(findings),'open_blocking_finding_ids':openb,'open_nonblocking_finding_ids':openn,'resolved_finding_ids':resolved,'accepted_risk_finding_ids':accepted,'remediation_directive_ids':[x['directive_id'] for x in directives],'required_route':route}
 if out['finding_summary']!=fs: issues.append(Issue('$.output.finding_summary','does not match findings/directives'))
 dims_ok=all(dc[d]==1 for d in DIMS); claims_ok=all(sr_cov[x]>=1 for x in srcchk); challenge_ok=len(challenges)>=minc and all(x['resolution']=='CONFIRMED' for x in challenges); evidence_ok=all(x.get('evidence_refs') for x in checks+assessments+challenges+findings+directives); scope_ok=all(x['scope_conformance'] for x in assessments if x['outcome']=='APPROVE') and not any(x['category']=='SCOPE_DRIFT' and x['status']=='OPEN' for x in findings); sem_ok=all(x['semantic_conformance'] for x in assessments if x['outcome']=='APPROVE') and not any(x['category'] in ['SEMANTIC_DRIFT','MODEL_OR_SOLUTION_DEFECT'] and x['status']=='OPEN' for x in findings); no_mut=all(not x['applied'] for x in directives)
 integ={'source_bundle_verified':source_verified,'reviewer_independent':independent,'mandatory_dimensions_complete':dims_ok,'change_coverage_complete':complete,'self_review_claims_covered':claims_ok,'evidence_challenges_complete':challenge_ok,'evidence_complete':evidence_ok,'scope_preserved':scope_ok,'semantic_boundary_preserved':sem_ok,'no_silent_mutation':no_mut}
 if out['integrity']!=integ: issues.append(Issue('$.output.integrity','does not match computed integrity'))
 ready=all(x['outcome'] in ['PASS','NOT_APPLICABLE'] for x in checks) and all(x['outcome']=='APPROVE' for x in assessments) and all(x['resolution']=='CONFIRMED' for x in challenges) and not openb and not directives and all(integ.values())
 if not ready and gate=='READY_FOR_VERIFICATION': gate,state='BLOCKED','TECHNICAL_REVIEW'
 if out['gate_decision']['status']!=gate or out['gate_decision']['next_state']!=state: issues.append(Issue('$.output.gate_decision',f'expected {gate} -> {state}'))
 expected_status='COMPLETE' if gate=='READY_FOR_VERIFICATION' else ('FAILED' if gate.startswith('RETURN_TO_') else 'BLOCKED')
 if out['metadata']['status']!=expected_status: issues.append(Issue('$.output.metadata.status',f'expected {expected_status}'))
 # Result contract.
 bd=bundle(checks,assessments,challenges,findings,directives,assignment,sb)
 if rc['technical_review_bundle_digest']!=bd: issues.append(Issue('$.result_contract.technical_review_bundle_digest',f'expected {bd}'))
 scalar={'technical_review_run_id':run,'assignment_id':assignment['assignment_id'],'reviewer_id':reviewer,'source_self_review_contract_id':src['contract_id'],'source_self_review_bundle_digest':src['self_review_bundle_digest'],'source_implementation_contract_id':ic['contract_id'],'source_implementation_bundle_digest':ic['implementation_bundle_digest'],'source_checklist_contract_id':cc['contract_id'],'repository_after_tree_digest':repo['tree_digest']}
 for k,v in scalar.items():
  if rc[k]!=v: issues.append(Issue(f'$.result_contract.{k}','source or identity binding mismatch'))
 exacts=[('technical_check_ids',{x['technical_check_id'] for x in checks}),('change_assessment_ids',{x['assessment_id'] for x in assessments}),('evidence_challenge_ids',{x['challenge_id'] for x in challenges}),('finding_ids',set(fby)),('remediation_directive_ids',set(dby))]
 for field,expected in exacts:
  if set(rc[field])!=expected: issues.append(Issue(f'$.result_contract.{field}','must exactly enumerate artifact IDs'))
 if rc['integrity']!=integ: issues.append(Issue('$.result_contract.integrity','must equal computed integrity'))
 if rc['verdict']['status']!=gate or rc['verdict']['next_state']!=state or sorted(rc['verdict']['blocking_finding_ids'])!=openb: issues.append(Issue('$.result_contract.verdict','does not match computed gate'))
 exp_rc='PASS' if gate=='READY_FOR_VERIFICATION' else ('FAIL' if gate.startswith('RETURN_TO_') else 'BLOCKED')
 if rc['status']!=exp_rc: issues.append(Issue('$.result_contract.status',f'expected {exp_rc}'))
 # Output artifacts.
 amap={'review_assignment':(a.assignment,1),'technical_checks':(a.technical_checks,len(checks)),'change_assessments':(a.change_assessments,len(assessments)),'evidence_challenges':(a.evidence_challenges,len(challenges)),'findings':(a.findings,len(findings)),'remediation_directives':(a.directives,len(directives)),'technical_review_result_contract':(a.result_contract,1)}
 for k,(p,n) in amap.items():
  ref=out['artifact_files'][k]
  if ref['record_count']!=n: issues.append(Issue(f'$.output.artifact_files.{k}.record_count',f'expected {n}'))
  actual=digest_file(p)
  if ref['digest']!=actual: issues.append(Issue(f'$.output.artifact_files.{k}.digest',f'expected {actual}'))
 if a.require_transition_ready and gate!='READY_FOR_VERIFICATION': issues.append(Issue('$.transition',f'package is not transition-ready; got {gate}'))
 return issues
def main():
 p=argparse.ArgumentParser(); p.add_argument('--kind',required=True,choices=['schema','input','output','assignment','technical_check','assessment','challenge','finding','directive','result_contract','package']); p.add_argument('--file')
 for x in ['input','output','assignment','self-review-output','self-review-contract','bounded-output','implementation-contract','checklist-contract','checklists','changes','verifications','repository-after','ledger','self-review-checks','self-review-conformance','self-review-audits','self-review-findings','self-review-directives','technical-checks','change-assessments','evidence-challenges','findings','directives','result-contract']: p.add_argument('--'+x,dest=x.replace('-','_'))
 p.add_argument('--require-transition-ready',action='store_true'); a=p.parse_args(); issues=[]
 try:
  if a.kind=='schema':
   for q in sorted((ROOT/'schemas').glob('*.json')): Draft202012Validator.check_schema(json.loads(q.read_text()))
  elif a.kind=='package':
   req=['input','output','assignment','self_review_output','self_review_contract','bounded_output','implementation_contract','checklist_contract','checklists','changes','verifications','repository_after','ledger','self_review_checks','self_review_conformance','self_review_audits','self_review_findings','self_review_directives','technical_checks','change_assessments','evidence_challenges','findings','directives','result_contract']; miss=[x for x in req if not getattr(a,x)]
   issues=[Issue('$','missing package arguments: '+', '.join(miss))] if miss else validate_package(a)
  else:
   if not a.file: issues=[Issue('$','--file required')]
   else: issues=structural(load(a.file),a.kind)
 except Exception as e: issues=[Issue('$',f'validator failure: {type(e).__name__}: {e}')]
 if issues:
  for i in issues: print(i,file=sys.stderr)
  return 1
 print('VALID')
 if a.kind=='package' and a.require_transition_ready: print('Package is transition-ready for VERIFICATION')
 return 0
if __name__=='__main__': raise SystemExit(main())
