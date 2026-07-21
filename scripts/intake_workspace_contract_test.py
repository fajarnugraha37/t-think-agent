#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bin'))
from tthink_runtime import audit_work_directory,intake_questions,suggest_work_id,validate_schema

def run(cmd,cwd,expect=0):
    p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if p.returncode!=expect:
        raise RuntimeError(f"exit {p.returncode}, expected {expect}: {' '.join(map(str,cmd))}\n{p.stdout}")
    return p.stdout

def check(ok,msg,issues):
    if not ok: issues.append(msg)

def main():
    issues=[]; passed=[]; ctl=str(ROOT/'bin/t-thinkctl.py')
    payload=intake_questions('Fix raw capture mapping bug')
    check(payload['filesystem_actions_allowed'] is False,'intake permits filesystem action',issues)
    check([q['id'] for q in payload['questions']]==['work_id','lane'],'bootstrap question order mismatch',issues)
    check(payload['questions'][1]['options']==['quick','standard','full'],'lane choices mismatch',issues)
    check(suggest_work_id('Please fix ABC-123 mapping')=='ABC-123','explicit ticket suggestion not preserved',issues)
    passed.append('mandatory two-question intake and deterministic suggestion')
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td)
        text=run([sys.executable,ctl,'intake','--task','Fix raw capture mapping bug','--format','json'],repo)
        check(not (repo/'.t-think').exists(),'intake created .t-think before answers',issues)
        check(json.loads(text)['questions'][0]['suggestion'].startswith('WORK-'),'CLI intake missing suggestion',issues)
        state_rel=run([sys.executable,ctl,'init','REQ-001','--repository-root',str(repo),'--lane','standard','--task','Fix raw capture mapping bug'],repo).strip()
        state_path=repo/state_rel; state=yaml.safe_load(state_path.read_text())
        work=repo/'.t-think/REQ-001'
        check(state['work_directory']=='.t-think/REQ-001','state work directory not canonical',issues)
        check((work/'scratch').is_dir(),'scratch directory missing',issues)
        check((work/'session/resume.yaml').is_file(),'resume checkpoint missing',issues)
        check((work/'session/activity.jsonl').is_file(),'activity journal missing',issues)
        check(not [p for p in (repo/'.t-think').iterdir() if p.is_file() and p.name!='.gitignore'],'root file created by init',issues)
        # Generate a delegation and verify exact write scope.
        state['current_state']='IMPLEMENTATION_REVIEW';state['active_skill']='t-implementation-review';state['active_agent']='t-think';state['human_gate_pending']=False
        state_path.write_text(yaml.safe_dump(state,sort_keys=False))
        dg_rel=run([sys.executable,ctl,'prepare-delegation','--file',str(state_path),'--track','technical_review','--objective','Review the actual implementation independently','--criterion','Find correctness regressions'],repo).strip()
        packet=yaml.safe_load((repo/dg_rel).read_text())
        check(packet['workspace']['active_work_directory']=='.t-think/REQ-001','packet active work directory mismatch',issues)
        check(packet['permissions']['governance_artifact_write']=='.t-think/REQ-001/**','packet has broad governance scope',issues)
        passed.append('canonical work-directory initialization and packet scope')
        # Reproduce observed pollution.
        (repo/'.t-think/blueprint-strategy-req-001.yaml').write_text('bad: root\n')
        (repo/'.t-think/verify-raw-consistency.ts').write_text('console.log("tmp")\n')
        (work/'scratch/check-runtime.ts').write_text('console.log("tmp")\n')
        report=audit_work_directory(state,require_clean=True)
        check(report['status']=='FAIL','polluted workspace passed audit',issues)
        check('.t-think/verify-raw-consistency.ts' in report['root_stray_files'],'root temporary script not detected',issues)
        check('.t-think/blueprint-strategy-req-001.yaml' in report['root_stray_files'],'root artifact not detected',issues)
        # Cleanup removes scratch and forbidden temporary scripts, but preserves misplaced YAML for explicit repair.
        run([sys.executable,ctl,'cleanup-workdir','--file',str(state_path),'--prune-forbidden-temporary'],repo,expect=1)
        check(not (repo/'.t-think/verify-raw-consistency.ts').exists(),'root temporary script not pruned',issues)
        check(not (work/'scratch/check-runtime.ts').exists(),'scratch temporary script not removed',issues)
        check((repo/'.t-think/blueprint-strategy-req-001.yaml').exists(),'cleanup silently deleted misplaced governance artifact',issues)
        (repo/'.t-think/blueprint-strategy-req-001.yaml').unlink()
        out=run([sys.executable,ctl,'audit-workdir','--file',str(state_path),'--require-clean'],repo)
        clean=json.loads(out); check(clean['status']=='PASS','clean workspace did not pass audit',issues)
        check(not validate_schema(clean,'workspace-hygiene-report.schema.json'),'hygiene report schema invalid',issues)
        passed.append('pollution detection, safe cleanup, and clean audit')
        # Reconciliation packet must be blocked while scratch is non-empty.
        state['current_state']='RECONCILIATION';state['active_skill']='t-reconciliation';state['active_agent']='t-reconciler';state_path.write_text(yaml.safe_dump(state,sort_keys=False))
        (work/'scratch/leftover.py').write_text('print(1)\n')
        blocked=run([sys.executable,ctl,'prepare-delegation','--file',str(state_path),'--objective','Reconcile closure evidence','--criterion','All evidence is traceable'],repo,expect=1)
        check('workspace hygiene blocks reconciliation' in blocked,'reconciliation not blocked by leftover scratch',issues)
        passed.append('reconciliation hygiene gate')
    report={'status':'FAIL' if issues else 'PASS','passed_contracts':passed,'issues':issues}
    (ROOT/'reports/intake-workspace-contract-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));return 1 if issues else 0
if __name__=='__main__':raise SystemExit(main())
