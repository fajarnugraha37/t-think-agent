#!/usr/bin/env python3
from __future__ import annotations
import shutil
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
REG=yaml.safe_load((ROOT/'orchestrator/agent-registry.yaml').read_text())
CORE=(ROOT/'orchestrator/t-think-core.md').read_text().rstrip()+"\n"
REPOSITORY_INTELLIGENCE=(ROOT/'orchestrator/repository-intelligence-policy.md').read_text().rstrip()+"\n"
AGENTS={a['name']:a for a in REG['agents']}; NAMES=list(AGENTS)
PLATFORM_SKILL_ROOT_TOKEN='__T_THINK_PLATFORM_SKILL_ROOT__'
PLATFORM_ROOT_NOTES={
'opencode':'''Use only OpenCode's native t-think skills from `~/.config/opencode/skills/t-*`. Never search or read `~/.agents/skills`, `~/.claude/skills`, `.codex`, or `.cursor` for t-think resources. Delegate only to registered terminal workers and keep depth one. Normal worktree tools are prompt-free. Never run gh. Use Git only for the explicit read-only commands in orchestrator/tool-permission-policy.yaml.''',
'codex':f'''Do not use global `~/.agents/skills` discovery for t-think. The only canonical Codex t-think resource root is `{PLATFORM_SKILL_ROOT_TOKEN}`. Read each active skill from `<root>/<skill-name>/SKILL.md` and resolve sibling resources relative to it. Never read another platform's t-think resources. Spawn only registered terminal workers and keep depth one. Never run gh or mutating Git commands.''',
'claude-code':f'''Do not use Claude's global Skill discovery for t-think because that directory can be scanned by another client. The only canonical Claude t-think resource root is `{PLATFORM_SKILL_ROOT_TOKEN}`. Use Read on `<root>/<skill-name>/SKILL.md`; never use the Skill tool or another platform's t-think resources. Delegate only to registered terminal workers. Never run gh or mutating Git commands.''',
'cursor':f'''The only canonical Cursor t-think resource root is `{PLATFORM_SKILL_ROOT_TOKEN}`. Read each active skill from `<root>/<skill-name>/SKILL.md`, resolve resources relative to it, and never search shared or another platform's t-think directories. Delegate only through the root orchestration flow. Never run gh or mutating Git commands.'''
}
PLATFORM_WORKER_NOTES={
'opencode':'''Load exactly the delegated skill through OpenCode's native mechanism from `~/.config/opencode/skills/t-*`. Never search or read `~/.agents/skills`, `~/.claude/skills`, `.codex`, or `.cursor` for t-think resources. Return one bounded result to t-think and never delegate recursively. Normal worktree tools are prompt-free. Never run gh or mutating Git commands.''',
'codex':f'''Do not use global `~/.agents/skills` discovery for t-think. Read the delegated skill only from `{PLATFORM_SKILL_ROOT_TOKEN}/<skill-name>/SKILL.md` and resolve resources relative to it. Never read another platform's t-think resources. The parent session owns orchestration; do not spawn child agents. Never run gh or mutating Git commands.''',
'claude-code':f'''Do not use Claude's global Skill discovery for t-think. Read the delegated skill only from `{PLATFORM_SKILL_ROOT_TOKEN}/<skill-name>/SKILL.md` and resolve resources relative to it. Never read shared or another platform's t-think resources. Agent and Skill are omitted from workers. Never run gh or mutating Git commands.''',
'cursor':f'''Read the delegated skill only from `{PLATFORM_SKILL_ROOT_TOKEN}/<skill-name>/SKILL.md` and resolve resources relative to it. Never search shared or another platform's t-think directories. Return one bounded result and do not delegate recursively. Never run gh or mutating Git commands.'''
}
current_platform=''

TRUSTED_EXTERNAL_PATHS = (
    '~/.config/opencode/skills/t-*/**',
    '~/.local/share/t-think/runtime/**',
)


def opencode_external_directory_permissions():
    # OpenCode uses the last matching rule. Deny everything first, then allow
    # only recursively nested, user-level t-think resources. POSIX separators
    # are intentional: OpenCode expands ~ and normalizes the pattern on every OS.
    return {'*': 'deny', **{path: 'allow' for path in TRUSTED_EXTERNAL_PATHS}}


PROTECTED_EDIT_PATHS = (
    '.git',
    '.git/**',
)

READ_ONLY_GIT_COMMANDS = (
    'git status',
    'git diff',
    'git log',
    'git show',
    'git rev-parse',
    'git ls-files',
    'git ls-tree',
    'git grep',
    'git cat-file',
    'git blame',
    'git shortlog',
    'git describe',
    'git check-ignore',
    'git merge-base',
    'git name-rev',
    'git for-each-ref',
    'git rev-list',
    'git diff-tree',
    'git diff-index',
    'git diff-files',
    'git show-ref',
    'git status --porcelain',
    'git branch --show-current',
    'git branch --list',
    'git tag --list',
    'git remote -v',
    'git remote get-url',
    'git config --get',
    'git config --get-all',
    'git config --get-regexp',
    'git config --list',
    'git symbolic-ref HEAD',
    'git symbolic-ref --short HEAD',
    'git submodule status',
    'git worktree list',
    'git stash list',
    'git reflog show',
)


def opencode_edit_permissions():
    # Worktree editing is prompt-free and unrestricted except for Git metadata.
    # Installed skill/runtime resources are external read-only dependencies.
    rules = {'*': 'allow'}
    rules.update({path: 'deny' for path in PROTECTED_EDIT_PATHS})
    rules.update({path: 'deny' for path in TRUSTED_EXTERNAL_PATHS})
    return rules


def opencode_bash_permissions():
    # OpenCode evaluates the last matching rule. Permit normal worktree commands,
    # deny all Git/GitHub CLI operations, then reopen an explicit read-only Git
    # subset. Keep gh denied last so no command variant is reopened.
    rules = {'*': 'allow', 'git': 'deny', 'git *': 'deny'}
    for command in READ_ONLY_GIT_COMMANDS:
        rules[command] = 'allow'
        rules[f'{command} *'] = 'allow'
        if command.startswith('git '):
            no_pager = 'git --no-pager ' + command[4:]
            rules[no_pager] = 'allow'
            rules[f'{no_pager} *'] = 'allow'
    rules.update({
        'cd .git': 'deny',
        'cd .git *': 'deny',
        'cd .git/*': 'deny',
        'cd .git\\*': 'deny',
        '* .git/config *': 'deny',
        '* .git/HEAD *': 'deny',
        '* .git/refs/*': 'deny',
        '* .git\\config *': 'deny',
        '* .git\\HEAD *': 'deny',
        '* .git\\refs\\*': 'deny',
        'gh': 'deny',
        'gh *': 'deny',
    })
    return rules


def opencode_base_permissions(task):
    return {
        '*': 'allow',
        'external_directory': opencode_external_directory_permissions(),
        'edit': opencode_edit_permissions(),
        'bash': opencode_bash_permissions(),
        'task': task,
        'doom_loop': 'allow',
    }
def dump_frontmatter(data): return '---\n'+yaml.safe_dump(data,sort_keys=False,width=120).strip()+'\n---\n'
def body(name):
    base = CORE if name == 't-think' else (ROOT/'agents'/name/'AGENT.md').read_text().rstrip()+'\n'
    shared = '\n\n' + REPOSITORY_INTELLIGENCE.rstrip() if name == 't-think' else ''
    note = PLATFORM_ROOT_NOTES[current_platform] if name == 't-think' else PLATFORM_WORKER_NOTES[current_platform]
    return base.rstrip()+shared+f"\n\n## Platform-isolated resources\n\n{note}\n"
def write_opencode():
    global current_platform; current_platform='opencode'; out=ROOT/'adapters/opencode'; out.mkdir(parents=True,exist_ok=True)
    task={'*':'deny',**{n:'allow' for n in NAMES}}
    fm={'description':'Govern an evidence-gated multi-agent software change with adaptive lanes and composite review phases.','mode':'primary','temperature':0.1,'permission':opencode_base_permissions(task)}
    note=f"\n## OpenCode adapter\n\nDelegate only to the {len(NAMES)} allowlisted terminal `t-*` workers. Use sequential delegation in economy mode.\n"
    (out/'t-think.md').write_text(dump_frontmatter(fm)+body('t-think')+note)
    for name,a in AGENTS.items():
        mode=a['permissions']['source_write']['mode']; perm=opencode_base_permissions('deny')
        (out/f'{name}.md').write_text(dump_frontmatter({'description':a['description'],'mode':'subagent','temperature':0.1,'permission':perm})+body(name))
def tq(s): return '"""'+s.replace('"""','\\"\\"\\"')+'"""'
def write_codex():
    global current_platform; current_platform='codex'; out=ROOT/'adapters/codex'; workers=out/'agents'; workers.mkdir(parents=True,exist_ok=True)
    note=f"\n## Codex adapter\n\nRun t-think as the root session. Spawn only the {len(NAMES)} registered terminal workers. Keep delegation depth one.\n"
    profile='# launch with: codex --profile t-think\nsandbox_mode = "workspace-write"\napproval_policy = "never"\ndeveloper_instructions = '+tq(body('t-think')+note)+'\n\n[agents]\nmax_depth = 1\nmax_threads = 4\ninterrupt_message = true\n'
    (out/'t-think.config.toml').write_text(profile)
    for name,a in AGENTS.items():
        sandbox='workspace-write'
        (workers/f'{name}.toml').write_text(f'name = "{name}"\ndescription = {tq(a["description"])}\nsandbox_mode = "{sandbox}"\ndeveloper_instructions = {tq(body(name))}\n')
def claude_tools(name):
    # t-think skills are loaded from the platform-private resource root by Read;
    # omit Skill so Claude cannot fall back to a cross-platform global copy.
    if name=='t-think': return f"Agent({', '.join(NAMES)}), Read, Grep, Glob, Bash, Write, Edit"
    return 'Read, Grep, Glob, Bash, Write, Edit'
def write_claude():
    global current_platform; current_platform='claude-code'; out=ROOT/'adapters/claude-code'; out.mkdir(parents=True,exist_ok=True)
    defs=[('t-think',{'description':'Govern an evidence-gated multi-agent software change end to end.'}),*AGENTS.items()]
    for name,a in defs: (out/f'{name}.md').write_text(dump_frontmatter({'name':name,'description':a['description'],'model':'inherit','tools':claude_tools(name),'permissionMode':'bypassPermissions'})+body(name))
def write_cursor():
    global current_platform; current_platform='cursor'; out=ROOT/'adapters/cursor'; out.mkdir(parents=True,exist_ok=True)
    defs=[('t-think',{'description':'Govern an evidence-gated multi-agent software change end to end.'}),*AGENTS.items()]
    for name,a in defs:
        readonly=False
        (out/f'{name}.md').write_text(dump_frontmatter({'name':name,'description':a['description'],'model':'inherit','readonly':readonly,'is_background':False})+body(name))
def main():
    for d in [ROOT/'adapters/opencode',ROOT/'adapters/codex',ROOT/'adapters/claude-code',ROOT/'adapters/cursor']:
        if d.exists(): shutil.rmtree(d)
        d.mkdir(parents=True,exist_ok=True)
    write_opencode();write_codex();write_claude();write_cursor()
    each=len(NAMES)+1; total=each*3+len(NAMES)+1
    print(f'generated {total} platform adapter artifacts ({each} OpenCode, 1 Codex profile + {len(NAMES)} workers, {each} Claude Code, {each} Cursor)')
if __name__=='__main__': main()
