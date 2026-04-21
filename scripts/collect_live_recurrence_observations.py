from __future__ import annotations

import argparse
import json

from aoa_sdk.recurrence.api import RecurrenceAPI
from aoa_sdk.recurrence.io import persist_observation_packet
from aoa_sdk.workspace.discovery import Workspace


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect live recurrence observations from owner-authored surfaces."
    )
    parser.add_argument(
        "--workspace-root", default=".", help="Federation/workspace root."
    )
    parser.add_argument(
        "--producer", action="append", default=None, help="Repeatable producer filter."
    )
    parser.add_argument(
        "--max-per-producer", type=int, default=200, help="Safety cap per producer."
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output path for the observation packet.",
    )
    parser.add_argument(
        "--json", action="store_true", help="Print machine-readable JSON."
    )
    args = parser.parse_args()

    workspace = Workspace.discover(args.workspace_root)
    api = RecurrenceAPI(workspace)
    packet = api.live_observations(
        producers=args.producer,
        max_observations_per_producer=args.max_per_producer,
    )
    report_path = persist_observation_packet(workspace, packet, output=args.output)
    payload = packet.model_dump(mode="json")
    payload["report_path"] = str(report_path)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    else:
        print(f"report_path: {report_path}")
        print(f"observations: {len(packet.observations)}")


if __name__ == "__main__":
    main()
