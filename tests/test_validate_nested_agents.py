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
    _write(repo_root / "AGENTS.md", "# AGENTS.md\n## Validation route\nRoot [`VALIDATION.md`](VALIDATION.md) is the human procedure route; scripts/release_check.py and the accepted graph runner remain authoritative.\n")
    _write(repo_root / "VALIDATION.md", "# VALIDATION.md\nRoot procedure route.\n")
    _write(
        repo_root / "DESIGN.AGENTS.md",
        "# DESIGN.AGENTS.md\n## Conditional route shape\n"
        "## Relevant routes\n"
        "Executable procedures live in root VALIDATION.md.\n",
    )
    for rel_path, snippets in validator.REQUIRED_AGENTS_DOCS.items():
        _write(repo_root / rel_path, "# AGENTS.md\n" + "\n".join(snippets) + "\n")


class ValidateNestedAgentsTests(unittest.TestCase):
    def test_minimal_required_tree_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            result = validator.validate(repo_root)
            self.assertEqual((), result.issues)

    def test_stale_inherited_routes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            stale = next(iter(validator.REQUIRED_AGENTS_DOCS))
            _write(
                repo_root / stale,
                "# AGENTS.md\n" + validator.GENERIC_NESTED_ROUTE_PREFIX
                + validator.REPEATED_VALIDATION_PARAGRAPH + "\n",
            )
            result = validator.validate(repo_root)
            self.assertTrue(any("repeated repository validation route" in issue for issue in result.issues))
            self.assertTrue(any("repeated root conditional route" in issue for issue in result.issues))

    def test_missing_root_agents_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = validator.validate(Path(tmp))
            self.assertIn("AGENTS.md: root guidance file is missing", result.issues)

    def test_root_validation_route_requires_clickable_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            _write(
                repo_root / "AGENTS.md",
                "# AGENTS.md\n## Validation route\n"
                "VALIDATION.md owns procedure; scripts/release_check.py and the accepted graph runner remain authoritative.\n",
            )
            result = validator.validate(repo_root)
            self.assertIn(
                "AGENTS.md: root validation route must link to VALIDATION.md",
                result.issues,
            )

    def test_missing_required_doc_fails_when_required_docs_exist(self) -> None:
        if not validator.REQUIRED_AGENTS_DOCS:
            self.skipTest("repository has no required nested AGENTS.md docs yet")
        first_rel = next(iter(validator.REQUIRED_AGENTS_DOCS))
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            (repo_root / first_rel).unlink()
            result = validator.validate(repo_root)
            self.assertTrue(any(first_rel in issue for issue in result.issues))

    def test_missing_required_snippet_fails_when_required_docs_exist(self) -> None:
        if not validator.REQUIRED_AGENTS_DOCS:
            self.skipTest("repository has no required nested AGENTS.md docs yet")
        first_rel = next(iter(validator.REQUIRED_AGENTS_DOCS))
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            _write(repo_root / first_rel, "# AGENTS.md\nToo thin.\n")
            result = validator.validate(repo_root)
            self.assertTrue(any(first_rel in issue and "missing required snippet" in issue for issue in result.issues))

    def test_advisory_can_become_strict(self) -> None:
        if not validator.ADVISORY_AGENT_DIRS:
            self.skipTest("repository has no advisory AGENTS.md candidates")
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            (repo_root / validator.ADVISORY_AGENT_DIRS[0]).mkdir(parents=True, exist_ok=True)
            result = validator.validate(repo_root, strict_advisory=True)
            self.assertTrue(any("high-risk directory" in issue for issue in result.issues))

    def test_runnable_procedure_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            _write(
                repo_root / "AGENTS.md",
                "# AGENTS.md\n## Validation route\n" + chr(96) * 3 + "bash\npython -m pytest -q\n" + chr(96) * 3 + "\n",
            )
            result = validator.validate(repo_root)
            self.assertTrue(any("runnable procedure fence" in issue for issue in result.issues))

    def test_unconditional_readme_inventory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            _write(
                repo_root / "AGENTS.md",
                "# AGENTS.md\n## Relevant routes\nRead README.md before editing.\n",
            )
            result = validator.validate(repo_root)
            self.assertTrue(any("unconditional README inventory" in issue for issue in result.issues))

    def test_command_list_and_inline_command_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            _write_minimal_required_tree(repo_root)
            _write(
                repo_root / "AGENTS.md",
                "# AGENTS.md\n## Validation route\n"
                "1. python -m pytest -q\n"
                "Use `FOO=bar $ python -m pytest -q` when needed.\n",
            )
            result = validator.validate(repo_root)
            self.assertTrue(any("runnable command line" in issue for issue in result.issues))
            self.assertTrue(any("inline runnable command" in issue for issue in result.issues))


if __name__ == "__main__":
    unittest.main()
