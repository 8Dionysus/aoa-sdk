"""Read-only recurrence support for recursor role readiness.

The helpers in this module read `aoa-agents` readiness surfaces and build compact
workspace projections. They do not mutate owner repositories, install Codex
agents, spawn agents, or open Agon runtime.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .recursor_boundary import (
    BOUNDARY_STOP_LINES,
    boundary_status,
    check_projection_candidate,
    check_role_contract,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> Optional[Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        return {"_error": "invalid_json", "path": str(path), "message": str(exc)}


def _repo(workspace_root: Path, name: str) -> Path:
    direct = workspace_root / name
    if direct.exists():
        return direct
    if workspace_root.name == name:
        return workspace_root
    return direct


def _seed_status(violations: List[Dict[str, Any]], diagnostics: List[Dict[str, Any]]) -> str:
    if violations:
        return "fail"
    if any(diagnostic.get("severity") == "critical" for diagnostic in diagnostics):
        return "fail"
    if diagnostics:
        return "warn"
    return "pass"


def _materialize_seed(
    value: Optional[Any],
    *,
    missing_kind: str,
    path: str,
    default: Dict[str, Any],
    diagnostics: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if value is None:
        diagnostics.append({"kind": missing_kind, "severity": "warning", "path": path})
        return default
    if isinstance(value, dict) and value.get("_error") == "invalid_json":
        diagnostics.append(
            {
                "kind": "invalid_seed_json",
                "severity": "critical",
                "path": path,
                "message": value.get("message"),
            }
        )
        return default
    if not isinstance(value, dict):
        diagnostics.append({"kind": "invalid_seed_shape", "severity": "critical", "path": path})
        return default
    return value


def build_recursor_readiness_projection(workspace_root: str | Path) -> Dict[str, Any]:
    """Build a compact read-only projection from `aoa-agents` readiness surfaces."""
    root = Path(workspace_root)
    agents = _repo(root, "aoa-agents")
    roles_path = "aoa-agents/config/recursor_roles.seed.json"
    pair_path = "aoa-agents/config/recursor_pair.seed.json"
    projection_path = "aoa-agents/config/codex_recursor_projection.candidate.json"
    roles = _read_json(agents / "config" / "recursor_roles.seed.json")
    pair = _read_json(agents / "config" / "recursor_pair.seed.json")
    projection = _read_json(agents / "config" / "codex_recursor_projection.candidate.json")

    diagnostics: List[Dict[str, Any]] = []
    roles = _materialize_seed(
        roles,
        missing_kind="missing_roles_seed",
        path=roles_path,
        default={"roles": []},
        diagnostics=diagnostics,
    )
    pair = _materialize_seed(
        pair,
        missing_kind="missing_pair_seed",
        path=pair_path,
        default={},
        diagnostics=diagnostics,
    )
    projection = _materialize_seed(
        projection,
        missing_kind="missing_projection_candidate",
        path=projection_path,
        default={},
        diagnostics=diagnostics,
    )

    violations: List[Dict[str, Any]] = []
    if isinstance(roles, dict):
        for role in roles.get("roles", []):
            if isinstance(role, dict):
                violations.extend(check_role_contract(role))
    if isinstance(projection, dict):
        violations.extend(check_projection_candidate(projection))

    role_rows = []
    if isinstance(roles, dict):
        for role in roles.get("roles", []):
            if not isinstance(role, dict):
                continue
            role_rows.append(
                {
                    "recursor_id": role.get("recursor_id"),
                    "readiness_status": role.get("readiness_status"),
                    "default_kind": role.get("default_form", {}).get("kind"),
                    "arena_eligible": role.get("default_form", {}).get("arena_eligible"),
                    "projection_status": role.get("codex_projection", {}).get("status"),
                    "install_by_default": role.get("codex_projection", {}).get("install_by_default"),
                }
            )

    return {
        "schema_version": "recursor-readiness-projection/v1",
        "generated_at": _utc_now(),
        "workspace_root": str(root),
        "source_repo": str(agents),
        "status": _seed_status(violations, diagnostics),
        "roles": role_rows,
        "pair_activation_status": pair.get("activation_status") if isinstance(pair, dict) else None,
        "projection_status": projection.get("projection_status") if isinstance(projection, dict) else None,
        "install_by_default": projection.get("install_by_default") if isinstance(projection, dict) else None,
        "violations": violations,
        "diagnostics": diagnostics,
        "stop_lines": BOUNDARY_STOP_LINES,
    }


def build_recursor_boundary_scan_report(workspace_root: str | Path) -> Dict[str, Any]:
    """Build a boundary scan report for the recursor readiness surfaces."""
    projection = build_recursor_readiness_projection(workspace_root)
    violations = list(projection.get("violations", []))
    diagnostics = list(projection.get("diagnostics", []))
    status = _seed_status(violations, diagnostics)
    return {
        "schema_version": "recursor-boundary-scan-report/v1",
        "generated_at": _utc_now(),
        "workspace_root": projection["workspace_root"],
        "status": status,
        "violations": violations,
        "warnings": diagnostics + [
            {
                "kind": "readiness_not_runtime",
                "severity": "info",
                "message": "Recursor readiness surfaces are visible but not active runtime agents.",
            }
        ],
        "checked_stop_lines": BOUNDARY_STOP_LINES,
        "summary": {
            "role_count": len(projection.get("roles", [])),
            "pair_activation_status": projection.get("pair_activation_status"),
            "projection_status": projection.get("projection_status"),
            "install_by_default": projection.get("install_by_default"),
        },
    }


def build_recursor_projection_candidates(workspace_root: str | Path) -> Dict[str, Any]:
    """Read projection candidates, preserving candidate-only posture."""
    root = Path(workspace_root)
    agents = _repo(root, "aoa-agents")
    candidate = _read_json(agents / "config" / "codex_recursor_projection.candidate.json")
    if candidate is None:
        return {
            "schema_version": "recursor-projection-candidates-projection/v1",
            "generated_at": _utc_now(),
            "status": "warn",
            "candidate_agents": [],
            "violations": [],
            "diagnostics": [{"kind": "missing_projection_candidate"}],
        }
    if not isinstance(candidate, dict) or candidate.get("_error"):
        return {
            "schema_version": "recursor-projection-candidates-projection/v1",
            "generated_at": _utc_now(),
            "status": "fail",
            "candidate_agents": [],
            "violations": [{"kind": "invalid_projection_candidate", "message": str(candidate)}],
            "diagnostics": [],
        }
    violations = check_projection_candidate(candidate)
    return {
        "schema_version": "recursor-projection-candidates-projection/v1",
        "generated_at": _utc_now(),
        "status": boundary_status(violations),
        "projection_status": candidate.get("projection_status"),
        "install_by_default": candidate.get("install_by_default"),
        "requires_owner_review": candidate.get("requires_owner_review"),
        "candidate_agents": candidate.get("candidate_agents", []),
        "violations": violations,
        "diagnostics": [],
    }
