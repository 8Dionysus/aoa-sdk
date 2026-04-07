from __future__ import annotations

from pathlib import Path
from shutil import copytree
from typing import Callable

import pytest


FIXTURE_WORKSPACE = Path(__file__).parent / "fixtures" / "workspace"


@pytest.fixture()
def workspace_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    copytree(FIXTURE_WORKSPACE, tmp_path, dirs_exist_ok=True)
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def install_host_skills() -> Callable[[Path, list[str], str], Path]:
    def _install(workspace_root: Path, skill_names: list[str], scope: str = "workspace") -> Path:
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
