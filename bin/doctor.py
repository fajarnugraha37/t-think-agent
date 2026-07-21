#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,sys,tomllib
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator

PLATFORMS=('opencode','codex','claude','cursor')
AGENTS=('t-think','t-investigator','t-modeler','t-planner','t-critic','t-builder','t-reviewer','t-verifier','t-reconciler')

def frontmatter(path:Path):
    m=re.match(r'---\n(.*?)\n---\n',path.read_text(),re.S)
    if not m: raise ValueError('missing YAML frontmatter')
    return yaml.safe_load(m.group(1))

def main():
    p=argparse.ArgumentParser(); p.add_argument('--home',type=Path,default=Path.home()); p.add_argument('--target',choices=['all',*PLATFORMS],default='all')
    a=p.parse_args(); h=a.home.expanduser().resolve(); errors=[]
    manifest_path=h/'.local/share/t-think/installation-manifest.json'
    if not manifest_path.exists(): errors.append('missing installation manifest')
    runtime=h/'.local/share/t-think/runtime'
    for req in ['VERSION','bin/t-thinkctl.py','bin/validate_delegation.py','bin/audit_boundaries.py','bin/validate_result.py','orchestrator/agent-registry.yaml','orchestrator/phase-registry.yaml','schemas/delegation-packet.schema.json']:
        if not (runtime/req).exists(): errors.append(f'missing runtime component: {req}')
    skills=sorted((h/'.agents/skills').glob('t-*/SKILL.md'))
    if len(skills)!=15: errors.append(f'expected 15 shared skills, found {len(skills)}')
    for f in skills:
        try:
            data=frontmatter(f)
            if data.get('name')!=f.parent.name: errors.append(f'name/folder mismatch: {f}')
            if not data.get('description'): errors.append(f'missing description: {f}')
        except Exception as e: errors.append(f'invalid skill {f}: {e}')
    targets=list(PLATFORMS) if a.target=='all' else [a.target]
    dirs={'opencode':h/'.config/opencode/agents','claude':h/'.claude/agents','cursor':h/'.cursor/agents'}
    for platform in targets:
        if platform=='codex':
            profile=h/'.codex/t-think.config.toml'; workers=h/'.codex/agents'
            found=sorted(workers.glob('t-*.toml'))
            if not profile.exists(): errors.append('missing Codex t-think root profile')
            if len(found)!=8: errors.append(f'expected 8 Codex worker agents, found {len(found)}')
            if profile.exists():
                try:
                    d=tomllib.loads(profile.read_text())
                    if not d.get('developer_instructions'): errors.append('Codex t-think profile missing developer_instructions')
                    if 'model' in d or 'model_reasoning_effort' in d: errors.append('Codex t-think profile pins model or reasoning')
                    agents=d.get('agents',{})
                    if agents.get('max_depth')!=1: errors.append('Codex profile max_depth must be 1')
                    if not isinstance(agents.get('max_threads'),int) or agents.get('max_threads')<1: errors.append('Codex profile max_threads invalid')
                except Exception as e: errors.append(f'invalid Codex t-think profile: {e}')
            for name in AGENTS[1:]:
                f=workers/f'{name}.toml'
                if not f.exists(): errors.append(f'missing codex agent: {name}'); continue
                try:
                    d=tomllib.loads(f.read_text())
                    for k in ('name','description','developer_instructions'):
                        if not d.get(k): errors.append(f'codex/{name} missing {k}')
                    if d.get('name')!=name: errors.append(f'codex/{name} name mismatch')
                    if 'model' in d or 'model_reasoning_effort' in d: errors.append(f'codex/{name} pins model or reasoning')
                    expected='workspace-write' if name in ('t-builder','t-verifier') else 'read-only'
                    if d.get('sandbox_mode')!=expected: errors.append(f'codex/{name} sandbox_mode should be {expected}')
                except Exception as e: errors.append(f'invalid codex/{name}: {e}')
            continue
        found=sorted(dirs[platform].glob('t-*.md'))
        if len(found)!=9: errors.append(f'expected 9 {platform} agents, found {len(found)}')
        for name in AGENTS:
            f=dirs[platform]/f'{name}.md'
            if not f.exists(): errors.append(f'missing {platform} agent: {name}'); continue
            try:
                d=frontmatter(f)
                if platform in ('claude','cursor') and d.get('name')!=name: errors.append(f'{platform}/{name} name mismatch')
                if platform=='opencode':
                    expected='primary' if name=='t-think' else 'subagent'
                    if d.get('mode')!=expected: errors.append(f'opencode/{name} mode should be {expected}')
                    if 'model' in d: errors.append(f'opencode/{name} pins model')
                if platform=='claude':
                    if d.get('model')!='inherit': errors.append(f'claude/{name} must inherit model')
                    tools=str(d.get('tools',''))
                    if name=='t-think' and 'Agent(' not in tools: errors.append('claude/t-think missing agent allowlist')
                    if name!='t-think' and 'Agent' in tools: errors.append(f'claude/{name} may spawn nested agents')
                if platform=='cursor':
                    if d.get('model')!='inherit': errors.append(f'cursor/{name} must inherit model')
                    expected=name not in ('t-think','t-builder','t-verifier')
                    if d.get('readonly') is not expected: errors.append(f'cursor/{name} readonly mismatch')
            except Exception as e: errors.append(f'invalid {platform}/{name}: {e}')
    if 'claude' in targets:
        linked=list((h/'.claude/skills').glob('t-*/SKILL.md'))
        if len(linked)!=15: errors.append(f'expected 15 Claude skills, found {len(linked)}')
    print(json.dumps({'status':'FAIL' if errors else 'PASS','skills':len(skills),'adapter_artifacts_per_target':9,'targets':targets,'errors':errors},indent=2))
    return 1 if errors else 0
if __name__=='__main__': raise SystemExit(main())
