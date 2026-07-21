#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import tomllib
from pathlib import Path

import yaml

PLATFORMS = ("opencode", "codex", "claude", "cursor")
OPENCODE_TRUSTED_EXTERNAL = (
    "~/.config/opencode/skills/t-*/**",
    "~/.local/share/t-think/runtime/**",
)
FORBIDDEN_SHARED_MARKERS = (".agents/skills", ".claude/skills")


def frontmatter(path: Path):
    match = re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
    if not match:
        raise ValueError("missing YAML frontmatter")
    return yaml.safe_load(match.group(1))


def _walk_permission_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_permission_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_permission_values(item)
    else:
        yield value


def expected_skill_root(home: Path, platform: str) -> Path:
    if platform == "opencode":
        return home / ".config/opencode/skills"
    if platform == "codex":
        return home / ".codex/t-think/skills"
    if platform == "claude":
        return home / ".claude/t-think/skills"
    return home / ".cursor/t-think/skills"


def check_no_legacy_shared_skills(home: Path, skill_names: list[str], errors: list[str]) -> None:
    for root in (home / ".agents/skills", home / ".claude/skills"):
        for name in skill_names:
            if (root / name).exists() or (root / name).is_symlink():
                errors.append(f"legacy shared t-think skill remains: {root / name}")
            for backup in root.glob(f"{name}.bak-*"):
                errors.append(f"legacy installer backup remains: {backup}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--target", choices=["all", *PLATFORMS], default="all")
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    errors: list[str] = []

    manifest_path = home / ".local/share/t-think/installation-manifest.json"
    runtime = home / ".local/share/t-think/runtime"
    if not manifest_path.exists():
        errors.append("missing installation manifest")
        manifest = {"targets": [], "installed": [], "platform_skill_roots": {}}
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema_version") != "2.0.0":
            errors.append("installation manifest is not platform-isolated schema 2.0.0")
        if manifest.get("backups"):
            errors.append("installation manifest contains persistent backups")

    for required in [
        "VERSION",
        "bin/t-thinkctl.py",
        "bin/tthink_paths.py",
        "bin/validate_delegation.py",
        "bin/audit_boundaries.py",
        "bin/validate_result.py",
        "orchestrator/agent-registry.yaml",
        "orchestrator/phase-registry.yaml",
        "orchestrator/composite-phase-policy.yaml",
        "orchestrator/intake-policy.yaml",
        "orchestrator/workspace-hygiene-policy.yaml",
        "orchestrator/tool-permission-policy.yaml",
        "schemas/delegation-packet.schema.json",
        "schemas/workspace-hygiene-report.schema.json",
    ]:
        if not (runtime / required).exists():
            errors.append(f"missing runtime component: {required}")

    worker_names: list[str] = []
    registry = runtime / "orchestrator/agent-registry.yaml"
    if registry.exists():
        worker_names = [
            item["name"]
            for item in yaml.safe_load(registry.read_text(encoding="utf-8"))["agents"]
        ]
    names = ["t-think", *worker_names]
    expected_agents = len(names)
    skill_names = sorted(
        {
            item.get("name")
            for item in manifest.get("installed", [])
            if item.get("kind") == "platform-skill" and item.get("name")
        }
    )
    targets = list(PLATFORMS) if args.target == "all" else [args.target]

    check_no_legacy_shared_skills(home, skill_names, errors)
    transaction_root = home / ".local/share/t-think/.transactions"
    if transaction_root.exists() and any(transaction_root.iterdir()):
        errors.append(f"stale install transaction remains: {transaction_root}")

    for platform in targets:
        configured = manifest.get("platform_skill_roots", {}).get(platform)
        expected_root = expected_skill_root(home, platform)
        if not configured:
            errors.append(f"missing manifest skill root for {platform}")
            skill_root = expected_root
        else:
            skill_root = Path(configured)
            if skill_root.resolve() != expected_root.resolve():
                errors.append(
                    f"{platform} skill root is not platform-private: {skill_root} != {expected_root}"
                )
        if skill_root.exists() and list(skill_root.glob("t-*.bak-*")):
            errors.append(f"persistent installer backup remains in {skill_root}")
        found_skills = sorted(skill_root.glob("t-*/SKILL.md")) if skill_root.exists() else []
        if len(found_skills) != len(skill_names):
            errors.append(
                f"expected {len(skill_names)} {platform} skills in {skill_root}, found {len(found_skills)}"
            )
        for skill_file in found_skills:
            try:
                data = frontmatter(skill_file)
                if data.get("name") != skill_file.parent.name:
                    errors.append(f"name/folder mismatch: {skill_file}")
                if not (skill_file.parent / "RESOURCE_INDEX.md").is_file():
                    errors.append(f"missing resource index: {skill_file.parent}")
            except Exception as error:
                errors.append(f"invalid skill {skill_file}: {error}")

    dirs = {
        "opencode": home / ".config/opencode/agents",
        "claude": home / ".claude/agents",
        "cursor": home / ".cursor/agents",
    }
    for platform in targets:
        expected_root_text = str(expected_skill_root(home, platform))
        if platform == "codex":
            profile = home / ".codex/t-think.config.toml"
            workers = home / ".codex/agents"
            found = list(workers.glob("t-*.toml"))
            if not profile.exists():
                errors.append("missing Codex root profile")
            if len(found) != len(worker_names):
                errors.append(
                    f"expected {len(worker_names)} Codex workers, found {len(found)}"
                )
            codex_files = [profile, *found]
            for file in codex_files:
                if not file.exists():
                    continue
                text = file.read_text(encoding="utf-8")
                if expected_root_text not in text:
                    errors.append(f"{file}: missing Codex-private skill root")
                if "__T_THINK_PLATFORM_SKILL_ROOT__" in text:
                    errors.append(f"{file}: unresolved skill-root token")
            if profile.exists():
                try:
                    data = tomllib.loads(profile.read_text(encoding="utf-8"))
                    if data.get("agents", {}).get("max_depth") != 1:
                        errors.append("Codex max_depth must be 1")
                    if (
                        data.get("approval_policy") != "never"
                        or data.get("sandbox_mode") != "workspace-write"
                    ):
                        errors.append("Codex prompt-free workspace profile invalid")
                    if "model" in data or "model_reasoning_effort" in data:
                        errors.append("Codex root pins model")
                except Exception as error:
                    errors.append(f"invalid Codex profile: {error}")
            continue

        found = list(dirs[platform].glob("t-*.md"))
        if len(found) != expected_agents:
            errors.append(
                f"expected {expected_agents} {platform} agents, found {len(found)}"
            )
        for name in names:
            file = dirs[platform] / f"{name}.md"
            if not file.exists():
                errors.append(f"missing {platform} agent: {name}")
                continue
            try:
                data = frontmatter(file)
                text = file.read_text(encoding="utf-8")
                if platform in ("claude", "cursor") and data.get("name") != name:
                    errors.append(f"{platform}/{name} name mismatch")
                if "__T_THINK_PLATFORM_SKILL_ROOT__" in text:
                    errors.append(f"{platform}/{name} unresolved skill-root token")
                if platform == "opencode":
                    if data.get("mode") != ("primary" if name == "t-think" else "subagent"):
                        errors.append(f"opencode/{name} mode mismatch")
                    permission = data.get("permission", {})
                    external = permission.get("external_directory")
                    if not isinstance(external, dict) or external.get("*") != "deny":
                        errors.append(
                            f"opencode/{name} external_directory must deny by default"
                        )
                    else:
                        for pattern in OPENCODE_TRUSTED_EXTERNAL:
                            if external.get(pattern) != "allow":
                                errors.append(
                                    f"opencode/{name} missing recursive external allow: {pattern}"
                                )
                        for forbidden in (
                            "~/.agents/skills/t-*/**",
                            "~/.claude/skills/t-*/**",
                        ):
                            if forbidden in external:
                                errors.append(
                                    f"opencode/{name} trusts cross-platform skill root: {forbidden}"
                                )
                    if permission.get("*") != "allow":
                        errors.append(
                            f"opencode/{name} global tool default must allow"
                        )
                    if any(
                        value == "ask"
                        for value in _walk_permission_values(permission)
                    ):
                        errors.append(f"opencode/{name} contains ask permission")
                    bash = permission.get("bash", {})
                    if not isinstance(bash, dict) or bash.get("*") != "allow":
                        errors.append(
                            f"opencode/{name} bash must allow normal worktree commands"
                        )
                    elif (
                        bash.get("git") != "deny"
                        or bash.get("git *") != "deny"
                        or bash.get("gh") != "deny"
                        or bash.get("gh *") != "deny"
                    ):
                        errors.append(f"opencode/{name} Git/GH boundary invalid")
                    edit = permission.get("edit", {})
                    if (
                        not isinstance(edit, dict)
                        or edit.get("*") != "allow"
                        or edit.get(".git/**") != "deny"
                    ):
                        errors.append(f"opencode/{name} edit profile invalid")
                    if expected_root_text.replace(str(home), "~") not in text and "~/.config/opencode/skills" not in text:
                        errors.append(f"opencode/{name} missing OpenCode-only skill source")
                if platform == "claude":
                    if data.get("permissionMode") != "bypassPermissions":
                        errors.append(
                            f"claude/{name} permission mode is not bypassPermissions"
                        )
                    if "Skill" in str(data.get("tools", "")):
                        errors.append(
                            f"claude/{name} still exposes global Skill discovery"
                        )
                    if expected_root_text not in text:
                        errors.append(f"claude/{name} missing Claude-private skill root")
                    if name != "t-think" and "Agent" in str(data.get("tools", "")):
                        errors.append(f"claude/{name} can nest")
                if platform == "cursor":
                    if data.get("readonly") is not False:
                        errors.append(f"cursor/{name} remains readonly")
                    if expected_root_text not in text:
                        errors.append(f"cursor/{name} missing Cursor-private skill root")
            except Exception as error:
                errors.append(f"invalid {platform}/{name}: {error}")

    print(
        json.dumps(
            {
                "status": "FAIL" if errors else "PASS",
                "skills_per_platform": len(skill_names),
                "role_workers": len(worker_names),
                "targets": targets,
                "errors": errors,
            },
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
