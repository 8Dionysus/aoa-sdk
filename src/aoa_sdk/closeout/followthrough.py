from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, cast
import json

from ..compatibility import load_surface
from ..errors import SurfaceNotFound
from ..loaders import load_json, write_json
from ..models import (
    CloseoutManifest,
    CloseoutOwnerHandoff,
    KernelNextStepBrief,
    OwnerFollowThroughBrief,
    ProjectCoreSkillKernelSurface,
    WorkflowFollowThroughBrief,
)


def _build_kernel_next_step_brief(
    self,
    *,
    manifest_path: Path,
    manifest: CloseoutManifest,
) -> KernelNextStepBrief:
    kernel = ProjectCoreSkillKernelSurface.model_validate(
        load_surface(self.workspace, "aoa-skills.project_core_skill_kernel.min")
    )
    detail_receipts, core_receipts = self._load_kernel_receipt_batches(
        manifest_path=manifest_path,
        manifest=manifest,
        kernel=kernel,
    )
    current_detail_event_kinds = self._collect_current_detail_event_kinds(
        detail_receipts=detail_receipts,
        core_receipts=core_receipts,
    )
    current_session_skill_names = self._collect_current_session_skill_names(
        kernel=kernel,
        detail_receipts=detail_receipts,
        core_receipts=core_receipts,
    )
    kernel_usage_counts = self._load_kernel_usage_counts(
        kernel_id=kernel.kernel_id,
        kernel_skills=kernel.skills,
    )
    missing_kernel_skill_names = [
        skill_name
        for skill_name in kernel.skills
        if skill_name not in set(current_session_skill_names)
    ]
    suggested_action, suggested_skill_name, suggested_owner_repo, reason = self._resolve_kernel_next_step(
        kernel=kernel,
        detail_receipts=detail_receipts,
        current_session_skill_names=current_session_skill_names,
        current_detail_event_kinds=current_detail_event_kinds,
        missing_kernel_skill_names=missing_kernel_skill_names,
    )
    return KernelNextStepBrief(
        kernel_id=kernel.kernel_id,
        current_session_skill_names=current_session_skill_names,
        current_session_detail_event_kinds=current_detail_event_kinds,
        missing_kernel_skill_names=missing_kernel_skill_names,
        kernel_usage_counts=kernel_usage_counts,
        suggested_action=suggested_action,
        suggested_skill_name=suggested_skill_name,
        suggested_owner_repo=suggested_owner_repo,
        reason=reason,
        stats_surface_ref=kernel.governance_contract.stats_surface,
    )

def _build_owner_follow_through_briefs(
    self,
    *,
    manifest_path: Path,
    manifest: CloseoutManifest,
) -> list[OwnerFollowThroughBrief]:
    kernel = ProjectCoreSkillKernelSurface.model_validate(
        load_surface(self.workspace, "aoa-skills.project_core_skill_kernel.min")
    )
    detail_receipts, _ = self._load_kernel_receipt_batches(
        manifest_path=manifest_path,
        manifest=manifest,
        kernel=kernel,
    )
    briefs_by_key: dict[str, OwnerFollowThroughBrief] = {}
    for brief in self._build_harvest_follow_through_briefs(
        manifest_path=manifest_path,
        detail_receipts=detail_receipts,
    ):
        briefs_by_key[self._owner_follow_through_key(brief)] = brief
    for brief in self._build_quest_follow_through_briefs(
        manifest_path=manifest_path,
        detail_receipts=detail_receipts,
    ):
        briefs_by_key[self._owner_follow_through_key(brief)] = brief
    return sorted(
        briefs_by_key.values(),
        key=lambda item: (item.owner_repo, item.next_surface, item.unit_ref),
    )

def _build_workflow_follow_through_briefs(
    self,
    *,
    manifest_path: Path,
    manifest: CloseoutManifest,
    kernel_next_step_brief: KernelNextStepBrief | None,
) -> list[WorkflowFollowThroughBrief]:
    kernel = ProjectCoreSkillKernelSurface.model_validate(
        load_surface(self.workspace, "aoa-skills.project_core_skill_kernel.min")
    )
    detail_receipts, _ = self._load_kernel_receipt_batches(
        manifest_path=manifest_path,
        manifest=manifest,
        kernel=kernel,
    )
    briefs_by_skill: dict[str, WorkflowFollowThroughBrief] = {}

    if (
        kernel_next_step_brief is not None
        and kernel_next_step_brief.suggested_action == "invoke-core-skill"
        and kernel_next_step_brief.suggested_skill_name is not None
    ):
        briefs_by_skill[kernel_next_step_brief.suggested_skill_name] = WorkflowFollowThroughBrief(
            source_kind="kernel-next-step",
            skill_name=kernel_next_step_brief.suggested_skill_name,
            suggested_action="invoke-core-skill",
            reason=kernel_next_step_brief.reason,
            evidence_refs=[kernel_next_step_brief.stats_surface_ref],
        )

    progression_receipt = self._latest_detail_receipt(
        detail_receipts,
        event_kind="progression_delta_receipt",
    )
    if progression_receipt is not None:
        payload = progression_receipt.get("payload")
        verdict = payload.get("verdict") if isinstance(payload, dict) else None
        axis_deltas = payload.get("axis_deltas") if isinstance(payload, dict) else None
        negative_axes = (
            sorted(
                axis
                for axis, delta in axis_deltas.items()
                if isinstance(axis, str) and isinstance(delta, int) and delta < 0
            )
            if isinstance(axis_deltas, dict)
            else []
        )
        if verdict in {"reanchor", "downgrade"} and "aoa-session-self-diagnose" not in briefs_by_skill:
            detail = (
                f"progression closed with {verdict} and negative axes in {', '.join(negative_axes)}"
                if negative_axes
                else f"progression closed with {verdict}"
            )
            briefs_by_skill["aoa-session-self-diagnose"] = WorkflowFollowThroughBrief(
                source_kind="progression-caution",
                skill_name="aoa-session-self-diagnose",
                suggested_action="invoke-core-skill",
                reason=(
                    f"{detail}, so the next honest workflow move is bounded self-diagnosis before the next mutation-heavy follow-through."
                ),
                evidence_refs=self._extract_evidence_ref_strings(progression_receipt.get("evidence_refs")),
            )

    diagnosis_receipt = self._latest_detail_receipt(
        detail_receipts,
        event_kind="diagnosis_packet_receipt",
    )
    if diagnosis_receipt is None:
        diagnosis_receipt = self._latest_detail_receipt(
            detail_receipts,
            event_kind="skill_run_receipt",
        )
    repair_receipt = self._latest_detail_receipt(
        detail_receipts,
        event_kind="repair_cycle_receipt",
    )
    if diagnosis_receipt is not None and repair_receipt is None:
        payload = diagnosis_receipt.get("payload")
        diagnosis_types = payload.get("diagnosis_types") if isinstance(payload, dict) else None
        diagnosis_summary = (
            ", ".join(item for item in diagnosis_types if isinstance(item, str))
            if isinstance(diagnosis_types, list)
            else "an unresolved diagnosis packet"
        )
        briefs_by_skill["aoa-session-self-repair"] = WorkflowFollowThroughBrief(
            source_kind="diagnosis-gap",
            skill_name="aoa-session-self-repair",
            suggested_action="invoke-core-skill",
            reason=(
                f"closeout already carries {diagnosis_summary}, but no repair_cycle_receipt landed yet, so the next honest workflow move is bounded self-repair."
            ),
            evidence_refs=self._extract_evidence_ref_strings(diagnosis_receipt.get("evidence_refs")),
        )

    workflow_order = {
        "aoa-automation-opportunity-scan": 0,
        "aoa-session-route-forks": 1,
        "aoa-session-self-diagnose": 2,
        "aoa-session-self-repair": 3,
        "aoa-session-progression-lift": 4,
        "aoa-quest-harvest": 5,
    }
    return sorted(
        briefs_by_skill.values(),
        key=lambda item: (workflow_order.get(item.skill_name, 99), item.skill_name),
    )

def _build_harvest_follow_through_briefs(
    self,
    *,
    manifest_path: Path,
    detail_receipts: list[dict[str, Any]],
) -> list[OwnerFollowThroughBrief]:
    briefs: list[OwnerFollowThroughBrief] = []
    for receipt in detail_receipts:
        if receipt.get("event_kind") != "harvest_packet_receipt":
            continue
        packet_paths = self._resolve_receipt_evidence_paths(
            manifest_path=manifest_path,
            evidence_refs=receipt.get("evidence_refs"),
            preferred_kinds={"harvest_packet"},
        )
        for packet_path in packet_paths:
            try:
                packet = load_json(packet_path)
            except (FileNotFoundError, json.JSONDecodeError, ValueError):
                continue
            if not isinstance(packet, dict):
                continue
            for candidate in packet.get("accepted_candidates", []):
                if not isinstance(candidate, dict):
                    continue
                owner_repo = candidate.get("owner_repo_recommendation")
                next_surface = candidate.get("chosen_next_artifact")
                unit_ref = candidate.get("candidate_ref")
                if not all(
                    isinstance(value, str) and value
                    for value in (owner_repo, next_surface, unit_ref)
                ):
                    continue
                owner_repo_str = cast(str, owner_repo)
                next_surface_str = cast(str, next_surface)
                unit_ref_str = cast(str, unit_ref)
                owner_reason = candidate.get("owner_reason")
                reason = (
                    owner_reason
                    if isinstance(owner_reason, str) and owner_reason
                    else "Harvest named this as a reusable owner-layer candidate, so the next honest move is a bounded owner-surface draft."
                )
                evidence_refs = [str(packet_path)]
                evidence_anchors = candidate.get("evidence_anchors")
                if isinstance(evidence_anchors, list):
                    evidence_refs.extend(
                        anchor
                        for anchor in evidence_anchors
                        if isinstance(anchor, str) and anchor
                    )
                briefs.append(
                    OwnerFollowThroughBrief(
                        source_kind="harvest-candidate",
                        unit_ref=unit_ref_str,
                        unit_name=candidate.get("unit_name")
                        if isinstance(candidate.get("unit_name"), str)
                        else None,
                        owner_repo=owner_repo_str,
                        next_surface=next_surface_str,
                        suggested_action="draft-owner-artifact",
                        abstraction_shape=candidate.get("abstraction_shape")
                        if isinstance(candidate.get("abstraction_shape"), str)
                        else None,
                        nearest_wrong_target=candidate.get("nearest_wrong_target")
                        if isinstance(candidate.get("nearest_wrong_target"), str)
                        else None,
                        reason=reason,
                        evidence_refs=self._unique_strings(evidence_refs),
                    )
                )
    return briefs

def _build_quest_follow_through_briefs(
    self,
    *,
    manifest_path: Path,
    detail_receipts: list[dict[str, Any]],
) -> list[OwnerFollowThroughBrief]:
    briefs: list[OwnerFollowThroughBrief] = []
    for receipt in detail_receipts:
        if receipt.get("event_kind") != "quest_promotion_receipt":
            continue
        payload = receipt.get("payload")
        if not isinstance(payload, dict):
            continue
        owner_repo = payload.get("owner_repo")
        next_surface = payload.get("next_surface")
        promotion_verdict = payload.get("promotion_verdict")
        if not all(
            isinstance(value, str) and value
            for value in (owner_repo, next_surface, promotion_verdict)
        ):
            continue
        owner_repo_str = cast(str, owner_repo)
        next_surface_str = cast(str, next_surface)
        promotion_verdict_str = cast(str, promotion_verdict)
        unit_ref = payload.get("bounded_unit_ref")
        if not isinstance(unit_ref, str) or not unit_ref:
            event_id = receipt.get("event_id")
            unit_ref = event_id if isinstance(event_id, str) and event_id else next_surface
        unit_ref_str = cast(str, unit_ref)
        briefs.append(
            OwnerFollowThroughBrief(
                source_kind="quest-promotion",
                unit_ref=unit_ref_str,
                unit_name=self._load_quest_unit_name(
                    manifest_path=manifest_path,
                    receipt=receipt,
                ),
                owner_repo=owner_repo_str,
                next_surface=next_surface_str,
                suggested_action="author-owner-artifact",
                promotion_verdict=promotion_verdict_str,
                nearest_wrong_target=payload.get("nearest_wrong_target")
                if isinstance(payload.get("nearest_wrong_target"), str)
                else None,
                reason=(
                    f"Quest promotion closed with {promotion_verdict_str}, so the next honest move is to author the owner-layer artifact."
                ),
                evidence_refs=self._extract_evidence_ref_strings(receipt.get("evidence_refs")),
            )
        )
    return briefs

def _load_quest_unit_name(
    self,
    *,
    manifest_path: Path,
    receipt: dict[str, Any],
) -> str | None:
    triage_paths = self._resolve_receipt_evidence_paths(
        manifest_path=manifest_path,
        evidence_refs=receipt.get("evidence_refs"),
        preferred_kinds={"quest_triage"},
    )
    for triage_path in triage_paths:
        try:
            payload = load_json(triage_path)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            continue
        if not isinstance(payload, dict):
            continue
        quest_unit_name = payload.get("quest_unit_name")
        if isinstance(quest_unit_name, str) and quest_unit_name:
            return quest_unit_name
    return None

def _owner_follow_through_key(self, brief: OwnerFollowThroughBrief) -> str:
    return brief.unit_ref or brief.next_surface

def _collect_current_detail_event_kinds(
    self,
    *,
    detail_receipts: list[dict[str, Any]],
    core_receipts: list[dict[str, Any]],
) -> list[str]:
    event_kinds: list[str] = []
    for receipt in detail_receipts:
        event_kind = receipt.get("event_kind")
        if isinstance(event_kind, str) and event_kind and event_kind not in event_kinds:
            event_kinds.append(event_kind)
    for receipt in core_receipts:
        payload = receipt.get("payload")
        detail_event_kind = payload.get("detail_event_kind") if isinstance(payload, dict) else None
        if (
            isinstance(detail_event_kind, str)
            and detail_event_kind
            and detail_event_kind not in event_kinds
        ):
            event_kinds.append(detail_event_kind)
    return event_kinds

def _collect_current_session_skill_names(
    self,
    *,
    kernel: ProjectCoreSkillKernelSurface,
    detail_receipts: list[dict[str, Any]],
    core_receipts: list[dict[str, Any]],
) -> list[str]:
    skill_contracts = {item.skill_name: item for item in kernel.skill_contracts}
    detail_event_to_skill = {
        item.detail_event_kind: item.skill_name for item in kernel.skill_contracts
    }
    detected_skill_names: set[str] = set()

    for receipt in core_receipts:
        payload = receipt.get("payload")
        skill_name = payload.get("skill_name") if isinstance(payload, dict) else None
        if isinstance(skill_name, str) and skill_name in skill_contracts:
            detected_skill_names.add(skill_name)

    for receipt in detail_receipts:
        event_kind = receipt.get("event_kind")
        if isinstance(event_kind, str) and event_kind in detail_event_to_skill:
            detected_skill_names.add(detail_event_to_skill[event_kind])
            continue
        object_ref = receipt.get("object_ref")
        object_id = object_ref.get("id") if isinstance(object_ref, dict) else None
        if isinstance(object_id, str) and object_id in skill_contracts:
            detected_skill_names.add(object_id)

    return [skill_name for skill_name in kernel.skills if skill_name in detected_skill_names]

def _load_kernel_usage_counts(
    self,
    *,
    kernel_id: str,
    kernel_skills: list[str],
) -> dict[str, int]:
    usage_counts = {skill_name: 0 for skill_name in kernel_skills}
    try:
        summary = load_surface(self.workspace, "aoa-stats.core_skill_application_summary.min")
    except SurfaceNotFound:
        return usage_counts
    for item in summary.get("skills", []):
        if not isinstance(item, dict):
            continue
        if item.get("kernel_id") != kernel_id:
            continue
        skill_name = item.get("skill_name")
        application_count = item.get("application_count")
        if isinstance(skill_name, str) and skill_name in usage_counts and isinstance(application_count, int):
            usage_counts[skill_name] = application_count
    return usage_counts

def _resolve_kernel_next_step(
    self,
    *,
    kernel: ProjectCoreSkillKernelSurface,
    detail_receipts: list[dict[str, Any]],
    current_session_skill_names: list[str],
    current_detail_event_kinds: list[str],
    missing_kernel_skill_names: list[str],
) -> tuple[
    Literal["invoke-core-skill", "shift-to-owner-layer", "hold"],
    str | None,
    str | None,
    str,
]:
    detail_event_kind_set = set(current_detail_event_kinds)
    quest_receipt = self._latest_detail_receipt(
        detail_receipts, event_kind="quest_promotion_receipt"
    )
    if quest_receipt is not None:
        payload = quest_receipt.get("payload")
        owner_repo = payload.get("owner_repo") if isinstance(payload, dict) else None
        return (
            "shift-to-owner-layer",
            None,
            owner_repo if isinstance(owner_repo, str) else None,
            "Current closeout already finished with quest promotion, so the next honest move is owner-layer follow-through.",
        )

    if "progression_delta_receipt" in detail_event_kind_set:
        return self._invoke_core_skill_brief(
            "aoa-quest-harvest",
            "Progression has been recorded for this session, so the next core step is final quest triage.",
        )
    if "repair_cycle_receipt" in detail_event_kind_set:
        return self._invoke_core_skill_brief(
            "aoa-session-progression-lift",
            "Repair has landed but progression has not, so the next core step is explicit progression lift.",
        )
    if (
        "diagnosis_packet_receipt" in detail_event_kind_set
        or "skill_run_receipt" in detail_event_kind_set
    ):
        return self._invoke_core_skill_brief(
            "aoa-session-self-repair",
            "Diagnosis has landed but repair has not, so the next core step is bounded self-repair.",
        )
    automation_receipt = self._latest_detail_receipt(
        detail_receipts, event_kind="automation_candidate_receipt"
    )
    if automation_receipt is not None:
        payload = automation_receipt.get("payload")
        checkpoint_required = (
            payload.get("checkpoint_required") if isinstance(payload, dict) else None
        )
        if checkpoint_required is True:
            return self._invoke_core_skill_brief(
                "aoa-session-self-diagnose",
                "Automation scan raised a checkpoint-required candidate, so the next core step is self-diagnosis.",
            )
    if "decision_fork_receipt" in detail_event_kind_set:
        return self._invoke_core_skill_brief(
            "aoa-session-self-diagnose",
            "Route forks have been captured without diagnosis yet, so the next core step is self-diagnosis.",
        )
    if "automation_candidate_receipt" in detail_event_kind_set:
        return self._invoke_core_skill_brief(
            "aoa-session-route-forks",
            "Automation candidates exist without a fork decision yet, so the next core step is route selection.",
        )
    if "harvest_packet_receipt" in detail_event_kind_set:
        return self._invoke_core_skill_brief(
            "aoa-automation-opportunity-scan",
            "Harvest has landed without automation classification yet, so the next core step is automation opportunity scan.",
        )

    if missing_kernel_skill_names:
        highest_index = max(
            (kernel.skills.index(skill_name) for skill_name in current_session_skill_names),
            default=-1,
        )
        later_missing = [
            skill_name
            for skill_name in kernel.skills[highest_index + 1 :]
            if skill_name in missing_kernel_skill_names
        ]
        target_skill = later_missing[0] if later_missing else missing_kernel_skill_names[0]
        return self._invoke_core_skill_brief(
            target_skill,
            "Current closeout only covers part of the project-core kernel, so the next honest move is the next missing core skill in canonical order.",
        )

    return (
        "hold",
        None,
        None,
        "Current closeout already covers the full kernel without an unresolved next-step rule, so the honest next move is to hold.",
    )

def _invoke_core_skill_brief(
    self, skill_name: str, reason: str
) -> tuple[Literal["invoke-core-skill"], str, None, str]:
    return (
        "invoke-core-skill",
        skill_name,
        None,
        reason,
    )

def _latest_detail_receipt(
    self,
    detail_receipts: list[dict[str, Any]],
    *,
    event_kind: str,
) -> dict[str, Any] | None:
    matching = [
        receipt
        for receipt in detail_receipts
        if receipt.get("event_kind") == event_kind
    ]
    if not matching:
        return None
    return max(
        matching,
        key=lambda receipt: (
            str(receipt.get("observed_at", "")),
            str(receipt.get("event_id", "")),
        ),
    )

def _write_owner_handoff(
    self,
    *,
    manifest_path: Path,
    manifest: CloseoutManifest,
    briefs: list[OwnerFollowThroughBrief],
    workflow_briefs: list[WorkflowFollowThroughBrief],
) -> Path | None:
    if not briefs and not workflow_briefs:
        return None
    handoff_dir = self._resolve_queue_dir(None, leaf="handoffs")
    handoff_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = handoff_dir / f"{self._safe_closeout_filename(manifest.closeout_id)}.owner-handoff.json"
    payload = CloseoutOwnerHandoff(
        schema_version=1,
        closeout_id=manifest.closeout_id,
        session_ref=manifest.session_ref,
        manifest_path=str(manifest_path),
        generated_at=datetime.now(timezone.utc),
        items=briefs,
        workflow_items=workflow_briefs,
    )
    write_json(handoff_path, payload.model_dump(mode="json"))
    return handoff_path
