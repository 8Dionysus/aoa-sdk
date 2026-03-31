from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson

from ..errors import SurfaceNotFound


def load_json(path: str | Path) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        raise SurfaceNotFound(f"JSON surface not found: {file_path}")

    return orjson.loads(file_path.read_bytes())


def write_json(path: str | Path, payload: Any) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
