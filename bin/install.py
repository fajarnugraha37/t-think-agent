#!/usr/bin/env python3
from __future__ import annotations
import argparse, filecmp, json, os, shutil, sys, time
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
SKILLS=ROOT/'skills'; ADAPTERS=ROOT/'adapters'
PLATFORMS=('opencode','codex','claude','cursor')
RUNTIME_DIRS=('bin','orchestrator','schemas','templates','agents')

def same_content(src:Path,dst:Path)->bool:
    """Return true when an existing copy is byte-for-byte equivalent."""
    if dst.is_symlink():
        try: return dst.resolve()==src.resolve()
        except OSError: return False
    if src.is_file() and dst.is_file():
        return filecmp.cmp(src,dst,shallow=False)
    if not (src.is_dir() and dst.is_dir()): return False
    src_entries={p.relative_to(src).as_posix():p for p in src.rglob('*') if p.is_file() or p.is_symlink()}
    dst_entries={p.relative_to(dst).as_posix():p for p in dst.rglob('*') if p.is_file() or p.is_symlink()}
    if src_entries.keys()!=dst_entries.keys(): return False
    for key,sp in src_entries.items():
        dp=dst_entries[key]
        if sp.is_symlink() or dp.is_symlink():
            if not (sp.is_symlink() and dp.is_symlink() and sp.readlink()==dp.readlink()): return False
        elif not filecmp.cmp(sp,dp,shallow=False): return False
    return True

def copy_or_link(src:Path,dst:Path,mode:str,force:bool,backups:list[dict]):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists() or dst.is_symlink():
        if same_content(src,dst): return 'unchanged'
        if not force: raise RuntimeError(f'Destination exists with different content: {dst}. Use --force to back it up and replace it.')
        backup=dst.with_name(dst.name+f'.bak-{time.time_ns()}')
        dst.rename(backup); backups.append({'destination':str(dst),'backup':str(backup)})
    if mode=='symlink': dst.symlink_to(src,target_is_directory=src.is_dir())
    elif src.is_dir(): shutil.copytree(src,dst)
    else: shutil.copy2(src,dst)
    return 'installed'

def platform_files(platform:str):
    source_name='claude-code' if platform=='claude' else platform
    if platform=='codex':
        return [(ADAPTERS/'codex/t-think.config.toml','profile'), *[(f,'agent') for f in sorted((ADAPTERS/'codex/agents').glob('t-*.toml'))]]
    return [(f,'agent') for f in sorted((ADAPTERS/source_name).glob('t-*.md'))]

def adapter_destination(home:Path,platform:str,src:Path,kind:str)->Path:
    if platform=='opencode': return home/'.config/opencode/agents'/src.name
    if platform=='codex' and kind=='profile': return home/'.codex/t-think.config.toml'
    if platform=='codex': return home/'.codex/agents'/src.name
    if platform=='claude': return home/'.claude/agents'/src.name
    return home/'.cursor/agents'/src.name

def main():
    p=argparse.ArgumentParser(description='Install t-think and all role subagents globally')
    p.add_argument('--target',action='append',choices=[*PLATFORMS,'all'],default=[])
    p.add_argument('--mode',choices=['copy','symlink'],default='copy')
    p.add_argument('--home',type=Path,default=Path.home())
    p.add_argument('--force',action='store_true')
    a=p.parse_args(); targets=set(PLATFORMS if not a.target or 'all' in a.target else a.target)
    if os.name=='nt' and a.mode=='symlink': raise RuntimeError('Use copy mode on Windows unless developer symlink privileges are configured.')
    home=a.home.expanduser().resolve(); backups=[]; installed=[]
    state_root=home/'.local/share/t-think'; runtime=state_root/'runtime'
    for part in RUNTIME_DIRS:
        src=ROOT/part; dst=runtime/part
        installed.append({'kind':'runtime','name':part,'path':str(dst),'status':copy_or_link(src,dst,a.mode,a.force,backups)})
    version_dst=runtime/'VERSION'
    installed.append({'kind':'runtime','name':'VERSION','path':str(version_dst),'status':copy_or_link(ROOT/'VERSION',version_dst,a.mode,a.force,backups)})
    shared=home/'.agents/skills'
    for skill in sorted(SKILLS.glob('t-*')):
        if skill.is_dir():
            dst=shared/skill.name
            installed.append({'kind':'skill','name':skill.name,'path':str(dst),'status':copy_or_link(skill,dst,a.mode,a.force,backups)})
    worker_count=len([x for x in (ROOT/'agents').iterdir() if x.is_dir()])
    for platform in sorted(targets):
        files=platform_files(platform)
        expected=worker_count+1
        if len(files)!=expected: raise RuntimeError(f'Expected {expected} {platform} adapter artifacts, found {len(files)}')
        for src,kind in files:
            dst=adapter_destination(home,platform,src,kind)
            name='t-think' if kind=='profile' else src.stem
            installed.append({'kind':kind,'platform':platform,'name':name,'path':str(dst),'status':copy_or_link(src,dst,a.mode,a.force,backups)})
    if 'claude' in targets:
        for skill in sorted(SKILLS.glob('t-*')):
            if skill.is_dir():
                src=shared/skill.name; dst=home/'.claude/skills'/skill.name
                mode='symlink' if os.name!='nt' else 'copy'
                installed.append({'kind':'claude-skill-view','name':skill.name,'path':str(dst),'status':copy_or_link(src,dst,mode,a.force,backups)})
    manifest={'schema_version':'1.0.0','bundle_version':(ROOT/'VERSION').read_text().strip(),'bundle_root':str(ROOT),'runtime_root':str(runtime),'mode':a.mode,'targets':sorted(targets),'installed':installed,'backups':backups}
    schema=json.loads((ROOT/'schemas/installation-manifest.schema.json').read_text())
    errs=list(Draft202012Validator(schema).iter_errors(manifest))
    if errs: raise RuntimeError('Installation manifest invalid: '+'; '.join(e.message for e in errs))
    state_root.mkdir(parents=True,exist_ok=True)
    (state_root/'installation-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2)); return 0
if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as exc: print(f'INSTALL FAILED: {exc}',file=sys.stderr); raise SystemExit(1)
