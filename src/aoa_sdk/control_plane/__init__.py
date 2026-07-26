"""Agent OS control-plane implementation families.

The SDK coordinates typed decisions and lifecycle clients. Runtime execution
stays behind external adapter boundaries.
"""

from .api import ControlPlaneAPI

__all__ = ["ControlPlaneAPI"]
