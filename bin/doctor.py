#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,tomllib
from pathlib import Path
import yaml
PLATFORMS=('opencode','codex','claude','cursor')
TRUSTED_EXTERNAL=('~/.agents/skills/t-*/**','~/.claude/skills/t-*/**','~/.config/opencode/skills/t-*/**','~/.local/share/t-think/runtime/**')
def frontmatter(path):
 m=re.match(r'---\n(.*?)\n---\n',path.read_text(),re.S)
 if not m:raise ValueError('missing YAML frontmatter')
 return yaml.safe_load(m.group(1))
def _walk_permission_values(value):
 if isinstance(value,dict):
  for item in value.values():yield from _walk_permission_values(item)
 elif isinstance(value,list):
  for item in value:yield from _walk_permission_values(item)
 else:yield value
def main():
 p=argparse.ArgumentParser();p.add_argument('--home',type=Path,default=Path.home());p.add_argument('--target',choices=['all',*PLATFORMS],default='all');a=p.parse_args();h=a.home.expanduser().resolve();errors=[]
 manifest=h/'.local/share/t-think/installation-manifest.json';runtime=h/'.local/share/t-think/runtime'
 if not manifest.exists():errors.append('missing installation manifest')
 for req in ['VERSION','bin/t-thinkctl.py','bin/tthink_paths.py','bin/validate_delegation.py','bin/audit_boundaries.py','bin/validate_result.py','orchestrator/agent-registry.yaml','orchestrator/phase-registry.yaml','orchestrator/composite-phase-policy.yaml','orchestrator/intake-policy.yaml','orchestrator/workspace-hygiene-policy.yaml','orchestrator/tool-permission-policy.yaml','schemas/delegation-packet.schema.json','schemas/workspace-hygiene-report.schema.json']:
  if not (runtime/req).exists():errors.append(f'missing runtime component: {req}')
 worker_names=[]
 if (runtime/'orchestrator/agent-registry.yaml').exists():worker_names=[x['name'] for x in yaml.safe_load((runtime/'orchestrator/agent-registry.yaml').read_text())['agents']]
 names=['t-think',*worker_names];expected_agents=len(names);expected_skills=len([x for x in (runtime/'skills').iterdir() if x.is_dir()]) if (runtime/'skills').exists() else None
 # skills are installed from source but runtime intentionally excludes skills; derive from manifest when needed.
 installed_manifest=json.loads(manifest.read_text()) if manifest.exists() else {'installed':[]}
 skill_names=sorted({x.get('name') for x in installed_manifest.get('installed',[]) if x.get('kind')=='skill'})
 expected_skills=len(skill_names)
 skills=sorted((h/'.agents/skills').glob('t-*/SKILL.md'))
 if len(skills)!=expected_skills:errors.append(f'expected {expected_skills} shared skills, found {len(skills)}')
 for f in skills:
  try:
   d=frontmatter(f)
   if d.get('name')!=f.parent.name:errors.append(f'name/folder mismatch: {f}')
   if not (f.parent/'RESOURCE_INDEX.md').is_file():errors.append(f'missing resource index: {f.parent}')
   skill_text=f.read_text()
   if 'BEGIN T-THINK PORTABLE RESOURCE CONTRACT' not in skill_text:errors.append(f'missing portable resource contract: {f}')
  except Exception as e:errors.append(f'invalid skill {f}: {e}')
 targets=list(PLATFORMS) if a.target=='all' else [a.target];dirs={'opencode':h/'.config/opencode/agents','claude':h/'.claude/agents','cursor':h/'.cursor/agents'}
 for platform in targets:
  if platform=='codex':
   profile=h/'.codex/t-think.config.toml';workers=h/'.codex/agents';found=list(workers.glob('t-*.toml'))
   if not profile.exists():errors.append('missing Codex root profile')
   if len(found)!=len(worker_names):errors.append(f'expected {len(worker_names)} Codex workers, found {len(found)}')
   if profile.exists():
    try:
     d=tomllib.loads(profile.read_text());
     if d.get('agents',{}).get('max_depth')!=1:errors.append('Codex max_depth must be 1')
     if d.get('approval_policy')!='never' or d.get('sandbox_mode')!='workspace-write':errors.append('Codex prompt-free workspace profile invalid')
     if 'model' in d or 'model_reasoning_effort' in d:errors.append('Codex root pins model')
    except Exception as e:errors.append(f'invalid Codex profile: {e}')
   for name in worker_names:
    f=workers/f'{name}.toml'
    if not f.exists():errors.append(f'missing codex worker: {name}')
    else:
     try:
      if tomllib.loads(f.read_text()).get('sandbox_mode')!='workspace-write':errors.append(f'codex/{name} worker is not workspace-write')
     except Exception as e:errors.append(f'invalid codex/{name}: {e}')
   continue
  found=list(dirs[platform].glob('t-*.md'))
  if len(found)!=expected_agents:errors.append(f'expected {expected_agents} {platform} agents, found {len(found)}')
  for name in names:
   f=dirs[platform]/f'{name}.md'
   if not f.exists():errors.append(f'missing {platform} agent: {name}');continue
   try:
    d=frontmatter(f)
    if platform in ('claude','cursor') and d.get('name')!=name:errors.append(f'{platform}/{name} name mismatch')
    if platform=='opencode':
     if d.get('mode')!=('primary' if name=='t-think' else 'subagent'):errors.append(f'opencode/{name} mode mismatch')
     perm=d.get('permission',{})
     ext=perm.get('external_directory')
     if not isinstance(ext,dict) or ext.get('*')!='deny':errors.append(f'opencode/{name} external_directory must deny by default')
     else:
      for pattern in TRUSTED_EXTERNAL:
       if ext.get(pattern)!='allow':errors.append(f'opencode/{name} missing recursive external allow: {pattern}')
     if perm.get('*')!='allow':errors.append(f'opencode/{name} global tool default must allow')
     if any(v=='ask' for v in _walk_permission_values(perm)):errors.append(f'opencode/{name} contains ask permission')
     bash=perm.get('bash',{})
     if not isinstance(bash,dict) or bash.get('*')!='allow':errors.append(f'opencode/{name} bash must allow normal worktree commands')
     elif bash.get('git')!='deny' or bash.get('git *')!='deny' or bash.get('gh')!='deny' or bash.get('gh *')!='deny':errors.append(f'opencode/{name} Git/GH boundary invalid')
     edit=perm.get('edit',{})
     if not isinstance(edit,dict) or edit.get('*')!='allow' or edit.get('.git/**')!='deny':errors.append(f'opencode/{name} edit profile invalid')
    if platform=='claude' and d.get('permissionMode')!='bypassPermissions':errors.append(f'claude/{name} permission mode is not bypassPermissions')
    if platform=='claude' and name!='t-think' and 'Agent' in str(d.get('tools','')):errors.append(f'claude/{name} can nest')
    if platform=='cursor' and d.get('readonly') is not False:errors.append(f'cursor/{name} remains readonly')
   except Exception as e:errors.append(f'invalid {platform}/{name}: {e}')
 if 'claude' in targets:
  linked=list((h/'.claude/skills').glob('t-*/SKILL.md'))
  if len(linked)!=expected_skills:errors.append(f'expected {expected_skills} Claude skills, found {len(linked)}')
 print(json.dumps({'status':'FAIL' if errors else 'PASS','skills':len(skills),'role_workers':len(worker_names),'targets':targets,'errors':errors},indent=2));return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
