from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from ..compatibility import load_surface
from ..errors import RepoNotFound, SurfaceNotFound
from ..workspace.discovery import Workspace
from .rebase import (
    CheckpointEvidenceHandoffPlan,
    CodexLocalAgentTarget,
    MemoExportPlan,
    OwnerEvidenceHandoff,
    ProgressionOverlay,
    QuestPassport,
    RemoteTaskResult,
    ReturnPlan,
    SelfAgentCheckpoint,
    StressBundle,
    SummonDecision,
    SummonIntent,
    build_checkpoint_evidence_bundle,
    build_checkpoint_evidence_handoff_plan,
    build_codex_local_target,
    build_memo_export_plan,
    build_owner_evidence_handoff,
    build_reviewed_return_handoff,
    build_runtime_return_closeout_receipt,
    build_summon_return_checkpoint_fixture,
    build_summon_request_payload,
    build_summon_result_payload,
    build_transition_decision_payload,
    build_return_plan,
    merge_stress_signals,
    progression_allows,
    recommended_cohort,
    assess_summon,
)
from .rebase.models import CohortPattern


SUMMON_REQUEST_SCHEMA_RELATIVE_PATH = Path(
    "mechanics/checkpoint/parts/child-task-reentry/schemas/summon-request-v4.schema.json"
)
SUMMON_RESULT_SCHEMA_RELATIVE_PATH = Path(
    "mechanics/checkpoint/parts/child-task-reentry/schemas/summon-result-v4.schema.json"
)


class A2AAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def summon_request_schema_path(self) -> Path:
        return self.workspace.surface_path("aoa-sdk", SUMMON_REQUEST_SCHEMA_RELATIVE_PATH)

    def summon_result_schema_path(self) -> Path:
        return self.workspace.surface_path("aoa-sdk", SUMMON_RESULT_SCHEMA_RELATIVE_PATH)

    def summon_request_schema(self) -> dict[str, Any]:
        return self._load_schema(self.summon_request_schema_path())

    def summon_result_schema(self) -> dict[str, Any]:
        return self._load_schema(self.summon_result_schema_path())

    def recommended_cohort(self, passport: QuestPassport) -> CohortPattern:
        return recommended_cohort(passport)

    def assess_summon(
        self,
        passport: QuestPassport,
        intent: SummonIntent,
        *,
        stress_bundle: StressBundle | None = None,
        progression: ProgressionOverlay | None = None,
        self_agent_checkpoint: SelfAgentCheckpoint | None = None,
    ) -> SummonDecision:
        return assess_summon(
            passport,
            intent,
            stress_bundle=stress_bundle,
            progression=progression,
            self_agent_checkpoint=self_agent_checkpoint,
        )

    def progression_allows(
        self,
        passport: QuestPassport,
        cohort: CohortPattern,
        overlay: ProgressionOverlay | None,
    ) -> tuple[bool, list[str]]:
        return progression_allows(passport, cohort, overlay)

    def merge_stress_signals(self, signals) -> StressBundle:
        return merge_stress_signals(signals)

    def build_summon_request(
        self,
        passport: QuestPassport,
        intent: SummonIntent,
        *,
        expected_outputs: Iterable[str] | None = None,
        progression_overlay_ref: str | None = None,
        self_agent_checkpoint_ref: str | None = None,
        stress_bundle_ref: str | None = None,
        checkpoint_note_ref: str | None = None,
        codex_trace_ref: str | None = None,
        reviewed_artifact_path: str | None = None,
        audit_refs: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        return build_summon_request_payload(
            passport,
            intent,
            expected_outputs=expected_outputs,
            progression_overlay_ref=progression_overlay_ref,
            self_agent_checkpoint_ref=self_agent_checkpoint_ref,
            stress_bundle_ref=stress_bundle_ref,
            checkpoint_note_ref=checkpoint_note_ref,
            codex_trace_ref=codex_trace_ref,
            reviewed_artifact_path=reviewed_artifact_path,
            audit_refs=audit_refs,
        )

    def build_summon_result(
        self,
        decision: SummonDecision,
        *,
        codex_local_target: CodexLocalAgentTarget | None = None,
        return_plan: ReturnPlan | None = None,
        checkpoint_handoff_plan: CheckpointEvidenceHandoffPlan | None = None,
        memo_export_plan: MemoExportPlan | None = None,
        owner_handoffs: Iterable[OwnerEvidenceHandoff] | None = None,
    ) -> dict[str, Any]:
        return build_summon_result_payload(
            decision,
            codex_local_target=codex_local_target,
            return_plan=return_plan,
            checkpoint_handoff_plan=checkpoint_handoff_plan,
            memo_export_plan=memo_export_plan,
            owner_handoffs=owner_handoffs,
        )

    def build_codex_local_target(
        self,
        role: str,
        *,
        workspace_root: str | None = None,
        agent_id: str | None = None,
    ) -> CodexLocalAgentTarget:
        return build_codex_local_target(
            role,
            workspace_root=workspace_root or str(self.workspace.federation_root),
            agent_id=agent_id,
            projection_entry=self._codex_projection_entry(role),
        )

    def build_return_plan(
        self,
        remote_task: RemoteTaskResult,
        decision: SummonDecision,
        *,
        anchor_artifact: str = "bounded_plan",
        checkpoint_note_ref: str | None = None,
        codex_trace_ref: str | None = None,
        force: bool = False,
    ) -> ReturnPlan | None:
        return build_return_plan(
            remote_task,
            decision,
            anchor_artifact=anchor_artifact,
            checkpoint_note_ref=checkpoint_note_ref,
            codex_trace_ref=codex_trace_ref,
            force=force,
        )

    def build_transition_decision_payload(
        self, return_plan: ReturnPlan
    ) -> dict[str, Any]:
        return build_transition_decision_payload(return_plan)

    def build_checkpoint_evidence_handoff_plan(
        self,
        *,
        session_ref: str,
        reviewed_artifact_path: str,
        checkpoint_note_ref: str | None = None,
        codex_trace_ref: str | None = None,
        surviving_checkpoint_clusters: list[str] | None = None,
        return_plan: ReturnPlan | None = None,
    ) -> CheckpointEvidenceHandoffPlan:
        return build_checkpoint_evidence_handoff_plan(
            session_ref=session_ref,
            reviewed_artifact_path=reviewed_artifact_path,
            checkpoint_note_ref=checkpoint_note_ref,
            codex_trace_ref=codex_trace_ref,
            surviving_checkpoint_clusters=surviving_checkpoint_clusters,
            return_plan=return_plan,
        )

    def build_checkpoint_evidence_bundle(
        self,
        plan: CheckpointEvidenceHandoffPlan,
        *,
        owner_handoffs: list[OwnerEvidenceHandoff] | None = None,
    ) -> dict[str, Any]:
        return build_checkpoint_evidence_bundle(
            plan,
            owner_handoffs=owner_handoffs,
        )

    def build_memo_export_plan(
        self,
        remote_task: RemoteTaskResult,
        *,
        reviewed_artifact_path: str | None = None,
        stress_bundle: StressBundle | None = None,
        return_plan: ReturnPlan | None = None,
        checkpoint_note_ref: str | None = None,
        recovery_window: bool = False,
    ) -> MemoExportPlan:
        return build_memo_export_plan(
            remote_task,
            reviewed_artifact_path=reviewed_artifact_path,
            stress_bundle=stress_bundle,
            return_plan=return_plan,
            checkpoint_note_ref=checkpoint_note_ref,
            recovery_window=recovery_window,
        )

    def build_owner_evidence_handoff(
        self,
        *,
        owner_ref: str,
        candidate_kind: str,
        reason: str,
        evidence_refs: list[str],
        capability_ref: str | None = None,
        review_required: bool = True,
    ) -> OwnerEvidenceHandoff:
        return build_owner_evidence_handoff(
            owner_ref=owner_ref,
            candidate_kind=candidate_kind,
            reason=reason,
            evidence_refs=evidence_refs,
            capability_ref=capability_ref,
            review_required=review_required,
        )

    def build_reviewed_return_handoff(
        self,
        remote_task: RemoteTaskResult,
        decision: SummonDecision,
        *,
        session_ref: str,
        reviewed_artifact_path: str,
        owner_handoffs: list[OwnerEvidenceHandoff],
        audit_refs: list[str] | None = None,
        stress_bundle: StressBundle | None = None,
        memo_export_plan: MemoExportPlan | None = None,
        return_plan: ReturnPlan | None = None,
        checkpoint_handoff_plan: CheckpointEvidenceHandoffPlan | None = None,
        codex_target: CodexLocalAgentTarget | None = None,
    ) -> dict[str, Any]:
        return build_reviewed_return_handoff(
            remote_task,
            decision,
            session_ref=session_ref,
            reviewed_artifact_path=reviewed_artifact_path,
            owner_handoffs=owner_handoffs,
            audit_refs=audit_refs,
            stress_bundle=stress_bundle,
            memo_export_plan=memo_export_plan,
            return_plan=return_plan,
            checkpoint_handoff_plan=checkpoint_handoff_plan,
            codex_target=codex_target,
        )

    def build_runtime_return_closeout_receipt(
        self,
        remote_task: RemoteTaskResult,
        decision: SummonDecision,
        *,
        session_ref: str,
        reviewed_artifact_path: str | None = None,
        stress_bundle: StressBundle | None = None,
        return_plan: ReturnPlan | None = None,
        checkpoint_handoff_plan: CheckpointEvidenceHandoffPlan | None = None,
        codex_target: CodexLocalAgentTarget | None = None,
        observed_at: str | None = None,
        owner_repo: str = "abyss-stack",
        actor_ref: str = "abyss-stack.runtime-a2a",
    ) -> dict[str, Any]:
        return build_runtime_return_closeout_receipt(
            remote_task,
            decision,
            session_ref=session_ref,
            reviewed_artifact_path=reviewed_artifact_path,
            stress_bundle=stress_bundle,
            return_plan=return_plan,
            checkpoint_handoff_plan=checkpoint_handoff_plan,
            codex_target=codex_target,
            observed_at=observed_at,
            owner_repo=owner_repo,
            actor_ref=actor_ref,
        )

    def build_summon_return_checkpoint_fixture(
        self,
        *,
        observed_at: str | None = None,
    ) -> dict[str, Any]:
        kwargs = {"observed_at": observed_at} if observed_at is not None else {}
        return build_summon_return_checkpoint_fixture(**kwargs)

    def _load_schema(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _codex_projection_entry(self, role: str) -> dict[str, Any] | None:
        try:
            payload = load_surface(self.workspace, "aoa-agents.codex_projection_manifest")
        except (RepoNotFound, SurfaceNotFound):
            return None
        generated_agents = payload.get("generated_agents")
        if not isinstance(generated_agents, list):
            return None

        for entry in generated_agents:
            if isinstance(entry, dict) and entry.get("name") == role:
                return entry
        return None
