#!/usr/bin/env python3
from __future__ import annotations
import json,re,tomllib
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
PHASES=[('PROBLEM_ALIGNMENT','t-problem-alignment','t-think'),('INVESTIGATION','t-investigation','t-investigator'),('SYSTEM_MODEL','t-system-modeling','t-modeler'),('MODEL_CRITIQUE','t-model-critique','t-critic'),('SOLUTION_DESIGN','t-solution-design','t-modeler'),('SOLUTION_CRITIQUE','t-solution-critique','t-critic'),('IMPLEMENTATION_BLUEPRINT','t-implementation-blueprint','t-think'),('BLUEPRINT_CRITIQUE','t-blueprint-critique','t-think'),('BOUNDED_IMPLEMENTATION','t-bounded-implementation','t-builder'),('IMPLEMENTATION_REVIEW','t-implementation-review','t-think'),('VERIFICATION','t-verification','t-verifier'),('RECONCILIATION','t-reconciliation','t-reconciler')]
SKILL_STATES={
 't-problem-alignment':'PROBLEM_ALIGNMENT','t-investigation':'INVESTIGATION','t-system-modeling':'SYSTEM_MODEL','t-model-critique':'MODEL_CRITIQUE','t-solution-design':'SOLUTION_DESIGN','t-solution-critique':'SOLUTION_CRITIQUE',
 't-implementation-blueprint':'IMPLEMENTATION_BLUEPRINT','t-implementation-planning':'IMPLEMENTATION_BLUEPRINT','t-checklist-builder':'IMPLEMENTATION_BLUEPRINT',
 't-blueprint-critique':'BLUEPRINT_CRITIQUE','t-plan-critique':'BLUEPRINT_CRITIQUE','t-checklist-critique':'BLUEPRINT_CRITIQUE','t-bounded-implementation':'BOUNDED_IMPLEMENTATION',
 't-implementation-review':'IMPLEMENTATION_REVIEW','t-self-review':'IMPLEMENTATION_REVIEW','t-technical-review':'IMPLEMENTATION_REVIEW','t-security-review':'IMPLEMENTATION_REVIEW','t-breaking-review':'IMPLEMENTATION_REVIEW',
 't-verification':'VERIFICATION','t-reconciliation':'RECONCILIATION'}
def fm(path):
 m=re.match(r'---\n(.*?)\n---\n',path.read_text(),re.S); return yaml.safe_load(m.group(1)) if m else None
def main():
 issues=[]
 preg=yaml.safe_load((ROOT/'orchestrator/phase-registry.yaml').read_text()); rows=preg.get('phases',[])
 expected_states=[x[0] for x in PHASES]
 if [x.get('state') for x in rows]!=expected_states: issues.append('phase registry does not match canonical 12-phase lifecycle')
 for row,(state,skill,agent) in zip(rows,PHASES):
  if row.get('skill')!=skill or row.get('agent')!=agent: issues.append(f'{state}: skill/agent mismatch')
  for field in ('source_write_mode','context','composite'): 
   if field not in row: issues.append(f'{state}: missing {field}')
 actual={p.name for p in (ROOT/'skills').iterdir() if p.is_dir()}
 if actual!=set(SKILL_STATES): issues.append(f'skill directories mismatch: missing={sorted(set(SKILL_STATES)-actual)} extra={sorted(actual-set(SKILL_STATES))}')
 for name,state in SKILL_STATES.items():
  base=ROOT/'skills'/name; file=base/'SKILL.md'
  for req in (file,base/'schemas',base/'templates',base/'validators/validate.py',base/'examples',base/'tests',base/'orchestrator/transition-contract.yaml'):
   if not req.exists(): issues.append(f'missing {req.relative_to(ROOT)}')
  if file.exists():
   data=fm(file)
   if not data: issues.append(f'{name}: invalid frontmatter')
   elif data.get('name')!=name or data.get('lifecycle_state')!=state: issues.append(f'{name}: frontmatter identity/state mismatch')
 lanes=yaml.safe_load((ROOT/'orchestrator/lane-registry.yaml').read_text())
 expected_paths={
 'quick':['PROBLEM_ALIGNMENT','BOUNDED_IMPLEMENTATION','IMPLEMENTATION_REVIEW','VERIFICATION','RECONCILIATION','COMPLETED'],
 'standard':['PROBLEM_ALIGNMENT','INVESTIGATION','SOLUTION_DESIGN','IMPLEMENTATION_BLUEPRINT','BLUEPRINT_CRITIQUE','BOUNDED_IMPLEMENTATION','IMPLEMENTATION_REVIEW','VERIFICATION','RECONCILIATION','COMPLETED'],
 'full':expected_states+['COMPLETED']}
 for lane,path in expected_paths.items():
  if lanes['lanes'][lane]['phase_path']!=path: issues.append(f'{lane}: phase path mismatch')
 if lanes['lanes']['quick']['role_types']!=['t-builder','t-reviewer','t-verifier']: issues.append('quick lane must require builder, reviewer, verifier')
 comp=yaml.safe_load((ROOT/'orchestrator/composite-phase-policy.yaml').read_text())['phases']
 expected_tracks={'IMPLEMENTATION_BLUEPRINT':['strategy','execution_checklist'],'BLUEPRINT_CRITIQUE':['strategy_critique','execution_critique'],'IMPLEMENTATION_REVIEW':['self_review','technical_review','security_review','breaking_review']}
 for phase,ids in expected_tracks.items():
  got=[x['id'] for x in comp.get(phase,{}).get('tracks',[])]
  if got!=ids: issues.append(f'{phase}: composite tracks mismatch')
 review={x['id']:x for x in comp['IMPLEMENTATION_REVIEW']['tracks']}
 if set(review['self_review']['lanes'])!=set(expected_paths) or set(review['technical_review']['lanes'])!=set(expected_paths): issues.append('self and technical review must run in every lane')
 for rid in ('security_review','breaking_review'):
  if set(review[rid]['lanes'])!={'standard','full'}: issues.append(f'{rid} must run in standard and full')
 areg=yaml.safe_load((ROOT/'orchestrator/agent-registry.yaml').read_text()); agents=areg.get('agents',[])
 if areg.get('topology')!='star' or areg.get('max_delegation_depth')!=1 or len(agents)!=10: issues.append('agent registry must be star/depth-1 with 10 terminal workers')
 schema=json.loads((ROOT/'schemas/agent-manifest.schema.json').read_text())
 for a in agents:
  es=list(Draft202012Validator(schema).iter_errors(a))
  if es: issues.append(f'{a.get("name")}: invalid agent manifest: {[e.message for e in es]}')
  if a.get('permissions',{}).get('spawn_subagent')!='deny': issues.append(f'{a.get("name")}: nested delegation allowed')
 count=len(agents)+1
 for platform in ('opencode','claude-code','cursor'):
  got=len(list((ROOT/'adapters'/platform).glob('t-*.md')))
  if got!=count: issues.append(f'{platform}: expected {count}, got {got}')
 codex=ROOT/'adapters/codex/t-think.config.toml'; workers=list((ROOT/'adapters/codex/agents').glob('t-*.toml'))
 if not codex.exists() or len(workers)!=len(agents): issues.append('codex adapter count mismatch')
 core=(ROOT/'orchestrator/t-think-core.md').read_text()
 if len(core)>18000: issues.append(f'core too large: {len(core)}')
 report={'status':'FAIL' if issues else 'PASS','canonical_phases':12,'installed_skills':len(SKILL_STATES),'role_subagents':10,'governance_lanes':3,'platform_agent_adapters':44,'issues':issues,'core_characters':len(core)}
 (ROOT/'reports').mkdir(exist_ok=True);(ROOT/'reports/alignment-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 1 if issues else 0
if __name__=='__main__': raise SystemExit(main())
