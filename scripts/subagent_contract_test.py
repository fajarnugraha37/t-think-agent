#!/usr/bin/env python3
from __future__ import annotations
import copy,json,re,sys,tomllib
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bin'))
from tthink_runtime import audit_boundaries,validate_delegation,validate_result
D='a'*64
def packet(phase,agent,skill,mode='deny',approved=None,generated=None,lane='full',track=None,next_state=None):
 return {'schema_version':'2.0.0','identity':{'work_id':'W-1','run_id':'RUN-1','invocation_id':'INV-1','parent_agent':'t-think','target_agent':agent},'lifecycle':{'current_phase':phase,'skill':skill,'attempt':1,'lane':lane,'artifact_mode':{'quick':'compact','standard':'normal','full':'exhaustive'}[lane],'expected_next_state':next_state or phase,'track':track},'objective':{'statement':'Complete the authorized bounded phase contract','completion_criteria':['Produce schema-valid evidence-backed output']},'workspace':{'root':'.','discovery':{'respect_vcs_ignore':True,'include_untracked':True,'include_ignored':False}},'permissions':{'workspace_read':'allow','outside_workspace':'deny','source_write':mode,'governance_artifact_write':'.t-think/**','approved_write_targets':approved or [],'generated_output_paths':generated or [],'protected_paths':['.git/**','.env','.env.*','**/secrets/**'],'ignored_file_access':{'mode':'deny','human_approval_ref':None},'spawn_subagent':'deny'},'artifact_inputs':[],'output_contract':{'schema':f'skills/{skill}/schemas/output.schema.json','artifact_path':f'.t-think/W-1/artifacts/{track or phase.lower()}.yaml','result_path':'.t-think/W-1/results/INV-1.yaml','boundary_report_path':'.t-think/W-1/boundary-reports/INV-1.yaml'},'stop_conditions':['missing evidence','new semantic decision']}
def activity(**kw):
 d={'source_changes':[],'governance_artifact_changes':['.t-think/W-1/artifacts/x.yaml'],'generated_output_changes':[],'outside_workspace_access':[],'ignored_file_access':[]};d.update(kw);return d
def check(ok,msg,issues):
 if not ok:issues.append(msg)
def main():
 issues=[];passed=[];reg=yaml.safe_load((ROOT/'orchestrator/agent-registry.yaml').read_text());schema=json.loads((ROOT/'schemas/agent-manifest.schema.json').read_text())
 check(len(reg['agents'])==10 and reg['topology']=='star' and reg['max_delegation_depth']==1,'registry must contain 10 terminal depth-1 workers',issues)
 for a in reg['agents']:
  check(not list(Draft202012Validator(schema).iter_errors(a)),f'invalid manifest {a["name"]}',issues);check(a['permissions']['spawn_subagent']=='deny',f'{a["name"]} can nest',issues)
 passed.append('agent manifests and star topology')
 inv=packet('INVESTIGATION','t-investigator','t-investigation',next_state='SYSTEM_MODEL');check(not validate_delegation(inv),f'investigation rejected {validate_delegation(inv)}',issues)
 build=packet('BOUNDED_IMPLEMENTATION','t-builder','t-bounded-implementation','approved_targets_only',['src/**'],['target/**'],next_state='IMPLEMENTATION_REVIEW');check(not validate_delegation(build),f'build rejected {validate_delegation(build)}',issues)
 check(audit_boundaries(build,activity(source_changes=['src/x.ts'],generated_output_changes=['target/x']))['status']=='PASS','authorized builder activity rejected',issues)
 check(audit_boundaries(build,activity(source_changes=['other/x.ts']))['status']=='FAIL','unapproved source accepted',issues)
 passed.append('read and write boundaries')
 tracks=[('quick','self_review','t-builder','t-self-review'),('quick','technical_review','t-reviewer','t-technical-review'),('standard','security_review','t-security-reviewer','t-security-review'),('standard','breaking_review','t-breaking-reviewer','t-breaking-review')]
 for lane,track,agent,skill in tracks:
  p=packet('IMPLEMENTATION_REVIEW',agent,skill,lane=lane,track=track,next_state='IMPLEMENTATION_REVIEW');check(not validate_delegation(p),f'{lane}/{track} rejected: {validate_delegation(p)}',issues);check(audit_boundaries(p,activity(source_changes=['src/x']))['status']=='FAIL',f'{track} wrote source',issues)
 bad=packet('IMPLEMENTATION_REVIEW','t-security-reviewer','t-security-review',lane='quick',track='security_review',next_state='IMPLEMENTATION_REVIEW');check(bool(validate_delegation(bad)),'quick security track incorrectly active',issues)
 no_track=packet('IMPLEMENTATION_REVIEW','t-reviewer','t-technical-review',lane='standard',next_state='IMPLEMENTATION_REVIEW');check(bool(validate_delegation(no_track)),'composite delegation without track accepted',issues)
 passed.append('lane-specific independent review tracks')
 boundary=audit_boundaries(inv,activity());result={'schema_version':'2.0.0','invocation_id':'INV-1','agent':'t-investigator','phase':'INVESTIGATION','skill':'t-investigation','track':None,'status':'COMPLETED','artifact':{'path':'.t-think/W-1/artifacts/investigation.yaml','sha256':D},'claim_counts':{'FACT':1,'INFERENCE':0,'ASSUMPTION':0,'UNKNOWN':0,'CONFLICT':0},'evidence':{'referenced':1,'missing':0},'unresolved_items':[],'recommended_transition':{'state':'SYSTEM_MODEL','gate':None},'validation':{'schema_passed':True,'semantic_checks_passed':True},'boundary_report':{'path':'.t-think/W-1/boundary-reports/INV-1.yaml','sha256':D,'status':'PASS'}}
 check(not validate_result(result,inv,boundary),f'valid result rejected {validate_result(result,inv,boundary)}',issues)
 tp=packet('IMPLEMENTATION_REVIEW','t-reviewer','t-technical-review',lane='quick',track='technical_review',next_state='IMPLEMENTATION_REVIEW');tb=audit_boundaries(tp,activity());tr=copy.deepcopy(result);tr.update({'agent':'t-reviewer','phase':'IMPLEMENTATION_REVIEW','skill':'t-technical-review','track':'technical_review'});tr['recommended_transition']['state']='IMPLEMENTATION_REVIEW';check(not validate_result(tr,tp,tb),f'track result rejected {validate_result(tr,tp,tb)}',issues)
 tr['track']='self_review';check(bool(validate_result(tr,tp,tb)),'mismatched track result accepted',issues)
 passed.append('result envelope track binding')
 n=len(reg['agents']);expected=n+1
 for platform in ('opencode','claude-code','cursor'):check(len(list((ROOT/'adapters'/platform).glob('t-*.md')))==expected,f'{platform} count mismatch',issues)
 check(len(list((ROOT/'adapters/codex/agents').glob('t-*.toml')))==n,'Codex worker count mismatch',issues)
 passed.append('platform adapter structure')
 report={'status':'FAIL' if issues else 'PASS','passed_contracts':passed,'issues':issues};(ROOT/'reports/subagent-contract-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 1 if issues else 0
if __name__=='__main__':raise SystemExit(main())
