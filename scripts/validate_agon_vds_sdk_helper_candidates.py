from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "generated" / "agon_vds_sdk_helper_candidates.min.json"


def validate() -> dict:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert data["registry_id"] == "agon.vds_sdk_helper_candidates.registry.v1"
    assert data["wave"] == "XI"
    assert data["live_protocol"] is False
    assert data["runtime_effect"] == "none"
    assert data["helper_count"] >= 6

    for item in data["helpers"]:
        assert item.get("must_not_emit")
        assert item.get("may_emit") is not None

    assert "no_runtime_transition" in data["stop_lines"]
    for helper in data["helpers"]:
        may_emit = helper.get("may_emit", [])
        assert "runtime_state_transition" not in may_emit
        assert "live_verdict" not in may_emit

    return data


if __name__ == "__main__":
    data = validate()
    print(
        "validated {count} VDS SDK helper candidates".format(
            count=data["helper_count"]
        )
    )
