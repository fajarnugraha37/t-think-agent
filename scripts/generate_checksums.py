#!/usr/bin/env python3
from __future__ import annotations
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"CHECKSUMS.sha256"
rows=[]
for p in sorted(ROOT.rglob("*")):
    if p.is_file() and p!=OUT and "__pycache__" not in p.parts and p.suffix!=".pyc":
        rows.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}")
OUT.write_text("\n".join(rows)+"\n")
print(f"wrote {len(rows)} checksums")
