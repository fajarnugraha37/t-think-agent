#!/usr/bin/env python3
from __future__ import annotations
import json,re,tomllib
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
issues=[]
profiles=yaml.safe_load((ROOT/'orchestrator/model-profiles.yaml').read_text()); econ=profiles['profiles']['economy']
if profiles.get('default')!='economy': issues.append('economy is not default')
if econ.get('subagents_enabled') is not True: issues.append('economy must use role subagents')
if econ.get('max_active_skills')!=1: issues.append('economy max_active_skills must be 1')
if econ.get('max_concurrent_subagents')!=1: issues.append('economy must be sequential with one active subagent')
if econ.get('parallel_subagents') is not False: issues.append('economy parallel_subagents must be false')
if econ.get('max_delegation_depth')!=1: issues.append('economy delegation depth must be 1')
if econ.get('model')!='inherit': issues.append('economy model must inherit')
core=(ROOT/'orchestrator/t-think-core.md').read_text()
if len(core)>18000: issues.append(f'core too large: {len(core)}')
for f in sorted((ROOT/'skills').glob('t-*/SKILL.md')):
    n=len(f.read_text())
    if n>20000: issues.append(f'skill too large for economy profile: {f.parent.name}={n}')
for f in sorted((ROOT/'agents').glob('t-*/AGENT.md')):
    n=len(f.read_text())
    if n>8000: issues.append(f'role agent too large for economy profile: {f.parent.name}={n}')
for f in sorted((ROOT/'adapters/opencode').glob('t-*.md')):
    front=yaml.safe_load(re.match(r'---\n(.*?)\n---\n',f.read_text(),re.S).group(1))
    if 'model' in front: issues.append(f'OpenCode adapter pins a model: {f.name}')
codex_profile=ROOT/'adapters/codex/t-think.config.toml'
if not codex_profile.exists():
    issues.append('Codex root profile missing')
else:
    d=tomllib.loads(codex_profile.read_text())
    if 'model' in d or 'model_reasoning_effort' in d: issues.append('Codex root profile pins model/reasoning')
    if d.get('agents',{}).get('max_depth')!=1: issues.append('Codex root profile must keep max_depth=1')
for f in sorted((ROOT/'adapters/codex/agents').glob('t-*.toml')):
    d=tomllib.loads(f.read_text())
    if 'model' in d or 'model_reasoning_effort' in d: issues.append(f'Codex worker pins model/reasoning: {f.name}')
for f in sorted((ROOT/'adapters/claude-code').glob('t-*.md')):
    d=yaml.safe_load(re.match(r'---\n(.*?)\n---\n',f.read_text(),re.S).group(1))
    if d.get('model')!='inherit': issues.append(f'Claude adapter must inherit: {f.name}')
    if 'skills' in d: issues.append(f'Claude adapter preloads skills: {f.name}')
    if f.stem!='t-think' and 'Agent' in str(d.get('tools','')): issues.append(f'Claude worker can recursively delegate: {f.name}')
for f in sorted((ROOT/'adapters/cursor').glob('t-*.md')):
    d=yaml.safe_load(re.match(r'---\n(.*?)\n---\n',f.read_text(),re.S).group(1))
    if d.get('model')!='inherit': issues.append(f'Cursor adapter must inherit: {f.name}')
report={'status':'FAIL' if issues else 'PASS','issues':issues,'core_characters':len(core),'role_agent_character_sizes':{f.parent.name:len(f.read_text()) for f in sorted((ROOT/'agents').glob('t-*/AGENT.md'))},'skill_character_sizes':{f.parent.name:len(f.read_text()) for f in sorted((ROOT/'skills').glob('t-*/SKILL.md'))}}
(ROOT/'reports/economy-contract-report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2)); raise SystemExit(1 if issues else 0)
