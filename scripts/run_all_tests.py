#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
REPORTS = ROOT / "reports"

COMMANDS = {
    "t-problem-alignment": {
        "validate": [
            ["python3", "validators/validate.py", "--kind", "input", "--file", "examples/valid-input.yaml"],
            ["python3", "validators/validate.py", "--kind", "output", "--file", "examples/valid-output-approved.yaml", "--require-transition-ready"],
        ],
        "test": [["python3", "-m", "unittest", "discover", "-s", "tests", "-v"]],
    },
    "t-investigation": {"validate": [["make", "validate"]], "test": [["make", "test"]]},
    "t-system-modeling": {"validate": [["make", "validate"]], "test": [["make", "test"]]},
    "t-model-critique": {"validate": [["make", "validate"]], "test": [["make", "test"]]},
    "t-solution-design": {"validate": [["make", "validate-transition"], ["make", "validate-single"]], "test": [["make", "test"]]},
    "t-solution-critique": {"validate": [["make", "schemas"], ["make", "validate-example"]], "test": [["make", "test"]]},
    "t-implementation-planning": {"validate": [["make", "schemas"], ["make", "validate-example"], ["make", "validate-routes"]], "test": [["make", "test"]]},
    "t-plan-critique": {"validate": [["make", "validate-schemas"], ["make", "validate-example"]], "test": [["make", "test"]]},
    "t-checklist-builder": {"validate": [["make", "validate"]], "test": [["make", "test"]]},
    "t-checklist-critique": {"validate": [["make", "schema"], ["make", "validate"], ["make", "validate-routes"]], "test": [["make", "test"]]},
    "t-bounded-implementation": {"validate": [["make", "validate"]], "test": [["make", "test"]]},
    "t-self-review": {"validate": [["make", "validate"], ["make", "loopback"]], "test": [["make", "test"]]},
    "t-technical-review": {"validate": [["make", "validate"]], "test": [["make", "test"]]},
    "t-verification": {"validate": [["make", "schemas"], ["make", "validate"], ["make", "validate-loopback"]], "test": [["make", "test"]]},
    "t-reconciliation": {"validate": [["make", "schemas"], ["make", "validate"]], "test": [["make", "test"]]},
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["validate", "test"], required=True)
    parser.add_argument("--skill", action="append", help="Run only the named skill; may be repeated")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--report-name", help="Optional report filename without directory")
    args = parser.parse_args()

    selected = args.skill or list(COMMANDS)
    unknown = sorted(set(selected) - set(COMMANDS))
    if unknown:
        print(f"Unknown skills: {unknown}", file=sys.stderr)
        return 2

    REPORTS.mkdir(exist_ok=True)
    results = []
    failed = False
    for skill_name in selected:
        workdir = SKILLS / skill_name
        for command in COMMANDS[skill_name][args.mode]:
            print(f"[{args.mode}] {skill_name}: {' '.join(command)}", flush=True)
            started = time.monotonic()
            proc = subprocess.run(
                command,
                cwd=workdir,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=args.timeout,
                check=False,
            )
            elapsed = round(time.monotonic() - started, 3)
            print(proc.stdout, end="")
            result = {
                "skill": skill_name,
                "mode": args.mode,
                "command": command,
                "exit_code": proc.returncode,
                "elapsed_seconds": elapsed,
                "output": proc.stdout,
            }
            results.append(result)
            if proc.returncode != 0:
                failed = True
                print(f"FAILED: {skill_name}: {' '.join(command)}", file=sys.stderr)
                break
        if failed:
            break

    report_path = REPORTS / (args.report_name or f"{args.mode}-report.json")
    report_path.write_text(json.dumps({"status": "FAIL" if failed else "PASS", "results": results}, indent=2) + "\n")
    if failed:
        return 1
    print(f"{args.mode.upper()} PASS: {len(results)} command(s) across {len(selected)} skill(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
