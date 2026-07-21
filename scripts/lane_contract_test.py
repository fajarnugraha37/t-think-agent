#!/usr/bin/env python3
from __future__ import annotations
import copy,json,subprocess,sys,tempfile
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bin'))
from tthink_runtime import build_phase_waivers,classify_lane,composite_tracks,lane_config,phase_path,promotion_state,resolve_route,validate_schema
EXPECTED={
'quick':['PROBLEM_ALIGNMENT','BOUNDED_IMPLEMENTATION','IMPLEMENTATION_REVIEW','VERIFICATION','RECONCILIATION','COMPLETED'],
'standard':['PROBLEM_ALIGNMENT','INVESTIGATION','SOLUTION_DESIGN','IMPLEMENTATION_BLUEPRINT','BLUEPRINT_CRITIQUE','BOUNDED_IMPLEMENTATION','IMPLEMENTATION_REVIEW','VERIFICATION','RECONCILIATION','COMPLETED'],
'full':['PROBLEM_ALIGNMENT','INVESTIGATION','SYSTEM_MODEL','MODEL_CRITIQUE','SOLUTION_DESIGN','SOLUTION_CRITIQUE','IMPLEMENTATION_BLUEPRINT','BLUEPRINT_CRITIQUE','BOUNDED_IMPLEMENTATION','IMPLEMENTATION_REVIEW','VERIFICATION','RECONCILIATION','COMPLETED']}
def check(ok,msg,issues):
 if not ok:issues.append(msg)
def state(lane,phase):
 c=lane_config(lane);return {'schema_version':'2.3.0','work_id':'W-1','current_state':phase,'current_run_id':'RUN-1','model_profile':'economy','repository_root':'.','work_directory':'.t-think/W-1','active_skill':None,'active_agent':None,'last_gate':None,'last_validator':None,'human_gate_pending':False,'governance_lane':{'requested':lane,'selected':lane,'artifact_mode':c['artifact_mode'],'risk_score':0,'hard_triggers':[],'assessment_path':'.t-think/W-1/artifacts/lane-assessment.yaml','waiver_path':'.t-think/W-1/artifacts/phase-waivers.yaml','promotion_count':0},'history':[]}
def run(cmd,cwd=None,expect=0):
 p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if p.returncode!=expect:raise RuntimeError(f"exit {p.returncode}, expected {expect}: {' '.join(map(str,cmd))}\n{p.stdout}")
 return p.stdout
def main():
 issues=[];passed=[]
 for lane,path in EXPECTED.items():check(phase_path(lane)==path,f'{lane} path mismatch',issues)
 passed.append('exact quick, standard, and full phase paths')
 expected_tracks={
 ('quick','IMPLEMENTATION_REVIEW'):['self_review','technical_review'],
 ('standard','IMPLEMENTATION_BLUEPRINT'):['strategy','execution_checklist'],('standard','BLUEPRINT_CRITIQUE'):['strategy_critique','execution_critique'],('standard','IMPLEMENTATION_REVIEW'):['self_review','technical_review','security_review','breaking_review'],
 ('full','IMPLEMENTATION_BLUEPRINT'):['strategy','execution_checklist'],('full','BLUEPRINT_CRITIQUE'):['strategy_critique','execution_critique'],('full','IMPLEMENTATION_REVIEW'):['self_review','technical_review','security_review','breaking_review']}
 for (lane,phase),ids in expected_tracks.items():
  got=[x['id'] for x in composite_tracks(phase,lane)];check(got==ids,f'{lane}/{phase} tracks {got}',issues)
 for lane in EXPECTED:
  for phase in EXPECTED[lane][:-1]:
   r=resolve_route(state(lane,phase));check(r['state']==phase and r['lane']==lane,f'route mismatch {lane}/{phase}',issues)
   if phase in ('IMPLEMENTATION_BLUEPRINT','BLUEPRINT_CRITIQUE','IMPLEMENTATION_REVIEW'):check(r['composite'] and r['agent']=='t-think',f'{phase} not root aggregate',issues)
 passed.append('composite track activation and route metadata')
 assessments=[
  classify_lane(work_id='A',requested_lane='auto',declared_signals=['local_reversible','existing_reproduction']),
  classify_lane(work_id='B',requested_lane='auto',declared_signals=['multiple_modules']),
  classify_lane(work_id='C',requested_lane='quick',declared_signals=['security_boundary'])]
 check(assessments[0]['selected_lane']=='quick','bounded reversible task not quick',issues)
 check(assessments[1]['selected_lane'] in ('standard','full'),'multi-module task classified quick',issues)
 check(assessments[2]['selected_lane']=='full' and assessments[2]['forced_promotion'],'hard trigger did not force full',issues)
 for a in assessments:check(not validate_schema(a,'lane-assessment.schema.json'),f'invalid assessment {a["work_id"]}',issues)
 for lane in EXPECTED:
  w=build_phase_waivers('W',lane);check(not validate_schema(w,'phase-waiver.schema.json'),f'{lane} waiver invalid',issues)
 passed.append('deterministic classification and explicit waivers')
 check(promotion_state('quick','standard','VERIFICATION')=='INVESTIGATION','late quick promotion must loop to investigation',issues)
 check(promotion_state('standard','full','VERIFICATION')=='SYSTEM_MODEL','late standard promotion must loop to system model',issues)
 passed.append('monotonic promotion loopback')
 with tempfile.TemporaryDirectory() as td:
  cwd=Path(td);ctl=str(ROOT/'bin/t-thinkctl.py')
  out=run([sys.executable,ctl,'init','W-CLI','--base','.t-think','--repository-root','.', '--lane','standard','--task','medium feature'],cwd).strip();sp=cwd/out
  d=yaml.safe_load(sp.read_text());check(d['schema_version']=='2.4.0','CLI did not initialize resumable schema',issues)
  d['current_state']='IMPLEMENTATION_REVIEW';d['active_skill']='t-implementation-review';d['active_agent']='t-think';d['human_gate_pending']=False;sp.write_text(yaml.safe_dump(d,sort_keys=False))
  route=json.loads(run([sys.executable,ctl,'route','--file',str(sp)],cwd));check([x['id'] for x in route['tracks']]==['self_review','technical_review','security_review','breaking_review'],'CLI route review tracks mismatch',issues)
  dg=run([sys.executable,ctl,'prepare-delegation','--file',str(sp),'--track','security_review','--objective','Perform dedicated security review of the actual diff','--criterion','Evaluate all security categories'],cwd).strip();packet=yaml.safe_load((cwd/dg).read_text())
  check(packet['identity']['target_agent']=='t-security-reviewer','security track target mismatch',issues)
  check(packet['permissions']['source_write']=='deny','security review can write source',issues)
  check(packet['lifecycle']['expected_next_state']=='IMPLEMENTATION_REVIEW','track incorrectly advances lifecycle',issues)
 passed.append('CLI composite delegation')
 report={'status':'FAIL' if issues else 'PASS','passed_contracts':passed,'issues':issues};(ROOT/'reports/lane-contract-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 1 if issues else 0
if __name__=='__main__':raise SystemExit(main())
