#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys,tempfile
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
def run(cmd,cwd=None):
 p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if p.returncode:raise RuntimeError(f'{" ".join(map(str,cmd))}\n{p.stdout}')
 return p.stdout
def main():
 results=[];skill_count=len([p for p in (ROOT/'skills').iterdir() if p.is_dir()]);worker_count=len(yaml.safe_load((ROOT/'orchestrator/agent-registry.yaml').read_text())['agents']);agent_count=worker_count+1
 with tempfile.TemporaryDirectory() as td:
  home=Path(td)/'User Name-Üser';home.mkdir();run([sys.executable,str(ROOT/'bin/install.py'),'--target','all','--mode','copy','--home',str(home)]);run([sys.executable,str(ROOT/'bin/doctor.py'),'--target','all','--home',str(home)])
  second=json.loads(run([sys.executable,str(ROOT/'bin/install.py'),'--target','all','--mode','copy','--home',str(home)]));assert all(x['status']=='unchanged' for x in second['installed']);assert len(list((home/'.agents/skills').glob('t-*/SKILL.md')))==skill_count
  installed_ctl=home/'.local/share/t-think/runtime/bin/t-thinkctl.py'
  resolved=Path(run([sys.executable,str(installed_ctl),'paths','--home',str(home),'--skill','t-reconciliation','--resource','templates/output.template.yaml','--native-only']).strip())
  assert resolved==home/'.agents/skills/t-reconciliation/templates/output.template.yaml'
  assert resolved.is_file()
  for d in [home/'.config/opencode/agents',home/'.claude/agents',home/'.cursor/agents']:assert len(list(d.glob('t-*.md')))==agent_count
  assert len(list((home/'.codex/agents').glob('t-*.toml')))==worker_count;run([sys.executable,str(ROOT/'bin/uninstall.py'),'--home',str(home)]);results.append(f'idempotent copy install/doctor/path-resolution/uninstall with {worker_count} terminal workers and {skill_count} skills in a home path containing spaces and Unicode')
 if sys.platform!='win32':
  with tempfile.TemporaryDirectory() as td:
   home=Path(td)/'home';home.mkdir();run([sys.executable,str(ROOT/'bin/install.py'),'--target','all','--mode','symlink','--home',str(home)]);run([sys.executable,str(ROOT/'bin/doctor.py'),'--target','all','--home',str(home)]);run([sys.executable,str(ROOT/'bin/uninstall.py'),'--home',str(home)]);results.append('symlink install/doctor/uninstall')
 with tempfile.TemporaryDirectory() as td:
  cwd=Path(td);ctl=str(ROOT/'bin/t-thinkctl.py');state=cwd/run([sys.executable,ctl,'init','DEMO-1','--repository-root',str(cwd),'--lane','standard'],cwd).strip();d=yaml.safe_load(state.read_text());d['current_state']='IMPLEMENTATION_REVIEW';d['active_skill']='t-implementation-review';d['active_agent']='t-think';d['human_gate_pending']=False;state.write_text(yaml.safe_dump(d,sort_keys=False));route=json.loads(run([sys.executable,ctl,'route','--file',str(state)],cwd));assert [x['id'] for x in route['tracks']]==['self_review','technical_review','security_review','breaking_review']
  dg=cwd/run([sys.executable,ctl,'prepare-delegation','--file',str(state),'--track','breaking_review','--objective','Detect breaking behavior in flow rules validation structures and mappings','--criterion','Evaluate every breaking category'],cwd).strip();run([sys.executable,str(ROOT/'bin/validate_delegation.py'),'--file',str(dg)],cwd);results.append('composite route and breaking-review delegation')
 report={'status':'PASS','smoke_tests':results,'scope':'isolated temporary HOME; no real user configuration modified'};(ROOT/'reports/installation-smoke-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
