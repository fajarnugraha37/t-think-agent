#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,shutil
from pathlib import Path


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


def prune_empty(path: Path, stop: Path) -> None:
    current=path
    while current != stop and stop in current.parents:
        try:
            current.rmdir()
        except OSError:
            break
        current=current.parent


def main() -> int:
    parser=argparse.ArgumentParser(description='Uninstall manifest-owned t-think files')
    parser.add_argument('--home',type=Path,default=Path.home())
    parser.add_argument('--restore-backups',action='store_true',help='Compatibility no-op for pre-2.5 manifests')
    args=parser.parse_args()
    home=args.home.expanduser().resolve()
    state_root=home/'.local/share/t-think'
    manifest_path=state_root/'installation-manifest.json'
    if not manifest_path.exists():
        print('No t-think installation manifest found')
        return 0
    data=json.loads(manifest_path.read_text(encoding='utf-8'))
    installed=[Path(item['path']) for item in data.get('installed',[])]
    for path in reversed(installed):
        remove_path(path)
    if args.restore_backups:
        for item in reversed(data.get('backups',[])):
            destination=Path(item['destination']); backup=Path(item['backup'])
            if backup.exists() and not destination.exists():
                backup.rename(destination)
    manifest_path.unlink(missing_ok=True)
    shutil.rmtree(state_root/'.transactions',ignore_errors=True)

    # Remove only empty t-think-owned parent directories; preserve unrelated config.
    roots=[Path(value) for value in data.get('platform_skill_roots',{}).values()]
    for root in roots:
        prune_empty(root,home)
    for path in (
        home/'.config/opencode/agents',
        home/'.codex/agents',
        home/'.claude/agents',
        home/'.cursor/agents',
        home/'.codex/t-think',
        home/'.claude/t-think',
        home/'.cursor/t-think',
        state_root/'runtime',
        state_root,
    ):
        prune_empty(path,home)
    print('t-think uninstalled')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
