#!/usr/bin/env python3
"""Audit portable paths, resource links, templates, and OpenCode permissions."""
from __future__ import annotations

import csv
import json
import re
import sys
import tomllib
import importlib.util
from pathlib import Path, PurePosixPath, PureWindowsPath

import yaml

ROOT = Path(__file__).resolve().parents[1]
RESOURCE_DIRS = ("templates", "schemas", "validators", "orchestrator", "docs", "examples")
START = "<!-- BEGIN T-THINK PORTABLE RESOURCE CONTRACT -->"
END = "<!-- END T-THINK PORTABLE RESOURCE CONTRACT -->"
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FORBIDDEN_PATH_PATTERNS = (
    (re.compile(r"~\\"), "home path uses a backslash after ~"),
    (re.compile(r"%USERPROFILE%\\", re.I), "USERPROFILE path is manually concatenated"),
    (re.compile(r"\b[A-Za-z]:\\(?:Users|Documents and Settings)\\", re.I), "hard-coded Windows user path"),
    (re.compile(r"(?:templates|schemas|validators|examples|docs)\\[A-Za-z0-9_.-]"), "skill resource uses backslashes"),
)
TRUSTED_EXTERNAL = [
    "~/.config/opencode/skills/t-*/**",
    "~/.local/share/t-think/runtime/**",
]
FORBIDDEN_SHARED_EXTERNAL = [
    "~/.agents/skills/t-*/**",
    "~/.claude/skills/t-*/**",
]


def local_link_target(raw: str) -> str | None:
    target = raw.split("#", 1)[0]
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return None
    return target


def validate_relative_identifier(value: str, context: str, issues: list[str]) -> None:
    if "\\" in value:
        issues.append(f"{context}: backslash in portable resource identifier {value!r}")
    if value.startswith(("/", "~", "$HOME", "${HOME}", "%USERPROFILE%")):
        issues.append(f"{context}: non-relative resource identifier {value!r}")
    if re.match(r"^[A-Za-z]:", value):
        issues.append(f"{context}: drive-qualified resource identifier {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        issues.append(f"{context}: non-normalized or escaping resource identifier {value!r}")


def validate_content(path: Path, issues: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
        suffix = path.suffix.lower()
        if suffix in {".yaml", ".yml"}:
            list(yaml.safe_load_all(text))
        elif suffix == ".json":
            json.loads(text)
        elif suffix == ".jsonl":
            for number, line in enumerate(text.splitlines(), 1):
                if line.strip():
                    json.loads(line)
        elif suffix == ".csv":
            list(csv.reader(text.splitlines()))
        elif suffix == ".py":
            compile(text, str(path), "exec")
    except Exception as error:
        issues.append(f"{path.relative_to(ROOT)}: invalid UTF-8 or structured content: {error}")


def audit_skill(skill: Path, issues: list[str]) -> tuple[int, int]:
    skill_md = skill / "SKILL.md"
    index = skill / "RESOURCE_INDEX.md"
    text = skill_md.read_text(encoding="utf-8")
    if START not in text or END not in text:
        issues.append(f"{skill.name}: missing portable resource contract")
    if not index.is_file():
        issues.append(f"{skill.name}: missing RESOURCE_INDEX.md")
        return 0, 0

    indexed: set[str] = set()
    index_text = index.read_text(encoding="utf-8")
    for source, markdown in ((skill_md, text), (index, index_text)):
        for raw in LINK.findall(markdown):
            target = local_link_target(raw)
            if target is None:
                continue
            validate_relative_identifier(target, str(source.relative_to(ROOT)), issues)
            resolved = (source.parent / Path(*PurePosixPath(target).parts)).resolve()
            try:
                resolved.relative_to(skill.resolve())
            except ValueError:
                issues.append(f"{source.relative_to(ROOT)}: link escapes skill root: {target}")
                continue
            if not resolved.exists():
                issues.append(f"{source.relative_to(ROOT)}: missing link target: {target}")
            if source == index:
                indexed.add(target)

    actual: set[str] = set()
    for directory in RESOURCE_DIRS:
        base = skill / directory
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            relative = path.relative_to(skill).as_posix()
            actual.add(relative)
            validate_content(path, issues)
    if actual != indexed:
        missing = sorted(actual - indexed)
        stale = sorted(indexed - actual)
        if missing:
            issues.append(f"{skill.name}: resources absent from RESOURCE_INDEX.md: {missing}")
        if stale:
            issues.append(f"{skill.name}: stale RESOURCE_INDEX.md links: {stale}")
    return len(actual), len(indexed)



def audit_repository_markdown_links(issues: list[str]) -> int:
    files = [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "MANIFEST.md"]
    files.extend(sorted((ROOT / "docs").rglob("*.md")))
    files.extend(sorted((ROOT / "skills").glob("t-*/README.md")))
    checked = 0
    for source in files:
        if not source.is_file():
            continue
        for raw in LINK.findall(source.read_text(encoding="utf-8")):
            target = local_link_target(raw)
            if target is None:
                continue
            # Root documentation may legitimately link to directories or files,
            # but never to a user-home, drive-qualified, or backslash path.
            validate_relative_identifier(target, str(source.relative_to(ROOT)), issues)
            resolved = source.parent.joinpath(*PurePosixPath(target).parts).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                issues.append(f"{source.relative_to(ROOT)}: documentation link escapes bundle: {target}")
                continue
            if not resolved.exists():
                issues.append(f"{source.relative_to(ROOT)}: missing documentation link target: {target}")
            checked += 1
    return checked

def audit_opencode(issues: list[str]) -> int:
    count = 0
    for adapter in sorted((ROOT / "adapters" / "opencode").glob("t-*.md")):
        count += 1
        match = re.match(r"---\n(.*?)\n---\n", adapter.read_text(encoding="utf-8"), re.S)
        if not match:
            issues.append(f"{adapter.relative_to(ROOT)}: missing frontmatter")
            continue
        data = yaml.safe_load(match.group(1))
        permission = data.get("permission", {})
        external = permission.get("external_directory")
        if not isinstance(external, dict):
            issues.append(f"{adapter.relative_to(ROOT)}: external_directory must be a path rule map")
            continue
        keys = list(external)
        if not keys or keys[0] != "*" or external.get("*") != "deny":
            issues.append(f"{adapter.relative_to(ROOT)}: external_directory must deny '*' first")
        for pattern in TRUSTED_EXTERNAL:
            if external.get(pattern) != "allow":
                issues.append(f"{adapter.relative_to(ROOT)}: missing recursive allow {pattern}")
        for pattern in FORBIDDEN_SHARED_EXTERNAL:
            if pattern in external:
                issues.append(f"{adapter.relative_to(ROOT)}: cross-platform shared allow present {pattern}")
        for pattern in keys:
            if pattern != "*" and not pattern.endswith("/**"):
                issues.append(f"{adapter.relative_to(ROOT)}: non-recursive external path pattern {pattern}")
        edit = permission.get("edit")
        if isinstance(edit, dict):
            for pattern in TRUSTED_EXTERNAL:
                if edit.get(pattern) != "deny":
                    issues.append(f"{adapter.relative_to(ROOT)}: trusted external resources must be edit-denied: {pattern}")
    return count


def audit_generated_path_literals(issues: list[str]) -> None:
    roots = [ROOT / "skills", ROOT / "adapters", ROOT / "agents", ROOT / "orchestrator"]
    files: list[Path] = []
    for root in roots:
        files.extend(path for path in root.rglob("*") if path.is_file() and path.suffix in {".md", ".yaml", ".yml", ".toml", ".json"})
    for path in files:
        text = path.read_text(encoding="utf-8")
        for pattern, label in FORBIDDEN_PATH_PATTERNS:
            if pattern.search(text):
                issues.append(f"{path.relative_to(ROOT)}: {label}")


def audit_cross_platform_semantics(issues: list[str]) -> dict[str, dict[str, str]]:
    sys.path.insert(0, str(ROOT / "bin"))
    from tthink_paths import platform_examples

    resource = "templates/output.template.yaml"
    expected = {
        "opencode": {
            "linux": "/home/user/.config/opencode/skills/t-reconciliation/templates/output.template.yaml",
            "macos": "/Users/user/.config/opencode/skills/t-reconciliation/templates/output.template.yaml",
            "windows": r"C:\Users\user\.config\opencode\skills\t-reconciliation\templates\output.template.yaml",
        },
        "codex": {
            "linux": "/home/user/.codex/t-think/skills/t-reconciliation/templates/output.template.yaml",
            "macos": "/Users/user/.codex/t-think/skills/t-reconciliation/templates/output.template.yaml",
            "windows": r"C:\Users\user\.codex\t-think\skills\t-reconciliation\templates\output.template.yaml",
        },
        "claude": {
            "linux": "/home/user/.claude/t-think/skills/t-reconciliation/templates/output.template.yaml",
            "macos": "/Users/user/.claude/t-think/skills/t-reconciliation/templates/output.template.yaml",
            "windows": r"C:\Users\user\.claude\t-think\skills\t-reconciliation\templates\output.template.yaml",
        },
        "cursor": {
            "linux": "/home/user/.cursor/t-think/skills/t-reconciliation/templates/output.template.yaml",
            "macos": "/Users/user/.cursor/t-think/skills/t-reconciliation/templates/output.template.yaml",
            "windows": r"C:\Users\user\.cursor\t-think\skills\t-reconciliation\templates\output.template.yaml",
        },
    }
    actual = {
        platform: platform_examples("t-reconciliation", resource, platform)
        for platform in expected
    }
    if actual != expected:
        issues.append(f"platform-isolated path joining mismatch: expected={expected}, actual={actual}")
    for platform, paths in actual.items():
        for os_kind, value in paths.items():
            normalized = value.replace("\\", "/")
            if "/.agents/skills/" in normalized:
                issues.append(f"{platform}/{os_kind}: shared .agents discovery leaked into path")
            if "/.claude/skills/" in normalized:
                issues.append(f"{platform}/{os_kind}: shared Claude skill discovery leaked into path")
    return actual



def audit_windows_codex_toml_materialization(issues: list[str]) -> int:
    spec = importlib.util.spec_from_file_location("tthink_installer", ROOT / "bin/install.py")
    if spec is None or spec.loader is None:
        issues.append("could not load installer for Windows TOML audit")
        return 0
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    windows_root = Path(str(PureWindowsPath(r"C:\Users\User Name\.codex\t-think\skills")))
    files = [ROOT / "adapters/codex/t-think.config.toml", *sorted((ROOT / "adapters/codex/agents").glob("t-*.toml"))]
    for source in files:
        rendered = source.read_text(encoding="utf-8").replace(
            module.SKILL_ROOT_TOKEN,
            module.adapter_skill_root_text(source, windows_root),
        )
        try:
            data = tomllib.loads(rendered)
        except Exception as error:
            issues.append(f"{source.relative_to(ROOT)}: Windows path breaks TOML: {error}")
            continue
        instructions = data.get("developer_instructions", "")
        expected_root = str(PureWindowsPath(r"C:\Users\User Name\.codex\t-think\skills"))
        if expected_root not in instructions:
            issues.append(f"{source.relative_to(ROOT)}: materialized Windows root missing after TOML parse")
    return len(files)


def audit_resolver_rejections(issues: list[str]) -> None:
    sys.path.insert(0, str(ROOT / "bin"))
    from tthink_paths import validate_resource_identifier

    invalid = [
        r"templates\output.template.yaml",
        "../templates/output.template.yaml",
        "/templates/output.template.yaml",
        "~/templates/output.template.yaml",
        "$HOME/templates/output.template.yaml",
        "%USERPROFILE%/templates/output.template.yaml",
        "C:/Users/user/templates/output.template.yaml",
        "templates/./output.template.yaml",
    ]
    for value in invalid:
        try:
            validate_resource_identifier(value)
        except ValueError:
            continue
        issues.append(f"resolver accepted forbidden resource identifier: {value!r}")
    valid = "templates/output.template.yaml"
    try:
        got = validate_resource_identifier(valid)
        if str(got) != valid:
            issues.append(f"resolver normalized canonical identifier unexpectedly: {got}")
    except Exception as error:
        issues.append(f"resolver rejected canonical identifier: {error}")

def main() -> int:
    issues: list[str] = []
    skills = sorted(path for path in (ROOT / "skills").glob("t-*") if path.is_dir())
    resources = 0
    indexed = 0
    for skill in skills:
        actual_count, indexed_count = audit_skill(skill, issues)
        resources += actual_count
        indexed += indexed_count
    documentation_links = audit_repository_markdown_links(issues)
    adapters = audit_opencode(issues)
    audit_generated_path_literals(issues)
    audit_resolver_rejections(issues)
    windows_codex_toml_files = audit_windows_codex_toml_materialization(issues)
    examples = audit_cross_platform_semantics(issues)
    report = {
        "status": "FAIL" if issues else "PASS",
        "skills": len(skills),
        "portable_resources": resources,
        "indexed_resources": indexed,
        "opencode_adapters": adapters,
        "documentation_links": documentation_links,
        "windows_codex_toml_files": windows_codex_toml_files,
        "platform_path_semantics": examples,
        "issues": issues,
    }
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "path-template-contract-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
