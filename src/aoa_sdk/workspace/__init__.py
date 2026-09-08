"""Workspace discovery and bootstrap entrypoints with lazy leaf imports."""

from typing import TYPE_CHECKING

from .discovery import Workspace

if TYPE_CHECKING:
    from .bootstrap import bootstrap_workspace
    from .os_profile import bootstrap_os_profile

__all__ = ["Workspace", "bootstrap_workspace", "bootstrap_os_profile"]


def __getattr__(name: str) -> object:
    if name == "bootstrap_workspace":
        from .bootstrap import bootstrap_workspace

        globals()[name] = bootstrap_workspace
        return bootstrap_workspace
    if name == "bootstrap_os_profile":
        from .os_profile import bootstrap_os_profile

        globals()[name] = bootstrap_os_profile
        return bootstrap_os_profile
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
