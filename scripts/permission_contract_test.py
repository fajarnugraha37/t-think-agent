#!/usr/bin/env python3
from __future__ import annotations
import json,re,tomllib
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
TOKEN='__T_THINK_PLATFORM_SKILL_ROOT__'
OPENCODE_TRUSTED=(
    '~/.config/opencode/skills/t-*/**',
    '~/.local/share/t-think/runtime/**',
)
FORBIDDEN_SHARED=(
    '~/.agents/skills/t-*/**',
    '~/.claude/skills/t-*/**',
)
EXPECTED_PLATFORM_PATTERNS={
    'opencode':['~/.config/opencode/skills/t-*/**','~/.local/share/t-think/runtime/**'],
    'codex':['~/.codex/t-think/skills/t-*/**','~/.local/share/t-think/runtime/**'],
    'claude_code':['~/.claude/t-think/skills/t-*/**','~/.local/share/t-think/runtime/**'],
    'cursor':['~/.cursor/t-think/skills/t-*/**','~/.local/share/t-think/runtime/**'],
}
READONLY=(
    'git status','git diff','git log','git show','git rev-parse','git ls-files',
    'git ls-tree','git grep','git cat-file','git blame','git shortlog','git describe',
    'git check-ignore','git merge-base','git name-rev','git for-each-ref','git rev-list',
    'git diff-tree','git diff-index','git diff-files','git show-ref','git branch --show-current',
    'git branch --list','git tag --list','git remote -v','git remote get-url',
    'git config --get','git config --get-all','git config --get-regexp','git config --list',
    'git symbolic-ref HEAD','git symbolic-ref --short HEAD','git submodule status',
    'git worktree list','git stash list','git reflog show',
)
def fm(path:Path):
    m=re.match(r'---\n(.*?)\n---\n',path.read_text(encoding='utf-8'),re.S)
    return yaml.safe_load(m.group(1)) if m else None
def walk_values(value):
    if isinstance(value,dict):
        for v in value.values(): yield from walk_values(v)
    elif isinstance(value,list):
        for v in value: yield from walk_values(v)
    else: yield value
def main():
    issues=[]
    files=sorted((ROOT/'adapters/opencode').glob('t-*.md'))
    for path in files:
        data=fm(path)
        if not data:
            issues.append(f'{path.name}: invalid frontmatter'); continue
        p=data.get('permission',{})
        if any(v=='ask' for v in walk_values(p)):
            issues.append(f'{path.name}: contains ask permission')
        if p.get('*')!='allow': issues.append(f'{path.name}: global tool default is not allow')
        ext=p.get('external_directory',{})
        if list(ext)[:1]!=['*'] or ext.get('*')!='deny': issues.append(f'{path.name}: external directory is not deny-first')
        for x in OPENCODE_TRUSTED:
            if ext.get(x)!='allow': issues.append(f'{path.name}: missing OpenCode-only external allow {x}')
        for x in FORBIDDEN_SHARED:
            if x in ext: issues.append(f'{path.name}: trusts cross-platform shared root {x}')
        extra={k for k,v in ext.items() if k!='*' and v=='allow'}-set(OPENCODE_TRUSTED)
        if extra: issues.append(f'{path.name}: unexpected external allows {sorted(extra)}')
        edit=p.get('edit',{})
        if edit.get('*')!='allow': issues.append(f'{path.name}: worktree edit tool is not prompt-free')
        for x in ('.git','.git/**',*OPENCODE_TRUSTED):
            if edit.get(x)!='deny': issues.append(f'{path.name}: protected edit rule missing {x}')
        bash=p.get('bash',{})
        keys=list(bash)
        if not keys or keys[0]!='*' or bash.get('*')!='allow': issues.append(f'{path.name}: bash is not allow-first')
        if bash.get('git')!='deny' or bash.get('git *')!='deny': issues.append(f'{path.name}: git default deny missing')
        for command in READONLY:
            if bash.get(command)!='allow' or bash.get(command+' *')!='allow': issues.append(f'{path.name}: readonly git allow missing {command}')
        if bash.get('gh')!='deny' or bash.get('gh *')!='deny': issues.append(f'{path.name}: gh deny missing')
        if keys[-2:]!=['gh','gh *']: issues.append(f'{path.name}: gh deny must be final')
        if TOKEN in path.read_text(encoding='utf-8'): issues.append(f'{path.name}: OpenCode must not use materialized private-root token')
        if path.stem=='t-think':
            task=p.get('task',{})
            if task.get('*')!='deny' or len([x for x,v in task.items() if x!='*' and v=='allow'])!=10: issues.append('t-think: task allowlist mismatch')
        elif p.get('task')!='deny': issues.append(f'{path.name}: nested task not denied')

    codex_profile=ROOT/'adapters/codex/t-think.config.toml'
    codex=tomllib.loads(codex_profile.read_text(encoding='utf-8'))
    if codex.get('approval_policy')!='never': issues.append('Codex approval_policy must be never')
    if codex.get('sandbox_mode')!='workspace-write': issues.append('Codex root must use workspace-write')
    if TOKEN not in codex_profile.read_text(encoding='utf-8'): issues.append('Codex root profile lacks private skill-root token')
    for path in (ROOT/'adapters/codex/agents').glob('t-*.toml'):
        if tomllib.loads(path.read_text(encoding='utf-8')).get('sandbox_mode')!='workspace-write': issues.append(f'{path.name}: Codex worker is not workspace-write')
        if TOKEN not in path.read_text(encoding='utf-8'): issues.append(f'{path.name}: Codex worker lacks private skill-root token')

    for path in (ROOT/'adapters/claude-code').glob('t-*.md'):
        d=fm(path)
        if d.get('permissionMode')!='bypassPermissions': issues.append(f'{path.name}: Claude permissionMode is not bypassPermissions')
        tools=str(d.get('tools',''))
        for tool in ('Read','Bash','Write','Edit'):
            if tool not in tools: issues.append(f'{path.name}: Claude missing tool {tool}')
        if 'Skill' in tools: issues.append(f'{path.name}: Claude exposes shared/global Skill discovery')
        if path.stem!='t-think' and 'Agent(' in tools: issues.append(f'{path.name}: Claude worker can delegate')
        if TOKEN not in path.read_text(encoding='utf-8'): issues.append(f'{path.name}: Claude adapter lacks private skill-root token')

    for path in (ROOT/'adapters/cursor').glob('t-*.md'):
        d=fm(path)
        if d.get('readonly') is not False: issues.append(f'{path.name}: Cursor adapter remains readonly')
        if TOKEN not in path.read_text(encoding='utf-8'): issues.append(f'{path.name}: Cursor adapter lacks private skill-root token')

    policy=yaml.safe_load((ROOT/'orchestrator/tool-permission-policy.yaml').read_text(encoding='utf-8'))
    if policy.get('profile')!='workspace-autonomous': issues.append('workspace-autonomous policy missing')
    if policy.get('native_tool_protected_paths')!=['.git','.git/**']:
        issues.append('native worktree path boundary must protect only .git and .git/**')
    workspace=policy.get('workspace',{})
    if workspace.get('normal_tool_calls')!='allow_without_prompt' or workspace.get('outside_workspace')!='deny':
        issues.append('workspace permission policy is not prompt-free and worktree-contained')
    trusted=workspace.get('trusted_external_resources',{})
    if trusted.get('isolation')!='platform_specific': issues.append('trusted external resources are not platform-isolated')
    if trusted.get('patterns_by_platform')!=EXPECTED_PLATFORM_PATTERNS: issues.append('platform-specific resource patterns mismatch')
    if trusted.get('forbidden_shared_discovery_roots')!=['~/.agents/skills','~/.claude/skills']:
        issues.append('shared discovery roots are not explicitly forbidden')
    if policy.get('vcs',{}).get('github_cli',{}).get('policy')!='deny_all': issues.append('policy does not deny gh')

    report={'status':'FAIL' if issues else 'PASS','opencode_agents':len(files),'readonly_git_patterns':len(READONLY),'platform_resource_isolation':True,'issues':issues}
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/permission-contract-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 1 if issues else 0
if __name__=='__main__': raise SystemExit(main())
