from __future__ import annotations

from pathlib import Path

import pytest

from aoa_sdk import AoASDK


LIVE_WORKSPACE_ROOT = Path("/srv/aoa-sdk")
LIVE_ABYSS_STACK_SOURCE = Path("~/src/abyss-stack").expanduser().resolve()


@pytest.mark.skipif(
    not LIVE_WORKSPACE_ROOT.exists() or not LIVE_ABYSS_STACK_SOURCE.exists(),
    reason="live /srv workspace or ~/src/abyss-stack source checkout is unavailable",
)
def test_live_workspace_prefers_home_src_abyss_stack_and_keeps_core_compat_green() -> None:
    sdk = AoASDK.from_workspace(LIVE_WORKSPACE_ROOT)
    report = {entry.surface_id: entry for entry in sdk.compatibility.check_all()}

    assert sdk.workspace.repo_path("abyss-stack") == LIVE_ABYSS_STACK_SOURCE
    assert sdk.workspace.repo_origins["abyss-stack"] == "manifest:repos.abyss-stack.preferred"
    assert report["aoa-techniques.technique_capsules"].compatible is True
    assert report["aoa-techniques.technique_sections.full"].compatible is True
    assert report["aoa-playbooks.playbook_federation_surfaces.min"].compatible is True
    assert report["aoa-kag.kag_registry.min"].compatible is True
    assert report["aoa-kag.tos_zarathustra_route_retrieval_pack.min"].compatible is True
