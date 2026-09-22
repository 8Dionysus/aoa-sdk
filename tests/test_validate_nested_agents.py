from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_nested_agents.py"
SPEC = importlib.util.spec_from_file_location("validate_nested_agents", SCRIPT_PATH)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_minimal_required_tree(repo_root: Path) -> None:
    _write(
        repo_root / "AGENTS.md",
        "# AGENTS.md\n## Checks\n"
        "Use [the procedure](VALIDATION.md); scripts/release_check.py owns the gate.\n",
    )
    _write(repo_root / "VALIDATION.md", "# Checks\nRoot procedure route.\n")
    _write(repo_root / "scripts/release_check.py", "# Executable gate fixture.\n")
    _write(
        repo_root / "DESIGN.AGENTS.md",
        "# Agent guidance design\nSee VALIDATION.md for executable procedures.\n",
    )
    # The map supplies the coverage fixture, not the semantic oracle.
    # Independently authored prose must pass without repeating validator phrases.
    for rel_path in validator.REQUIRED_AGENTS_DOCS:
        _write(repo_root / rel_path, "# AGENTS.md\nLocal source owners retain authority.\n")


class ValidateNestedAgentsTests(unittest.TestCase):
    def test_structural_tree_does_not_require_editorial_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            result = validator.validate(repo_root)
            self.assertEqual((), result.issues)

    def test_safe_route_label_and_guidance_rewording_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            _write(
                repo_root / "AGENTS.md",
                "# AGENTS.md\n## Verification\n"
                "Follow [checks for the selected path](./VALIDATION.md#focused-checks).\n"
                "The executable gate is scripts/release_check.py.\n",
            )
            _write(
                repo_root / "src/aoa_sdk/AGENTS.md",
                "# AGENTS.md\nSDK facades expose typed handles, not sibling authority.\n",
            )
            self.assertEqual((), validator.validate(repo_root).issues)

    def test_missing_root_agents_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = validator.validate(Path(tmp))
            self.assertIn("AGENTS.md: root guidance file is missing", result.issues)

    def test_root_validation_route_requires_clickable_owner(self) -> None:
        for route in (
            "VALIDATION.md", "[Checks](elsewhere.md)", "[Checks](VALIDATION.md.bak)",
            "![Checks](VALIDATION.md)", "```text\n[Checks](VALIDATION.md)\n```",
            "`[Checks](VALIDATION.md)`", "<!-- [Checks](VALIDATION.md) -->",
        ):
            with self.subTest(route=route), tempfile.TemporaryDirectory() as tmp:
                repo_root = Path(tmp)
                _write_minimal_required_tree(repo_root)
                _write(
                    repo_root / "AGENTS.md",
                    f"# AGENTS.md\n{route}; scripts/release_check.py owns the gate.\n",
                )
                self.assertIn(
                    "AGENTS.md: root validation route must link to VALIDATION.md",
                    validator.validate(repo_root).issues,
                )

    def test_reference_style_validation_route_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            _write(
                repo_root / "AGENTS.md",
                "# AGENTS.md\n[The procedure][checks]. scripts/release_check.py owns the gate.\n"
                "\n[checks]: ./VALIDATION.md#focused-checks\n",
            )
            self.assertEqual((), validator.validate(repo_root).issues)

    def test_named_route_and_required_documents_cannot_disappear(self) -> None:
        # These expected locations are independent of the implementation's map.
        for relative, expected in (
            ("src/aoa_sdk/AGENTS.md", "src/aoa_sdk/AGENTS.md: required nested AGENTS.md is missing"),
            ("tests/AGENTS.md", "tests/AGENTS.md: required nested AGENTS.md is missing"),
            ("VALIDATION.md", "VALIDATION.md: root human validation entrypoint is missing"),
            ("DESIGN.AGENTS.md", "DESIGN.AGENTS.md: design surface is missing"),
            ("scripts/release_check.py", "scripts/release_check.py: root executable gate is missing"),
        ):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as tmp:
                repo_root = Path(tmp)
                _write_minimal_required_tree(repo_root)
                (repo_root / relative).unlink()
                self.assertIn(expected, validator.validate(repo_root).issues)

    def test_required_card_must_have_agents_heading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            _write(repo_root / "tests/AGENTS.md", "This is not an agent route card.\n")
            self.assertIn(
                "tests/AGENTS.md: missing AGENTS heading",
                validator.validate(repo_root).issues,
            )

    def test_root_gate_and_design_procedure_routes_are_retained(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            _write(
                repo_root / "AGENTS.md",
                "# AGENTS.md\n[Checks](VALIDATION.md)\nSee scripts/release_check.py.bak.\n",
            )
            _write(repo_root / "DESIGN.AGENTS.md", "# Design\nSee VALIDATION.md.bak.\n")
            issues = validator.validate(repo_root).issues
            self.assertIn(
                "AGENTS.md: root validation route missing 'scripts/release_check.py'", issues
            )
            self.assertIn(
                "DESIGN.AGENTS.md: validation procedures do not route through VALIDATION.md",
                issues,
            )

    def test_unmapped_card_and_advisory_directory_escalate_only_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            _write(repo_root / "new-district/AGENTS.md", "# AGENTS.md\nLocal route.\n")
            (repo_root / "examples").mkdir()
            result = validator.validate(repo_root)
            self.assertEqual((), result.issues)
            self.assertEqual(2, len(result.warnings))
            self.assertTrue(validator.validate(repo_root, fail_on_untracked=True).issues)
            self.assertEqual(
                result.warnings, validator.validate(repo_root, strict_advisory=True).issues
            )

    def test_runnable_procedures_are_rejected_in_root_and_nested_cards(self) -> None:
        fence = chr(96) * 3
        inline = chr(96)
        cases = (
            (f"{fence}bash\npython -m pytest -q\n{fence}\n", "runnable procedure fence"),
            ("1. python -m pytest -q\n", "runnable command line"),
            (f"Use {inline}FOO=bar $ python -m pytest -q{inline}.\n", "inline runnable command"),
        )
        for relative in ("AGENTS.md", "tests/AGENTS.md"):
            for content, expected in cases:
                with self.subTest(relative=relative, expected=expected):
                    with tempfile.TemporaryDirectory() as tmp:
                        repo_root = Path(tmp)
                        _write_minimal_required_tree(repo_root)
                        path = repo_root / relative
                        _write(path, path.read_text(encoding="utf-8") + content)
                        self.assertTrue(any(
                            expected in issue for issue in validator.validate(repo_root).issues
                        ))

    def test_source_path_mentions_and_non_command_code_are_allowed(self) -> None:
        fence = chr(96) * 3
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            _write(
                repo_root / "tests/AGENTS.md",
                "# AGENTS.md\nSee src/aoa_sdk/ and tests/ for source and checks.\n"
                f"{fence}python\nfrom aoa_sdk import AoASDK\n{fence}\n",
            )
            self.assertEqual((), validator.validate(repo_root).issues)


if __name__ == "__main__":
    unittest.main()
