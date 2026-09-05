"""Public SDK entrypoint without initializing unrelated facades on leaf imports."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .api import AoASDK

__all__ = ["AoASDK"]


def __getattr__(name: str) -> object:
    if name != "AoASDK":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .api import AoASDK

    globals()[name] = AoASDK
    return AoASDK


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
