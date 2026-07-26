"""Deterministic SDK routing producer with explicit authority postures.

Import :mod:`aoa_sdk.control_plane.routing.shadow`,
:mod:`aoa_sdk.control_plane.routing.candidate`,
:mod:`aoa_sdk.control_plane.routing.release_candidate`, or
:mod:`aoa_sdk.control_plane.routing.canonical` explicitly. Keeping package
import side effects empty also makes module command execution deterministic.
"""
