from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "validators" / "validate.py"
EX = ROOT / "examples"


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class ValidatorTests(unittest.TestCase):
    def test_valid_input(self) -> None:
        result = run_validator("--kind", "input", "--file", str(EX / "valid-input.yaml"))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_valid_transition_ready_package(self) -> None:
        result = run_validator(
            "--kind", "package",
            "--file", str(EX / "valid-output-ready.yaml"),
            "--elements", str(EX / "valid-model-elements.jsonl"),
            "--relations", str(EX / "valid-model-relations.jsonl"),
            "--traceability", str(EX / "valid-traceability-matrix.csv"),
            "--ledger", str(EX / "valid-evidence-ledger.jsonl"),
            "--require-transition-ready",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("transition-ready", result.stdout)

    def test_partial_coverage_is_rejected(self) -> None:
        result = run_validator(
            "--kind", "package",
            "--file", str(EX / "invalid-output-partial-coverage.yaml"),
            "--elements", str(EX / "valid-model-elements.jsonl"),
            "--relations", str(EX / "valid-model-relations.jsonl"),
            "--traceability", str(EX / "valid-traceability-matrix.csv"),
            "--ledger", str(EX / "valid-evidence-ledger.jsonl"),
            "--require-transition-ready",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("must be FULL", result.stderr)

    def test_dangling_evidence_is_rejected(self) -> None:
        result = run_validator(
            "--kind", "package",
            "--file", str(EX / "valid-output-ready.yaml"),
            "--elements", str(EX / "invalid-model-elements-dangling-evidence.jsonl"),
            "--relations", str(EX / "valid-model-relations.jsonl"),
            "--traceability", str(EX / "valid-traceability-matrix.csv"),
            "--ledger", str(EX / "valid-evidence-ledger.jsonl"),
            "--require-transition-ready",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("F-999", result.stderr)

    def test_dangling_relation_endpoint_is_rejected(self) -> None:
        result = run_validator(
            "--kind", "package",
            "--file", str(EX / "valid-output-ready.yaml"),
            "--elements", str(EX / "valid-model-elements.jsonl"),
            "--relations", str(EX / "invalid-model-relations-dangling-endpoint.jsonl"),
            "--traceability", str(EX / "valid-traceability-matrix.csv"),
            "--ledger", str(EX / "valid-evidence-ledger.jsonl"),
            "--require-transition-ready",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("MDL-999", result.stderr)

    def test_valid_element_file(self) -> None:
        result = run_validator("--kind", "element", "--file", str(EX / "valid-model-elements.jsonl"))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_valid_relation_file(self) -> None:
        result = run_validator("--kind", "relation", "--file", str(EX / "valid-model-relations.jsonl"))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_valid_traceability_file(self) -> None:
        result = run_validator("--kind", "traceability", "--file", str(EX / "valid-traceability-matrix.csv"))
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
