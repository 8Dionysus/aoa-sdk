from pathlib import Path

from aoa_sdk import AoASDK


def test_evals_local_read_path(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    listed = sdk.evals.list(category="artifact")
    capsule = sdk.evals.inspect("aoa-bounded-change-quality")
    expanded = sdk.evals.expand("aoa-bounded-change-quality", sections=["verification"])
    comparison = sdk.evals.comparison_entries(name="aoa-regression-same-task")

    assert [item.name for item in listed] == ["aoa-bounded-change-quality"]
    assert capsule.name == "aoa-bounded-change-quality"
    assert [section.key for section in expanded.sections] == ["verification"]
    assert comparison.baseline_mode == "fixed-baseline"
