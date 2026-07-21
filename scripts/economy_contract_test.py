#!/usr/bin/env python3
from __future__ import annotations
import json,re,tomllib
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1];issues=[]
profiles=yaml.safe_load((ROOT/'orchestrator/model-profiles.yaml').read_text());e=profiles['profiles']['economy']
checks=[(profiles.get('default')=='economy','economy is not default'),(e.get('subagents_enabled') is True,'subagents disabled'),(e.get('max_active_skills')==1,'one active skill not enforced'),(e.get('max_concurrent_subagents')==1,'economy must be sequential'),(e.get('parallel_subagents') is False,'parallel economy workers enabled'),(e.get('max_delegation_depth')==1,'depth must be one'),(e.get('model')=='inherit','model must inherit')]
for ok,msg in checks:
 if not ok:issues.append(msg)
lanes=yaml.safe_load((ROOT/'orchestrator/lane-registry.yaml').read_text());budgets=yaml.safe_load((ROOT/'orchestrator/context-budget-policy.yaml').read_text())
if lanes['lanes']['quick']['role_types']!=['t-builder','t-reviewer','t-verifier']:issues.append('quick lane must include independent technical reviewer')
if budgets.get('common',{}).get('one_active_skill') is not True:issues.append('one-active-skill budget missing')
if budgets['lanes']['quick']['max_source_files_per_worker']>8:issues.append('quick source context exceeds 8 files')
comp=yaml.safe_load((ROOT/'orchestrator/composite-phase-policy.yaml').read_text())
for phase,c in comp['phases'].items():
 for t in c['tracks']:
  if not t.get('fresh_context'):issues.append(f'{phase}/{t["id"]}: fresh context not required')
  if t.get('source_write_mode')!='deny':issues.append(f'{phase}/{t["id"]}: composite track can write source')
core=(ROOT/'orchestrator/t-think-core.md').read_text()
if len(core)>18000:issues.append(f'core too large: {len(core)}')
for f in (ROOT/'skills').glob('t-*/SKILL.md'):
 if len(f.read_text())>20000:issues.append(f'skill too large: {f.parent.name}')
for f in (ROOT/'agents').glob('t-*/AGENT.md'):
 if len(f.read_text())>8000:issues.append(f'agent too large: {f.parent.name}')
for f in (ROOT/'adapters/opencode').glob('t-*.md'):
 d=yaml.safe_load(re.match(r'---\n(.*?)\n---\n',f.read_text(),re.S).group(1))
 if 'model' in d:issues.append(f'OpenCode pins model: {f.name}')
profile=ROOT/'adapters/codex/t-think.config.toml'
if profile.exists():
 d=tomllib.loads(profile.read_text())
 if 'model' in d or d.get('agents',{}).get('max_depth')!=1:issues.append('Codex root model/depth invalid')
else:issues.append('Codex profile missing')
for f in (ROOT/'adapters/claude-code').glob('t-*.md'):
 d=yaml.safe_load(re.match(r'---\n(.*?)\n---\n',f.read_text(),re.S).group(1))
 if d.get('model')!='inherit':issues.append(f'Claude model not inherited: {f.name}')
 if f.stem!='t-think' and 'Agent' in str(d.get('tools','')):issues.append(f'Claude worker can nest: {f.name}')
report={'status':'FAIL' if issues else 'PASS','issues':issues,'core_characters':len(core)};(ROOT/'reports/economy-contract-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(1 if issues else 0)
