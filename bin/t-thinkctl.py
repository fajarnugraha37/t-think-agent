#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys,uuid
from datetime import datetime,timezone
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
from tthink_runtime import ROOT,load_data,dump_data,validate_delegation

REG=yaml.safe_load((ROOT/'orchestrator/phase-registry.yaml').read_text())
MAP={p['state']:p for p in REG['phases']}
SCHEMA=json.loads((ROOT/'schemas/work-state.schema.json').read_text())
WORKSPACE_POLICY=yaml.safe_load((ROOT/'orchestrator/workspace-policy.yaml').read_text())

def validate(data):
    errs=sorted(Draft202012Validator(SCHEMA).iter_errors(data),key=lambda e:list(e.path))
    if errs: raise ValueError('; '.join(f"{'.'.join(map(str,e.path)) or '$'}: {e.message}" for e in errs))

def route(data):
    state=data['current_state']
    if state=='COMPLETED': return {'state':state,'skill':None,'agent':None,'status':'terminal','model_profile':data['model_profile']}
    phase=MAP[state]
    return {'state':state,'skill':phase['skill'],'skill_path':str(ROOT/phase['path']),'agent':phase['agent'],'agent_manifest':None if phase['agent']=='t-think' else str(ROOT/'agents'/phase['agent']/'agent.yaml'),'success_state':phase['success_state'],'repository_mutation':phase['repository_mutation'],'source_write_mode':phase['source_write_mode'],'context':phase['context'],'model_profile':data['model_profile']}

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('init'); q.add_argument('work_id'); q.add_argument('--base',type=Path,default=Path('.t-think')); q.add_argument('--repository-root',type=Path,default=Path('.')); q.add_argument('--profile',choices=['economy','balanced','high-assurance'],default='economy')
    q=sub.add_parser('route'); q.add_argument('--file',type=Path,required=True)
    q=sub.add_parser('validate-state'); q.add_argument('--file',type=Path,required=True)
    q=sub.add_parser('prepare-delegation'); q.add_argument('--file',type=Path,required=True); q.add_argument('--objective',required=True); q.add_argument('--criterion',action='append',required=True); q.add_argument('--attempt',type=int,default=1); q.add_argument('--artifact-input',action='append',default=[],help='PATH=SHA256'); q.add_argument('--approved-write-target',action='append',default=[]); q.add_argument('--generated-output',action='append',default=[]); q.add_argument('--ignored-file-approval-ref'); q.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.cmd=='init':
        wd=a.base/a.work_id; wd.mkdir(parents=True,exist_ok=False)
        for d in ('artifacts','delegations','results','boundary-reports','evidence'): (wd/d).mkdir()
        data={'schema_version':'2.1.0','work_id':a.work_id,'current_state':'PROBLEM_ALIGNMENT','current_run_id':'RUN-'+uuid.uuid4().hex[:12].upper(),'model_profile':a.profile,'repository_root':str(a.repository_root.resolve()),'work_directory':str(wd),'active_skill':'t-problem-alignment','active_agent':'t-think','last_gate':None,'last_validator':None,'human_gate_pending':True,'history':[{'at':datetime.now(timezone.utc).isoformat(),'event':'INITIALIZED'}]}
        path=wd/'state.yaml'; dump_data(path,data); print(path); return 0
    data=load_data(a.file); validate(data)
    if a.cmd=='validate-state': print('STATE VALID'); return 0
    if a.cmd=='route': print(json.dumps(route(data),indent=2)); return 0
    r=route(data)
    if r['agent'] in (None,'t-think'): raise ValueError('Current phase is handled directly by t-think and cannot be delegated')
    invocation='INV-'+uuid.uuid4().hex[:12].upper()
    artifact_inputs=[]
    for item in a.artifact_input:
        if '=' not in item: raise ValueError('--artifact-input must be PATH=SHA256')
        ref,digest=item.rsplit('=',1); artifact_inputs.append({'ref':ref,'sha256':digest})
    ignored={'mode':'human_approved' if a.ignored_file_approval_ref else 'deny','human_approval_ref':a.ignored_file_approval_ref}
    phase_slug=data['current_state'].lower().replace('_','-')
    work_prefix=Path(data['work_directory']).as_posix()
    packet={'schema_version':'1.0.0','identity':{'work_id':data['work_id'],'run_id':data['current_run_id'],'invocation_id':invocation,'parent_agent':'t-think','target_agent':r['agent']},'lifecycle':{'current_phase':data['current_state'],'skill':r['skill'],'attempt':a.attempt},'objective':{'statement':a.objective,'completion_criteria':a.criterion},'workspace':{'root':data['repository_root'],'discovery':WORKSPACE_POLICY['discovery_defaults']},'permissions':{'workspace_read':'allow','outside_workspace':'deny','source_write':r['source_write_mode'],'governance_artifact_write':'.t-think/**','approved_write_targets':a.approved_write_target,'generated_output_paths':a.generated_output,'protected_paths':WORKSPACE_POLICY['protected_paths'],'ignored_file_access':ignored,'spawn_subagent':'deny'},'artifact_inputs':artifact_inputs,'output_contract':{'schema':f'skills/{r["skill"]}/schemas/output.schema.json','artifact_path':f'{work_prefix}/artifacts/{phase_slug}.yaml','result_path':f'{work_prefix}/results/{invocation}.yaml','boundary_report_path':f'{work_prefix}/boundary-reports/{invocation}.yaml'},'stop_conditions':['required evidence is unavailable','scope or permission conflict','artifact digest mismatch','a new semantic decision is required','phase completion criteria cannot be satisfied without guessing']}
    errors=validate_delegation(packet)
    if errors: raise ValueError('Delegation invalid: '+'; '.join(errors))
    out=a.out or Path(data['work_directory'])/'delegations'/f'{invocation}.yaml'; out.parent.mkdir(parents=True,exist_ok=True); dump_data(out,packet); print(out); return 0
if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as e: print(f'ERROR: {e}',file=sys.stderr); raise SystemExit(1)
