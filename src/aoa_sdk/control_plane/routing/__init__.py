"""Deterministic SDK routing producer with explicit non-publishing postures.

Import :mod:`aoa_sdk.control_plane.routing.shadow` or
:mod:`aoa_sdk.control_plane.routing.candidate` explicitly. Keeping package
import side effects empty also makes module command execution deterministic.
"""
