#!/usr/bin/env python3
from __future__ import annotations
import copy,json,re,subprocess,sys,tempfile,tomllib
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bin'))
from tthink_runtime import validate_delegation,audit_boundaries,validate_result

DIGEST='a'*64

def packet(phase,agent,skill,mode='deny',approved=None,generated=None,ignored=None):
    return {'schema_version':'1.0.0','identity':{'work_id':'W-1','run_id':'RUN-1','invocation_id':'INV-1','parent_agent':'t-think','target_agent':agent},'lifecycle':{'current_phase':phase,'skill':skill,'attempt':1},'objective':{'statement':'Complete the authorized phase contract','completion_criteria':['Produce schema-valid evidence-backed output']},'workspace':{'root':'.','discovery':{'respect_vcs_ignore':True,'include_untracked':True,'include_ignored':False}},'permissions':{'workspace_read':'allow','outside_workspace':'deny','source_write':mode,'governance_artifact_write':'.t-think/**','approved_write_targets':approved or [],'generated_output_paths':generated or [],'protected_paths':['.git/**','.env','.env.*','**/secrets/**','**/*credential*','**/*private-key*'],'ignored_file_access':ignored or {'mode':'deny','human_approval_ref':None},'spawn_subagent':'deny'},'artifact_inputs':[],'output_contract':{'schema':f'skills/{skill}/schemas/output.schema.json','artifact_path':f'.t-think/W-1/artifacts/{phase.lower()}.yaml','result_path':'.t-think/W-1/results/INV-1.yaml','boundary_report_path':'.t-think/W-1/boundary-reports/INV-1.yaml'},'stop_conditions':['missing evidence','new semantic decision']}

def activity(**kw):
    base={'source_changes':[],'governance_artifact_changes':['.t-think/W-1/artifacts/x.yaml'],'generated_output_changes':[],'outside_workspace_access':[],'ignored_file_access':[]}; base.update(kw); return base

def check(condition,msg,issues):
    if not condition: issues.append(msg)

def main():
    issues=[]; passed=[]
    reg=yaml.safe_load((ROOT/'orchestrator/agent-registry.yaml').read_text()); phase=yaml.safe_load((ROOT/'orchestrator/phase-registry.yaml').read_text())
    check(reg['topology']=='star' and reg['max_delegation_depth']==1,'registry topology/depth invalid',issues)
    check(len(reg['agents'])==8,'expected 8 role subagents',issues)
    schema=json.loads((ROOT/'schemas/agent-manifest.schema.json').read_text())
    for a in reg['agents']:
        errs=list(Draft202012Validator(schema).iter_errors(a)); check(not errs,f'agent schema invalid {a["name"]}: {[e.message for e in errs]}',issues)
        check(a['permissions']['spawn_subagent']=='deny',f'{a["name"]} can spawn subagent',issues)
        check(a['permissions']['discovery']['respect_vcs_ignore'] is True and a['permissions']['discovery']['include_ignored'] is False,f'{a["name"]} ignore discovery invalid',issues)
    check(all('agent' in p and 'source_write_mode' in p for p in phase['phases']),'phase registry missing role/write mode',issues)
    passed.append('registry and agent manifests')

    inv=packet('INVESTIGATION','t-investigator','t-investigation')
    check(not validate_delegation(inv),f'valid investigation delegation rejected: {validate_delegation(inv)}',issues)
    bad=copy.deepcopy(inv); bad['permissions']['source_write']='approved_targets_only'; bad['permissions']['approved_write_targets']=['src/X.java']
    check(bool(validate_delegation(bad)),'investigator write delegation accepted',issues)
    check(audit_boundaries(inv,activity(source_changes=['src/X.java']))['status']=='FAIL','investigator source edit not blocked',issues)
    passed.append('read-only investigation boundary')

    build=packet('BOUNDED_IMPLEMENTATION','t-builder','t-bounded-implementation','approved_targets_only',['src/Order.java','tests/**'],['target/**'])
    check(not validate_delegation(build),f'valid builder delegation rejected: {validate_delegation(build)}',issues)
    br=audit_boundaries(build,activity(source_changes=['src/Order.java','tests/OrderTest.java'],generated_output_changes=['target/test-report.xml']))
    check(br['status']=='PASS',f'valid builder activity rejected: {br["violations"]}',issues)
    check(audit_boundaries(build,activity(source_changes=['src/Other.java']))['status']=='FAIL','unapproved builder edit accepted',issues)
    check(audit_boundaries(build,activity(source_changes=['.env']))['status']=='FAIL','protected edit accepted',issues)
    passed.append('approved target and protected path enforcement')

    review=packet('SELF_REVIEW','t-builder','t-self-review','deny')
    check(not validate_delegation(review),f'self-review delegation invalid: {validate_delegation(review)}',issues)
    check(audit_boundaries(review,activity(source_changes=['src/Order.java']))['status']=='FAIL','self-review source edit accepted',issues)
    passed.append('self-review write disabled')

    verify=packet('VERIFICATION','t-verifier','t-verification','generated_outputs_only',generated=['target/**','reports/**'])
    check(not validate_delegation(verify),f'verifier delegation invalid: {validate_delegation(verify)}',issues)
    check(audit_boundaries(verify,activity(generated_output_changes=['reports/result.json']))['status']=='PASS','valid generated output rejected',issues)
    check(audit_boundaries(verify,activity(source_changes=['src/Order.java']))['status']=='FAIL','verifier source edit accepted',issues)
    passed.append('verifier generated-output boundary')

    check(audit_boundaries(inv,activity(ignored_file_access=['.env']))['status']=='FAIL','ignored read without approval accepted',issues)
    approved=packet('INVESTIGATION','t-investigator','t-investigation',ignored={'mode':'human_approved','human_approval_ref':'HAP-1'})
    check(audit_boundaries(approved,activity(ignored_file_access=['ignored-fixture.txt']))['status']=='PASS','human-approved ignored read rejected',issues)
    check(audit_boundaries(inv,activity(outside_workspace_access=['../other']))['status']=='FAIL','outside workspace access accepted',issues)
    passed.append('ignored and outside-workspace boundaries')

    boundary=audit_boundaries(inv,activity())
    result={'schema_version':'1.0.0','invocation_id':'INV-1','agent':'t-investigator','phase':'INVESTIGATION','skill':'t-investigation','status':'COMPLETED','artifact':{'path':'.t-think/W-1/artifacts/investigation.yaml','sha256':DIGEST},'claim_counts':{'FACT':1,'INFERENCE':0,'ASSUMPTION':0,'UNKNOWN':0,'CONFLICT':0},'evidence':{'referenced':1,'missing':0},'unresolved_items':[],'recommended_transition':{'state':'SYSTEM_MODEL','gate':None},'validation':{'schema_passed':True,'semantic_checks_passed':True},'boundary_report':{'path':'.t-think/W-1/boundary-reports/INV-1.yaml','sha256':DIGEST,'status':'PASS'}}
    check(not validate_result(result,inv,boundary),f'valid result rejected: {validate_result(result,inv,boundary)}',issues)
    badr=copy.deepcopy(result); badr['recommended_transition']['state']='COMPLETED'
    check(bool(validate_result(badr,inv,boundary)),'invalid transition result accepted',issues)
    passed.append('result envelope cross-validation')

    for platform in ('opencode','claude-code','cursor'):
        files=sorted((ROOT/'adapters'/platform).glob('t-*.md')); check(len(files)==9,f'{platform} adapter count {len(files)}',issues)
        for f in files:
            text=f.read_text(); m=re.match(r'---\n(.*?)\n---\n',text,re.S); check(bool(m),f'{platform}/{f.name} missing frontmatter',issues)
            if m:
                d=yaml.safe_load(m.group(1)); check(d.get('model') in (None,'inherit'),f'{platform}/{f.name} pins model',issues)
                if platform=='claude-code' and f.stem!='t-think': check('Agent' not in str(d.get('tools','')),f'Claude worker {f.stem} can nest',issues)
    profile=ROOT/'adapters/codex/t-think.config.toml'; workers=sorted((ROOT/'adapters/codex/agents').glob('t-*.toml'))
    check(profile.exists(),'Codex root profile missing',issues); check(len(workers)==8,f'Codex worker count {len(workers)}',issues)
    if profile.exists():
        d=tomllib.loads(profile.read_text()); check('model' not in d and 'model_reasoning_effort' not in d,'Codex root profile pins model',issues)
        check(d.get('agents',{}).get('max_depth')==1,'Codex root profile max_depth must be 1',issues)
        check('t-think' in d.get('developer_instructions',''),'Codex root profile missing t-think instructions',issues)
    for f in workers:
        d=tomllib.loads(f.read_text()); check('model' not in d and 'model_reasoning_effort' not in d,f'codex/{f.name} pins model',issues)
        if f.stem not in ('t-builder','t-verifier'): check(d.get('sandbox_mode')=='read-only',f'codex/{f.name} not read-only',issues)
    passed.append('platform adapter structure and model neutrality')

    report={'status':'FAIL' if issues else 'PASS','passed_contracts':passed,'issues':issues}
    (ROOT/'reports/subagent-contract-report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2)); return 1 if issues else 0
if __name__=='__main__': raise SystemExit(main())
