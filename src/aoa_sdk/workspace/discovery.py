from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

@dataclass(slots=True)
class Workspace:
    root: Path

    @classmethod
    def discover(cls, root: str | Path) -> "Workspace":
        return cls(Path(root).expanduser().resolve())
