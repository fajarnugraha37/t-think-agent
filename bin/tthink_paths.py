#!/usr/bin/env python3
"""Cross-platform resolution of platform-isolated t-think skill resources."""
from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = re.compile(r"^t-[a-z0-9]+(?:-[a-z0-9]+)*$")
FORBIDDEN_TOKENS = ("~", "$HOME", "${HOME}", "%USERPROFILE%")
PLATFORMS = ("opencode", "codex", "claude", "cursor")


def validate_skill_name(name: str) -> str:
    if not SKILL_NAME.fullmatch(name):
        raise ValueError(f"invalid t-think skill name: {name!r}")
    return name


def validate_platform(platform: str) -> str:
    if platform not in PLATFORMS:
        raise ValueError(f"invalid platform: {platform!r}; expected one of {PLATFORMS}")
    return platform


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


def infer_platform(manifest: dict | None, platform: str | None) -> str:
    if platform:
        return validate_platform(platform)
    if manifest:
        targets = manifest.get("targets", [])
        if len(targets) == 1:
            return validate_platform(targets[0])
    raise ValueError(
        "platform is required when multiple t-think targets are installed; pass --platform"
    )


def configured_skill_root(home: Path, platform: str, manifest: dict | None) -> Path:
    validate_platform(platform)
    if manifest:
        configured = manifest.get("platform_skill_roots", {}).get(platform)
        if configured:
            return Path(configured).expanduser()
    # Deterministic fallbacks match the v2.5+ installer, never shared discovery.
    if platform == "opencode":
        return home / ".config/opencode/skills"
    if platform == "codex":
        return home / ".codex/t-think/skills"
    if platform == "claude":
        return home / ".claude/t-think/skills"
    return home / ".cursor/t-think/skills"


def candidate_skill_roots(
    name: str, home: Path | None = None, platform: str | None = None
) -> tuple[str, list[Path]]:
    validate_skill_name(name)
    resolved_home = (home or Path.home()).expanduser().resolve()
    manifest = installation_manifest(resolved_home)
    selected = infer_platform(manifest, platform)
    candidates: list[Path] = []
    configured = configured_skill_root(resolved_home, selected, manifest) / name

    # An installation manifest is authoritative: never fall back to the bundle
    # source tree and accidentally hide a missing or cross-platform install.
    if manifest:
        candidates.append(configured)
    else:
        source = ROOT / "skills" / name
        if source.is_dir():
            candidates.append(source)
        if configured not in candidates:
            candidates.append(configured)
    return selected, candidates


def find_skill_root(
    name: str, home: Path | None = None, platform: str | None = None
) -> tuple[str, Path]:
    selected, checked = candidate_skill_roots(name, home, platform)
    for path in checked:
        if (path / "SKILL.md").is_file():
            return selected, path.resolve()
    rendered = ", ".join(str(path) for path in checked)
    raise FileNotFoundError(
        f"skill {name!r} for platform {selected!r} was not found; checked: {rendered}"
    )


def resolve_skill_resource(
    name: str,
    resource: str,
    home: Path | None = None,
    platform: str | None = None,
) -> tuple[str, Path]:
    relative = validate_resource_identifier(resource)
    selected, root = find_skill_root(name, home, platform)
    target = root.joinpath(*relative.parts).resolve()
    try:
        target.relative_to(root)
    except ValueError as error:
        raise ValueError("resolved resource escapes the skill root") from error
    if not target.is_file():
        raise FileNotFoundError(f"skill resource does not exist: {target}")
    return selected, target


def _platform_base(platform: str, os_kind: str):
    validate_platform(platform)
    if os_kind == "windows":
        home = PureWindowsPath(r"C:\Users\user")
        mapping = {
            "opencode": home / ".config/opencode/skills",
            "codex": home / ".codex/t-think/skills",
            "claude": home / ".claude/t-think/skills",
            "cursor": home / ".cursor/t-think/skills",
        }
    else:
        prefix = "/Users/user" if os_kind == "macos" else "/home/user"
        home = PurePosixPath(prefix)
        mapping = {
            "opencode": home / ".config/opencode/skills",
            "codex": home / ".codex/t-think/skills",
            "claude": home / ".claude/t-think/skills",
            "cursor": home / ".cursor/t-think/skills",
        }
    return mapping[platform]


def platform_examples(name: str, resource: str, platform: str) -> dict[str, str]:
    validate_skill_name(name)
    relative = validate_resource_identifier(resource)
    linux = _platform_base(platform, "linux") / name / relative
    mac = _platform_base(platform, "macos") / name / relative
    windows = _platform_base(platform, "windows") / name / PureWindowsPath(*relative.parts)
    return {"linux": str(linux), "macos": str(mac), "windows": str(windows)}
