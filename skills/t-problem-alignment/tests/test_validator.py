from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "validators" / "validate.py"
SPEC = importlib.util.spec_from_file_location("problem_alignment_validator", VALIDATOR_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ValidatorTests(unittest.TestCase):
    def test_valid_input(self) -> None:
        issues = VALIDATOR.validate("input", ROOT / "examples" / "valid-input.yaml")
        self.assertEqual([], [str(issue) for issue in issues])

    def test_valid_draft_output(self) -> None:
        issues = VALIDATOR.validate("output", ROOT / "examples" / "valid-output-draft.yaml")
        self.assertEqual([], [str(issue) for issue in issues])

    def test_valid_approved_output_is_transition_ready(self) -> None:
        issues = VALIDATOR.validate(
            "output",
            ROOT / "examples" / "valid-output-approved.yaml",
            require_transition_ready=True,
        )
        self.assertEqual([], [str(issue) for issue in issues])

    def test_invalid_output_is_rejected(self) -> None:
        issues = VALIDATOR.validate(
            "output",
            ROOT / "examples" / "invalid-output-hidden-assumption.yaml",
            require_transition_ready=True,
        )
        self.assertTrue(issues)
        messages = "\n".join(str(issue) for issue in issues)
        self.assertIn("contains_root_cause_hypothesis", messages)


if __name__ == "__main__":
    unittest.main()
