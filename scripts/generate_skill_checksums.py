#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    skills = sorted(path for path in (ROOT / "skills").glob("t-*") if path.is_dir())
    total = 0
    for skill in skills:
        output = skill / "CHECKSUMS.sha256"
        rows = []
        for path in sorted(skill.rglob("*")):
            if not path.is_file() or path == output or "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            rows.append(f"{digest}  {path.relative_to(skill).as_posix()}")
        output.write_text("\n".join(rows) + "\n", encoding="utf-8")
        total += len(rows)
        print(f"{skill.name}: {len(rows)} checksums")
    print(f"wrote {total} per-skill checksum entries across {len(skills)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
