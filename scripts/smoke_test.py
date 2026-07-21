#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(cmd,cwd=None):
    p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if p.returncode: raise RuntimeError(f"{' '.join(map(str,cmd))}\n{p.stdout}")
    return p.stdout

def main():
    results=[]
    with tempfile.TemporaryDirectory() as td:
        home=Path(td)/'home'; home.mkdir()
        run([sys.executable,str(ROOT/'bin/install.py'),'--target','all','--mode','copy','--home',str(home)])
        run([sys.executable,str(ROOT/'bin/doctor.py'),'--target','all','--home',str(home)])
        second=json.loads(run([sys.executable,str(ROOT/'bin/install.py'),'--target','all','--mode','copy','--home',str(home)]))
        assert second['installed'] and all(x['status']=='unchanged' for x in second['installed'])
        assert len(list((home/'.agents/skills').glob('t-*/SKILL.md')))==15
        for d in [home/'.config/opencode/agents',home/'.claude/agents',home/'.cursor/agents']: assert len(list(d.glob('t-*.md')))==9
        assert (home/'.codex/t-think.config.toml').exists()
        assert len(list((home/'.codex/agents').glob('t-*.toml')))==8
        assert (home/'.local/share/t-think/runtime/bin/t-thinkctl.py').exists()
        run([sys.executable,str(ROOT/'bin/uninstall.py'),'--home',str(home)])
        assert not list((home/'.agents/skills').glob('t-*/SKILL.md'))
        results.append('idempotent copy install/doctor/uninstall with root orchestrators and 8 role workers')
    if sys.platform!='win32':
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)/'home'; home.mkdir()
            run([sys.executable,str(ROOT/'bin/install.py'),'--target','all','--mode','symlink','--home',str(home)])
            run([sys.executable,str(ROOT/'bin/doctor.py'),'--target','all','--home',str(home)])
            assert all(p.is_symlink() for p in (home/'.agents/skills').glob('t-*'))
            run([sys.executable,str(ROOT/'bin/uninstall.py'),'--home',str(home)])
            results.append('symlink install/doctor/uninstall with runtime')
    with tempfile.TemporaryDirectory() as td:
        cwd=Path(td); out=run([sys.executable,str(ROOT/'bin/t-thinkctl.py'),'init','DEMO-1','--repository-root',str(cwd)],cwd=cwd)
        state=cwd/out.strip(); route=json.loads(run([sys.executable,str(ROOT/'bin/t-thinkctl.py'),'route','--file',str(state)],cwd=cwd))
        assert route['skill']=='t-problem-alignment' and route['agent']=='t-think'
        data=__import__('yaml').safe_load(state.read_text()); data['current_state']='INVESTIGATION'; data['active_skill']='t-investigation'; data['active_agent']='t-investigator'; state.write_text(__import__('yaml').safe_dump(data,sort_keys=False))
        delegation_out=run([sys.executable,str(ROOT/'bin/t-thinkctl.py'),'prepare-delegation','--file',str(state),'--objective','Trace the actual execution path','--criterion','Identify entry points','--criterion','Identify transaction boundaries'],cwd=cwd)
        delegation=cwd/delegation_out.strip(); run([sys.executable,str(ROOT/'bin/validate_delegation.py'),'--file',str(delegation)],cwd=cwd)
        results.append('state routing and delegation generation')
    report={'status':'PASS','smoke_tests':results,'scope':'isolated temporary HOME; no real user configuration modified'}
    (ROOT/'reports').mkdir(exist_ok=True); (ROOT/'reports/installation-smoke-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
