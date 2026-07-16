from __future__ import annotations

from pathlib import Path
from shutil import copytree
from typing import Callable

import pytest


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "src" / "aoa_sdk"
        ).is_dir():
            return candidate
    raise RuntimeError(f"could not find aoa-sdk repo root from {start}")


FIXTURE_WORKSPACE = find_repo_root(Path(__file__).resolve()) / "tests" / "fixtures" / "workspace"
RUNTIME_IDENTITY_ENV_KEYS = (
    "AOA_RUNTIME_SESSION_FILE",
    "AOA_SESSION_CREATED_AT",
    "AOA_SESSION_ID",
    "CODEX_ROLLOUT_PATH",
    "CODEX_THREAD_ID",
)


@pytest.fixture(autouse=True)
def isolate_host_runtime_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep mechanics tests from inheriting the live Codex session."""

    for key in RUNTIME_IDENTITY_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture()
def workspace_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    copytree(FIXTURE_WORKSPACE, tmp_path, dirs_exist_ok=True)
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def install_host_skills() -> Callable[[Path, list[str], str], Path]:
    def _install(
        workspace_root: Path, skill_names: list[str], scope: str = "workspace"
    ) -> Path:
        if scope == "workspace":
            install_root = workspace_root / ".agents" / "skills"
        elif scope == "repo":
            install_root = workspace_root / "aoa-sdk" / ".agents" / "skills"
        else:
            raise ValueError(f"unsupported install scope {scope!r}")

        for skill_name in skill_names:
            skill_dir = install_root / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                skill_file.write_text(f"# {skill_name}\n", encoding="utf-8")
        return install_root

    return _install
