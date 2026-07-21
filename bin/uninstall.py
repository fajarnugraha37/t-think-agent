#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,shutil
from pathlib import Path

def main():
    p=argparse.ArgumentParser(); p.add_argument('--home',type=Path,default=Path.home()); p.add_argument('--restore-backups',action='store_true')
    a=p.parse_args(); home=a.home.expanduser().resolve(); state_root=home/'.local/share/t-think'; mf=state_root/'installation-manifest.json'
    if not mf.exists(): print('No t-think installation manifest found'); return 0
    data=json.loads(mf.read_text())
    for item in reversed(data.get('installed',[])):
        path=Path(item['path'])
        if path.is_symlink() or path.is_file(): path.unlink(missing_ok=True)
        elif path.is_dir(): shutil.rmtree(path)
    if a.restore_backups:
        for b in reversed(data.get('backups',[])):
            dst=Path(b['destination']); backup=Path(b['backup'])
            if backup.exists() and not dst.exists(): backup.rename(dst)
    mf.unlink(missing_ok=True)
    try: state_root.rmdir()
    except OSError: pass
    print('t-think uninstalled')
if __name__=='__main__': raise SystemExit(main())
