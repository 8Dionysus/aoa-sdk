from __future__ import annotations

from pathlib import Path
from shutil import copytree

import pytest


FIXTURE_WORKSPACE = Path(__file__).parent / "fixtures" / "workspace"


@pytest.fixture()
def workspace_root(tmp_path: Path) -> Path:
    copytree(FIXTURE_WORKSPACE, tmp_path, dirs_exist_ok=True)
    return tmp_path
