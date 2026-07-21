#!/usr/bin/env python3
from __future__ import annotations
import tomllib
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
REG=yaml.safe_load((ROOT/'orchestrator/agent-registry.yaml').read_text())
CORE=(ROOT/'orchestrator/t-think-core.md').read_text().rstrip()+"\n"
AGENTS={a['name']:a for a in REG['agents']}
NAMES=[a['name'] for a in REG['agents']]

PLATFORM_NOTES={
 'opencode':'Use the Skill tool to load exactly the delegated phase skill. Respect native permissions and return control to t-think; never invoke another subagent.',
 'codex':'Use global Agent Skills from $HOME/.agents/skills. The parent session owns orchestration. Do not spawn child agents.',
 'claude-code':'Load the active skill through the Skill tool. The Agent tool is intentionally omitted from worker definitions, so nested delegation is unavailable.',
 'cursor':'Use globally installed Agent Skills. Keep this worker foreground and return one bounded result to t-think. Do not delegate recursively.',
}

def body(name:str)->str:
    if name=='t-think': return CORE
    text=(ROOT/'agents'/name/'AGENT.md').read_text().rstrip()+"\n"
    return text+f"\n## Platform note\n\n{PLATFORM_NOTES[current_platform]}\n"

def dump_frontmatter(data:dict)->str:
    return '---\n'+yaml.safe_dump(data,sort_keys=False,width=120).strip()+'\n---\n'

def write_opencode():
    global current_platform; current_platform='opencode'
    out=ROOT/'adapters/opencode'; out.mkdir(parents=True,exist_ok=True)
    task={'*':'deny', **{n:'allow' for n in NAMES}}
    primary={
      'description':'Govern an evidence-gated multi-agent software change with deterministic routing, human gates, bounded writes, independent review, verification, and reconciliation.',
      'mode':'primary','temperature':0.1,
      'permission':{'read':'allow','glob':'allow','grep':'allow','list':'allow','skill':'allow','edit':'ask','bash':'ask','external_directory':'deny','task':task}
    }
    (out/'t-think.md').write_text(dump_frontmatter(primary)+body('t-think')+'\n## OpenCode adapter\n\nDelegate only to the eight allowlisted `t-*` subagents. Use sequential delegation in economy mode.\n')
    for name,a in AGENTS.items():
        sw=a['permissions']['source_write']['mode']
        perm={'read':'allow','glob':'allow','grep':'allow','list':'allow','skill':'allow','external_directory':'deny','task':'deny'}
        if sw=='approved_targets_only':
            perm['edit']='ask'; perm['bash']='ask'
        elif sw=='generated_outputs_only':
            perm['edit']='deny'; perm['bash']='ask'
        else:
            perm['edit']='deny'; perm['bash']='ask' if a['permissions']['command_policy']!='read-only' else 'ask'
        fm={'description':a['description'],'mode':'subagent','temperature':0.1,'permission':perm}
        (out/f'{name}.md').write_text(dump_frontmatter(fm)+body(name))

def toml_quote(s:str)->str:
    return '"""'+s.replace('"""','\\"\\"\\"')+'"""'

def write_codex():
    """Generate a root-session profile plus eight depth-1 custom workers.

    Codex custom agents are spawned sessions. Therefore t-think must be the
    root session selected with ``codex --profile t-think``; otherwise a
    t-think custom child at depth 1 could not spawn its workers while
    ``agents.max_depth = 1`` is enforced.
    """
    global current_platform; current_platform='codex'
    out=ROOT/'adapters/codex'; workers=out/'agents'
    workers.mkdir(parents=True,exist_ok=True)
    profile_note='\n## Codex adapter\n\nThis configuration runs `t-think` as the root session selected with `codex --profile t-think`. Spawn only the eight registered role agents. Keep delegation depth at one; workers are terminal children. The economy lifecycle profile delegates sequentially even though the native thread ceiling permits bounded read-only parallelism in other profiles.\n'
    profile=(
        '# t-think root-session profile; launch with: codex --profile t-think\n'
        'sandbox_mode = "workspace-write"\n'
        'approval_policy = "on-request"\n'
        f'developer_instructions = {toml_quote(CORE + profile_note)}\n\n'
        '[agents]\n'
        'max_depth = 1\n'
        'max_threads = 4\n'
        'interrupt_message = true\n'
    )
    (out/'t-think.config.toml').write_text(profile)
    for name,a in AGENTS.items():
        desc=a['description']
        sandbox='workspace-write' if name in ('t-builder','t-verifier') else 'read-only'
        content=f'name = "{name}"\ndescription = {toml_quote(desc)}\nsandbox_mode = "{sandbox}"\ndeveloper_instructions = {toml_quote(body(name))}\n'
        (workers/f'{name}.toml').write_text(content)

def claude_tools(name:str)->str:
    if name=='t-think':
        return 'Agent(t-investigator, t-modeler, t-planner, t-critic, t-builder, t-reviewer, t-verifier, t-reconciler), Read, Grep, Glob, Bash, Skill, Write, Edit'
    if name=='t-builder': return 'Read, Grep, Glob, Bash, Skill, Write, Edit'
    return 'Read, Grep, Glob, Bash, Skill'

def write_claude():
    global current_platform; current_platform='claude-code'
    out=ROOT/'adapters/claude-code'; out.mkdir(parents=True,exist_ok=True)
    all_defs=[('t-think',{'description':'Govern an evidence-gated multi-agent software change end to end.'})]+list(AGENTS.items())
    for name,a in all_defs:
        fm={'name':name,'description':a['description'],'model':'inherit','tools':claude_tools(name),'permissionMode':'default'}
        (out/f'{name}.md').write_text(dump_frontmatter(fm)+body(name))

def write_cursor():
    global current_platform; current_platform='cursor'
    out=ROOT/'adapters/cursor'; out.mkdir(parents=True,exist_ok=True)
    all_defs=[('t-think',{'description':'Govern an evidence-gated multi-agent software change end to end.'})]+list(AGENTS.items())
    for name,a in all_defs:
        readonly=name not in ('t-think','t-builder','t-verifier')
        fm={'name':name,'description':a['description'],'model':'inherit','readonly':readonly,'is_background':False}
        (out/f'{name}.md').write_text(dump_frontmatter(fm)+body(name))

def main():
    import shutil
    for d in [ROOT/'adapters/opencode',ROOT/'adapters/codex',ROOT/'adapters/claude-code',ROOT/'adapters/cursor']:
        if d.exists(): shutil.rmtree(d)
        d.mkdir(parents=True,exist_ok=True)
    write_opencode(); write_codex(); write_claude(); write_cursor()
    print('generated 36 platform adapter artifacts (9 OpenCode, 1 Codex root profile + 8 workers, 9 Claude Code, 9 Cursor)')
if __name__=='__main__': main()
