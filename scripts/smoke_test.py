#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys,tempfile
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
TOKEN='__T_THINK_PLATFORM_SKILL_ROOT__'
PLATFORM_ROOTS={
 'opencode':Path('.config/opencode/skills'),
 'codex':Path('.codex/t-think/skills'),
 'claude':Path('.claude/t-think/skills'),
 'cursor':Path('.cursor/t-think/skills'),
}
def run(cmd,cwd=None,expect=0):
 p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
 if p.returncode!=expect:raise RuntimeError(f'{" ".join(map(str,cmd))}\nexpected={expect} actual={p.returncode}\n{p.stdout}')
 return p.stdout
def seed_legacy(home:Path,skill_names:list[str]):
 for root in (home/'.agents/skills',home/'.claude/skills'):
  for name in skill_names:
   d=root/name;d.mkdir(parents=True,exist_ok=True);(d/'SKILL.md').write_text('legacy\n',encoding='utf-8')
  for name in ('t-reconciliation','t-builder','t-think'):
   b=root/f'{name}.bak-1784651500999690200';b.mkdir(parents=True,exist_ok=True);(b/'old.txt').write_text('legacy backup\n',encoding='utf-8')
  unrelated=root/'t-user-owned-skill';unrelated.mkdir(parents=True,exist_ok=True);(unrelated/'SKILL.md').write_text('keep\n',encoding='utf-8')
def assert_isolated_install(home:Path,skill_names:list[str],worker_count:int,agent_count:int):
 for platform,relative in PLATFORM_ROOTS.items():
  root=home/relative
  found=sorted(p.parent.name for p in root.glob('t-*/SKILL.md'))
  assert found==skill_names,(platform,len(found),found[:3])
 for root in (home/'.agents/skills',home/'.claude/skills'):
  for name in skill_names:
   assert not (root/name).exists(),root/name
  assert not list(root.glob('t-*.bak-*')),list(root.glob('t-*.bak-*'))
  assert (root/'t-user-owned-skill/SKILL.md').is_file()
 for d in [home/'.config/opencode/agents',home/'.claude/agents',home/'.cursor/agents']:
  assert len(list(d.glob('t-*.md')))==agent_count
 assert len(list((home/'.codex/agents').glob('t-*.toml')))==worker_count
 files=[home/'.codex/t-think.config.toml',*sorted((home/'.codex/agents').glob('t-*.toml')),*sorted((home/'.claude/agents').glob('t-*.md')),*sorted((home/'.cursor/agents').glob('t-*.md'))]
 expected={'codex':str(home/PLATFORM_ROOTS['codex']),'claude':str(home/PLATFORM_ROOTS['claude']),'cursor':str(home/PLATFORM_ROOTS['cursor'])}
 for path in files:
  text=path.read_text(encoding='utf-8')
  assert TOKEN not in text,path
  platform='codex' if '.codex' in path.parts else 'claude' if '.claude' in path.parts else 'cursor'
  assert expected[platform] in text,(path,expected[platform])

def main():
 print('[smoke] start',flush=True);results=[]
 skill_names=sorted(p.name for p in (ROOT/'skills').iterdir() if p.is_dir())
 skill_count=len(skill_names)
 worker_count=len(yaml.safe_load((ROOT/'orchestrator/agent-registry.yaml').read_text(encoding='utf-8'))['agents']);agent_count=worker_count+1
 with tempfile.TemporaryDirectory() as td:
  print('[smoke] copy install + legacy migration',flush=True)
  home=Path(td)/'User Name-Üser';home.mkdir();seed_legacy(home,skill_names)
  first=json.loads(run([sys.executable,str(ROOT/'bin/install.py'),'--target','all','--mode','copy','--home',str(home)]))
  assert first['schema_version']=='2.0.0';assert len(first['migrations'])>=skill_count*2
  assert not first['backups']
  assert_isolated_install(home,skill_names,worker_count,agent_count)
  run([sys.executable,str(ROOT/'bin/doctor.py'),'--target','all','--home',str(home)])
  second=json.loads(run([sys.executable,str(ROOT/'bin/install.py'),'--target','all','--mode','copy','--home',str(home)]))
  assert all(x['status']=='unchanged' for x in second['installed'])
  installed_ctl=home/'.local/share/t-think/runtime/bin/t-thinkctl.py'
  for platform,relative in PLATFORM_ROOTS.items():
   resolved=Path(run([sys.executable,str(installed_ctl),'paths','--home',str(home),'--platform',platform,'--skill','t-reconciliation','--resource','templates/output.template.yaml','--native-only']).strip())
   assert resolved==home/relative/'t-reconciliation/templates/output.template.yaml',(platform,resolved)
   assert resolved.is_file()
  # Force replacement remains atomic and never creates sibling backups.
  modified=home/PLATFORM_ROOTS['opencode']/'t-reconciliation/SKILL.md';modified.write_text('modified\n',encoding='utf-8')
  run([sys.executable,str(ROOT/'bin/install.py'),'--target','all','--mode','copy','--home',str(home),'--force'])
  assert 'modified' not in modified.read_text(encoding='utf-8')
  for root in [home/r for r in PLATFORM_ROOTS.values()]: assert not list(root.glob('t-*.bak-*'))
  assert not list((home/'.local/share/t-think').glob('.transactions/*'))
  run([sys.executable,str(ROOT/'bin/doctor.py'),'--target','all','--home',str(home)])
  run([sys.executable,str(ROOT/'bin/uninstall.py'),'--home',str(home)])
  for relative in PLATFORM_ROOTS.values():
   assert not list((home/relative).glob('t-*/SKILL.md'))
  assert (home/'.agents/skills/t-user-owned-skill/SKILL.md').is_file()
  assert (home/'.claude/skills/t-user-owned-skill/SKILL.md').is_file()
  results.append(f'platform-isolated copy install, exact legacy migration, private path resolution, atomic force upgrade, doctor, and uninstall with {worker_count} terminal workers and {skill_count} skills')
 if sys.platform!='win32':
  with tempfile.TemporaryDirectory() as td:
   print('[smoke] symlink install',flush=True)
   home=Path(td)/'home';home.mkdir();run([sys.executable,str(ROOT/'bin/install.py'),'--target','all','--mode','symlink','--home',str(home)]);assert_isolated_install_without_legacy(home,skill_names,worker_count,agent_count);run([sys.executable,str(ROOT/'bin/doctor.py'),'--target','all','--home',str(home)]);run([sys.executable,str(ROOT/'bin/uninstall.py'),'--home',str(home)]);results.append('platform-isolated symlink install/doctor/uninstall')
 results.append('runtime lifecycle behavior is covered by intake_workspace_contract_test.py')
 report={'status':'PASS','smoke_tests':results,'scope':'isolated temporary HOME; exact legacy t-think paths only; unrelated user skills preserved'};(ROOT/'reports/installation-smoke-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2));return 0

def assert_isolated_install_without_legacy(home:Path,skill_names:list[str],worker_count:int,agent_count:int):
 for relative in PLATFORM_ROOTS.values():
  assert sorted(p.parent.name for p in (home/relative).glob('t-*/SKILL.md'))==skill_names
 assert not (home/'.agents/skills').exists()
 assert not (home/'.claude/skills').exists()
 for d in [home/'.config/opencode/agents',home/'.claude/agents',home/'.cursor/agents']: assert len(list(d.glob('t-*.md')))==agent_count
 assert len(list((home/'.codex/agents').glob('t-*.toml')))==worker_count

if __name__=='__main__':raise SystemExit(main())
