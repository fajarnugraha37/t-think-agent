#!/usr/bin/env python3
from __future__ import annotations
import shutil
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
REG=yaml.safe_load((ROOT/'orchestrator/agent-registry.yaml').read_text())
CORE=(ROOT/'orchestrator/t-think-core.md').read_text().rstrip()+"\n"
AGENTS={a['name']:a for a in REG['agents']}; NAMES=list(AGENTS)
PLATFORM_NOTES={
'opencode':'Load exactly the delegated skill. Return one bounded result to t-think; never delegate recursively. Normal worktree tools are prompt-free. Never run gh. Use Git only for the explicit read-only commands in orchestrator/tool-permission-policy.yaml and never bypass that restriction through aliases, wrappers, or indirect shell invocation.',
'codex':'Use global Agent Skills. The parent session owns orchestration. Do not spawn child agents. Normal worktree tools run without approval prompts. Never run gh or mutating Git commands; Git is read-only as defined by orchestrator/tool-permission-policy.yaml.',
'claude-code':'Load the active skill through Skill. Agent is omitted from workers, so nested delegation is unavailable. The adapter bypasses permission prompts inside the project. Never run gh or mutating Git commands; Git is read-only as defined by orchestrator/tool-permission-policy.yaml.',
'cursor':'Use globally installed Agent Skills and return one bounded result to t-think. Do not delegate recursively. Keep work inside the project. Never run gh or mutating Git commands; Git is read-only as defined by orchestrator/tool-permission-policy.yaml.'}
current_platform=''

TRUSTED_EXTERNAL_PATHS = (
    '~/.agents/skills/t-*/**',
    '~/.claude/skills/t-*/**',
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
    if name=='t-think': return CORE
    return (ROOT/'agents'/name/'AGENT.md').read_text().rstrip()+f"\n\n## Platform note\n\n{PLATFORM_NOTES[current_platform]}\n"
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
    profile='# launch with: codex --profile t-think\nsandbox_mode = "workspace-write"\napproval_policy = "never"\ndeveloper_instructions = '+tq(CORE+note)+'\n\n[agents]\nmax_depth = 1\nmax_threads = 4\ninterrupt_message = true\n'
    (out/'t-think.config.toml').write_text(profile)
    for name,a in AGENTS.items():
        sandbox='workspace-write'
        (workers/f'{name}.toml').write_text(f'name = "{name}"\ndescription = {tq(a["description"])}\nsandbox_mode = "{sandbox}"\ndeveloper_instructions = {tq(body(name))}\n')
def claude_tools(name):
    if name=='t-think': return f"Agent({', '.join(NAMES)}), Read, Grep, Glob, Bash, Skill, Write, Edit"
    return 'Read, Grep, Glob, Bash, Skill, Write, Edit'
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
