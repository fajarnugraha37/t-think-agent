#!/usr/bin/env python3
"""Generate portable resource indexes and contracts for every t-think skill."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
START = "<!-- BEGIN T-THINK PORTABLE RESOURCE CONTRACT -->"
END = "<!-- END T-THINK PORTABLE RESOURCE CONTRACT -->"
RESOURCE_DIRS = ("templates", "schemas", "validators", "orchestrator", "docs", "examples")


def resource_files(skill: Path) -> list[Path]:
    files: list[Path] = []
    for directory in RESOURCE_DIRS:
        base = skill / directory
        if not base.exists():
            continue
        files.extend(
            path
            for path in base.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix not in {".pyc", ".pyo"}
        )
    return sorted(files, key=lambda path: path.relative_to(skill).as_posix())


def write_index(skill: Path, files: list[Path]) -> None:
    groups: dict[str, list[str]] = {}
    for path in files:
        relative = path.relative_to(skill).as_posix()
        groups.setdefault(relative.split("/", 1)[0], []).append(relative)

    lines = [
        f"# Portable Resource Index — {skill.name}",
        "",
        "All links are relative to the directory containing `SKILL.md`. They are canonical POSIX-style resource identifiers, not user-home or operating-system paths.",
        "",
    ]
    for directory in RESOURCE_DIRS:
        entries = groups.get(directory, [])
        if not entries:
            continue
        lines.extend([f"## {directory.title()}", ""])
        lines.extend(f"- [`{entry}`]({entry})" for entry in entries)
        lines.append("")
    (skill / "RESOURCE_INDEX.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def contract(skill: Path) -> str:
    common = []
    for relative in (
        "templates/input.template.yaml",
        "templates/output.template.yaml",
        "schemas/input.schema.json",
        "schemas/output.schema.json",
        "validators/validate.py",
    ):
        if (skill / relative).is_file():
            common.append(f"- [`{relative}`]({relative})")
    common_text = "\n".join(common) if common else "- See the generated [resource index](RESOURCE_INDEX.md)."
    return f"""{START}
## Portable resource contract

- Resolve every bundled resource relative to the directory containing this `SKILL.md`.
- Read the generated [resource index](RESOURCE_INDEX.md) before opening templates, schemas, validators, examples, or supporting documentation.
- Treat linked `/`-separated paths as portable relative resource identifiers. Never construct a global path with `~`, `$HOME`, `%USERPROFILE%`, a drive letter, or backslashes.
- Prefer the host's native skill/resource loader. When an absolute filesystem path is unavoidable, join the platform-reported skill root and the relative identifier with the host path API; never concatenate path strings manually.
- If a required resource cannot be opened, return `BLOCKED` with reason `SKILL_RESOURCE_UNAVAILABLE`. Do not recreate a template from memory, infer its shape, or continue with an invented format.

Frequently required resources:

{common_text}
{END}"""


def update_skill(skill: Path) -> None:
    files = resource_files(skill)
    write_index(skill, files)
    path = skill / "SKILL.md"
    text = path.read_text(encoding="utf-8").rstrip()
    block = contract(skill)
    if START in text:
        before, rest = text.split(START, 1)
        if END not in rest:
            raise ValueError(f"unterminated portable resource contract: {path}")
        _, after = rest.split(END, 1)
        text = before.rstrip() + "\n\n" + block + after
    else:
        text += "\n\n" + block
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    skills = sorted(path for path in SKILLS.glob("t-*") if path.is_dir())
    for skill in skills:
        update_skill(skill)
    print(f"updated portable resource contracts and indexes for {len(skills)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
