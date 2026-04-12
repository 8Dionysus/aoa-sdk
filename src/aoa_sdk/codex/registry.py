from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from ..errors import RecordNotFound, SurfaceNotFound
from ..loaders.json_file import load_json
from ..models import CodexPlaneDeployStatusSnapshot
from ..workspace.discovery import Workspace


ROLLOUT_DIR_RELATIVE_PATH = ".codex/generated/rollout"
TRUST_STATE_FILENAME = "codex_plane_trust_state.current.json"
REGENERATION_REPORT_FILENAME = "codex_plane_regeneration_report.latest.json"
ROLLOUT_RECEIPT_FILENAME = "codex_plane_rollout_receipt.latest.json"
TrustPosture = Literal[
    "unknown",
    "root_mismatch",
    "config_inactive",
    "trusted_ready",
    "rollout_active",
    "rollback_recommended",
]
RolloutState = Literal[
    "render_only",
    "dry_run_ready",
    "applied",
    "verified",
    "drifted",
    "rollback_recommended",
]
NextAction = Literal["none", "run_doctor", "rerender", "rerollout", "rollback"]


class CodexAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def deploy_status(self) -> CodexPlaneDeployStatusSnapshot:
        workspace_root = self.workspace.federation_root
        rollout_root = workspace_root / ROLLOUT_DIR_RELATIVE_PATH
        trust = self._load_required(rollout_root / TRUST_STATE_FILENAME)
        regeneration = self._load_required(rollout_root / REGENERATION_REPORT_FILENAME)
        receipt = self._load_required(rollout_root / ROLLOUT_RECEIPT_FILENAME)

        trust_posture = _coerce_trust_posture(trust.get("trust_posture"))
        rollout_state = _coerce_rollout_state(receipt.get("deployment_state"))
        stable_names_ok = trust.get("stable_names_ok") is True
        project_config_active = trust.get("project_config_active") is True
        hooks_active = trust.get("hooks_enabled") is True
        active_mcp_servers = sorted(
            {
                str(name)
                for name in trust.get("mcp_server_names_detected", [])
                if isinstance(name, str) and name
            }
        )
        drift_detected = (
            rollout_state in {"drifted", "rollback_recommended"}
            or trust_posture == "rollback_recommended"
            or not stable_names_ok
        )

        return CodexPlaneDeployStatusSnapshot(
            workspace_root=str(workspace_root),
            trust_posture=trust_posture,
            latest_trust_state_ref=str(trust.get("trust_state_id") or ""),
            latest_rollout_receipt_ref=str(receipt.get("rollout_receipt_id") or ""),
            project_config_active=project_config_active,
            hooks_active=hooks_active,
            active_mcp_servers=active_mcp_servers,
            rollout_state=rollout_state,
            drift_detected=drift_detected,
            next_action=_next_action(
                trust_posture=trust_posture,
                rollout_state=rollout_state,
                doctor_result=str(receipt.get("doctor_result") or "warn"),
                project_config_active=project_config_active,
                hooks_active=hooks_active,
                stable_names_ok=stable_names_ok,
            ),
            observed_at=_latest_timestamp(
                trust.get("captured_at"),
                regeneration.get("generated_at"),
                receipt.get("verified_at"),
            ),
        )

    def _load_required(self, path: Path) -> dict[str, Any]:
        try:
            payload = load_json(path)
        except SurfaceNotFound as exc:
            raise RecordNotFound(f"Missing Codex rollout artifact: {path}") from exc
        if not isinstance(payload, dict):
            raise RecordNotFound(f"Invalid Codex rollout artifact: {path}")
        return payload


def _next_action(
    *,
    trust_posture: TrustPosture,
    rollout_state: RolloutState,
    doctor_result: str,
    project_config_active: bool,
    hooks_active: bool,
    stable_names_ok: bool,
) -> NextAction:
    if (
        trust_posture == "rollback_recommended"
        or rollout_state == "rollback_recommended"
        or doctor_result == "fail"
    ):
        return "rollback"
    if not project_config_active or trust_posture == "config_inactive":
        return "rollback" if rollout_state in {"applied", "verified", "drifted"} else "rerender"
    if trust_posture == "root_mismatch":
        return "rollback" if rollout_state in {"applied", "verified", "drifted"} else "rerender"
    if not hooks_active or not stable_names_ok:
        return "rollback" if rollout_state in {"applied", "verified"} else "rerollout"
    if rollout_state in {"applied", "dry_run_ready"}:
        return "run_doctor"
    if rollout_state in {"render_only", "drifted"}:
        return "rerollout"
    return "none"


def _coerce_trust_posture(value: object) -> TrustPosture:
    if value in {
        "unknown",
        "root_mismatch",
        "config_inactive",
        "trusted_ready",
        "rollout_active",
        "rollback_recommended",
    }:
        return cast(TrustPosture, value)
    return "unknown"


def _coerce_rollout_state(value: object) -> RolloutState:
    if value in {
        "render_only",
        "dry_run_ready",
        "applied",
        "verified",
        "drifted",
        "rollback_recommended",
    }:
        return cast(RolloutState, value)
    return "render_only"


def _latest_timestamp(*values: object) -> datetime:
    timestamps: list[datetime] = []
    for value in values:
        if isinstance(value, str) and value:
            timestamps.append(datetime.fromisoformat(value.replace("Z", "+00:00")))
    if not timestamps:
        raise RecordNotFound("Codex rollout artifacts are missing timestamp fields")
    return max(timestamps).astimezone(UTC)
