from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "agon_vds_sdk_helper_candidates.seed.json"
OUTPUT = ROOT / "generated" / "agon_vds_sdk_helper_candidates.min.json"


def compact(obj: dict) -> str:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def build_registry() -> dict:
    seed = json.loads(CONFIG.read_text(encoding="utf-8"))
    return {
        "registry_id": seed["registry_id"],
        "version": seed["version"],
        "wave": seed["wave"],
        "status": seed["status"],
        "live_protocol": False,
        "runtime_effect": "none",
        "helper_count": len(seed["helpers"]),
        "helpers": seed["helpers"],
        "stop_lines": seed["stop_lines"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = compact(build_registry())

    if args.check:
        assert OUTPUT.exists(), f"missing {OUTPUT}"
        assert (
            OUTPUT.read_text(encoding="utf-8") == rendered
        ), "generated agon_vds_sdk_helper_candidates.min.json is stale"
        print("agon_vds_sdk_helper_candidates.min.json is up to date")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
