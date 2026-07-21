#!/usr/bin/env python3
from __future__ import annotations

import argparse
import filecmp
import json
import os
import shutil
import sys
import uuid
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
ADAPTERS = ROOT / "adapters"
PLATFORMS = ("opencode", "codex", "claude", "cursor")
RUNTIME_DIRS = ("bin", "orchestrator", "schemas", "templates", "agents")
SKILL_ROOT_TOKEN = "__T_THINK_PLATFORM_SKILL_ROOT__"


def same_content(src: Path, dst: Path) -> bool:
    if dst.is_symlink():
        try:
            return dst.resolve() == src.resolve()
        except OSError:
            return False
    if src.is_file() and dst.is_file():
        return filecmp.cmp(src, dst, shallow=False)
    if not (src.is_dir() and dst.is_dir()):
        return False
    src_entries = {
        p.relative_to(src).as_posix(): p
        for p in src.rglob("*")
        if p.is_file() or p.is_symlink()
    }
    dst_entries = {
        p.relative_to(dst).as_posix(): p
        for p in dst.rglob("*")
        if p.is_file() or p.is_symlink()
    }
    if src_entries.keys() != dst_entries.keys():
        return False
    for key, source in src_entries.items():
        target = dst_entries[key]
        if source.is_symlink() or target.is_symlink():
            if not (
                source.is_symlink()
                and target.is_symlink()
                and source.readlink() == target.readlink()
            ):
                return False
        elif not filecmp.cmp(source, target, shallow=False):
            return False
    return True


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


class InstallTransaction:
    def __init__(self, state_root: Path):
        self.root = state_root / ".transactions" / uuid.uuid4().hex
        self.root.mkdir(parents=True, exist_ok=True)
        self.replaced: list[tuple[Path, Path]] = []
        self.created: list[Path] = []

    def stage_existing(self, destination: Path) -> None:
        backup = self.root / f"backup-{len(self.replaced):04d}"
        backup.parent.mkdir(parents=True, exist_ok=True)
        destination.rename(backup)
        self.replaced.append((destination, backup))

    def record_created(self, destination: Path) -> None:
        self.created.append(destination)

    def rollback(self) -> None:
        for destination in reversed(self.created):
            remove_path(destination)
        for destination, backup in reversed(self.replaced):
            remove_path(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            backup.rename(destination)
        shutil.rmtree(self.root, ignore_errors=True)

    def commit(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        try:
            self.root.parent.rmdir()
        except OSError:
            pass


def copy_or_link(
    src: Path,
    dst: Path,
    mode: str,
    force: bool,
    transaction: InstallTransaction,
) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        if same_content(src, dst):
            return "unchanged"
        if not force:
            raise RuntimeError(
                f"Destination exists with different content: {dst}. Use --force to replace it atomically."
            )
        transaction.stage_existing(dst)
    if mode == "symlink":
        dst.symlink_to(src, target_is_directory=src.is_dir())
    elif src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    transaction.record_created(dst)
    return "installed"


def install_materialized_text(
    source: Path,
    destination: Path,
    replacements: dict[str, str],
    force: bool,
    transaction: InstallTransaction,
) -> str:
    text = source.read_text(encoding="utf-8")
    for token, value in replacements.items():
        text = text.replace(token, value)
    if SKILL_ROOT_TOKEN in text:
        raise RuntimeError(f"Unresolved adapter token in {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        if destination.is_file() and destination.read_text(encoding="utf-8") == text:
            return "unchanged"
        if not force:
            raise RuntimeError(
                f"Destination exists with different content: {destination}. Use --force to replace it atomically."
            )
        transaction.stage_existing(destination)
    destination.write_text(text, encoding="utf-8")
    transaction.record_created(destination)
    return "installed"



def adapter_skill_root_text(source: Path, root: Path) -> str:
    """Render an absolute root safely for the adapter's serialization format.

    TOML basic strings treat Windows backslashes as escape sequences,
    so materialized Codex files must double them. Markdown adapters can contain
    the native path verbatim inside code spans.
    """
    value = str(root)
    if source.suffix.lower() == ".toml":
        return value.replace("\\", "\\\\").replace('"', '\\"')
    return value

def platform_files(platform: str) -> list[tuple[Path, str]]:
    source_name = "claude-code" if platform == "claude" else platform
    if platform == "codex":
        return [
            (ADAPTERS / "codex/t-think.config.toml", "profile"),
            *[
                (file, "agent")
                for file in sorted((ADAPTERS / "codex/agents").glob("t-*.toml"))
            ],
        ]
    return [
        (file, "agent")
        for file in sorted((ADAPTERS / source_name).glob("t-*.md"))
    ]


def adapter_destination(home: Path, platform: str, src: Path, kind: str) -> Path:
    if platform == "opencode":
        return home / ".config/opencode/agents" / src.name
    if platform == "codex" and kind == "profile":
        return home / ".codex/t-think.config.toml"
    if platform == "codex":
        return home / ".codex/agents" / src.name
    if platform == "claude":
        return home / ".claude/agents" / src.name
    return home / ".cursor/agents" / src.name


def platform_skill_root(home: Path, platform: str) -> Path:
    if platform == "opencode":
        # Native OpenCode-only discovery path. Do not use Claude-compatible or
        # generic Agent Skills paths because OpenCode scans those too.
        return home / ".config/opencode/skills"
    if platform == "codex":
        # Platform-private resources. Codex agents read the exact SKILL.md path
        # declared in their materialized TOML instead of global ~/.agents scan.
        return home / ".codex/t-think/skills"
    if platform == "claude":
        # Deliberately not ~/.claude/skills: OpenCode scans that directory.
        return home / ".claude/t-think/skills"
    return home / ".cursor/t-think/skills"


def exact_skill_names() -> list[str]:
    return sorted(path.name for path in SKILLS.glob("t-*") if path.is_dir())


def legacy_installation_candidates(home: Path, skill_names: list[str]) -> list[tuple[Path, str]]:
    """Return only paths produced by pre-2.5 t-think installers.

    Exact canonical skill names are used for live directories. Backup cleanup is
    limited to canonical skill/role prefixes so unrelated user resources are not
    touched.
    """
    candidates: list[tuple[Path, str]] = []
    shared_roots = (home / ".agents/skills", home / ".claude/skills")
    managed_agent_roots = (
        home / ".config/opencode/agents",
        home / ".codex/agents",
        home / ".claude/agents",
        home / ".cursor/agents",
    )
    canonical_prefixes = set(skill_names)
    canonical_prefixes.update(path.name for path in (ROOT / "agents").iterdir() if path.is_dir())
    canonical_prefixes.add("t-think")

    for root in shared_roots:
        if not root.exists():
            continue
        for name in skill_names:
            live = root / name
            if live.exists() or live.is_symlink():
                candidates.append((live, "legacy-shared-skill"))
        for prefix in sorted(canonical_prefixes):
            for backup in sorted(root.glob(f"{prefix}.bak-*")):
                candidates.append((backup, "legacy-installer-backup"))

    for root in managed_agent_roots:
        if not root.exists():
            continue
        for prefix in sorted(canonical_prefixes):
            for backup in sorted(root.glob(f"{prefix}.bak-*")):
                candidates.append((backup, "legacy-installer-backup"))

    # Preserve order while removing duplicate paths.
    seen: set[Path] = set()
    result: list[tuple[Path, str]] = []
    for path, reason in candidates:
        if path not in seen:
            seen.add(path)
            result.append((path, reason))
    return result


def stage_legacy_installations(
    home: Path,
    skill_names: list[str],
    transaction: InstallTransaction,
) -> list[dict]:
    """Stage legacy shared copies for transactional removal.

    The old paths are moved under the private transaction directory. A failed
    install restores them; a successful commit deletes the transaction. No
    persistent sibling `.bak-*` directory is ever created.
    """
    migrations: list[dict] = []
    for path, reason in legacy_installation_candidates(home, skill_names):
        transaction.stage_existing(path)
        migrations.append({"path": str(path), "reason": reason})
    return migrations


def remove_empty_legacy_parents(home: Path) -> None:
    for path in (
        home / ".agents/skills",
        home / ".agents",
        home / ".claude/skills",
    ):
        try:
            path.rmdir()
        except OSError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install t-think with platform-isolated skill/resource roots"
    )
    parser.add_argument(
        "--target", action="append", choices=[*PLATFORMS, "all"], default=[]
    )
    parser.add_argument("--mode", choices=["copy", "symlink"], default="copy")
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--keep-legacy-shared-skills",
        action="store_true",
        help="Do not remove exact pre-2.5 t-think copies from ~/.agents/skills and ~/.claude/skills",
    )
    args = parser.parse_args()
    targets = set(
        PLATFORMS if not args.target or "all" in args.target else args.target
    )
    if os.name == "nt" and args.mode == "symlink":
        raise RuntimeError(
            "Use copy mode on Windows unless developer symlink privileges are configured."
        )

    home = args.home.expanduser().resolve()
    state_root = home / ".local/share/t-think"
    runtime = state_root / "runtime"
    transaction = InstallTransaction(state_root)
    committed = False
    installed: list[dict] = []
    migrations: list[dict] = []
    skill_names = exact_skill_names()
    roots = {platform: platform_skill_root(home, platform) for platform in sorted(targets)}

    try:
        for part in RUNTIME_DIRS:
            source = ROOT / part
            destination = runtime / part
            installed.append(
                {
                    "kind": "runtime",
                    "name": part,
                    "path": str(destination),
                    "status": copy_or_link(
                        source, destination, args.mode, args.force, transaction
                    ),
                }
            )
        version_destination = runtime / "VERSION"
        installed.append(
            {
                "kind": "runtime",
                "name": "VERSION",
                "path": str(version_destination),
                "status": copy_or_link(
                    ROOT / "VERSION",
                    version_destination,
                    args.mode,
                    args.force,
                    transaction,
                ),
            }
        )

        for platform in sorted(targets):
            root = roots[platform]
            for skill_name in skill_names:
                source = SKILLS / skill_name
                destination = root / skill_name
                installed.append(
                    {
                        "kind": "platform-skill",
                        "platform": platform,
                        "name": skill_name,
                        "path": str(destination),
                        "status": copy_or_link(
                            source, destination, args.mode, args.force, transaction
                        ),
                    }
                )

        worker_count = len(
            [item for item in (ROOT / "agents").iterdir() if item.is_dir()]
        )
        for platform in sorted(targets):
            files = platform_files(platform)
            expected = worker_count + 1
            if len(files) != expected:
                raise RuntimeError(
                    f"Expected {expected} {platform} adapter artifacts, found {len(files)}"
                )
            for source, kind in files:
                replacements = {
                    SKILL_ROOT_TOKEN: adapter_skill_root_text(source, roots[platform])
                }
                destination = adapter_destination(home, platform, source, kind)
                name = "t-think" if kind == "profile" else source.stem
                installed.append(
                    {
                        "kind": kind,
                        "platform": platform,
                        "name": name,
                        "path": str(destination),
                        "status": install_materialized_text(
                            source,
                            destination,
                            replacements,
                            args.force,
                            transaction,
                        ),
                    }
                )

        if not args.keep_legacy_shared_skills:
            migrations.extend(stage_legacy_installations(home, skill_names, transaction))

        manifest = {
            "schema_version": "2.0.0",
            "bundle_version": (ROOT / "VERSION").read_text().strip(),
            "bundle_root": str(ROOT),
            "runtime_root": str(runtime),
            "mode": args.mode,
            "targets": sorted(targets),
            "platform_skill_roots": {
                platform: str(root) for platform, root in roots.items()
            },
            "installed": installed,
            "backups": [],
            "migrations": migrations,
        }
        schema = json.loads(
            (ROOT / "schemas/installation-manifest.schema.json").read_text()
        )
        errors = list(Draft202012Validator(schema).iter_errors(manifest))
        if errors:
            raise RuntimeError(
                "Installation manifest invalid: "
                + "; ".join(error.message for error in errors)
            )
        state_root.mkdir(parents=True, exist_ok=True)
        manifest_path = state_root / "installation-manifest.json"
        if manifest_path.exists() or manifest_path.is_symlink():
            transaction.stage_existing(manifest_path)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        transaction.record_created(manifest_path)
        transaction.commit()
        committed = True
        if not args.keep_legacy_shared_skills:
            remove_empty_legacy_parents(home)

        print(json.dumps(manifest, indent=2))
        return 0
    except Exception:
        if not committed:
            transaction.rollback()
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"INSTALL FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
