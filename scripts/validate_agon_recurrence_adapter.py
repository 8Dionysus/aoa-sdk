#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "generated" / "agon_recurrence_adapter_registry.min.json"

REQUIRED_STOP_LINES = {
    "no_arena_session_creation",
    "no_sealed_commit_creation",
    "no_live_move_execution",
    "no_verdict_authority",
    "no_scar_write",
    "no_retention_scheduling",
    "no_rank_mutation",
    "no_tree_of_sophia_promotion",
    "no_hidden_scheduler",
    "no_auto_owner_mutation",
    "no_assistant_contestant_drift",
    "no_source_meaning_rewrite",
}

REQUIRED_REPOS = {
    "Agents-of-Abyss",
    "aoa-agents",
    "aoa-routing",
    "aoa-playbooks",
    "aoa-techniques",
    "aoa-skills",
}

def fail(msg: str) -> int:
    print(f"agon recurrence adapter validation failed: {msg}", file=sys.stderr)
    return 1

def main() -> int:
    builder = ROOT / "scripts" / "build_agon_recurrence_adapter_registry.py"
    result = subprocess.run([sys.executable, str(builder), "--check"], cwd=ROOT)
    if result.returncode != 0:
        return result.returncode

    data = json.loads(REG.read_text(encoding="utf-8"))
    if data.get("interlude") != "R4":
        return fail("interlude must be R4")
    if data.get("owner_repo") != "aoa-sdk":
        return fail("owner_repo must be aoa-sdk")
    if data.get("live_protocol") is not False:
        return fail("live_protocol must be false")
    if data.get("runtime_effect") != "none":
        return fail("runtime_effect must be none")
    missing = REQUIRED_STOP_LINES - set(data.get("stop_lines", []))
    if missing:
        return fail(f"missing stop-lines: {sorted(missing)}")
    components = data.get("components", [])
    repos = {c.get("owner_repo") for c in components}
    if not REQUIRED_REPOS.issubset(repos):
        return fail(f"missing owner repos: {sorted(REQUIRED_REPOS - repos)}")
    refs = [c.get("component_ref") for c in components]
    if len(refs) != len(set(refs)):
        return fail("duplicate component refs")
    for comp in components:
        if not comp.get("manifest_path", "").endswith(".json"):
            return fail(f"bad manifest path for {comp.get('component_ref')}")
        if not comp.get("hook_manifest_path", "").endswith(".json"):
            return fail(f"bad hook manifest path for {comp.get('component_ref')}")
        if not comp.get("observed_surfaces"):
            return fail(f"missing observed surfaces for {comp.get('component_ref')}")
        if comp.get("review_lane") not in {"general", "playbook", "technique", "skill", "eval"}:
            return fail(f"bad review lane for {comp.get('component_ref')}: {comp.get('review_lane')}")
    for example in data.get("example_review_surfaces", []):
        path = ROOT / example
        if not path.exists():
            return fail(f"missing example review surface: {example}")
    print("agon recurrence adapter validation passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
