from pathlib import Path

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.errors import InvalidSurface


def test_generic_routing_rejects_skills_and_points_to_exact_inspection_and_kag(
    workspace_root: Path,
) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    calls = (
        lambda: sdk.routing.pick(kind="skill", query="durable repository decision"),
        lambda: sdk.routing.inspect(kind="skill", id_or_name="aoa-decision"),
        lambda: sdk.routing.expand(kind="skill", id_or_name="aoa-decision"),
    )
    for call in calls:
        with pytest.raises(InvalidSurface, match="exact owner-surface inspection.*KAG"):
            call()

    assert [entry.name for entry in sdk.skills.catalog().skills] == ["aoa-decision"]
    assert sdk.skills.capability("skill.aoa-decision").node.owner.repo == "aoa-skills"


def test_stats_regrounding_hints_read_routing_advisory_surface(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    payload = sdk.routing.stats_regrounding_hints_payload()
    hints = sdk.routing.stats_regrounding_hints(
        surface_name="core_skill_application_summary",
    )

    assert payload.coverage_thin_signal_flags == []
    assert [hint.hint_id for hint in hints] == [
        "stats-reground:core_skill_application_summary",
    ]
    assert hints[0].advisory_only is True
    assert hints[0].primary_action.target_repo == "aoa-skills"
    assert [action.target_repo for action in hints[0].secondary_actions] == [
        "aoa-stats",
        "aoa-stats",
    ]
    assert "fallback_actions" not in hints[0].model_dump()
