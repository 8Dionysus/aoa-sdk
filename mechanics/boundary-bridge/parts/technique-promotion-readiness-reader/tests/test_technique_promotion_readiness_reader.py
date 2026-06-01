from pathlib import Path

from aoa_sdk import AoASDK


def test_techniques_promotion_readiness_local_read_path(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    readiness_entries = sdk.techniques.promotion_readiness()
    canonical_entry = sdk.techniques.promotion_readiness("AOA-T-0001")
    promoted_entry = sdk.techniques.promotion_readiness("repo-doc-surface-lift")

    assert readiness_entries[0].technique_id == "AOA-T-0001"
    assert readiness_entries[0].technique_name == "plan-diff-apply-verify-report"
    assert len(readiness_entries) >= 90
    assert canonical_entry.status == "canonical"
    assert canonical_entry.readiness_passed is True
    assert promoted_entry.technique_id == "AOA-T-0046"
    assert promoted_entry.status == "promoted"
    assert promoted_entry.readiness_passed is False
    assert promoted_entry.blockers == ["missing_canonical_readiness_note"]
