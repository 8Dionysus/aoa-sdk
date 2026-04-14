from __future__ import annotations

from datetime import datetime, timezone

from ..workspace.discovery import Workspace
from .models import (
    BeaconEntry,
    BeaconPacket,
    BeaconRule,
    BeaconStatus,
    ObservationPacket,
    ObservationRecord,
)
from .registry import RecurrenceRegistry, load_registry


STATUS_ORDER: dict[BeaconStatus, int] = {
    "hint": 0,
    "watch": 1,
    "candidate": 2,
    "review_ready": 3,
}


def build_beacon_packet(
    workspace: Workspace,
    *,
    observations: ObservationPacket,
    registry: RecurrenceRegistry | None = None,
) -> BeaconPacket:
    registry = registry or load_registry(workspace)
    by_component: dict[str, list[ObservationRecord]] = {}
    for item in observations.observations:
        by_component.setdefault(item.component_ref, []).append(item)

    entries: list[BeaconEntry] = []

    for loaded in registry.iter_components():
        component = loaded.component
        component_observations = by_component.get(component.component_ref, [])
        if not component.beacon_rules or not component_observations:
            continue

        for rule in component.beacon_rules:
            matches = [item for item in component_observations if observation_matches_rule(item, rule)]
            if not matches:
                continue

            suppression_flags = [flag for flag in rule.suppress_when if any(item.signal == flag for item in component_observations)]
            status = derive_status(rule, matches, suppression_flags=suppression_flags)
            reason = build_reason(rule, matches, status, suppression_flags)
            decision_surface = rule.decision_surface or first_or_none(component.decision_surfaces)
            entries.append(
                BeaconEntry(
                    beacon_ref=rule.beacon_ref,
                    kind=rule.kind,
                    status=status,
                    component_ref=component.component_ref,
                    owner_repo=component.owner_repo,
                    target_repo=rule.target_repo or component.owner_repo,
                    decision_surface=decision_surface,
                    reason=reason,
                    evidence_refs=sorted({ref for item in matches for ref in item.evidence_refs}),
                    source_inputs=sorted({ref for item in matches for ref in item.source_inputs}),
                    related_signals=sorted({item.signal for item in matches}),
                    suppression_flags=suppression_flags,
                    recommended_actions=list(rule.recommended_actions or default_actions(rule.kind, status)),
                )
            )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return BeaconPacket(
        packet_ref=f"beacons:{stamp}",
        workspace_root=observations.workspace_root,
        signal_ref=observations.signal_ref,
        entries=sorted(
            entries,
            key=lambda item: (item.owner_repo, item.component_ref, item.kind, STATUS_ORDER[item.status]),
        ),
    )


def observation_matches_rule(item: ObservationRecord, rule: BeaconRule) -> bool:
    if rule.match_signals and item.signal not in rule.match_signals:
        return False
    if rule.match_categories and item.category not in rule.match_categories:
        return False
    if rule.observation_inputs and not set(item.source_inputs).intersection(rule.observation_inputs):
        return False
    return True


def derive_status(
    rule: BeaconRule,
    matches: list[ObservationRecord],
    *,
    suppression_flags: list[str],
) -> BeaconStatus:
    thresholds = rule.thresholds
    count = len(matches)
    unique_sources = len({source for item in matches for source in item.source_inputs})
    unique_evidence = len({ref for item in matches for ref in item.evidence_refs})

    status: BeaconStatus = "hint"
    if count >= thresholds.watch_observations:
        status = "watch"
    if (
        count >= thresholds.candidate_observations
        and unique_sources >= thresholds.min_unique_sources
        and unique_evidence >= thresholds.min_unique_evidence_refs
    ):
        status = "candidate"
    if (
        count >= thresholds.review_ready_observations
        and unique_sources >= thresholds.min_unique_sources
        and unique_evidence >= thresholds.min_unique_evidence_refs
    ):
        status = "review_ready"

    if suppression_flags and STATUS_ORDER[status] > STATUS_ORDER["watch"]:
        status = "watch"
    return status


def build_reason(
    rule: BeaconRule,
    matches: list[ObservationRecord],
    status: BeaconStatus,
    suppression_flags: list[str],
) -> str:
    count = len(matches)
    unique_sources = len({source for item in matches for source in item.source_inputs})
    unique_evidence = len({ref for item in matches for ref in item.evidence_refs})
    base = (
        f"{rule.kind} reached {status} with {count} matching observation(s), "
        f"{unique_sources} unique source input(s), and {unique_evidence} evidence ref(s)"
    )
    if suppression_flags:
        return base + f"; suppressed by {', '.join(sorted(suppression_flags))}"
    return base


def default_actions(kind: str, status: BeaconStatus) -> list[str]:
    prompts: dict[str, list[str]] = {
        "new_technique_candidate": [
            "refresh cross-layer technique candidate intake",
            "check overlap and boundedness before distillation",
        ],
        "technique_overlap_hold": [
            "keep the candidate on overlap hold until separability sharpens",
        ],
        "canonical_pressure": [
            "refresh promotion-readiness evidence",
            "open canonical review only after explicit owner judgment",
        ],
        "unused_skill_opportunity": [
            "inspect the applicability map and defer/skip notes",
            "check whether a nearby skill should have triggered",
        ],
        "skill_trigger_drift": [
            "refresh trigger evals and mirrored collision cases in the same change set",
        ],
        "skill_bundle_candidate": [
            "capture the repeated workflow as a bounded skill-bundle candidate",
        ],
        "portable_eval_candidate": [
            "open portable eval boundary review",
            "check trace bridge and runner/report contracts",
        ],
        "progression_evidence_candidate": [
            "restate the claim as route-scoped progression evidence",
        ],
        "overclaim_alarm": [
            "tighten claim wording and reanchor proof boundaries",
        ],
        "playbook_candidate": [
            "capture the recurring scenario as a playbook candidate",
        ],
        "subagent_recipe_candidate": [
            "record an explicit subagent recipe without turning it into auto-orchestration",
        ],
        "automation_seed_candidate": [
            "record an automation seed example without creating a live scheduler lane",
        ],
    }
    actions = list(prompts.get(kind, ["review the candidate at the owning decision surface"]))
    if status == "review_ready":
        actions.append("prepare a review packet rather than auto-promoting")
    return actions


def first_or_none(values: list[str]) -> str | None:
    return values[0] if values else None
