#!/usr/bin/env python3
from __future__ import annotations
import json,re,tomllib
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
EXPECTED=[('t-problem-alignment','PROBLEM_ALIGNMENT','INVESTIGATION','t-think'),('t-investigation','INVESTIGATION','SYSTEM_MODEL','t-investigator'),('t-system-modeling','SYSTEM_MODEL','MODEL_CRITIQUE','t-modeler'),('t-model-critique','MODEL_CRITIQUE','SOLUTION_DESIGN','t-critic'),('t-solution-design','SOLUTION_DESIGN','SOLUTION_CRITIQUE','t-modeler'),('t-solution-critique','SOLUTION_CRITIQUE','IMPLEMENTATION_PLAN','t-critic'),('t-implementation-planning','IMPLEMENTATION_PLAN','PLAN_CRITIQUE','t-planner'),('t-plan-critique','PLAN_CRITIQUE','IMPLEMENTATION_CHECKLIST','t-critic'),('t-checklist-builder','IMPLEMENTATION_CHECKLIST','CHECKLIST_CRITIQUE','t-planner'),('t-checklist-critique','CHECKLIST_CRITIQUE','BOUNDED_IMPLEMENTATION','t-critic'),('t-bounded-implementation','BOUNDED_IMPLEMENTATION','SELF_REVIEW','t-builder'),('t-self-review','SELF_REVIEW','TECHNICAL_REVIEW','t-builder'),('t-technical-review','TECHNICAL_REVIEW','VERIFICATION','t-reviewer'),('t-verification','VERIFICATION','RECONCILIATION','t-verifier'),('t-reconciliation','RECONCILIATION','COMPLETED','t-reconciler')]

def main():
    issues=[]; skills=ROOT/'skills'; reg=yaml.safe_load((ROOT/'orchestrator/phase-registry.yaml').read_text()); rows=reg.get('phases',[])
    if [(x['skill'],x['state'],x['success_state'],x['agent']) for x in rows]!=EXPECTED: issues.append('phase registry does not match canonical skill/state/agent order')
    actual=sorted(p.name for p in skills.iterdir() if p.is_dir()); expected=sorted(x[0] for x in EXPECTED)
    if actual!=expected: issues.append(f'skill directories mismatch: {actual}')
    for name,state,_,_ in EXPECTED:
        root=skills/name; f=root/'SKILL.md'
        for req in [f,root/'schemas',root/'templates',root/'validators/validate.py',root/'examples',root/'tests',root/'orchestrator/transition-contract.yaml']:
            if not req.exists(): issues.append(f'missing {req.relative_to(ROOT)}')
        if not f.exists(): continue
        m=re.match(r'---\n(.*?)\n---\n',f.read_text(),re.S)
        if not m: issues.append(f'{name}: invalid frontmatter'); continue
        fm=yaml.safe_load(m.group(1))
        if fm.get('name')!=name: issues.append(f'{name}: frontmatter name mismatch')
        if fm.get('lifecycle_state')!=state: issues.append(f'{name}: lifecycle state mismatch')
        if '## Small-model execution contract' not in f.read_text(): issues.append(f'{name}: missing small-model contract')
    areg=yaml.safe_load((ROOT/'orchestrator/agent-registry.yaml').read_text())
    if areg.get('topology')!='star' or areg.get('max_delegation_depth')!=1: issues.append('agent registry topology/depth invalid')
    if len(areg.get('agents',[]))!=8: issues.append('expected 8 role subagents')
    schema=json.loads((ROOT/'schemas/agent-manifest.schema.json').read_text())
    phase_by_agent={}
    for a in areg.get('agents',[]):
        errs=list(Draft202012Validator(schema).iter_errors(a))
        if errs: issues.append(f'{a.get("name")}: invalid manifest: {[e.message for e in errs]}')
        for p in a.get('phases',[]):
            if p in phase_by_agent: issues.append(f'phase {p} assigned to multiple agents')
            phase_by_agent[p]=a['name']
        if a.get('permissions',{}).get('spawn_subagent')!='deny': issues.append(f'{a.get("name")}: nested delegation allowed')
    for _,state,_,agent in EXPECTED:
        if state!='PROBLEM_ALIGNMENT' and phase_by_agent.get(state)!=agent: issues.append(f'{state}: agent registry mismatch')
    for platform in ('opencode','claude-code','cursor'):
        files=sorted((ROOT/'adapters'/platform).glob('t-*.md'))
        if len(files)!=9: issues.append(f'{platform}: expected 9 adapters, found {len(files)}')
    codex_profile=ROOT/'adapters/codex/t-think.config.toml'
    codex_workers=sorted((ROOT/'adapters/codex/agents').glob('t-*.toml'))
    if not codex_profile.exists() or len(codex_workers)!=8: issues.append(f'codex: expected 1 root profile and 8 workers, found profile={codex_profile.exists()} workers={len(codex_workers)}')
    core=(ROOT/'orchestrator/t-think-core.md').read_text()
    if len(core)>18000: issues.append(f'core too large: {len(core)}')
    for phrase in ['star','approved_write_targets','.gitignore','t-investigator','t-reconciler']:
        if phrase not in core: issues.append(f'core missing {phrase}')
    if (ROOT/'migration').exists() or (ROOT/'migrations').exists(): issues.append('migration directory must not exist')
    report={'status':'FAIL' if issues else 'PASS','skills':15,'role_subagents':8,'platform_agent_adapters':36,'issues':issues,'core_characters':len(core)}
    (ROOT/'reports').mkdir(exist_ok=True); (ROOT/'reports/alignment-report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2)); return 1 if issues else 0
if __name__=='__main__': raise SystemExit(main())
