from aoa_sdk.cli.common import OWNER_CHECKPOINT_HOOK_REPOS
from aoa_sdk.checkpoints.registry import OWNER_MUTABLE_REPOS
from aoa_sdk.release.api import OWNER_RELEASE_REPOS
from aoa_sdk.workspace.roots import KNOWN_REPOS, WORKSPACE_OPTIONAL_REPOS


def test_dashboard_discovery_does_not_grant_mutation_authority() -> None:
    assert "aoa-dashboard" in KNOWN_REPOS
    assert "aoa-dashboard" in WORKSPACE_OPTIONAL_REPOS
    assert "aoa-dashboard" not in OWNER_MUTABLE_REPOS
    assert "aoa-dashboard" not in OWNER_CHECKPOINT_HOOK_REPOS
    assert "aoa-dashboard" not in OWNER_RELEASE_REPOS
