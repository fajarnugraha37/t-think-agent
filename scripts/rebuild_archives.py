#!/usr/bin/env python3
from __future__ import annotations
import shutil, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"archives"; OUT.mkdir(exist_ok=True)
for old in OUT.glob("*.zip"): old.unlink()
for skill in sorted((ROOT/"skills").iterdir()):
    if not skill.is_dir(): continue
    target=OUT/f"{skill.name}.zip"
    with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(skill.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix!=".pyc": z.write(p,Path(skill.name)/p.relative_to(skill))
    print(target.name)
