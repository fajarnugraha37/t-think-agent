#!/usr/bin/env python3
"""Cross-platform discovery and resolution of installed t-think skill resources."""
from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = re.compile(r"^t-[a-z0-9]+(?:-[a-z0-9]+)*$")
FORBIDDEN_TOKENS = ("~", "$HOME", "${HOME}", "%USERPROFILE%")


def validate_skill_name(name: str) -> str:
    if not SKILL_NAME.fullmatch(name):
        raise ValueError(f"invalid t-think skill name: {name!r}")
    return name


def validate_resource_identifier(resource: str) -> PurePosixPath:
    if not resource or resource.strip() != resource:
        raise ValueError("resource identifier must be a non-empty trimmed relative path")
    if "\\" in resource:
        raise ValueError("resource identifier must use '/' separators, never backslashes")
    if any(token.lower() in resource.lower() for token in FORBIDDEN_TOKENS):
        raise ValueError("resource identifier must not contain a home-directory token")
    if re.match(r"^[A-Za-z]:", resource) or PureWindowsPath(resource).is_absolute():
        raise ValueError("resource identifier must not contain a Windows drive or absolute path")
    raw_parts = resource.split("/")
    if any(part in ("", ".", "..") for part in raw_parts):
        raise ValueError("resource identifier must be a normalized contained relative path")
    path = PurePosixPath(resource)
    if path.is_absolute():
        raise ValueError("resource identifier must be a normalized contained relative path")
    return path


def installation_manifest(home: Path) -> dict | None:
    path = home / ".local" / "share" / "t-think" / "installation-manifest.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_skill_roots(name: str, home: Path | None = None) -> list[Path]:
    validate_skill_name(name)
    resolved_home = (home or Path.home()).expanduser().resolve()
    candidates: list[Path] = []

    source = ROOT / "skills" / name
    if source.is_dir():
        candidates.append(source)

    manifest = installation_manifest(resolved_home)
    if manifest:
        for item in manifest.get("installed", []):
            if item.get("kind") in {"skill", "claude-skill-view"} and item.get("name") == name:
                path = Path(item["path"]).expanduser()
                if path not in candidates:
                    candidates.append(path)

    for path in (
        resolved_home / ".agents" / "skills" / name,
        resolved_home / ".claude" / "skills" / name,
        resolved_home / ".config" / "opencode" / "skills" / name,
        resolved_home / ".cursor" / "skills" / name,
    ):
        if path not in candidates:
            candidates.append(path)
    return candidates


def find_skill_root(name: str, home: Path | None = None) -> Path:
    checked = candidate_skill_roots(name, home)
    for path in checked:
        if (path / "SKILL.md").is_file():
            return path.resolve()
    rendered = ", ".join(str(path) for path in checked)
    raise FileNotFoundError(f"skill {name!r} was not found; checked: {rendered}")


def resolve_skill_resource(name: str, resource: str, home: Path | None = None) -> Path:
    relative = validate_resource_identifier(resource)
    root = find_skill_root(name, home)
    target = root.joinpath(*relative.parts).resolve()
    try:
        target.relative_to(root)
    except ValueError as error:
        raise ValueError("resolved resource escapes the skill root") from error
    if not target.is_file():
        raise FileNotFoundError(f"skill resource does not exist: {target}")
    return target


def platform_examples(name: str, resource: str) -> dict[str, str]:
    relative = validate_resource_identifier(resource)
    posix = PurePosixPath("/home/user/.agents/skills") / name / relative
    mac = PurePosixPath("/Users/user/.agents/skills") / name / relative
    windows = PureWindowsPath(r"C:\Users\user\.agents\skills") / name / PureWindowsPath(*relative.parts)
    return {"linux": str(posix), "macos": str(mac), "windows": str(windows)}
