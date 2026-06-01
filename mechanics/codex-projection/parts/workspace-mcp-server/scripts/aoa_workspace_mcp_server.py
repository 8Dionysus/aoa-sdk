from __future__ import annotations

import sys
from pathlib import Path

def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "aoa_sdk").is_dir():
            return candidate
    raise RuntimeError(f"could not locate aoa-sdk repository root from {start}")


REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aoa_sdk.codex.workspace_mcp import main  # noqa: E402


if __name__ == "__main__":
    main()
