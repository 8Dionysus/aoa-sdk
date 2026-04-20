from __future__ import annotations

from datetime import datetime, timezone

from ..workspace.discovery import Workspace
from .models import WiringPlan, WiringSnippet


SESSION_STOP_REPORT = ".aoa/recurrence/hooks/session_stop.latest.json"
OBSERVATION_REPORT = ".aoa/recurrence/observations/session.latest.json"
BEACON_REPORT = ".aoa/recurrence/beacons/session.latest.json"
USAGE_GAP_REPORT = ".aoa/recurrence/usage-gaps/session.latest.json"
REVIEW_QUEUE_REPORT = ".aoa/recurrence/review-queues/session.latest.json"
REVIEW_SUMMARY_REPORT = ".aoa/recurrence/review-summaries/session.latest.json"


def build_wiring_plan(workspace: Workspace) -> WiringPlan:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snippets = [
        WiringSnippet(
            snippet_ref="wiring:session_start",
            scope="session_start",
            title="Codex SessionStart recurrence hooks",
            target_path=".codex/hooks/session_start.recurrence.sh",
            commands=[
                "aoa recur hooks run --event session_start --root . --json",
            ],
            notes="Use the shared-root SessionStart seam for discovery and early observation only.",
        ),
        WiringSnippet(
            snippet_ref="wiring:user_prompt_submit",
            scope="user_prompt_submit",
            title="Codex UserPromptSubmit change detection",
            target_path=".codex/hooks/user_prompt_submit.recurrence.sh",
            commands=[
                "aoa recur detect <repo-root> --from git:HEAD~1..HEAD --root . --json",
            ],
            notes="Use placeholders until the host runtime provides the active repo root and diff base.",
        ),
        WiringSnippet(
            snippet_ref="wiring:session_stop",
            scope="session_stop",
            title="Codex Stop review-surface pipeline",
            target_path=".codex/hooks/session_stop.recurrence.sh",
            commands=[
                f"aoa recur hooks run --event session_stop --signal <signal-path> --root . --report-output {SESSION_STOP_REPORT}",
                f"aoa recur observe --signal <signal-path> --hook-run {SESSION_STOP_REPORT} --root . --report-output {OBSERVATION_REPORT}",
                f"aoa recur beacon {OBSERVATION_REPORT} --root . --report-output {BEACON_REPORT}",
                f"aoa recur usage-gaps {BEACON_REPORT} --root . --report-output {USAGE_GAP_REPORT}",
                f"aoa recur review-queue {BEACON_REPORT} --usage-gaps {USAGE_GAP_REPORT} --root . --report-output {REVIEW_QUEUE_REPORT}",
                f"aoa recur review-summary {REVIEW_QUEUE_REPORT} --root . --report-output {REVIEW_SUMMARY_REPORT}",
            ],
            notes=(
                "Keep the pipeline reviewable. It should emit queues and summaries by default; "
                "generate dossiers on demand instead of mutating owner repos silently."
            ),
        ),
        WiringSnippet(
            snippet_ref="wiring:pre_commit",
            scope="pre_commit",
            title="Git pre-commit recurrence doctor",
            target_path=".githooks/pre-commit.recurrence",
            commands=[
                "aoa recur doctor --root . --json",
            ],
            notes="Pre-commit should stay quick and diagnostic. Do not turn it into a hidden repair loop.",
        ),
        WiringSnippet(
            snippet_ref="wiring:pre_push",
            scope="pre_push",
            title="Git pre-push recurrence doctor and review summary",
            target_path=".githooks/pre-push.recurrence",
            commands=[
                "aoa recur doctor --root . --json",
                f"test -f {REVIEW_QUEUE_REPORT} && aoa recur review-summary {REVIEW_QUEUE_REPORT} --root . --json || true",
            ],
            notes="Pre-push may look one step farther than pre-commit, but should still stop short of auto-resolution.",
        ),
        WiringSnippet(
            snippet_ref="wiring:ci",
            scope="ci",
            title="CI recurrence control-plane checks",
            target_path=".github/workflows/recurrence-control-plane.example.yml",
            commands=[
                "aoa recur doctor --root . --json",
                "pytest -q tests/test_recurrence_seed.py tests/test_recurrence_beacon_seed.py tests/test_recurrence_hook_pack_seed.py tests/test_recurrence_review_pack_seed.py tests/test_recurrence_wiring_pack_seed.py",
            ],
            notes="CI should prove the planted control-plane stays coherent before it widens further.",
        ),
    ]
    return WiringPlan(
        plan_ref=f"wiring-plan:{stamp}",
        workspace_root=str(workspace.root),
        snippets=snippets,
    )
