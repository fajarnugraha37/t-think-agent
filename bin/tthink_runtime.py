from __future__ import annotations
import fnmatch, hashlib, json
from pathlib import Path, PurePosixPath
from typing import Any
import yaml
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]

def load_data(path:Path)->Any:
    text=path.read_text()
    if path.suffix.lower()=='.json': return json.loads(text)
    return yaml.safe_load(text)

def dump_data(path:Path,data:Any)->None:
    if path.suffix.lower()=='.json': path.write_text(json.dumps(data,indent=2)+'\n')
    else: path.write_text(yaml.safe_dump(data,sort_keys=False,width=110))

def validate_schema(data:Any,schema_name:str)->list[str]:
    schema=json.loads((ROOT/'schemas'/schema_name).read_text())
    return [f"{'.'.join(map(str,e.path)) or '$'}: {e.message}" for e in sorted(Draft202012Validator(schema).iter_errors(data),key=lambda e:list(e.path))]

def registry():
    phases=yaml.safe_load((ROOT/'orchestrator/phase-registry.yaml').read_text())
    agents=yaml.safe_load((ROOT/'orchestrator/agent-registry.yaml').read_text())
    return ({p['state']:p for p in phases['phases']},{a['name']:a for a in agents['agents']})

def norm(path:str)->str:
    value=path.replace('\\','/').strip()
    while value.startswith('./'): value=value[2:]
    return str(PurePosixPath(value))

def is_outside(path:str)->bool:
    p=PurePosixPath(norm(path))
    return p.is_absolute() or '..' in p.parts

def matches(path:str,patterns:list[str])->bool:
    p=norm(path)
    return any(fnmatch.fnmatchcase(p,pat) or fnmatch.fnmatchcase('/'+p,pat) for pat in patterns)

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def validate_delegation(data:dict)->list[str]:
    errors=validate_schema(data,'delegation-packet.schema.json')
    if errors: return errors
    phases,agents=registry()
    phase=data['lifecycle']['current_phase']; target=data['identity']['target_agent']; skill=data['lifecycle']['skill']
    if phase not in phases: errors.append(f'unknown lifecycle phase: {phase}'); return errors
    row=phases[phase]
    if row['agent']!=target: errors.append(f'phase {phase} requires {row["agent"]}, got {target}')
    if row['skill']!=skill: errors.append(f'phase {phase} requires {row["skill"]}, got {skill}')
    if target not in agents: errors.append(f'unknown subagent: {target}'); return errors
    agent=agents[target]
    if phase not in agent['phases'] or skill not in agent['skills']: errors.append('agent manifest does not authorize phase/skill')
    perms=data['permissions']; expected=row['source_write_mode']
    if perms['source_write']!=expected: errors.append(f'phase {phase} source_write must be {expected}')
    if data['workspace']['discovery']!={'respect_vcs_ignore':True,'include_untracked':True,'include_ignored':False}:
        errors.append('workspace discovery must respect VCS ignore and exclude ignored files by default')
    if expected=='approved_targets_only' and not perms['approved_write_targets']:
        errors.append('bounded implementation requires at least one approved_write_target')
    if expected!='approved_targets_only' and perms['approved_write_targets']:
        errors.append(f'{phase} must not carry approved_write_targets')
    if expected=='generated_outputs_only' and not perms['generated_output_paths']:
        errors.append('verification requires declared generated_output_paths')
    if expected!='generated_outputs_only' and phase!='BOUNDED_IMPLEMENTATION' and perms['generated_output_paths']:
        errors.append(f'{phase} must not carry generated_output_paths')
    if perms['ignored_file_access']['mode']=='human_approved' and not perms['ignored_file_access']['human_approval_ref']:
        errors.append('human-approved ignored file access requires approval reference')
    if perms['ignored_file_access']['mode']=='deny' and perms['ignored_file_access']['human_approval_ref'] is not None:
        errors.append('denied ignored file access must not carry approval reference')
    protected=perms['protected_paths']
    for path in perms['approved_write_targets']+perms['generated_output_paths']:
        if is_outside(path): errors.append(f'path escapes workspace: {path}')
        if matches(path,protected): errors.append(f'authorized target overlaps protected path: {path}')
    for item in data['artifact_inputs']:
        if is_outside(item['ref']): errors.append(f'artifact input escapes workspace: {item["ref"]}')
    for key in ('artifact_path','result_path','boundary_report_path'):
        path=data['output_contract'][key]
        if is_outside(path): errors.append(f'{key} escapes workspace: {path}')
        if not norm(path).startswith('.t-think/'):
            errors.append(f'{key} must be below .t-think/: {path}')
    return errors

def audit_boundaries(packet:dict,activity:dict)->dict:
    errors=validate_delegation(packet)
    perms=packet['permissions']; target=packet['identity']['target_agent']; invocation=packet['identity']['invocation_id']
    source=[norm(x) for x in activity.get('source_changes',[])]
    governance=[norm(x) for x in activity.get('governance_artifact_changes',[])]
    generated=[norm(x) for x in activity.get('generated_output_changes',[])]
    outside=[str(x) for x in activity.get('outside_workspace_access',[])]
    ignored=[norm(x) for x in activity.get('ignored_file_access',[])]
    protected=perms['protected_paths']
    for p in source+governance+generated:
        if is_outside(p): errors.append(f'path escapes workspace: {p}')
        if matches(p,protected): errors.append(f'protected path touched: {p}')
    for p in governance:
        if not p.startswith('.t-think/'): errors.append(f'governance artifact outside .t-think/: {p}')
    mode=perms['source_write']
    if source:
        if mode!='approved_targets_only': errors.append(f'{target} changed source while mode is {mode}')
        for p in source:
            if not matches(p,perms['approved_write_targets']): errors.append(f'unapproved source change: {p}')
    if generated:
        allowed=perms['generated_output_paths']
        if mode not in ('generated_outputs_only','approved_targets_only'): errors.append(f'{target} created generated outputs while mode is {mode}')
        for p in generated:
            if not matches(p,allowed): errors.append(f'undeclared generated output: {p}')
    if outside: errors.extend(f'outside-workspace access: {p}' for p in outside)
    if ignored and perms['ignored_file_access']['mode']!='human_approved': errors.extend(f'ignored file read without approval: {p}' for p in ignored)
    return {'schema_version':'1.0.0','invocation_id':invocation,'agent':target,'status':'FAIL' if errors else 'PASS','source_changes':source,'governance_artifact_changes':governance,'generated_output_changes':generated,'outside_workspace_access':outside,'ignored_file_access':ignored,'violations':errors}

def validate_result(result:dict,packet:dict,boundary:dict)->list[str]:
    errors=validate_schema(result,'subagent-result.schema.json')
    errors+=validate_schema(boundary,'boundary-report.schema.json')
    if errors: return errors
    identity=packet['identity']; life=packet['lifecycle']
    if result['invocation_id']!=identity['invocation_id']: errors.append('result invocation_id mismatch')
    if result['agent']!=identity['target_agent']: errors.append('result agent mismatch')
    if result['phase']!=life['current_phase']: errors.append('result phase mismatch')
    if result['skill']!=life['skill']: errors.append('result skill mismatch')
    if boundary['invocation_id']!=identity['invocation_id'] or boundary['agent']!=identity['target_agent']: errors.append('boundary identity mismatch')
    if boundary['status']!='PASS' or result['boundary_report']['status']!='PASS': errors.append('boundary report did not pass')
    if result['status']=='COMPLETED' and not all(result['validation'].values()): errors.append('completed result has failed validation flags')
    phases,_=registry(); expected=phases[life['current_phase']]['success_state']
    if result['status']=='COMPLETED' and result['recommended_transition']['state']!=expected:
        errors.append(f'completed result must recommend {expected}')
    return errors
