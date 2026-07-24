#!/usr/bin/env python3
"""Shared deterministic routing derivation helpers.

The implementation is byte-compatible with the pinned predecessor while the
SDK remains a non-publishing shadow producer. Embedded compatibility
provenance changes only at the explicit G5 owner switch.
"""

from __future__ import annotations

import json
import os
import posixpath
import re
from pathlib import Path
from typing import Any, Iterable

import yaml


REPO_ROOT = Path(__file__).resolve().parents[4]
ACTIVE_KINDS = ("technique", "skill", "eval", "memo")
RESERVED_KINDS: tuple[str, ...] = ()
ALL_KINDS = ACTIVE_KINDS + RESERVED_KINDS
PAIRABLE_KINDS = ("technique", "skill", "eval")
RECOMMENDED_HOP_KINDS = ("technique", "skill", "eval")
AGENTS_REPO = "aoa-agents"
PLAYBOOKS_REPO = "aoa-playbooks"
KAG_REPO = "aoa-kag"
SDK_REPO = "aoa-sdk"
STATS_REPO = "aoa-stats"
PROFILE_REPO = "8Dionysus"
DIONYSUS_REPO = "Dionysus"
ABYSS_STACK_REPO = "abyss-stack"
AOA_ROOT_REPO = "Agents-of-Abyss"
TOS_REPO = "Tree-of-Sophia"
CANONICAL_REPO_BY_KIND = {
    "technique": "aoa-techniques",
    "skill": "aoa-skills",
    "eval": "aoa-evals",
    "memo": "aoa-memo",
}
KNOWN_REPOS = (
    "aoa-routing",
    AOA_ROOT_REPO,
    TOS_REPO,
    AGENTS_REPO,
    PLAYBOOKS_REPO,
    KAG_REPO,
    SDK_REPO,
    STATS_REPO,
    PROFILE_REPO,
    DIONYSUS_REPO,
    ABYSS_STACK_REPO,
) + tuple(CANONICAL_REPO_BY_KIND.values())


def default_dependency_root(repo_name: str, routing_root: Path | None = None) -> Path:
    """Resolve a sibling repo from a checkout, worktree, or live workspace root."""
    base_root = (routing_root or REPO_ROOT).resolve()
    candidates: list[Path] = []

    def add_candidate(path: Path) -> None:
        if path not in candidates:
            candidates.append(path)

    if repo_name == ABYSS_STACK_REPO:
        for env_name in ("ABYSS_STACK_ROOT", "AOA_SOURCE_ROOT"):
            configured_root = os.environ.get(env_name)
            if configured_root:
                add_candidate(Path(configured_root).expanduser())
        add_candidate(Path.home() / "src" / repo_name)

    for env_name in ("OS_ABYSS_ROOT", "AOA_WORKSPACE_ROOT"):
        configured_root = os.environ.get(env_name)
        if configured_root:
            repo_path = Path(configured_root).expanduser() / repo_name
            if repo_name == ABYSS_STACK_REPO:
                add_candidate(repo_path / "Configs")
            add_candidate(repo_path)

    for base in (base_root, base_root.parent, *base_root.parents):
        repo_path = base / repo_name
        if repo_name == ABYSS_STACK_REPO:
            add_candidate(repo_path / "Configs")
        add_candidate(repo_path)

    conventional_workspace = Path("/srv/AbyssOS")
    if (conventional_workspace / "AOA_WORKSPACE_ROOT").is_file():
        repo_path = conventional_workspace / repo_name
        if repo_name == ABYSS_STACK_REPO:
            add_candidate(repo_path / "Configs")
        add_candidate(repo_path)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    if repo_name == ABYSS_STACK_REPO:
        return Path.home() / "src" / repo_name
    return base_root.parent / repo_name


KIND_ORDER = {kind: index for index, kind in enumerate(ALL_KINDS)}
RELATION_REQUIRES = "requires"
RELATION_REQUIRED_BY = "required_by"
PENDING_TECHNIQUE_PREFIX = "AOA-T-PENDING-"
KAG_SOURCE_LIFT_TECHNIQUE_IDS = (
    "AOA-T-0018",
    "AOA-T-0019",
    "AOA-T-0020",
    "AOA-T-0021",
    "AOA-T-0022",
)
KAG_SOURCE_LIFT_TECHNIQUE_SET = set(KAG_SOURCE_LIFT_TECHNIQUE_IDS)
DIRECT_RELATION_TYPES = (
    "requires",
    "complements",
    "supersedes",
    "conflicts_with",
    "used_together_for",
    "derived_from",
    "shares_contract_with",
)
DIRECT_RELATION_TYPES_SET = set(DIRECT_RELATION_TYPES)
MODEL_TIER_SOURCE_REPO = AGENTS_REPO
MODEL_TIER_REGISTRY_PATH = "generated/model_tier_registry.json"
AGENT_REGISTRY_PATH = "generated/agent_registry.min.json"
RUNTIME_SEAM_BINDINGS_PATH = "generated/runtime_seam_bindings.json"
PLAYBOOK_REGISTRY_PATH = "generated/playbook_registry.min.json"
PLAYBOOK_PORTFOLIO_PATH = (
    "mechanics/portfolio-governance/parts/lifecycle-and-portfolio/docs/playbook-portfolio.md"
)
FEDERATION_SPINE_ROOT = "mechanics/boundary-bridge/parts/federation-spine"
FEDERATION_SPINE_PATH = f"{FEDERATION_SPINE_ROOT}/generated/federation_spine.min.json"
FEDERATION_SPINE_AUTHORITY_PATH = f"{FEDERATION_SPINE_ROOT}/docs/federation-spine.md"
AOA_ECOSYSTEM_REGISTRY_PATH = "generated/ecosystem_registry.min.json"
AOA_CENTER_ENTRY_MAP_PATH = "generated/center_entry_map.min.json"
PAIRING_SURFACE_REPO = "aoa-routing"
PAIRING_SURFACE_FILE = "generated/pairing_hints.min.json"
TINY_MODEL_ENTRYPOINTS_FILE = "generated/tiny_model_entrypoints.json"
FEDERATION_ENTRYPOINTS_FILE = "generated/federation_entrypoints.min.json"
RETURN_NAVIGATION_HINTS_FILE = "generated/return_navigation_hints.min.json"
QUEST_DISPATCH_HINTS_FILE = "generated/quest_dispatch_hints.min.json"
MEMO_INSPECT_SURFACE_FILE = "generated/memory/memory_catalog.min.json"
MEMO_EXPAND_SURFACE_FILE = "generated/memory/memory_sections.full.json"
MEMO_OBJECT_INSPECT_SURFACE_FILE = "generated/memory-objects/memory_object_catalog.min.json"
MEMO_OBJECT_CAPSULE_SURFACE_FILE = "generated/memory-objects/memory_object_capsules.json"
MEMO_OBJECT_EXPAND_SURFACE_FILE = "generated/memory-objects/memory_object_sections.full.json"
MEMO_CAPSULE_RECALL_MODES = ("semantic", "lineage")
DEFAULT_MEMO_RECALL_MODE = "semantic"
ROUTER_READY_RECALL_CONTRACT_PREFIX = "recall_contract.router."
MEMO_OBJECT_RECALL_FAMILY = "memory_objects"
MEMO_OBJECT_RECALL_DEFAULT_MODE = "working"
MEMO_OBJECT_RETURN_READY_CONTRACT = "examples/recall/recall_contract.object.working.return.json"
MEMO_OBJECT_RECALL_CONTRACTS_BY_MODE = {
    "working": "examples/recall/recall_contract.object.working.json",
    "semantic": "examples/recall/recall_contract.object.semantic.json",
    "lineage": "examples/recall/recall_contract.object.lineage.json",
}
KAG_DEFAULT_ENTRYPOINT_ID = "AOA-T-0019"
FEDERATION_ROOT_IDS = ("aoa-root", "tos-root")
FEDERATION_ACTIVE_ENTRY_KINDS = (
    "agent",
    "tier",
    "playbook",
    "kag_view",
    "source_route",
    "runtime_surface",
    "orientation_surface",
)
FEDERATION_DECLARED_ENTRY_KINDS = ("tos_node",)
FEDERATION_DEFAULT_AGENT_ENTRY_ID = "AOA-A-0001"
FEDERATION_DEFAULT_TIER_ENTRY_ID = "router"
FEDERATION_DEFAULT_PLAYBOOK_ENTRY_ID = "AOA-P-0008"
FEDERATION_DEFAULT_KAG_VIEW_ENTRY_ID = "aoa-techniques"
FEDERATION_DEFAULT_SOURCE_ROUTE_ENTRY_ID = "dionysus-source-route"
FEDERATION_DEFAULT_RUNTIME_SURFACE_ENTRY_ID = "aoa-sdk-control-plane"
FEDERATION_DEFAULT_ORIENTATION_SURFACE_ENTRY_ID = "8dionysus-public-route-map"
DIONYSUS_SOURCE_ROUTE_ANCHOR_PATH = (
    "docs/decisions/DION-D-0001-conversational-self-portrait.md"
)
AOA_SDK_WORKSPACE_TOML_PATH = ".aoa/workspace.toml"
AOA_SDK_WORKSPACE_CONTROL_PLANE_PATH = "generated/workspace_control_plane.min.json"
AOA_SDK_BOUNDARIES_PATH = "docs/boundaries.md"
AOA_STATS_SUMMARY_SURFACE_CATALOG_PATH = "generated/summary_surface_catalog.min.json"
AOA_STATS_ARCHITECTURE_PATH = "docs/ARCHITECTURE.md"
PROFILE_PUBLIC_ROUTE_MAP_PATH = "generated/public_route_map.min.json"
PROFILE_PUBLIC_ENTRY_POSTURE_PATH = "docs/PUBLIC_ENTRY_POSTURE.md"
ABYSS_STACK_DIAGNOSTIC_SURFACE_ROOT = "mechanics/diagnostic-spine/parts/diagnostic-surfaces"
ABYSS_STACK_DIAGNOSTIC_SESSION_PATH = (
    f"{ABYSS_STACK_DIAGNOSTIC_SURFACE_ROOT}/examples/diagnostic_session.min.example.json"
)
ABYSS_STACK_DIAGNOSTIC_SURFACE_CATALOG_PATH = (
    f"{ABYSS_STACK_DIAGNOSTIC_SURFACE_ROOT}/generated/diagnostic_surface_catalog.min.json"
)
ABYSS_STACK_DIAGNOSTIC_SPINE_PATH = (
    f"{ABYSS_STACK_DIAGNOSTIC_SURFACE_ROOT}/docs/DIAGNOSTIC_SPINE.md"
)
TOS_TINY_ENTRY_ROUTE_PATH = "ToS/public-compatibility/tos_tiny_entry_route.example.json"
TOS_ROOT_ENTRY_MAP_PATH = "ToS/derived-exports/root_entry_map.min.json"
TOS_TINY_ENTRY_ROUTE_ID = "tos-tiny-entry.zarathustra-prologue"
TOS_TINY_ENTRY_PRIMARY_HOP_FIELD = "bounded_hop"
TOS_TINY_ENTRY_LEGACY_HOP_FIELD = "lineage_or_context_hop"
TOS_TINY_ENTRY_DOCTRINE_PATH = "ToS/zarathustra/public-entry/TINY_ENTRY_ROUTE.md"
AOA_TECHNIQUES_KAG_VIEW_ENTRY_SURFACE_REF = (
    "aoa-techniques/generated/repo_doc_surface_manifest.min.json"
)
AOA_TECHNIQUES_KAG_VIEW_OBJECT_SURFACE_REF = "aoa-techniques/generated/technique_catalog.min.json"
AOA_TECHNIQUES_KAG_VIEW_EXAMPLE_OBJECT_IDS = ("AOA-T-0001", "AOA-T-0002", "AOA-T-0003")
AOA_TECHNIQUES_KAG_EXPORT_REF = "aoa-techniques/generated/kag_export.min.json"
AOA_TECHNIQUES_KAG_COMPACT_KIND = "technique"
AOA_TECHNIQUES_KAG_COMPACT_ENTRY_SURFACE_REF = "aoa-techniques/generated/technique_capsules.json"
AOA_TECHNIQUES_KAG_COMPACT_OBJECT_ID = "AOA-T-0043"
TECHNIQUE_KIND_SECOND_CUT_SOURCE_REPO = "aoa-techniques"
TECHNIQUE_KIND_SECOND_CUT_SURFACE_FILE = "generated/technique_kind_manifest.min.json"
TECHNIQUE_KIND_SECOND_CUT_COLLECTION_KEY = "kinds"
TECHNIQUE_KIND_SECOND_CUT_MATCH_FIELD = "kind"
TECHNIQUE_KIND_SECOND_CUT_SELECTION_AXIS = "kind"
TECHNIQUE_KIND_SECOND_CUT_PREREQUISITE_AXES = ("domain",)
TOS_KAG_VIEW_ENTRY_ID = TOS_REPO
TOS_KAG_VIEW_ENTRY_SURFACE_REFS = (
    "Tree-of-Sophia/README.md",
    "Tree-of-Sophia/ToS/zarathustra/public-entry/TINY_ENTRY_ROUTE.md",
)
TOS_KAG_VIEW_OBJECT_SURFACE_REF = (
    "Tree-of-Sophia/ToS/public-compatibility/tos_tiny_entry_route.example.json"
)
TOS_KAG_EXPORT_REF = "Tree-of-Sophia/ToS/derived-exports/kag_export.min.json"
TOS_KAG_COMPACT_KIND = "source_node"
TOS_KAG_COMPACT_ENTRY_SURFACE_REF = "Tree-of-Sophia/ToS/public-compatibility/source_node.example.json"
TOS_KAG_COMPACT_OBJECT_ID = "tos.source.thus-spoke-zarathustra.prologue"
TOS_KAG_VIEW_PLAYBOOK_ENTRY_ID = "AOA-P-0009"
TOS_ROUTE_RETRIEVAL_SURFACE_ID = "AOA-K-0011"
TOS_ROUTE_RETRIEVAL_SURFACE_NAME = "tos-zarathustra-route-retrieval-surface"
TOS_ROUTE_RETRIEVAL_SURFACE_REF = (
    "mechanics/boundary-bridge/parts/tos-retrieval-axis/generated/"
    "tos_zarathustra_route_retrieval_pack.min.json"
)
TOS_ROUTE_RETRIEVAL_MATCH_KEY = "retrieval_id"
TOS_ROUTE_RETRIEVAL_ID = "AOA-K-0011::thus-spoke-zarathustra/prologue-1"
TOS_ROUTE_RETRIEVAL_ROUTE_ID = "thus-spoke-zarathustra/prologue-1"
EXPECTED_TOS_KAG_VIEW_ADJUNCT = {
    "surface_id": TOS_ROUTE_RETRIEVAL_SURFACE_ID,
    "surface_name": TOS_ROUTE_RETRIEVAL_SURFACE_NAME,
    "surface_ref": TOS_ROUTE_RETRIEVAL_SURFACE_REF,
    "match_key": TOS_ROUTE_RETRIEVAL_MATCH_KEY,
    "target_value": TOS_ROUTE_RETRIEVAL_ID,
    "route_id": TOS_ROUTE_RETRIEVAL_ROUTE_ID,
}
AOA_CENTER_ROUTE_IDS = (
    "center-overview",
    "public-contour",
    "source-of-truth-rules",
)
AOA_CENTER_ROUTE_IDS_BY_SCHEMA = {
    "aoa_center_entry_map_v1": AOA_CENTER_ROUTE_IDS,
    "aoa_center_entry_map_v2": (
        "first-reading",
        "public-claim-validation",
        "ownership-routing",
    ),
}
TOS_ROOT_ROUTE_IDS = (
    "current-tiny-entry",
    "tree-first-model",
    "bounded-export",
)
OLD_STAGE_ROUTE_LABEL = "wa" + "ve"
OLD_BOOTSTRAP_ROUTE_LABEL = "se" + "ed"
FALLBACK_ROUTER_KIND = "technique"
RETURN_REASONS_BY_THIN_KIND = {
    "technique": ("artifact_contract_lost", "source_boundary_lost", "reroute_required"),
    "skill": ("artifact_contract_lost", "verification_lost", "source_boundary_lost"),
    "eval": ("verification_lost", "artifact_contract_lost", "source_boundary_lost"),
    "memo": ("checkpoint_continuity_needed", "artifact_contract_lost", "source_boundary_lost"),
}
RETURN_REASONS_BY_ROOT_ID = {
    "aoa-root": ("authority_unclear", "source_boundary_lost", "reroute_required"),
    "tos-root": ("authority_unclear", "source_boundary_lost", "reroute_required"),
}
RETURN_REASONS_BY_FEDERATION_KIND = {
    "agent": ("authority_unclear", "artifact_contract_lost", "reroute_required"),
    "tier": ("authority_unclear", "artifact_contract_lost", "reroute_required"),
    "playbook": ("authority_unclear", "artifact_contract_lost", "reroute_required"),
    "kag_view": ("authority_unclear", "source_boundary_lost", "reroute_required"),
    "source_route": ("authority_unclear", "source_boundary_lost", "reroute_required"),
    "runtime_surface": ("authority_unclear", "artifact_contract_lost", "reroute_required"),
    "orientation_surface": ("authority_unclear", "source_boundary_lost", "reroute_required"),
}
TIER_PHASE_ORDER = (
    "route",
    "plan",
    "do",
    "verify",
    "transition",
    "deep",
    "distill",
)
ROUTING_READMODEL_ARTIFACT_IDENTITY = {
    "artifact_class": "thin_routing_readmodel_bundle",
    "surface_state": "public_generated_routing_surfaces",
    "owner_repo": "aoa-routing",
    "authority_ref": "README.md#generated-outputs",
    "producer": "scripts/build_router.py from sibling generated catalogs, routing schemas, and bounded route mechanics",
    "consumer_expectation": (
        "Consumers verify artifact_identity, router_version, schema conformance, build_router --check, "
        "validate_router, and source-owned next-hop refs before using routing surfaces for dispatch."
    ),
    "privacy_boundary": "public route refs and compact summaries only; no private source payloads, secrets, live runtime state, or owner-corpus copies",
    "content_identity": "generated routing family rooted at generated/aoa_router.min.json and rebuilt by scripts/build_router.py",
    "abi_epoch": "aoa_routing_thin_router_v1",
    "contract_version": "routing/core/schemas/aoa-router.schema.json@aoa_routing_thin_router_v1#artifact_identity",
    "trust_layer": [
        "abi_contract_signature",
        "sbom",
        "slsa_in_toto",
    ],
    "verification": [
        "python scripts/validate_router.py",
        "python scripts/build_router.py --check",
        "python scripts/release_check.py",
    ],
}
QUEST_ROUTING_SOURCE_REPOS = (
    "aoa-techniques",
    "aoa-skills",
    "aoa-evals",
)
QUEST_ROUTING_ACTIONS_ENABLED = ("inspect", "expand", "handoff")
QUEST_ROUTING_CONTOUR_SCOPE = "source-only"
QUEST_ROUTING_CLOSED_STATES = frozenset({"done", "dropped"})
QUEST_ROUTING_EXPAND_DOC_BY_REPO = {
    "aoa-techniques": "mechanics/growth-cycle/parts/questbook-integration/README.md",
    "aoa-skills": "mechanics/questbook/docs/QUESTBOOK_SKILL_INTEGRATION.md",
    "aoa-evals": "docs/operations/QUESTBOOK_EVAL_INTEGRATION.md",
}
TASK_TO_TIER_HINT_SPECS = (
    {
        "task_family": "task-triage",
        "preferred_tier": "router",
        "fallback_tier": "planner",
        "use_when": "need the fastest classification of task shape, risk, and smallest next step",
    },
    {
        "task_family": "bounded-plan-shaping",
        "preferred_tier": "planner",
        "fallback_tier": "conductor",
        "use_when": "need an explicit bounded plan, checks, and escalation boundaries",
    },
    {
        "task_family": "bounded-execution",
        "preferred_tier": "executor",
        "fallback_tier": "planner",
        "use_when": "need the current bounded slice executed after the route and plan are already explicit",
    },
    {
        "task_family": "verification-pass",
        "preferred_tier": "verifier",
        "fallback_tier": "conductor",
        "use_when": "need contradiction checks, output review, or a named continue-stop-escalate decision",
    },
    {
        "task_family": "tier-transition-governance",
        "preferred_tier": "conductor",
        "fallback_tier": "verifier",
        "use_when": "need a route-level decision about continue, pause, escalate, or distill",
    },
    {
        "task_family": "high-cost-synthesis",
        "preferred_tier": "deep",
        "fallback_tier": "conductor",
        "use_when": "need rare deep synthesis, contradiction arbitration, or high-cost final judgment",
    },
    {
        "task_family": "distillation-and-writeback-prep",
        "preferred_tier": "archivist",
        "fallback_tier": "conductor",
        "use_when": "need summaries, decisions, and memory candidates distilled after a non-trivial run",
    },
)


class RouterError(RuntimeError):
    """Raised when build or validation inputs are inconsistent."""


def relative_posix(path: Path, root: Path | None = None) -> str:
    target_root = root or REPO_ROOT
    try:
        return path.relative_to(target_root).as_posix()
    except ValueError:
        return path.as_posix()


def load_json_file(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise RouterError(f"{relative_posix(path)} is missing") from exc
    except json.JSONDecodeError as exc:
        raise RouterError(f"{relative_posix(path)} is invalid JSON: {exc}") from exc


def load_yaml_file(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    except FileNotFoundError as exc:
        raise RouterError(f"{relative_posix(path)} is missing") from exc
    except yaml.YAMLError as exc:
        raise RouterError(f"{relative_posix(path)} is invalid YAML: {exc}") from exc


def parse_frontmatter_markdown(path: Path) -> tuple[dict[str, Any], str]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RouterError(f"{relative_posix(path)} is missing") from exc

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise RouterError(
            f"{relative_posix(path)} is missing YAML frontmatter opening delimiter"
        )

    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        raise RouterError(
            f"{relative_posix(path)} is missing YAML frontmatter closing delimiter"
        )

    frontmatter_text = "\n".join(lines[1:closing_index])
    body = "\n".join(lines[closing_index + 1 :])

    try:
        metadata = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as exc:
        raise RouterError(f"{relative_posix(path)} has invalid frontmatter YAML: {exc}") from exc

    if not isinstance(metadata, dict):
        raise RouterError(f"{relative_posix(path)} frontmatter must parse to a mapping")
    return metadata, body


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(
        payload,
        ensure_ascii=False,
        indent=None,
        separators=(",", ":"),
        sort_keys=False,
    )
    path.write_text(f"{text}\n", encoding="utf-8")


def ensure_mapping(data: Any, location: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise RouterError(f"{location} must be a mapping")
    return data


def ensure_list(data: Any, location: str) -> list[Any]:
    if not isinstance(data, list):
        raise RouterError(f"{location} must be a list")
    return data


def ensure_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RouterError(f"{location} must be a non-empty string")
    return value


def select_aoa_center_route_ids(payload: dict[str, Any], location: str) -> tuple[str, str, str]:
    schema_version = ensure_string(payload.get("schema_version"), f"{location}.schema_version")
    route_ids = {
        ensure_string(route.get("route_id"), f"{location}.routes[{index}].route_id")
        for index, route in enumerate(ensure_list(payload.get("routes"), f"{location}.routes"))
        if isinstance(route, dict)
    }
    expected_route_ids = AOA_CENTER_ROUTE_IDS_BY_SCHEMA.get(schema_version)
    if expected_route_ids is None:
        raise RouterError(f"{location}.schema_version has unsupported value {schema_version!r}")
    missing = [route_id for route_id in expected_route_ids if route_id not in route_ids]
    if missing:
        raise RouterError(
            f"{location}.routes missing required center route ids: {', '.join(missing)}"
        )
    return expected_route_ids


def ensure_bool(value: Any, location: str) -> bool:
    if not isinstance(value, bool):
        raise RouterError(f"{location} must be a boolean")
    return value


def ensure_int(value: Any, location: str) -> int:
    if not isinstance(value, int):
        raise RouterError(f"{location} must be an integer")
    return value


def ensure_string_list(values: Any, location: str) -> list[str]:
    items = ensure_list(values, location)
    result: list[str] = []
    for index, item in enumerate(items):
        result.append(ensure_string(item, f"{location}[{index}]"))
    return result


def require_keys(data: dict[str, Any], keys: Iterable[str], location: str) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise RouterError(f"{location} is missing required keys: {', '.join(missing)}")


def normalize_repo_name(raw: str) -> str:
    text = raw.strip()
    if not text:
        raise RouterError("repo value must not be empty")
    if text in KNOWN_REPOS:
        return text

    if text.startswith("git@"):
        text = text.split(":", 1)[-1]
    if "://" in text:
        text = text.split("://", 1)[-1]
        if "/" in text:
            text = text.split("/", 1)[-1]
    text = text.rstrip("/")
    if text.endswith(".git"):
        text = text[:-4]

    candidate = text.rsplit("/", 1)[-1]
    if candidate in KNOWN_REPOS:
        return candidate

    raise RouterError(f"unsupported repo reference '{raw}'")


def ensure_repo_relative_path(raw_path: str, location: str) -> str:
    value = ensure_string(raw_path, location)
    if re.match(r"^[A-Za-z]:[/\\\\]", value) or value.startswith(("/", "\\\\")):
        raise RouterError(f"{location} must be repo-relative, not absolute")
    normalized = value.replace("\\", "/")
    if ".." in Path(normalized).parts:
        raise RouterError(f"{location} must not traverse outside the repository root")
    canonical = posixpath.normpath(normalized)
    if canonical == ".":
        raise RouterError(f"{location} must be a repo-relative file path")
    return canonical


def ensure_repo_qualified_ref(value: Any, location: str) -> tuple[str, str]:
    raw_value = ensure_string(value, location)
    repo, separator, ref = raw_value.partition(":")
    if separator != ":":
        raise RouterError(f"{location} must use '<repo>:<path>' form")
    normalized_repo = normalize_repo_name(repo)
    normalized_ref = ensure_repo_relative_path(ref, f"{location}.path")
    return normalized_repo, normalized_ref


def make_repo_qualified_ref(repo: str, relative_path: str) -> str:
    normalized_repo = normalize_repo_name(repo)
    normalized_path = ensure_repo_relative_path(relative_path, f"{normalized_repo}.path")
    return f"{normalized_repo}:{normalized_path}"


def ensure_markdown_file(path: Path, location: str) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RouterError(f"{location} is missing") from exc
    if not text.strip():
        raise RouterError(f"{location} must not be empty")


def ensure_text_file(path: Path, location: str) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RouterError(f"{location} is missing") from exc
    if not text.strip():
        raise RouterError(f"{location} must not be empty")


def ensure_tos_route_surface_path(
    raw_path: Any,
    location: str,
    *,
    tos_root: Path,
    allow_null: bool = False,
) -> str | None:
    if raw_path is None:
        if allow_null:
            return None
        raise RouterError(f"{location} must be a repo-relative Tree-of-Sophia path")
    relative_path = ensure_repo_relative_path(raw_path, location)
    if ":" in relative_path:
        raise RouterError(f"{location} must stay Tree-of-Sophia-relative and must not use repo-qualified refs")
    if relative_path.startswith(("aoa-routing/", "aoa-kag/")):
        raise RouterError(f"{location} must stay inside Tree-of-Sophia and must not point at downstream repos")
    if not (tos_root / relative_path).exists():
        raise RouterError(f"{location} target 'Tree-of-Sophia/{relative_path}' is missing")
    return relative_path


def load_tos_tiny_entry_hop_surface(
    payload: dict[str, Any],
    location: str,
    *,
    tos_root: Path,
) -> str:
    bounded_hop = ensure_tos_route_surface_path(
        payload.get(TOS_TINY_ENTRY_PRIMARY_HOP_FIELD),
        f"{location}.{TOS_TINY_ENTRY_PRIMARY_HOP_FIELD}",
        tos_root=tos_root,
        allow_null=True,
    )
    legacy_hop = ensure_tos_route_surface_path(
        payload.get(TOS_TINY_ENTRY_LEGACY_HOP_FIELD),
        f"{location}.{TOS_TINY_ENTRY_LEGACY_HOP_FIELD}",
        tos_root=tos_root,
        allow_null=True,
    )
    if bounded_hop is None and legacy_hop is None:
        raise RouterError(
            f"{location} must define '{TOS_TINY_ENTRY_PRIMARY_HOP_FIELD}' or "
            f"'{TOS_TINY_ENTRY_LEGACY_HOP_FIELD}'"
        )
    if bounded_hop is not None and legacy_hop is not None and bounded_hop != legacy_hop:
        raise RouterError(
            f"{location}.{TOS_TINY_ENTRY_PRIMARY_HOP_FIELD} and "
            f"{location}.{TOS_TINY_ENTRY_LEGACY_HOP_FIELD} must resolve to the same "
            "Tree-of-Sophia surface during transition"
        )
    return bounded_hop or legacy_hop  # type: ignore[return-value]


def load_tos_tiny_entry_route(tos_root: Path) -> tuple[str, dict[str, Any]]:
    route_path = tos_root / TOS_TINY_ENTRY_ROUTE_PATH
    location = f"{TOS_REPO}/{TOS_TINY_ENTRY_ROUTE_PATH}"
    payload = ensure_mapping(load_json_file(route_path), location)

    route_id = ensure_string(payload.get("route_id"), f"{location}.route_id")
    if route_id != TOS_TINY_ENTRY_ROUTE_ID:
        raise RouterError(
            f"{location}.route_id must stay '{TOS_TINY_ENTRY_ROUTE_ID}' in the current routing contour"
        )

    root_surface = ensure_tos_route_surface_path(
        payload.get("root_surface"),
        f"{location}.root_surface",
        tos_root=tos_root,
    )
    if root_surface != "README.md":
        raise RouterError(f"{location}.root_surface must stay 'README.md' in the current routing contour")

    ensure_string(payload.get("node_kind"), f"{location}.node_kind")
    ensure_string(payload.get("node_id"), f"{location}.node_id")
    ensure_tos_route_surface_path(
        payload.get("capsule_surface"),
        f"{location}.capsule_surface",
        tos_root=tos_root,
    )
    ensure_tos_route_surface_path(
        payload.get("authority_surface"),
        f"{location}.authority_surface",
        tos_root=tos_root,
    )
    load_tos_tiny_entry_hop_surface(payload, location, tos_root=tos_root)
    ensure_tos_route_surface_path(
        payload.get("fallback"),
        f"{location}.fallback",
        tos_root=tos_root,
    )
    ensure_string(payload.get("non_identity_boundary"), f"{location}.non_identity_boundary")
    return TOS_TINY_ENTRY_ROUTE_PATH, payload


def is_pending_technique_id(identifier: str) -> bool:
    return identifier.startswith(PENDING_TECHNIQUE_PREFIX)


def sort_registry_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(entries, key=lambda entry: (KIND_ORDER[entry["kind"]], entry["id"]))


def sort_hops(hops: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(hops, key=lambda hop: (KIND_ORDER[hop["kind"]], hop["id"], hop["relation"]))


def load_technique_catalog_entries(techniques_root: Path) -> tuple[str, list[dict[str, Any]]]:
    for filename in ("technique_catalog.json", "technique_catalog.min.json"):
        catalog_path = techniques_root / "generated" / filename
        if not catalog_path.exists():
            continue
        payload = ensure_mapping(load_json_file(catalog_path), relative_posix(catalog_path))
        return catalog_path.relative_to(techniques_root).as_posix(), ensure_list(
            payload.get("techniques"),
            f"{relative_posix(catalog_path)}.techniques",
        )
    raise RouterError(
        f"{relative_posix(techniques_root / 'generated' / 'technique_catalog.json')} is missing"
    )


def load_model_tier_registry(
    agents_root: Path,
    registry_relative_path: str = MODEL_TIER_REGISTRY_PATH,
) -> tuple[str, dict[str, dict[str, str]]]:
    normalized_path = ensure_repo_relative_path(registry_relative_path, "tier_registry_path")
    registry_path = agents_root / normalized_path
    location = relative_posix(registry_path, agents_root)
    payload = ensure_mapping(load_json_file(registry_path), location)
    model_tiers = ensure_list(payload.get("model_tiers"), f"{location}.model_tiers")

    tier_index: dict[str, dict[str, str]] = {}
    for index, item in enumerate(model_tiers):
        tier_location = f"{location}.model_tiers[{index}]"
        tier = ensure_mapping(item, tier_location)
        require_keys(tier, ("id", "artifact_requirement"), tier_location)
        tier_id = ensure_string(tier["id"], f"{tier_location}.id")
        if tier_id in tier_index:
            raise RouterError(f"{tier_location}.id duplicates tier '{tier_id}'")
        tier_index[tier_id] = {
            "artifact_requirement": ensure_string(
                tier["artifact_requirement"],
                f"{tier_location}.artifact_requirement",
            )
        }
    return normalized_path, tier_index


def load_agent_registry_entries(agents_root: Path) -> tuple[str, list[dict[str, Any]]]:
    registry_path = agents_root / AGENT_REGISTRY_PATH
    location = relative_posix(registry_path, agents_root)
    payload = ensure_mapping(load_json_file(registry_path), location)
    agents = ensure_list(payload.get("agents"), f"{location}.agents")

    entries: list[dict[str, Any]] = []
    for index, item in enumerate(agents):
        agent_location = f"{location}.agents[{index}]"
        agent = ensure_mapping(item, agent_location)
        require_keys(agent, ("id", "name", "summary"), agent_location)
        entries.append(agent)
    return AGENT_REGISTRY_PATH, entries


def load_model_tier_entries(
    agents_root: Path,
    registry_relative_path: str = MODEL_TIER_REGISTRY_PATH,
) -> tuple[str, list[dict[str, Any]]]:
    normalized_path = ensure_repo_relative_path(registry_relative_path, "tier_registry_path")
    registry_path = agents_root / normalized_path
    location = relative_posix(registry_path, agents_root)
    payload = ensure_mapping(load_json_file(registry_path), location)
    model_tiers = ensure_list(payload.get("model_tiers"), f"{location}.model_tiers")

    entries: list[dict[str, Any]] = []
    for index, item in enumerate(model_tiers):
        tier_location = f"{location}.model_tiers[{index}]"
        tier = ensure_mapping(item, tier_location)
        require_keys(tier, ("id", "summary", "artifact_requirement"), tier_location)
        entries.append(tier)
    return normalized_path, entries


def load_runtime_seam_bindings(agents_root: Path) -> tuple[str, list[dict[str, Any]]]:
    bindings_path = agents_root / RUNTIME_SEAM_BINDINGS_PATH
    location = relative_posix(bindings_path, agents_root)
    payload = ensure_mapping(load_json_file(bindings_path), location)
    bindings = ensure_list(payload.get("bindings"), f"{location}.bindings")

    entries: list[dict[str, Any]] = []
    for index, item in enumerate(bindings):
        binding_location = f"{location}.bindings[{index}]"
        binding = ensure_mapping(item, binding_location)
        require_keys(binding, ("phase", "tier_id", "role_names", "artifact_type"), binding_location)
        entries.append(binding)
    return RUNTIME_SEAM_BINDINGS_PATH, entries


def load_playbook_registry_entries(playbooks_root: Path) -> tuple[str, list[dict[str, Any]]]:
    registry_path = playbooks_root / PLAYBOOK_REGISTRY_PATH
    location = relative_posix(registry_path, playbooks_root)
    payload = ensure_mapping(load_json_file(registry_path), location)
    playbooks = ensure_list(payload.get("playbooks"), f"{location}.playbooks")

    entries: list[dict[str, Any]] = []
    for index, item in enumerate(playbooks):
        playbook_location = f"{location}.playbooks[{index}]"
        playbook = ensure_mapping(item, playbook_location)
        require_keys(
            playbook,
            ("id", "name", "summary", "participating_agents", "expected_artifacts"),
            playbook_location,
        )
        entries.append(playbook)
    return PLAYBOOK_REGISTRY_PATH, entries


def load_federation_spine_entries(kag_root: Path) -> tuple[str, list[dict[str, Any]]]:
    spine_path = kag_root / FEDERATION_SPINE_PATH
    location = relative_posix(spine_path, kag_root)
    payload = ensure_mapping(load_json_file(spine_path), location)
    entries = ensure_list(payload.get("repos"), f"{location}.repos")

    # Accept the current compact aoa-kag spine shape while keeping the
    # router-facing KAG view cards stable for this routing contour.
    def normalize_adjunct_surfaces(
        repo_name: str,
        value: Any,
        adjunct_location: str,
    ) -> list[dict[str, str]]:
        adjunct_items = ensure_list(value, adjunct_location)
        normalized: list[dict[str, str]] = []
        for adjunct_index, raw_adjunct in enumerate(adjunct_items):
            item_location = f"{adjunct_location}[{adjunct_index}]"
            adjunct = ensure_mapping(raw_adjunct, item_location)
            require_keys(
                adjunct,
                (
                    "surface_id",
                    "surface_name",
                    "surface_ref",
                    "match_key",
                    "target_value",
                    "route_id",
                ),
                item_location,
            )
            normalized.append(
                {
                    "surface_id": ensure_string(
                        adjunct["surface_id"], f"{item_location}.surface_id"
                    ),
                    "surface_name": ensure_string(
                        adjunct["surface_name"], f"{item_location}.surface_name"
                    ),
                    "surface_ref": ensure_repo_relative_path(
                        adjunct["surface_ref"], f"{item_location}.surface_ref"
                    ),
                    "match_key": ensure_string(
                        adjunct["match_key"], f"{item_location}.match_key"
                    ),
                    "target_value": ensure_string(
                        adjunct["target_value"], f"{item_location}.target_value"
                    ),
                    "route_id": ensure_string(
                        adjunct["route_id"], f"{item_location}.route_id"
                    ),
                }
            )
        return normalized

    def normalize_repo_entry(
        repo_entry: dict[str, Any], repo_location: str
    ) -> dict[str, Any]:
        if all(
            key in repo_entry
            for key in (
                "current_entry_surface_refs",
                "current_object_surface_ref",
                "example_object_ids",
            )
        ):
            require_keys(
                repo_entry,
                (
                    "repo",
                    "current_entry_surface_refs",
                    "current_object_surface_ref",
                    "example_object_ids",
                    "adjunct_surfaces",
                ),
                repo_location,
            )
            repo_name = normalize_repo_name(
                ensure_string(repo_entry["repo"], f"{repo_location}.repo")
            )
            return {
                **repo_entry,
                "repo": repo_name,
                "adjunct_surfaces": normalize_adjunct_surfaces(
                    repo_name,
                    repo_entry["adjunct_surfaces"],
                    f"{repo_location}.adjunct_surfaces",
                ),
            }

        require_keys(
            repo_entry,
            (
                "repo",
                "pilot_posture",
                "entry_surface_ref",
                "export_ref",
                "object_id",
                "adjunct_surfaces",
            ),
            repo_location,
        )
        repo_name = normalize_repo_name(
            ensure_string(repo_entry["repo"], f"{repo_location}.repo")
        )
        pilot_posture = ensure_string(
            repo_entry["pilot_posture"], f"{repo_location}.pilot_posture"
        )
        entry_surface_ref = ensure_string(repo_entry["entry_surface_ref"], f"{repo_location}.entry_surface_ref")
        export_ref = ensure_string(repo_entry["export_ref"], f"{repo_location}.export_ref")
        object_id = ensure_string(repo_entry["object_id"], f"{repo_location}.object_id")
        compact_kind = ensure_string(repo_entry.get("kind"), f"{repo_location}.kind")
        adjunct_surfaces = normalize_adjunct_surfaces(
            repo_name,
            repo_entry["adjunct_surfaces"],
            f"{repo_location}.adjunct_surfaces",
        )
        if pilot_posture != "source_owned_export_tiny":
            raise RouterError(
                f"{repo_location}.pilot_posture must stay 'source_owned_export_tiny' in the compact federation spine format"
            )

        if repo_name == FEDERATION_DEFAULT_KAG_VIEW_ENTRY_ID:
            expected = {
                "export_ref": AOA_TECHNIQUES_KAG_EXPORT_REF,
                "kind": AOA_TECHNIQUES_KAG_COMPACT_KIND,
                "entry_surface_ref": AOA_TECHNIQUES_KAG_COMPACT_ENTRY_SURFACE_REF,
                "object_id": AOA_TECHNIQUES_KAG_COMPACT_OBJECT_ID,
            }
            actual = {
                "export_ref": export_ref,
                "kind": compact_kind,
                "entry_surface_ref": entry_surface_ref,
                "object_id": object_id,
            }
            for key, expected_value in expected.items():
                if actual[key] != expected_value:
                    raise RouterError(
                        f"{repo_location}.{key} must stay '{expected_value}' in the compact federation spine format"
                    )
            return {
                **repo_entry,
                "pilot_posture": "existing_generated_surfaces",
                "current_entry_surface_refs": [
                    AOA_TECHNIQUES_KAG_VIEW_ENTRY_SURFACE_REF
                ],
                "current_object_surface_ref": AOA_TECHNIQUES_KAG_VIEW_OBJECT_SURFACE_REF,
                "example_object_ids": list(AOA_TECHNIQUES_KAG_VIEW_EXAMPLE_OBJECT_IDS),
                "adjunct_surfaces": adjunct_surfaces,
            }
        if repo_name == TOS_KAG_VIEW_ENTRY_ID:
            expected = {
                "export_ref": TOS_KAG_EXPORT_REF,
                "kind": TOS_KAG_COMPACT_KIND,
                "entry_surface_ref": TOS_KAG_COMPACT_ENTRY_SURFACE_REF,
                "object_id": TOS_KAG_COMPACT_OBJECT_ID,
            }
            actual = {
                "export_ref": export_ref,
                "kind": compact_kind,
                "entry_surface_ref": entry_surface_ref,
                "object_id": object_id,
            }
            for key, expected_value in expected.items():
                if actual[key] != expected_value:
                    raise RouterError(
                        f"{repo_location}.{key} must stay '{expected_value}' in the compact federation spine format"
                    )
            return {
                **repo_entry,
                "pilot_posture": "source_owned_tiny_entry_route",
                "current_entry_surface_refs": list(TOS_KAG_VIEW_ENTRY_SURFACE_REFS),
                "current_object_surface_ref": TOS_KAG_VIEW_OBJECT_SURFACE_REF,
                "example_object_ids": [TOS_TINY_ENTRY_ROUTE_ID],
                "adjunct_surfaces": adjunct_surfaces,
            }
        raise RouterError(
            f"{repo_location}.repo '{repo_name}' is not supported in the compact federation spine format"
        )

    repos: list[dict[str, Any]] = []
    for index, item in enumerate(entries):
        repo_location = f"{location}.repos[{index}]"
        repo_entry = ensure_mapping(item, repo_location)
        repos.append(normalize_repo_entry(repo_entry, repo_location))

    repo_index = {repo["repo"]: repo for repo in repos}
    aoa_techniques_entry = repo_index.get(FEDERATION_DEFAULT_KAG_VIEW_ENTRY_ID)
    if aoa_techniques_entry is None:
        raise RouterError(
            "federation spine must publish aoa-techniques in the current routing contour"
        )
    if aoa_techniques_entry.get("adjunct_surfaces") != []:
        raise RouterError(
            "aoa-techniques.adjunct_surfaces must stay [] in the current routing contour"
        )
    tos_entry = repo_index.get(TOS_KAG_VIEW_ENTRY_ID)
    if tos_entry is None:
        raise RouterError(
            "federation spine must publish Tree-of-Sophia in the current routing contour"
        )
    if tos_entry.get("adjunct_surfaces") != [EXPECTED_TOS_KAG_VIEW_ADJUNCT]:
        raise RouterError(
            "Tree-of-Sophia.adjunct_surfaces must publish exactly the bounded "
            "AOA-K-0011 adjunct in the current routing contour"
        )
    return FEDERATION_SPINE_PATH, repos


def load_ecosystem_registry_entries(aoa_root: Path) -> tuple[str, list[dict[str, Any]]]:
    registry_path = aoa_root / AOA_ECOSYSTEM_REGISTRY_PATH
    location = relative_posix(registry_path, aoa_root)
    payload = ensure_mapping(load_json_file(registry_path), location)
    repos = ensure_list(payload.get("repos"), f"{location}.repos")
    for index, item in enumerate(repos):
        repo_location = f"{location}.repos[{index}]"
        repo_entry = ensure_mapping(item, repo_location)
        require_keys(repo_entry, ("name", "role"), repo_location)
    return AOA_ECOSYSTEM_REGISTRY_PATH, repos


def ensure_cross_repo_surface_ref(value: Any, location: str) -> tuple[str, str]:
    raw_value = ensure_string(value, location)
    repo_name, separator, remainder = raw_value.partition("/")
    if separator != "/":
        raise RouterError(f"{location} must use '<repo>/<path>' form")
    normalized_repo = normalize_repo_name(repo_name)
    normalized_path = ensure_repo_relative_path(remainder, f"{location}.path")
    return normalized_repo, normalized_path


def build_entry_action(
    *,
    verb: str,
    target_repo: str,
    target_surface: str,
    match_key: str,
    target_value: str,
) -> dict[str, str]:
    return {
        "verb": ensure_string(verb, "verb"),
        "target_repo": normalize_repo_name(target_repo),
        "target_surface": ensure_repo_relative_path(target_surface, "target_surface"),
        "match_key": ensure_string(match_key, "match_key"),
        "target_value": ensure_string(target_value, "target_value"),
    }


def load_live_quest_projection_entries(
    repo_root: Path,
    repo_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    normalized_repo = normalize_repo_name(repo_name)
    if normalized_repo not in QUEST_ROUTING_SOURCE_REPOS:
        raise RouterError(
            f"live quest routing currently supports only {', '.join(QUEST_ROUTING_SOURCE_REPOS)}"
        )

    catalog_path = repo_root / "generated" / "quest_catalog.min.json"
    dispatch_path = repo_root / "generated" / "quest_dispatch.min.json"
    catalog_entries = ensure_list(
        load_json_file(catalog_path),
        relative_posix(catalog_path),
    )
    dispatch_entries = ensure_list(
        load_json_file(dispatch_path),
        relative_posix(dispatch_path),
    )
    normalized_catalog_entries: list[dict[str, Any]] = []
    normalized_dispatch_entries: list[dict[str, Any]] = []
    for index, raw_entry in enumerate(catalog_entries):
        location = f"{relative_posix(catalog_path)}[{index}]"
        normalized_catalog_entries.append(ensure_mapping(raw_entry, location))
    for index, raw_entry in enumerate(dispatch_entries):
        location = f"{relative_posix(dispatch_path)}[{index}]"
        normalized_dispatch_entries.append(ensure_mapping(raw_entry, location))
    return normalized_catalog_entries, normalized_dispatch_entries


def build_quest_routing_source_roots(
    techniques_root: Path,
    skills_root: Path,
    evals_root: Path,
) -> dict[str, Path]:
    return {
        "aoa-techniques": techniques_root,
        "aoa-skills": skills_root,
        "aoa-evals": evals_root,
    }


def build_quest_routing_source_inputs() -> list[dict[str, str]]:
    source_inputs: list[dict[str, str]] = []
    for repo_name in QUEST_ROUTING_SOURCE_REPOS:
        source_inputs.extend(
            (
                {
                    "repo": repo_name,
                    "surface_kind": "quest_catalog",
                    "ref": "generated/quest_catalog.min.json",
                },
                {
                    "repo": repo_name,
                    "surface_kind": "quest_dispatch",
                    "ref": "generated/quest_dispatch.min.json",
                },
            )
        )
    return source_inputs


def build_quest_dispatch_hints_payload(
    techniques_root: Path,
    skills_root: Path,
    evals_root: Path,
) -> dict[str, Any]:
    source_roots = build_quest_routing_source_roots(
        techniques_root,
        skills_root,
        evals_root,
    )
    source_inputs = build_quest_routing_source_inputs()
    hints: list[dict[str, Any]] = []

    for repo_name in QUEST_ROUTING_SOURCE_REPOS:
        catalog_entries, dispatch_entries = load_live_quest_projection_entries(
            source_roots[repo_name],
            repo_name,
        )
        catalog_by_id: dict[str, dict[str, Any]] = {}
        for index, entry in enumerate(catalog_entries):
            location = f"{repo_name}/generated/quest_catalog.min.json[{index}]"
            require_keys(
                entry,
                (
                    "id",
                    "repo",
                    "state",
                    "band",
                    "difficulty",
                    "risk",
                    "source_path",
                    "public_safe",
                ),
                location,
            )
            quest_id = ensure_string(entry["id"], f"{location}.id")
            if quest_id in catalog_by_id:
                raise RouterError(f"{location}.id duplicates quest '{quest_id}'")
            catalog_by_id[quest_id] = {
                "repo": ensure_string(entry["repo"], f"{location}.repo"),
                "state": ensure_string(entry["state"], f"{location}.state"),
                "band": ensure_string(entry["band"], f"{location}.band"),
                "difficulty": ensure_string(entry["difficulty"], f"{location}.difficulty"),
                "risk": ensure_string(entry["risk"], f"{location}.risk"),
                "source_path": ensure_repo_relative_path(
                    entry["source_path"],
                    f"{location}.source_path",
                ),
                "public_safe": ensure_bool(entry["public_safe"], f"{location}.public_safe"),
            }
            if catalog_by_id[quest_id]["repo"] != repo_name:
                raise RouterError(f"{location}.repo must stay '{repo_name}'")

        dispatch_by_id: dict[str, dict[str, Any]] = {}
        for index, entry in enumerate(dispatch_entries):
            location = f"{repo_name}/generated/quest_dispatch.min.json[{index}]"
            require_keys(
                entry,
                (
                    "schema_version",
                    "id",
                    "repo",
                    "state",
                    "band",
                    "difficulty",
                    "risk",
                    "delegate_tier",
                    "source_path",
                    "public_safe",
                ),
                location,
            )
            schema_version = ensure_string(entry["schema_version"], f"{location}.schema_version")
            if schema_version != "quest_dispatch_v1":
                raise RouterError(
                    f"{location}.schema_version must stay 'quest_dispatch_v1'"
                )
            quest_id = ensure_string(entry["id"], f"{location}.id")
            if quest_id in dispatch_by_id:
                raise RouterError(f"{location}.id duplicates quest '{quest_id}'")
            dispatch_repo = ensure_string(entry["repo"], f"{location}.repo")
            dispatch_entry = {
                "repo": dispatch_repo,
                "state": ensure_string(entry["state"], f"{location}.state"),
                "band": ensure_string(entry["band"], f"{location}.band"),
                "difficulty": ensure_string(entry["difficulty"], f"{location}.difficulty"),
                "risk": ensure_string(entry["risk"], f"{location}.risk"),
                "delegate_tier": ensure_string(
                    entry["delegate_tier"],
                    f"{location}.delegate_tier",
                ),
                "source_path": ensure_repo_relative_path(
                    entry["source_path"],
                    f"{location}.source_path",
                ),
                "public_safe": ensure_bool(entry["public_safe"], f"{location}.public_safe"),
            }
            if dispatch_entry["repo"] != repo_name:
                raise RouterError(f"{location}.repo must stay '{repo_name}'")
            catalog_entry = catalog_by_id.get(quest_id)
            if catalog_entry is None:
                raise RouterError(
                    f"{location}.id '{quest_id}' is missing from {repo_name}/generated/quest_catalog.min.json"
                )
            for key in ("repo", "state", "band", "difficulty", "risk", "source_path", "public_safe"):
                if dispatch_entry[key] != catalog_entry[key]:
                    raise RouterError(
                        f"{location}.{key} must stay aligned with {repo_name}/generated/quest_catalog.min.json"
                    )
            dispatch_by_id[quest_id] = dispatch_entry

        missing_from_dispatch = sorted(set(catalog_by_id) - set(dispatch_by_id))
        extra_in_dispatch = sorted(set(dispatch_by_id) - set(catalog_by_id))
        if missing_from_dispatch or extra_in_dispatch:
            details: list[str] = []
            if missing_from_dispatch:
                details.append(f"missing in dispatch: {', '.join(missing_from_dispatch)}")
            if extra_in_dispatch:
                details.append(f"extra in dispatch: {', '.join(extra_in_dispatch)}")
            raise RouterError(
                f"{repo_name} live quest catalog/dispatch ids are not aligned ({'; '.join(details)})"
            )

        expand_surface = QUEST_ROUTING_EXPAND_DOC_BY_REPO[repo_name]
        for quest_id in sorted(dispatch_by_id):
            dispatch_entry = dispatch_by_id[quest_id]
            if not dispatch_entry["public_safe"]:
                continue
            if dispatch_entry["state"] in QUEST_ROUTING_CLOSED_STATES:
                continue
            hints.append(
                {
                    "schema_version": "quest_dispatch_hint_v2",
                    "id": quest_id,
                    "repo": dispatch_entry["repo"],
                    "state": dispatch_entry["state"],
                    "band": dispatch_entry["band"],
                    "difficulty": dispatch_entry["difficulty"],
                    "risk": dispatch_entry["risk"],
                    "delegate_tier": dispatch_entry["delegate_tier"],
                    "source_path": dispatch_entry["source_path"],
                    "public_safe": dispatch_entry["public_safe"],
                    "next_actions": [
                        build_entry_action(
                            verb="inspect",
                            target_repo=repo_name,
                            target_surface="generated/quest_dispatch.min.json",
                            match_key="id",
                            target_value=quest_id,
                        ),
                        build_entry_action(
                            verb="expand",
                            target_repo=repo_name,
                            target_surface=expand_surface,
                            match_key="path",
                            target_value=expand_surface,
                        ),
                        build_entry_action(
                            verb="handoff",
                            target_repo="aoa-routing",
                            target_surface=FEDERATION_ENTRYPOINTS_FILE,
                            match_key="id",
                            target_value=ensure_string(
                                dispatch_entry["delegate_tier"],
                                f"{location}.delegate_tier",
                            ),
                        ),
                    ],
                    "fallback": build_entry_action(
                        verb="inspect",
                        target_repo=repo_name,
                        target_surface="generated/quest_catalog.min.json",
                        match_key="id",
                        target_value=quest_id,
                    ),
                }
            )

    return {
        "version": 1,
        "contour_scope": QUEST_ROUTING_CONTOUR_SCOPE,
        "actions_enabled": list(QUEST_ROUTING_ACTIONS_ENABLED),
        "source_inputs": source_inputs,
        "hints": hints,
    }


def build_return_navigation_action(
    *,
    verb: str,
    target_repo: str,
    target_surface: str,
    match_field: str | None = None,
    target_value: str | None = None,
    section_key_field: str | None = None,
) -> dict[str, str]:
    action = {
        "verb": ensure_string(verb, "verb"),
        "target_repo": normalize_repo_name(target_repo),
        "target_surface": ensure_repo_relative_path(target_surface, "target_surface"),
    }
    if match_field is not None:
        action["match_field"] = ensure_string(match_field, "match_field")
    if target_value is not None:
        action["target_value"] = ensure_string(target_value, "target_value")
    if section_key_field is not None:
        action["section_key_field"] = ensure_string(section_key_field, "section_key_field")
    return action


def build_entry_hop(kind: str, identifier: str) -> dict[str, str]:
    if kind not in FEDERATION_ACTIVE_ENTRY_KINDS:
        raise RouterError(f"unsupported federation entry kind '{kind}'")
    return {
        "kind": kind,
        "id": ensure_string(identifier, f"{kind}.id"),
    }


def title_case_slug(value: str) -> str:
    return " ".join(part.capitalize() for part in value.replace("_", "-").split("-") if part)


def has_old_route_label(value: str | None) -> bool:
    if not value:
        return False
    text = value.lower()
    return OLD_STAGE_ROUTE_LABEL in text or OLD_BOOTSTRAP_ROUTE_LABEL in text


def normalize_active_route_label(value: str) -> str:
    text = value
    replacements = (
        (
            f"split-{OLD_STAGE_ROUTE_LABEL}-cross-repo-rollout",
            "cross-repo-staged-rollout",
        ),
        (
            f"{OLD_BOOTSTRAP_ROUTE_LABEL}-pack-publication-route",
            "source-pack-publication-route",
        ),
    )
    for old, new in replacements:
        text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)
    text = re.sub(
        rf"\b{OLD_STAGE_ROUTE_LABEL}(?:[-_ ]?[0-9]+)?\b",
        "contour",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        rf"\b{OLD_BOOTSTRAP_ROUTE_LABEL}(?:s|ed)?\b",
        "source",
        text,
        flags=re.IGNORECASE,
    )
    return text


def load_repo_doc_manifest_default_doc_id(repo_root: Path, manifest_relative_path: str) -> str:
    manifest_path = repo_root / manifest_relative_path
    location = relative_posix(manifest_path, repo_root)
    payload = ensure_mapping(load_json_file(manifest_path), location)
    docs = ensure_list(payload.get("docs"), f"{location}.docs")
    for index, item in enumerate(docs):
        doc_location = f"{location}.docs[{index}]"
        doc = ensure_mapping(item, doc_location)
        doc_id = ensure_string(doc.get("doc_id"), f"{doc_location}.doc_id")
        if doc_id == "readme":
            return doc_id
    if not docs:
        raise RouterError(f"{location}.docs must not be empty")
    first_doc = ensure_mapping(docs[0], f"{location}.docs[0]")
    return ensure_string(first_doc.get("doc_id"), f"{location}.docs[0].doc_id")


def find_playbook_authority_path(playbooks_root: Path, playbook_name: str) -> str | None:
    direct_path = Path("playbooks") / playbook_name / "PLAYBOOK.md"
    if (playbooks_root / direct_path).exists():
        return direct_path.as_posix()

    matches = sorted(
        path
        for path in (playbooks_root / "playbooks").glob(f"**/{playbook_name}/PLAYBOOK.md")
        if path.is_file()
    )
    if not matches:
        return None
    if len(matches) > 1:
        rendered = ", ".join(relative_posix(path, playbooks_root) for path in matches)
        raise RouterError(f"ambiguous playbook authority path for '{playbook_name}': {rendered}")
    return relative_posix(matches[0], playbooks_root)


def load_memo_catalog_surfaces(memo_root: Path) -> list[dict[str, Any]]:
    catalog_path = memo_root / MEMO_INSPECT_SURFACE_FILE
    payload = ensure_mapping(load_json_file(catalog_path), relative_posix(catalog_path))
    raw_surfaces = ensure_list(
        payload.get("memo_surfaces"),
        f"{relative_posix(catalog_path)}.memo_surfaces",
    )
    surfaces: list[dict[str, Any]] = []
    for index, item in enumerate(raw_surfaces):
        location = f"{relative_posix(catalog_path)}.memo_surfaces[{index}]"
        surfaces.append(ensure_mapping(item, location))
    return surfaces


def collect_memo_recall_mode_order(memo_surfaces: list[dict[str, Any]]) -> list[str]:
    ordered_modes: list[str] = []
    seen_modes: set[str] = set()
    for index, surface in enumerate(memo_surfaces):
        location = f"{MEMO_INSPECT_SURFACE_FILE}.memo_surfaces[{index}]"
        modes = ensure_string_list(surface.get("recall_modes"), f"{location}.recall_modes")
        for mode in modes:
            if mode in seen_modes:
                continue
            ordered_modes.append(mode)
            seen_modes.add(mode)
    return ordered_modes


def load_optional_parallel_memo_recall_families(memo_root: Path) -> dict[str, dict[str, Any]]:
    families: dict[str, dict[str, Any]] = {}
    object_family = load_optional_memo_object_recall_family(memo_root)
    if object_family is not None:
        families[MEMO_OBJECT_RECALL_FAMILY] = object_family
    return families


def load_optional_contract_capsule_surface(contract: dict[str, Any], location: str) -> str | None:
    capsule_surface = contract.get("capsule_surface")
    if capsule_surface is None:
        return None
    return ensure_repo_relative_path(capsule_surface, f"{location}.capsule_surface")


def load_optional_memo_object_recall_family(memo_root: Path) -> dict[str, Any] | None:
    catalog_path = memo_root / MEMO_OBJECT_INSPECT_SURFACE_FILE
    sections_path = memo_root / MEMO_OBJECT_EXPAND_SURFACE_FILE
    try:
        catalog_payload = ensure_mapping(load_json_file(catalog_path), relative_posix(catalog_path))
        ensure_list(
            catalog_payload.get("memory_objects"),
            f"{relative_posix(catalog_path)}.memory_objects",
        )
        sections_payload = ensure_mapping(
            load_json_file(sections_path),
            relative_posix(sections_path),
        )
        ensure_list(
            sections_payload.get("memory_objects"),
            f"{relative_posix(sections_path)}.memory_objects",
        )
    except RouterError:
        return None

    contracts_by_mode: dict[str, str] = {}
    capsule_surfaces_by_mode: dict[str, str] = {}
    for mode, relative_contract_path in MEMO_OBJECT_RECALL_CONTRACTS_BY_MODE.items():
        contract_path = memo_root / relative_contract_path
        location = relative_posix(contract_path, memo_root)
        try:
            contract = ensure_mapping(load_json_file(contract_path), location)
            require_keys(
                contract,
                ("mode", "inspect_surface", "expand_surface"),
                location,
            )
            contract_mode = ensure_string(contract["mode"], f"{location}.mode")
            inspect_surface = ensure_repo_relative_path(
                contract["inspect_surface"],
                f"{location}.inspect_surface",
            )
            expand_surface = ensure_repo_relative_path(
                contract["expand_surface"],
                f"{location}.expand_surface",
            )
            capsule_surface = load_optional_contract_capsule_surface(contract, location)
        except RouterError:
            return None
        if contract_mode != mode:
            return None
        if inspect_surface != MEMO_OBJECT_INSPECT_SURFACE_FILE:
            return None
        if expand_surface != MEMO_OBJECT_EXPAND_SURFACE_FILE:
            return None
        contracts_by_mode[mode] = location
        if capsule_surface is not None:
            capsule_surfaces_by_mode[mode] = capsule_surface

    family_payload = {
        "inspect_surface": MEMO_OBJECT_INSPECT_SURFACE_FILE,
        "expand_surface": MEMO_OBJECT_EXPAND_SURFACE_FILE,
        "default_mode": MEMO_OBJECT_RECALL_DEFAULT_MODE,
        "supported_modes": list(MEMO_OBJECT_RECALL_CONTRACTS_BY_MODE.keys()),
        "contracts_by_mode": contracts_by_mode,
    }
    if capsule_surfaces_by_mode:
        family_payload["capsule_surfaces_by_mode"] = capsule_surfaces_by_mode
    return family_payload


def load_router_ready_memo_recall_contracts(
    memo_root: Path,
    memo_surfaces: list[dict[str, Any]] | None = None,
) -> tuple[str | None, list[str], dict[str, str], dict[str, str]]:
    surfaces = memo_surfaces or load_memo_catalog_surfaces(memo_root)
    declared_modes = collect_memo_recall_mode_order(surfaces)
    declared_mode_set = set(declared_modes)
    contracts_by_mode: dict[str, str] = {}
    capsule_surfaces_by_mode: dict[str, str] = {}

    examples_dir = memo_root / "examples" / "recall"
    if examples_dir.exists():
        for contract_path in sorted(examples_dir.glob(f"{ROUTER_READY_RECALL_CONTRACT_PREFIX}*.json")):
            location = relative_posix(contract_path, memo_root)
            contract = ensure_mapping(load_json_file(contract_path), location)
            require_keys(
                contract,
                ("mode", "inspect_surface", "expand_surface"),
                location,
            )
            mode = ensure_string(contract["mode"], f"{location}.mode")
            if mode in contracts_by_mode:
                raise RouterError(f"{location} duplicates router-ready recall mode '{mode}'")
            if mode not in declared_mode_set:
                raise RouterError(
                    f"{location}.mode must be declared by aoa-memo/{MEMO_INSPECT_SURFACE_FILE}"
                )
            contracts_by_mode[mode] = location
            capsule_surface = load_optional_contract_capsule_surface(contract, location)
            if capsule_surface is not None:
                capsule_surfaces_by_mode[mode] = capsule_surface

    supported_modes = [mode for mode in declared_modes if mode in contracts_by_mode]
    if not supported_modes:
        return None, [], {}, {}

    default_mode = DEFAULT_MEMO_RECALL_MODE if DEFAULT_MEMO_RECALL_MODE in contracts_by_mode else supported_modes[0]
    return default_mode, supported_modes, contracts_by_mode, capsule_surfaces_by_mode


def build_router_payload(registry_entries: list[dict[str, Any]]) -> dict[str, Any]:
    projection = [
        {
            "kind": entry["kind"],
            "id": entry["id"],
            "name": entry["name"],
            "repo": entry["repo"],
            "path": entry["path"],
            "status": entry["status"],
            "summary": entry["summary"],
        }
        for entry in sort_registry_entries(list(registry_entries))
    ]
    return {
        "artifact_identity": ROUTING_READMODEL_ARTIFACT_IDENTITY,
        "router_version": 1,
        "entries": projection,
    }


def build_federation_entrypoints_payload(
    aoa_root: Path,
    techniques_root: Path,
    agents_root: Path,
    playbooks_root: Path,
    kag_root: Path,
    tos_root: Path,
    sdk_root: Path,
    stats_root: Path,
    source_route_root: Path,
    profile_root: Path,
    abyss_stack_root: Path,
) -> dict[str, Any]:
    load_ecosystem_registry_entries(aoa_root)
    ensure_markdown_file(aoa_root / "README.md", f"{AOA_ROOT_REPO}/README.md")
    ensure_markdown_file(aoa_root / "CHARTER.md", f"{AOA_ROOT_REPO}/CHARTER.md")
    aoa_center_entry_map = ensure_mapping(
        load_json_file(aoa_root / AOA_CENTER_ENTRY_MAP_PATH),
        f"{AOA_ROOT_REPO}/{AOA_CENTER_ENTRY_MAP_PATH}",
    )
    aoa_center_route_ids = select_aoa_center_route_ids(
        aoa_center_entry_map,
        f"{AOA_ROOT_REPO}/{AOA_CENTER_ENTRY_MAP_PATH}",
    )
    ensure_markdown_file(tos_root / "README.md", f"{TOS_REPO}/README.md")
    ensure_markdown_file(tos_root / "CHARTER.md", f"{TOS_REPO}/CHARTER.md")
    ensure_mapping(
        load_json_file(tos_root / TOS_ROOT_ENTRY_MAP_PATH),
        f"{TOS_REPO}/{TOS_ROOT_ENTRY_MAP_PATH}",
    )
    tos_tiny_entry_route_path, tos_tiny_entry_route = load_tos_tiny_entry_route(tos_root)
    ensure_markdown_file(
        tos_root / TOS_TINY_ENTRY_DOCTRINE_PATH,
        f"{TOS_REPO}/{TOS_TINY_ENTRY_DOCTRINE_PATH}",
    )
    ensure_markdown_file(
        kag_root / FEDERATION_SPINE_AUTHORITY_PATH,
        f"{KAG_REPO}/{FEDERATION_SPINE_AUTHORITY_PATH}",
    )
    ensure_markdown_file(
        source_route_root / DIONYSUS_SOURCE_ROUTE_ANCHOR_PATH,
        f"{DIONYSUS_REPO}/{DIONYSUS_SOURCE_ROUTE_ANCHOR_PATH}",
    )
    ensure_text_file(
        sdk_root / AOA_SDK_WORKSPACE_TOML_PATH,
        f"{SDK_REPO}/{AOA_SDK_WORKSPACE_TOML_PATH}",
    )
    ensure_mapping(
        load_json_file(sdk_root / AOA_SDK_WORKSPACE_CONTROL_PLANE_PATH),
        f"{SDK_REPO}/{AOA_SDK_WORKSPACE_CONTROL_PLANE_PATH}",
    )
    ensure_markdown_file(
        sdk_root / AOA_SDK_BOUNDARIES_PATH,
        f"{SDK_REPO}/{AOA_SDK_BOUNDARIES_PATH}",
    )
    ensure_mapping(
        load_json_file(stats_root / AOA_STATS_SUMMARY_SURFACE_CATALOG_PATH),
        f"{STATS_REPO}/{AOA_STATS_SUMMARY_SURFACE_CATALOG_PATH}",
    )
    ensure_markdown_file(
        stats_root / AOA_STATS_ARCHITECTURE_PATH,
        f"{STATS_REPO}/{AOA_STATS_ARCHITECTURE_PATH}",
    )
    ensure_mapping(
        load_json_file(profile_root / PROFILE_PUBLIC_ROUTE_MAP_PATH),
        f"{PROFILE_REPO}/{PROFILE_PUBLIC_ROUTE_MAP_PATH}",
    )
    ensure_markdown_file(
        profile_root / PROFILE_PUBLIC_ENTRY_POSTURE_PATH,
        f"{PROFILE_REPO}/{PROFILE_PUBLIC_ENTRY_POSTURE_PATH}",
    )
    ensure_mapping(
        load_json_file(abyss_stack_root / ABYSS_STACK_DIAGNOSTIC_SESSION_PATH),
        f"{ABYSS_STACK_REPO}/{ABYSS_STACK_DIAGNOSTIC_SESSION_PATH}",
    )
    ensure_mapping(
        load_json_file(abyss_stack_root / ABYSS_STACK_DIAGNOSTIC_SURFACE_CATALOG_PATH),
        f"{ABYSS_STACK_REPO}/{ABYSS_STACK_DIAGNOSTIC_SURFACE_CATALOG_PATH}",
    )
    ensure_markdown_file(
        abyss_stack_root / ABYSS_STACK_DIAGNOSTIC_SPINE_PATH,
        f"{ABYSS_STACK_REPO}/{ABYSS_STACK_DIAGNOSTIC_SPINE_PATH}",
    )

    agent_registry_path, agent_entries = load_agent_registry_entries(agents_root)
    model_tier_registry_path, tier_entries = load_model_tier_entries(agents_root)
    runtime_bindings_path, runtime_bindings = load_runtime_seam_bindings(agents_root)
    playbook_registry_path, playbook_entries = load_playbook_registry_entries(playbooks_root)
    federation_spine_path, kag_entries = load_federation_spine_entries(kag_root)

    def bounded_unique(values: Iterable[str], limit: int = 3) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            if value in seen:
                continue
            result.append(value)
            seen.add(value)
            if len(result) >= limit:
                break
        return result

    def append_mesh_entry(
        *,
        kind: str,
        entry_id: str,
        owner_repo: str,
        title: str,
        capsule_surface: str,
        authority_surface: str,
        next_entries: list[tuple[str, str]],
        risk: str,
    ) -> None:
        federation_entrypoints.append(
            {
                "kind": kind,
                "id": entry_id,
                "owner_repo": owner_repo,
                "title": title,
                "capsule_surface": capsule_surface,
                "authority_surface": authority_surface,
                "next_actions": [
                    build_entry_action(
                        verb="inspect",
                        target_repo=PAIRING_SURFACE_REPO,
                        target_surface=FEDERATION_ENTRYPOINTS_FILE,
                        match_key="id",
                        target_value=next_id,
                    )
                    for _, next_id in next_entries
                ],
                "fallback": build_entry_action(
                    verb="inspect",
                    target_repo=PAIRING_SURFACE_REPO,
                    target_surface=FEDERATION_ENTRYPOINTS_FILE,
                    match_key="id",
                    target_value="aoa-root",
                ),
                "risk": risk,
                "next_hops": [
                    build_entry_hop(next_kind, next_id) for next_kind, next_id in next_entries
                ],
            }
        )

    agent_id_by_name: dict[str, str] = {}
    agent_index: dict[str, dict[str, Any]] = {}
    for index, raw_agent in enumerate(agent_entries):
        location = f"{agent_registry_path}.agents[{index}]"
        agent_id = ensure_string(raw_agent["id"], f"{location}.id")
        agent_name = ensure_string(raw_agent["name"], f"{location}.name")
        agent_id_by_name[agent_name] = agent_id
        agent_index[agent_id] = raw_agent

    tier_index: dict[str, dict[str, Any]] = {}
    artifact_to_tier: dict[str, str] = {}
    for index, raw_tier in enumerate(tier_entries):
        location = f"{model_tier_registry_path}.model_tiers[{index}]"
        tier_id = ensure_string(raw_tier["id"], f"{location}.id")
        artifact_requirement = ensure_string(
            raw_tier["artifact_requirement"],
            f"{location}.artifact_requirement",
        )
        tier_index[tier_id] = raw_tier
        artifact_to_tier[artifact_requirement] = tier_id

    ordered_bindings = sorted(
        runtime_bindings,
        key=lambda binding: (
            TIER_PHASE_ORDER.index(
                ensure_string(
                    binding["phase"],
                    f"{runtime_bindings_path}.bindings.phase",
                )
            )
            if ensure_string(binding["phase"], f"{runtime_bindings_path}.bindings.phase")
            in TIER_PHASE_ORDER
            else len(TIER_PHASE_ORDER),
            ensure_string(binding["tier_id"], f"{runtime_bindings_path}.bindings.tier_id"),
        ),
    )
    tier_ids_by_agent_name: dict[str, list[str]] = {}
    agent_ids_by_tier: dict[str, list[str]] = {}
    for index, raw_binding in enumerate(ordered_bindings):
        location = f"{runtime_bindings_path}.bindings[{index}]"
        tier_id = ensure_string(raw_binding["tier_id"], f"{location}.tier_id")
        role_names = ensure_string_list(raw_binding["role_names"], f"{location}.role_names")
        for role_name in role_names:
            tier_ids_by_agent_name.setdefault(role_name, []).append(tier_id)
            bound_agent_id = agent_id_by_name.get(role_name)
            if bound_agent_id is not None:
                agent_ids_by_tier.setdefault(tier_id, []).append(bound_agent_id)

    for agent_id in (FEDERATION_DEFAULT_AGENT_ENTRY_ID,):
        if agent_id not in agent_index:
            raise RouterError(f"federation entry ABI requires agent '{agent_id}'")
    for tier_id in (FEDERATION_DEFAULT_TIER_ENTRY_ID,):
        if tier_id not in tier_index:
            raise RouterError(f"federation entry ABI requires tier '{tier_id}'")

    playbook_index: dict[str, dict[str, Any]] = {}
    for index, raw_playbook in enumerate(playbook_entries):
        location = f"{playbook_registry_path}.playbooks[{index}]"
        playbook_id = ensure_string(raw_playbook["id"], f"{location}.id")
        playbook_index[playbook_id] = raw_playbook
    if FEDERATION_DEFAULT_PLAYBOOK_ENTRY_ID not in playbook_index:
        raise RouterError(
            f"federation entry ABI requires playbook '{FEDERATION_DEFAULT_PLAYBOOK_ENTRY_ID}'"
        )
    if "AOA-P-0009" not in playbook_index:
        raise RouterError("federation entry ABI requires playbook 'AOA-P-0009'")

    kag_index: dict[str, dict[str, Any]] = {}
    for index, raw_kag_entry in enumerate(kag_entries):
        location = f"{federation_spine_path}.repos[{index}]"
        repo_name = normalize_repo_name(
            ensure_string(raw_kag_entry["repo"], f"{location}.repo")
        )
        kag_index[repo_name] = raw_kag_entry
    if FEDERATION_DEFAULT_KAG_VIEW_ENTRY_ID not in kag_index:
        raise RouterError(
            f"federation entry ABI requires KAG view '{FEDERATION_DEFAULT_KAG_VIEW_ENTRY_ID}'"
        )
    if TOS_KAG_VIEW_ENTRY_ID not in kag_index:
        raise RouterError(
            f"federation entry ABI requires KAG view '{TOS_KAG_VIEW_ENTRY_ID}'"
        )
    unsupported_kag_view_ids = set(kag_index) - {
        FEDERATION_DEFAULT_KAG_VIEW_ENTRY_ID,
        TOS_KAG_VIEW_ENTRY_ID,
    }
    if unsupported_kag_view_ids:
        unsupported = ", ".join(sorted(unsupported_kag_view_ids))
        raise RouterError(
            "current federation entry ABI only supports explicit KAG views for "
            f"{FEDERATION_DEFAULT_KAG_VIEW_ENTRY_ID} and {TOS_KAG_VIEW_ENTRY_ID}; got {unsupported}"
        )

    federation_entrypoints: list[dict[str, Any]] = []

    for agent_id in sorted(agent_index):
        agent = agent_index[agent_id]
        agent_name = ensure_string(agent["name"], f"{agent_id}.name")
        authority_path = f"agents/roles/{agent_name}/profile.json"
        ensure_mapping(
            load_json_file(agents_root / authority_path),
            f"{AGENTS_REPO}/{authority_path}",
        )
        related_tiers = bounded_unique(tier_ids_by_agent_name.get(agent_name, []))
        if not related_tiers:
            related_tiers = [FEDERATION_DEFAULT_TIER_ENTRY_ID]
        federation_entrypoints.append(
            {
                "kind": "agent",
                "id": agent_id,
                "owner_repo": AGENTS_REPO,
                "title": f"{title_case_slug(agent_name)} Agent",
                "capsule_surface": make_repo_qualified_ref(AGENTS_REPO, AGENT_REGISTRY_PATH),
                "authority_surface": make_repo_qualified_ref(AGENTS_REPO, authority_path),
                "next_actions": [
                    build_entry_action(
                        verb="inspect",
                        target_repo=PAIRING_SURFACE_REPO,
                        target_surface=FEDERATION_ENTRYPOINTS_FILE,
                        match_key="id",
                        target_value=tier_id,
                    )
                    for tier_id in related_tiers
                ],
                "fallback": build_entry_action(
                    verb="inspect",
                    target_repo=PAIRING_SURFACE_REPO,
                    target_surface=FEDERATION_ENTRYPOINTS_FILE,
                    match_key="id",
                    target_value=related_tiers[0],
                ),
                "risk": "Agent entry cards summarize role posture; confirm the source profile before treating a handoff hint as binding.",
                "next_hops": [build_entry_hop("tier", tier_id) for tier_id in related_tiers],
            }
        )

    for tier_id in sorted(tier_index):
        authority_path = f"agents/operating-model/tiers/{tier_id}.tier.json"
        ensure_mapping(
            load_json_file(agents_root / authority_path),
            f"{AGENTS_REPO}/{authority_path}",
        )
        related_agents = bounded_unique(agent_ids_by_tier.get(tier_id, []))
        if not related_agents:
            related_agents = [FEDERATION_DEFAULT_AGENT_ENTRY_ID]
        federation_entrypoints.append(
            {
                "kind": "tier",
                "id": tier_id,
                "owner_repo": AGENTS_REPO,
                "title": f"{title_case_slug(tier_id)} Tier",
                "capsule_surface": make_repo_qualified_ref(
                    AGENTS_REPO, MODEL_TIER_REGISTRY_PATH
                ),
                "authority_surface": make_repo_qualified_ref(AGENTS_REPO, authority_path),
                "next_actions": [
                    build_entry_action(
                        verb="inspect",
                        target_repo=PAIRING_SURFACE_REPO,
                        target_surface=FEDERATION_ENTRYPOINTS_FILE,
                        match_key="id",
                        target_value=agent_id,
                    )
                    for agent_id in related_agents
                ],
                "fallback": build_entry_action(
                    verb="inspect",
                    target_repo=PAIRING_SURFACE_REPO,
                    target_surface=FEDERATION_ENTRYPOINTS_FILE,
                    match_key="id",
                    target_value=related_agents[0],
                ),
                "risk": "Tier entry cards orient effort class and handoff posture; the tier contract remains authoritative in aoa-agents.",
                "next_hops": [build_entry_hop("agent", agent_id) for agent_id in related_agents],
            }
        )

    for playbook_id in sorted(playbook_index):
        playbook = playbook_index[playbook_id]
        playbook_name = ensure_string(playbook["name"], f"{playbook_id}.name")
        resolved_authority_path = find_playbook_authority_path(playbooks_root, playbook_name)
        if (
            resolved_authority_path is None
            or has_old_route_label(playbook_name)
            or has_old_route_label(resolved_authority_path)
        ):
            resolved_authority_path = PLAYBOOK_PORTFOLIO_PATH
        published_playbook_name = normalize_active_route_label(playbook_name)
        ensure_markdown_file(
            playbooks_root / resolved_authority_path,
            f"{PLAYBOOKS_REPO}/{resolved_authority_path}",
        )

        expected_artifacts = ensure_string_list(
            playbook["expected_artifacts"],
            f"{playbook_id}.expected_artifacts",
        )
        participating_agents = ensure_string_list(
            playbook["participating_agents"],
            f"{playbook_id}.participating_agents",
        )
        next_hops: list[dict[str, str]] = []
        next_actions: list[dict[str, str]] = []

        tier_hops = bounded_unique(
            artifact_to_tier[artifact]
            for artifact in expected_artifacts
            if artifact in artifact_to_tier
        )
        if tier_hops:
            next_hops = [build_entry_hop("tier", tier_id) for tier_id in tier_hops]
            next_actions = [
                build_entry_action(
                    verb="inspect",
                    target_repo=PAIRING_SURFACE_REPO,
                    target_surface=FEDERATION_ENTRYPOINTS_FILE,
                    match_key="id",
                    target_value=tier_id,
                )
                for tier_id in tier_hops
            ]
        else:
            agent_hops = bounded_unique(
                agent_id_by_name[agent_name]
                for agent_name in participating_agents
                if agent_name in agent_id_by_name
            )
            if not agent_hops:
                agent_hops = [FEDERATION_DEFAULT_AGENT_ENTRY_ID]
            next_hops = [build_entry_hop("agent", agent_id) for agent_id in agent_hops]
            next_actions = [
                build_entry_action(
                    verb="inspect",
                    target_repo=PAIRING_SURFACE_REPO,
                    target_surface=FEDERATION_ENTRYPOINTS_FILE,
                    match_key="id",
                    target_value=agent_id,
                )
                for agent_id in agent_hops
            ]

        fallback_target = next_actions[0]["target_value"]
        federation_entrypoints.append(
            {
                "kind": "playbook",
                "id": playbook_id,
                "owner_repo": PLAYBOOKS_REPO,
                "title": title_case_slug(published_playbook_name),
                "capsule_surface": make_repo_qualified_ref(
                    PLAYBOOKS_REPO, PLAYBOOK_REGISTRY_PATH
                ),
                "authority_surface": make_repo_qualified_ref(
                    PLAYBOOKS_REPO,
                    resolved_authority_path,
                ),
                "next_actions": next_actions,
                "fallback": build_entry_action(
                    verb="inspect",
                    target_repo=PAIRING_SURFACE_REPO,
                    target_surface=FEDERATION_ENTRYPOINTS_FILE,
                    match_key="id",
                    target_value=fallback_target,
                ),
                "risk": "Playbook entry cards compress scenario posture; read the source playbook bundle or portfolio doc before using the route as execution authority.",
                "next_hops": next_hops,
            }
        )

    for kag_view_id in sorted(kag_index):
        kag_entry = kag_index[kag_view_id]
        pilot_posture = ensure_string(
            kag_entry.get("pilot_posture"),
            f"{kag_view_id}.pilot_posture",
        )
        entry_surface_refs = ensure_string_list(
            kag_entry["current_entry_surface_refs"],
            f"{kag_view_id}.current_entry_surface_refs",
        )
        if not entry_surface_refs:
            raise RouterError(
                f"{kag_view_id}.current_entry_surface_refs must include at least one current entry surface"
            )
        object_surface_ref = ensure_string(
            kag_entry["current_object_surface_ref"],
            f"{kag_view_id}.current_object_surface_ref",
        )
        adjunct_surfaces = ensure_list(
            kag_entry.get("adjunct_surfaces"),
            f"{kag_view_id}.adjunct_surfaces",
        )
        example_object_ids = ensure_string_list(
            kag_entry["example_object_ids"],
            f"{kag_view_id}.example_object_ids",
        )
        if not example_object_ids:
            raise RouterError(f"{kag_view_id}.example_object_ids must not be empty")
        if kag_view_id == FEDERATION_DEFAULT_KAG_VIEW_ENTRY_ID:
            if pilot_posture != "existing_generated_surfaces":
                raise RouterError(
                    f"{kag_view_id}.pilot_posture must stay 'existing_generated_surfaces' in the current routing contour"
                )
            if entry_surface_refs != [AOA_TECHNIQUES_KAG_VIEW_ENTRY_SURFACE_REF]:
                raise RouterError(
                    f"{kag_view_id}.current_entry_surface_refs must stay '{AOA_TECHNIQUES_KAG_VIEW_ENTRY_SURFACE_REF}' in the current routing contour"
                )
            if object_surface_ref != AOA_TECHNIQUES_KAG_VIEW_OBJECT_SURFACE_REF:
                raise RouterError(
                    f"{kag_view_id}.current_object_surface_ref must stay '{AOA_TECHNIQUES_KAG_VIEW_OBJECT_SURFACE_REF}' in the current routing contour"
                )
            if example_object_ids != list(AOA_TECHNIQUES_KAG_VIEW_EXAMPLE_OBJECT_IDS):
                raise RouterError(
                    f"{kag_view_id}.example_object_ids must stay {list(AOA_TECHNIQUES_KAG_VIEW_EXAMPLE_OBJECT_IDS)!r} in the current routing contour"
                )
            if adjunct_surfaces != []:
                raise RouterError(
                    f"{kag_view_id}.adjunct_surfaces must stay [] in the current routing contour"
                )
            entry_target_repo, entry_target_surface = ensure_cross_repo_surface_ref(
                entry_surface_refs[0],
                f"{kag_view_id}.current_entry_surface_refs[0]",
            )
            object_target_repo, object_target_surface = ensure_cross_repo_surface_ref(
                object_surface_ref,
                f"{kag_view_id}.current_object_surface_ref",
            )
            entry_doc_id = load_repo_doc_manifest_default_doc_id(
                techniques_root,
                entry_target_surface,
            )
            title = f"{title_case_slug(kag_view_id)} Readiness View"
            next_actions = [
                build_entry_action(
                    verb="inspect",
                    target_repo=entry_target_repo,
                    target_surface=entry_target_surface,
                    match_key="doc_id",
                    target_value=entry_doc_id,
                ),
                build_entry_action(
                    verb="inspect",
                    target_repo=object_target_repo,
                    target_surface=object_target_surface,
                    match_key="id",
                    target_value=example_object_ids[0],
                ),
            ]
            risk = "KAG view cards summarize derived readiness and current source-facing surfaces; confirm aoa-kag doctrine and the owning repo before treating the view as canon."
            next_hops = [
                build_entry_hop("tier", FEDERATION_DEFAULT_TIER_ENTRY_ID),
                build_entry_hop("playbook", FEDERATION_DEFAULT_PLAYBOOK_ENTRY_ID),
            ]
        elif kag_view_id == TOS_KAG_VIEW_ENTRY_ID:
            if pilot_posture != "source_owned_tiny_entry_route":
                raise RouterError(
                    f"{kag_view_id}.pilot_posture must stay 'source_owned_tiny_entry_route' in the current routing contour"
                )
            if entry_surface_refs != list(TOS_KAG_VIEW_ENTRY_SURFACE_REFS):
                raise RouterError(
                    f"{kag_view_id}.current_entry_surface_refs must stay {list(TOS_KAG_VIEW_ENTRY_SURFACE_REFS)!r} in the current routing contour"
                )
            if object_surface_ref != TOS_KAG_VIEW_OBJECT_SURFACE_REF:
                raise RouterError(
                    f"{kag_view_id}.current_object_surface_ref must stay '{TOS_KAG_VIEW_OBJECT_SURFACE_REF}' in the current routing contour"
                )
            if example_object_ids != [TOS_TINY_ENTRY_ROUTE_ID]:
                raise RouterError(
                    f"{kag_view_id}.example_object_ids must stay ['{TOS_TINY_ENTRY_ROUTE_ID}'] in the current routing contour"
                )
            if adjunct_surfaces != [EXPECTED_TOS_KAG_VIEW_ADJUNCT]:
                raise RouterError(
                    f"{kag_view_id}.adjunct_surfaces must publish exactly the bounded "
                    "AOA-K-0011 adjunct in the current routing contour"
                )
            retrieval_adjunct = ensure_mapping(
                adjunct_surfaces[0],
                f"{kag_view_id}.adjunct_surfaces[0]",
            )
            adjunct_surface_ref = ensure_repo_relative_path(
                retrieval_adjunct["surface_ref"],
                f"{kag_view_id}.adjunct_surfaces[0].surface_ref",
            )
            adjunct_match_key = ensure_string(
                retrieval_adjunct["match_key"],
                f"{kag_view_id}.adjunct_surfaces[0].match_key",
            )
            adjunct_target_value = ensure_string(
                retrieval_adjunct["target_value"],
                f"{kag_view_id}.adjunct_surfaces[0].target_value",
            )
            title = "Tree-of-Sophia Readiness View"
            next_actions = [
                build_entry_action(
                    verb="inspect",
                    target_repo=TOS_REPO,
                    target_surface=TOS_TINY_ENTRY_DOCTRINE_PATH,
                    match_key="path",
                    target_value=TOS_TINY_ENTRY_DOCTRINE_PATH,
                ),
                build_entry_action(
                    verb="inspect",
                    target_repo=TOS_REPO,
                    target_surface=tos_tiny_entry_route_path,
                    match_key="route_id",
                    target_value=TOS_TINY_ENTRY_ROUTE_ID,
                ),
                build_entry_action(
                    verb="inspect",
                    target_repo=KAG_REPO,
                    target_surface=adjunct_surface_ref,
                    match_key=adjunct_match_key,
                    target_value=adjunct_target_value,
                ),
            ]
            risk = (
                "KAG view cards summarize derived readiness and current source-facing "
                "surfaces; Tree-of-Sophia remains authoritative for ToS meaning, and "
                "AOA-K-0011 is only a bounded handles-only adjunct that does not take "
                "routing or canon ownership."
            )
            next_hops = [
                build_entry_hop("tier", FEDERATION_DEFAULT_TIER_ENTRY_ID),
                build_entry_hop("playbook", TOS_KAG_VIEW_PLAYBOOK_ENTRY_ID),
            ]
        else:
            raise RouterError(f"unsupported KAG view '{kag_view_id}'")
        federation_entrypoints.append(
            {
                "kind": "kag_view",
                "id": kag_view_id,
                "owner_repo": KAG_REPO,
                "title": title,
                "capsule_surface": make_repo_qualified_ref(KAG_REPO, FEDERATION_SPINE_PATH),
                "authority_surface": make_repo_qualified_ref(KAG_REPO, FEDERATION_SPINE_AUTHORITY_PATH),
                "next_actions": next_actions,
                "fallback": build_entry_action(
                    verb="inspect",
                    target_repo=PAIRING_SURFACE_REPO,
                    target_surface=FEDERATION_ENTRYPOINTS_FILE,
                    match_key="id",
                    target_value=FEDERATION_DEFAULT_TIER_ENTRY_ID,
                ),
                "risk": risk,
                "next_hops": next_hops,
            }
        )

    append_mesh_entry(
        kind="source_route",
        entry_id=FEDERATION_DEFAULT_SOURCE_ROUTE_ENTRY_ID,
        owner_repo=DIONYSUS_REPO,
        title="Dionysus Legacy Source Route Boundary",
        capsule_surface=make_repo_qualified_ref(DIONYSUS_REPO, DIONYSUS_SOURCE_ROUTE_ANCHOR_PATH),
        authority_surface=make_repo_qualified_ref(DIONYSUS_REPO, DIONYSUS_SOURCE_ROUTE_ANCHOR_PATH),
        next_entries=[
            ("orientation_surface", FEDERATION_DEFAULT_ORIENTATION_SURFACE_ENTRY_ID),
            ("runtime_surface", FEDERATION_DEFAULT_RUNTIME_SURFACE_ENTRY_ID),
        ],
        risk=(
            "This compatibility entry points to the owner decision that retired the "
            "Dionysus source-incubation and source-route staging role. It is a stop and reroute "
            "boundary, not current implementation or planting authority."
        ),
    )
    append_mesh_entry(
        kind="runtime_surface",
        entry_id=FEDERATION_DEFAULT_RUNTIME_SURFACE_ENTRY_ID,
        owner_repo=SDK_REPO,
        title="aoa-sdk Control Plane",
        capsule_surface=make_repo_qualified_ref(SDK_REPO, AOA_SDK_WORKSPACE_CONTROL_PLANE_PATH),
        authority_surface=make_repo_qualified_ref(SDK_REPO, AOA_SDK_BOUNDARIES_PATH),
        next_entries=[
            ("runtime_surface", "aoa-stats-summary-catalog"),
            ("runtime_surface", "abyss-stack-diagnostic-spine"),
        ],
        risk=(
            "Runtime control-plane entry cards stay bounded to workspace discovery and "
            "source-owned boundaries; `aoa-sdk` must not be mistaken for the authority "
            "surface of sibling runtime or stats repos."
        ),
    )
    append_mesh_entry(
        kind="runtime_surface",
        entry_id="aoa-stats-summary-catalog",
        owner_repo=STATS_REPO,
        title="aoa-stats Summary Catalog",
        capsule_surface=make_repo_qualified_ref(
            STATS_REPO, AOA_STATS_SUMMARY_SURFACE_CATALOG_PATH
        ),
        authority_surface=make_repo_qualified_ref(STATS_REPO, AOA_STATS_ARCHITECTURE_PATH),
        next_entries=[("runtime_surface", FEDERATION_DEFAULT_RUNTIME_SURFACE_ENTRY_ID)],
        risk=(
            "Stats entry cards summarize derived observability only; `aoa-stats` does not "
            "replace the source-owned receipts and validators published by sibling repos."
        ),
    )
    append_mesh_entry(
        kind="runtime_surface",
        entry_id="abyss-stack-diagnostic-spine",
        owner_repo=ABYSS_STACK_REPO,
        title="abyss-stack Diagnostic Spine",
        capsule_surface=make_repo_qualified_ref(
            ABYSS_STACK_REPO, ABYSS_STACK_DIAGNOSTIC_SURFACE_CATALOG_PATH
        ),
        authority_surface=make_repo_qualified_ref(
            ABYSS_STACK_REPO, ABYSS_STACK_DIAGNOSTIC_SPINE_PATH
        ),
        next_entries=[
            ("runtime_surface", FEDERATION_DEFAULT_RUNTIME_SURFACE_ENTRY_ID),
            ("source_route", FEDERATION_DEFAULT_SOURCE_ROUTE_ENTRY_ID),
        ],
        risk=(
            "Runtime diagnostic entry cards stay anchored to the source checkout of "
            "`abyss-stack`; do not confuse the deployed `/srv/AbyssOS/abyss-stack` mirror with the "
            "authoritative source repository."
        ),
    )
    append_mesh_entry(
        kind="orientation_surface",
        entry_id=FEDERATION_DEFAULT_ORIENTATION_SURFACE_ENTRY_ID,
        owner_repo=PROFILE_REPO,
        title="8Dionysus Public Route Map",
        capsule_surface=make_repo_qualified_ref(PROFILE_REPO, PROFILE_PUBLIC_ROUTE_MAP_PATH),
        authority_surface=make_repo_qualified_ref(
            PROFILE_REPO, PROFILE_PUBLIC_ENTRY_POSTURE_PATH
        ),
        next_entries=[
            ("runtime_surface", FEDERATION_DEFAULT_RUNTIME_SURFACE_ENTRY_ID),
            ("source_route", FEDERATION_DEFAULT_SOURCE_ROUTE_ENTRY_ID),
        ],
        risk=(
            "Profile route cards are orientation-only; `8Dionysus` must not replace owner "
            "repo authority, release semantics, or runtime guarantees."
        ),
    )

    return {
        "schema_version": "aoa_routing_federation_entrypoints_v2",
        "schema_ref": "mechanics/boundary-bridge/parts/federation-entry/schemas/federation-entrypoints.schema.json",
        "owner_repo": "aoa-routing",
        "surface_kind": "federation_entrypoints",
        "artifact_identity": {
            "artifact_class": "generated_readmodel",
            "surface_state": "public_generated_navigation_surface",
            "owner_repo": "aoa-routing",
            "authority_ref": "mechanics/boundary-bridge/parts/federation-entry/docs/federation-entry-abi.md",
            "producer": "scripts/build_router.py from sibling owner-generated source inputs",
            "consumer_expectation": "consumers verify schema_version, schema_ref, source_inputs, owner authority refs, and validate_router/build_router --check before treating entry cards as usable orientation",
            "privacy_boundary": "public route references only; no copied owner payloads, private state, source corpora, or runtime secrets",
            "content_identity": "generated/federation_entrypoints.min.json rebuilt from declared source_inputs and compared by build_router --check",
            "abi_epoch": "aoa_routing_federation_entrypoints_v2",
            "contract_version": "federation-entrypoints.schema.json@aoa_routing_federation_entrypoints_v2#artifact_identity",
            "trust_layer": ["abi_contract_signature"],
            "verification": ["python scripts/validate_router.py", "python scripts/build_router.py --check"],
            "action": "ADD_CONSUMER_EXPECTATION",
        },
        "source_inputs": [
            {
                "name": "aoa_root_readme",
                "repo": AOA_ROOT_REPO,
                "role": "public_root",
                "ref": "README.md",
            },
            {
                "name": "aoa_center_entry_map",
                "repo": AOA_ROOT_REPO,
                "role": "root_capsule",
                "ref": AOA_CENTER_ENTRY_MAP_PATH,
            },
            {
                "name": "tos_root_readme",
                "repo": TOS_REPO,
                "role": "public_root",
                "ref": "README.md",
            },
            {
                "name": "tos_root_entry_map",
                "repo": TOS_REPO,
                "role": "root_capsule",
                "ref": TOS_ROOT_ENTRY_MAP_PATH,
            },
            {
                "name": "tos_tiny_entry_route",
                "repo": TOS_REPO,
                "role": "tiny_entry_handoff",
                "ref": tos_tiny_entry_route_path,
            },
            {
                "name": "agent_registry",
                "repo": AGENTS_REPO,
                "role": "agent_entries",
                "ref": agent_registry_path,
            },
            {
                "name": "model_tier_registry",
                "repo": AGENTS_REPO,
                "role": "tier_entries",
                "ref": model_tier_registry_path,
            },
            {
                "name": "runtime_seam_bindings",
                "repo": AGENTS_REPO,
                "role": "tier_role_bindings",
                "ref": runtime_bindings_path,
            },
            {
                "name": "playbook_registry",
                "repo": PLAYBOOKS_REPO,
                "role": "playbook_entries",
                "ref": playbook_registry_path,
            },
            {
                "name": "federation_spine",
                "repo": KAG_REPO,
                "role": "kag_views",
                "ref": federation_spine_path,
            },
            {
                "name": "dionysus_source_route_retirement_anchor",
                "repo": DIONYSUS_REPO,
                "role": "source_route_retirement",
                "ref": DIONYSUS_SOURCE_ROUTE_ANCHOR_PATH,
            },
            {
                "name": "aoa_sdk_workspace_control_plane",
                "repo": SDK_REPO,
                "role": "runtime_capsule",
                "ref": AOA_SDK_WORKSPACE_CONTROL_PLANE_PATH,
            },
            {
                "name": "aoa_sdk_workspace",
                "repo": SDK_REPO,
                "role": "runtime_anchor",
                "ref": AOA_SDK_WORKSPACE_TOML_PATH,
            },
            {
                "name": "aoa_stats_summary_surface_catalog",
                "repo": STATS_REPO,
                "role": "runtime_capsule",
                "ref": AOA_STATS_SUMMARY_SURFACE_CATALOG_PATH,
            },
            {
                "name": "8dionysus_public_route_map",
                "repo": PROFILE_REPO,
                "role": "orientation_surface",
                "ref": PROFILE_PUBLIC_ROUTE_MAP_PATH,
            },
            {
                "name": "abyss_stack_diagnostic_surface_catalog",
                "repo": ABYSS_STACK_REPO,
                "role": "runtime_capsule",
                "ref": ABYSS_STACK_DIAGNOSTIC_SURFACE_CATALOG_PATH,
            },
            {
                "name": "abyss_stack_diagnostic_session",
                "repo": ABYSS_STACK_REPO,
                "role": "runtime_anchor",
                "ref": ABYSS_STACK_DIAGNOSTIC_SESSION_PATH,
            },
        ],
        "root_entries": [
            {
                "id": "aoa-root",
                "owner_repo": AOA_ROOT_REPO,
                "title": "AoA Federation Root",
                "capsule_surface": make_repo_qualified_ref(AOA_ROOT_REPO, AOA_CENTER_ENTRY_MAP_PATH),
                "authority_surface": make_repo_qualified_ref(AOA_ROOT_REPO, "CHARTER.md"),
                "next_actions": [
                    build_entry_action(
                        verb="inspect",
                        target_repo=AOA_ROOT_REPO,
                        target_surface=AOA_CENTER_ENTRY_MAP_PATH,
                        match_key="route_id",
                        target_value=aoa_center_route_ids[0],
                    ),
                    build_entry_action(
                        verb="inspect",
                        target_repo=AOA_ROOT_REPO,
                        target_surface=AOA_CENTER_ENTRY_MAP_PATH,
                        match_key="route_id",
                        target_value=aoa_center_route_ids[1],
                    ),
                    build_entry_action(
                        verb="inspect",
                        target_repo=AOA_ROOT_REPO,
                        target_surface=AOA_CENTER_ENTRY_MAP_PATH,
                        match_key="route_id",
                        target_value=aoa_center_route_ids[2],
                    ),
                ],
                "fallback": build_entry_action(
                    verb="pick",
                    target_repo=PAIRING_SURFACE_REPO,
                    target_surface="generated/aoa_router.min.json",
                    match_key="kind",
                    target_value=FALLBACK_ROUTER_KIND,
                ),
                "risk": "AoA root orientation can be mistaken for source authority; use the source charter and owning repo surfaces before treating a route card as canon.",
                "next_hops": [
                    build_entry_hop("tier", FEDERATION_DEFAULT_TIER_ENTRY_ID),
                    build_entry_hop("playbook", FEDERATION_DEFAULT_PLAYBOOK_ENTRY_ID),
                    build_entry_hop("kag_view", FEDERATION_DEFAULT_KAG_VIEW_ENTRY_ID),
                ],
            },
            {
                "id": "tos-root",
                "owner_repo": TOS_REPO,
                "title": "ToS Federation Root",
                "capsule_surface": make_repo_qualified_ref(TOS_REPO, TOS_ROOT_ENTRY_MAP_PATH),
                "authority_surface": make_repo_qualified_ref(TOS_REPO, "CHARTER.md"),
                "next_actions": [
                    build_entry_action(
                        verb="inspect",
                        target_repo=TOS_REPO,
                        target_surface=TOS_ROOT_ENTRY_MAP_PATH,
                        match_key="route_id",
                        target_value=TOS_ROOT_ROUTE_IDS[0],
                    ),
                    build_entry_action(
                        verb="inspect",
                        target_repo=TOS_REPO,
                        target_surface=TOS_ROOT_ENTRY_MAP_PATH,
                        match_key="route_id",
                        target_value=TOS_ROOT_ROUTE_IDS[1],
                    ),
                    build_entry_action(
                        verb="inspect",
                        target_repo=TOS_REPO,
                        target_surface=TOS_ROOT_ENTRY_MAP_PATH,
                        match_key="route_id",
                        target_value=TOS_ROOT_ROUTE_IDS[2],
                    ),
                ],
                "fallback": build_entry_action(
                    verb="inspect",
                    target_repo=PAIRING_SURFACE_REPO,
                    target_surface=FEDERATION_ENTRYPOINTS_FILE,
                    match_key="id",
                    target_value="aoa-root",
                ),
                "risk": "ToS root orientation must keep Tree-of-Sophia authority in the charter while handing off to one source-owned tiny-entry route; downstream routing, KAG, and playbook hops remain secondary orientation rather than ToS authority replacement.",
                "next_hops": [
                    build_entry_hop("kag_view", TOS_KAG_VIEW_ENTRY_ID),
                    build_entry_hop("playbook", TOS_KAG_VIEW_PLAYBOOK_ENTRY_ID),
                ],
            },
        ],
        "active_entry_kinds": list(FEDERATION_ACTIVE_ENTRY_KINDS),
        "declared_entry_kinds": list(FEDERATION_DECLARED_ENTRY_KINDS),
        "entrypoints": sorted(
            federation_entrypoints,
            key=lambda entry: (
                FEDERATION_ACTIVE_ENTRY_KINDS.index(entry["kind"]),
                entry["id"],
            ),
        ),
    }


def build_return_navigation_hints_payload(
    techniques_root: Path,
    skills_root: Path,
    evals_root: Path,
    memo_root: Path,
    aoa_root: Path,
    stats_root: Path,
    agents_root: Path,
    playbooks_root: Path,
    kag_root: Path,
    tos_root: Path,
    sdk_root: Path,
    source_route_root: Path,
    profile_root: Path,
    abyss_stack_root: Path,
    hints_payload: dict[str, Any],
    federation_payload: dict[str, Any],
) -> dict[str, Any]:
    def ensure_enabled_action(action: Any, location: str) -> dict[str, Any]:
        payload = ensure_mapping(action, location)
        if payload.get("enabled") is not True:
            raise RouterError(f"{location}.enabled must stay true for return navigation inputs")
        return payload

    def ensure_source_surface_exists(repo_root: Path, relative_path: str, location: str) -> None:
        target_path = repo_root / relative_path
        if not target_path.exists():
            raise RouterError(
                f"{location} target '{relative_posix(target_path, repo_root)}' is missing"
            )

    hint_source_roots = {
        "technique": techniques_root,
        "skill": skills_root,
        "eval": evals_root,
        "memo": memo_root,
    }
    federation_owner_roots = {
        AOA_ROOT_REPO: aoa_root,
        TOS_REPO: tos_root,
        AGENTS_REPO: agents_root,
        PLAYBOOKS_REPO: playbooks_root,
        KAG_REPO: kag_root,
        SDK_REPO: sdk_root,
        STATS_REPO: stats_root,
        DIONYSUS_REPO: source_route_root,
        PROFILE_REPO: profile_root,
        ABYSS_STACK_REPO: abyss_stack_root,
    }

    hints = ensure_list(hints_payload.get("hints"), "task_to_surface_hints.json.hints")
    hint_by_kind: dict[str, dict[str, Any]] = {}
    for index, raw_hint in enumerate(hints):
        location = f"task_to_surface_hints.json.hints[{index}]"
        hint = ensure_mapping(raw_hint, location)
        kind = ensure_string(hint.get("kind"), f"{location}.kind")
        hint_by_kind[kind] = hint

    thin_router_returns: list[dict[str, Any]] = []
    for kind in ACTIVE_KINDS:
        location = f"{Path(RETURN_NAVIGATION_HINTS_FILE).name}.thin_router_returns[{kind}]"
        kind_hint = hint_by_kind.get(kind)
        if kind_hint is None:
            raise RouterError(f"{location} requires a published task_to_surface hint for '{kind}'")
        source_repo = ensure_string(kind_hint.get("source_repo"), f"{location}.source_repo")
        if source_repo != CANONICAL_REPO_BY_KIND[kind]:
            raise RouterError(
                f"{location}.source_repo must stay '{CANONICAL_REPO_BY_KIND[kind]}'"
            )
        actions = ensure_mapping(kind_hint.get("actions"), f"{location}.actions")

        if kind == "memo":
            ensure_enabled_action(actions.get("recall"), f"{location}.actions.recall")
            inspect_surface = MEMO_OBJECT_INSPECT_SURFACE_FILE
            return_contract_path = ensure_repo_relative_path(
                MEMO_OBJECT_RETURN_READY_CONTRACT,
                f"{location}.primary_action.target_surface",
            )
            return_contract_location = f"aoa-memo/{return_contract_path}"
            return_contract = ensure_mapping(
                load_json_file(memo_root / return_contract_path),
                return_contract_location,
            )
            require_keys(
                return_contract,
                (
                    "mode",
                    "inspect_surface",
                    "capsule_surface",
                    "expand_surface",
                    "checkpoint_continuity_supported",
                    "return_ready",
                ),
                return_contract_location,
            )
            if (
                ensure_string(return_contract.get("mode"), f"{return_contract_location}.mode")
                != MEMO_OBJECT_RECALL_DEFAULT_MODE
            ):
                raise RouterError(
                    f"{return_contract_location}.mode must stay '{MEMO_OBJECT_RECALL_DEFAULT_MODE}'"
                )
            if (
                ensure_repo_relative_path(
                    ensure_string(
                        return_contract.get("inspect_surface"),
                        f"{return_contract_location}.inspect_surface",
                    ),
                    f"{return_contract_location}.inspect_surface",
                )
                != MEMO_OBJECT_INSPECT_SURFACE_FILE
            ):
                raise RouterError(
                    f"{return_contract_location}.inspect_surface must stay '{MEMO_OBJECT_INSPECT_SURFACE_FILE}'"
                )
            if (
                ensure_repo_relative_path(
                    ensure_string(
                        return_contract.get("capsule_surface"),
                        f"{return_contract_location}.capsule_surface",
                    ),
                    f"{return_contract_location}.capsule_surface",
                )
                != MEMO_OBJECT_CAPSULE_SURFACE_FILE
            ):
                raise RouterError(
                    f"{return_contract_location}.capsule_surface must stay '{MEMO_OBJECT_CAPSULE_SURFACE_FILE}'"
                )
            if (
                ensure_repo_relative_path(
                    ensure_string(
                        return_contract.get("expand_surface"),
                        f"{return_contract_location}.expand_surface",
                    ),
                    f"{return_contract_location}.expand_surface",
                )
                != MEMO_OBJECT_EXPAND_SURFACE_FILE
            ):
                raise RouterError(
                    f"{return_contract_location}.expand_surface must stay '{MEMO_OBJECT_EXPAND_SURFACE_FILE}'"
                )
            if return_contract.get("checkpoint_continuity_supported") is not True:
                raise RouterError(
                    f"{return_contract_location}.checkpoint_continuity_supported must stay true"
                )
            if return_contract.get("return_ready") is not True:
                raise RouterError(f"{return_contract_location}.return_ready must stay true")
            ensure_source_surface_exists(memo_root, return_contract_path, f"{location}.primary_action")
            ensure_source_surface_exists(memo_root, inspect_surface, f"{location}.secondary_action")
            ensure_source_surface_exists(
                memo_root,
                MEMO_OBJECT_CAPSULE_SURFACE_FILE,
                f"{return_contract_location}.capsule_surface",
            )
            thin_router_returns.append(
                {
                    "context_kind": "memo",
                    "source_repo": source_repo,
                    "supported_return_reasons": list(RETURN_REASONS_BY_THIN_KIND["memo"]),
                    "primary_action": build_return_navigation_action(
                        verb="recall",
                        target_repo=source_repo,
                        target_surface=return_contract_path,
                    ),
                    "secondary_action": build_return_navigation_action(
                        verb="inspect",
                        target_repo=source_repo,
                        target_surface=inspect_surface,
                        match_field="id",
                    ),
                    "ownership_note": (
                        "Checkpoint continuity and recall meaning stay in aoa-memo; routing "
                        "only points back to the public return-ready contract and object surface."
                    ),
                }
            )
            continue

        inspect = ensure_enabled_action(actions.get("inspect"), f"{location}.actions.inspect")
        expand = ensure_enabled_action(actions.get("expand"), f"{location}.actions.expand")
        inspect_surface = ensure_repo_relative_path(
            ensure_string(
                inspect.get("surface_file"),
                f"{location}.actions.inspect.surface_file",
            ),
            f"{location}.actions.inspect.surface_file",
        )
        inspect_match = ensure_string(
            inspect.get("match_field"),
            f"{location}.actions.inspect.match_field",
        )
        expand_surface = ensure_repo_relative_path(
            ensure_string(
                expand.get("surface_file"),
                f"{location}.actions.expand.surface_file",
            ),
            f"{location}.actions.expand.surface_file",
        )
        expand_match = ensure_string(
            expand.get("match_field"),
            f"{location}.actions.expand.match_field",
        )
        expand_section_key = ensure_string(
            expand.get("section_key_field"),
            f"{location}.actions.expand.section_key_field",
        )
        source_root = hint_source_roots[kind]
        ensure_source_surface_exists(source_root, inspect_surface, f"{location}.primary_action")
        ensure_source_surface_exists(source_root, expand_surface, f"{location}.secondary_action")
        thin_router_returns.append(
            {
                "context_kind": kind,
                "source_repo": source_repo,
                "supported_return_reasons": list(RETURN_REASONS_BY_THIN_KIND[kind]),
                "primary_action": build_return_navigation_action(
                    verb="inspect",
                    target_repo=source_repo,
                    target_surface=inspect_surface,
                    match_field=inspect_match,
                ),
                "secondary_action": build_return_navigation_action(
                    verb="expand",
                    target_repo=source_repo,
                    target_surface=expand_surface,
                    match_field=expand_match,
                    section_key_field=None if kind == "skill" else expand_section_key,
                ),
                "ownership_note": {
                    "technique": (
                        "Technique meaning stays in aoa-techniques; routing only points back "
                        "to the smallest reviewable surface."
                    ),
                    "skill": (
                        "Workflow meaning stays in aoa-skills; routing only compresses the "
                        "re-entry hop."
                    ),
                    "eval": (
                        "Proof meaning stays in aoa-evals; routing only returns the reader "
                        "to the bounded proof surface."
                    ),
                }[kind],
            }
        )

    root_entries = ensure_list(
        federation_payload.get("root_entries"),
        "federation_entrypoints.min.json.root_entries",
    )
    root_by_id: dict[str, dict[str, Any]] = {}
    for index, raw_root_entry in enumerate(root_entries):
        location = f"federation_entrypoints.min.json.root_entries[{index}]"
        root_entry = ensure_mapping(raw_root_entry, location)
        root_id = ensure_string(root_entry.get("id"), f"{location}.id")
        root_by_id[root_id] = root_entry

    federation_root_returns: list[dict[str, Any]] = []
    for root_id in FEDERATION_ROOT_IDS:
        location = f"{Path(RETURN_NAVIGATION_HINTS_FILE).name}.federation_root_returns[{root_id}]"
        selected_root_entry = root_by_id.get(root_id)
        if selected_root_entry is None:
            raise RouterError(f"{location} requires federation root entry '{root_id}'")
        owner_repo = ensure_string(
            selected_root_entry.get("owner_repo"),
            f"{location}.owner_repo",
        )
        authority_repo, authority_surface = ensure_repo_qualified_ref(
            selected_root_entry.get("authority_surface"),
            f"{location}.primary_action",
        )
        if authority_repo != owner_repo:
            raise RouterError(f"{location}.primary_action must stay inside owner repo '{owner_repo}'")
        owner_root = federation_owner_roots[owner_repo]
        ensure_source_surface_exists(owner_root, authority_surface, f"{location}.primary_action")
        record = {
            "root_id": root_id,
            "owner_repo": owner_repo,
            "supported_return_reasons": list(RETURN_REASONS_BY_ROOT_ID[root_id]),
            "primary_action": build_return_navigation_action(
                verb="inspect",
                target_repo=authority_repo,
                target_surface=authority_surface,
            ),
            "fallback_action": build_return_navigation_action(
                verb="inspect",
                target_repo=PAIRING_SURFACE_REPO,
                target_surface=FEDERATION_ENTRYPOINTS_FILE,
                match_field="id",
                target_value=root_id,
            ),
            "ownership_note": {
                "aoa-root": (
                    "AoA root authority stays in Agents-of-Abyss. Routing may only point "
                    "back to that source-owned root."
                ),
                "tos-root": (
                    "ToS authority stays in Tree-of-Sophia. Routing may only restore the "
                    "source-owned root and the bounded tiny-entry re-entry hop."
                ),
            }[root_id],
        }
        if root_id == "tos-root":
            record["secondary_action"] = build_return_navigation_action(
                verb="inspect",
                target_repo=TOS_REPO,
                target_surface=TOS_TINY_ENTRY_ROUTE_PATH,
                match_field="route_id",
                target_value=TOS_TINY_ENTRY_ROUTE_ID,
            )
        federation_root_returns.append(record)

    federation_entries = ensure_list(
        federation_payload.get("entrypoints"),
        "federation_entrypoints.min.json.entrypoints",
    )
    entries_by_kind: dict[str, list[dict[str, Any]]] = {
        kind: [] for kind in FEDERATION_ACTIVE_ENTRY_KINDS
    }
    entries_by_id: dict[str, dict[str, Any]] = {}
    for index, raw_entry in enumerate(federation_entries):
        location = f"federation_entrypoints.min.json.entrypoints[{index}]"
        entry = ensure_mapping(raw_entry, location)
        entry_kind = ensure_string(entry.get("kind"), f"{location}.kind")
        if entry_kind in entries_by_kind:
            entries_by_kind[entry_kind].append(entry)
        entry_id = ensure_string(entry.get("id"), f"{location}.id")
        entries_by_id[entry_id] = entry

    federation_kind_return_specs = {
        "agent": {
            "owner_repo": AGENTS_REPO,
            "primary_surface": AGENT_REGISTRY_PATH,
            "ownership_note": (
                "Agent authority stays in aoa-agents; routing only restores the "
                "source-owned registry surface."
            ),
        },
        "tier": {
            "owner_repo": AGENTS_REPO,
            "primary_surface": MODEL_TIER_REGISTRY_PATH,
            "ownership_note": (
                "Tier authority stays in aoa-agents; routing only restores the "
                "source-owned registry surface."
            ),
        },
        "playbook": {
            "owner_repo": PLAYBOOKS_REPO,
            "primary_surface": PLAYBOOK_REGISTRY_PATH,
            "ownership_note": (
                "Playbook authority stays in aoa-playbooks; routing only restores the "
                "source-owned registry surface."
            ),
        },
        "kag_view": {
            "owner_repo": KAG_REPO,
            "primary_surface": FEDERATION_SPINE_PATH,
            "ownership_note": (
                "KAG readiness authority stays in aoa-kag; routing only restores the "
                "bounded derived entry surface."
            ),
        },
        "source_route": {
            "owner_repo": DIONYSUS_REPO,
            "primary_surface": DIONYSUS_SOURCE_ROUTE_ANCHOR_PATH,
            "ownership_note": (
                "Dionysus retired its former source-incubation route role; routing preserves a "
                "compatibility return to the owner decision and then stops before choosing "
                "a current implementation owner."
            ),
        },
        "runtime_surface": {
            "owner_repo": SDK_REPO,
            "primary_surface": AOA_SDK_WORKSPACE_CONTROL_PLANE_PATH,
            "ownership_note": (
                "Runtime surface re-entry uses the compact aoa-sdk control-plane capsule "
                "first; it does not replace runtime authority in aoa-stats or abyss-stack."
            ),
        },
        "orientation_surface": {
            "owner_repo": PROFILE_REPO,
            "primary_surface": PROFILE_PUBLIC_ROUTE_MAP_PATH,
            "ownership_note": (
                "Orientation authority stays narrow in 8Dionysus; routing only restores "
                "the public route map and must not turn the profile into an owner-layer "
                "authority replacement."
            ),
        },
    }

    federation_kind_returns: list[dict[str, Any]] = []
    for entry_kind in FEDERATION_ACTIVE_ENTRY_KINDS:
        location = f"{Path(RETURN_NAVIGATION_HINTS_FILE).name}.federation_kind_returns[{entry_kind}]"
        kind_entries = entries_by_kind.get(entry_kind) or []
        if not kind_entries:
            raise RouterError(f"{location} requires at least one federation entry of kind '{entry_kind}'")
        spec = federation_kind_return_specs[entry_kind]
        owner_repo = spec["owner_repo"]
        primary_surface = spec["primary_surface"]
        owner_root = federation_owner_roots[owner_repo]
        ensure_source_surface_exists(owner_root, primary_surface, f"{location}.primary_action")
        federation_kind_returns.append(
            {
                "entry_kind": entry_kind,
                "owner_repo": owner_repo,
                "supported_return_reasons": list(RETURN_REASONS_BY_FEDERATION_KIND[entry_kind]),
                "primary_action": build_return_navigation_action(
                    verb="inspect",
                    target_repo=owner_repo,
                    target_surface=primary_surface,
                ),
                "fallback_action": build_return_navigation_action(
                    verb="inspect",
                    target_repo=PAIRING_SURFACE_REPO,
                    target_surface=FEDERATION_ENTRYPOINTS_FILE,
                    match_field="kind",
                    target_value=entry_kind,
                ),
                "ownership_note": spec["ownership_note"],
            }
        )

    federation_entry_return_specs: dict[str, dict[str, Any]] = {
        "AOA-P-0031": {
            "entry_kind": "playbook",
            "owner_repo": PLAYBOOKS_REPO,
            "supported_return_reasons": (
                "authority_unclear",
                "artifact_contract_lost",
                "checkpoint_continuity_needed",
                "split_route_needed",
                "human_gate_required",
                "reroute_required",
            ),
            "primary_match_field": "id",
            "primary_target_value": "AOA-P-0031",
            "ownership_note": (
                "AOA-P-0031 owns only the reviewed summon child-return checkpoint route; "
                "routing returns to the playbook registry entry for split, human-gate, or "
                "checkpoint-continuity review, including the SDK E2E fixture re-entry, "
                "without absorbing summon, SDK, memo, eval, or runtime authority."
            ),
        },
        FEDERATION_DEFAULT_RUNTIME_SURFACE_ENTRY_ID: {
            "entry_kind": "runtime_surface",
            "owner_repo": SDK_REPO,
            "ownership_note": (
                "aoa-sdk owns the control-plane capsule for workspace discovery and "
                "compatibility posture; the capsule does not replace sibling runtime authority."
            ),
        },
        "aoa-stats-summary-catalog": {
            "entry_kind": "runtime_surface",
            "owner_repo": STATS_REPO,
            "ownership_note": (
                "aoa-stats owns the summary surface catalog as its compact runtime-entry capsule; "
                "routing must return there without copying stats payloads into its own registry."
            ),
        },
        "abyss-stack-diagnostic-spine": {
            "entry_kind": "runtime_surface",
            "owner_repo": ABYSS_STACK_REPO,
            "ownership_note": (
                "abyss-stack owns the diagnostic surface catalog in the source checkout; "
                "routing must return there without confusing /srv mirrors for source truth."
            ),
        },
        FEDERATION_DEFAULT_SOURCE_ROUTE_ENTRY_ID: {
            "entry_kind": "source_route",
            "owner_repo": DIONYSUS_REPO,
            "ownership_note": (
                "Dionysus owns the accepted decision that retired source-route staging; "
                "routing returns there as a compatibility stop rather than treating the "
                "former source-incubation garden as active."
            ),
        },
        FEDERATION_DEFAULT_ORIENTATION_SURFACE_ENTRY_ID: {
            "entry_kind": "orientation_surface",
            "owner_repo": PROFILE_REPO,
            "ownership_note": (
                "8Dionysus owns the public route map as an orientation-only capsule; it must "
                "not become an authority replacement for owner repos."
            ),
        },
    }
    federation_entry_returns: dict[str, dict[str, Any]] = {}
    for entry_id, spec in federation_entry_return_specs.items():
        location = f"{Path(RETURN_NAVIGATION_HINTS_FILE).name}.federation_entry_returns.{entry_id}"
        selected_entry = entries_by_id.get(entry_id)
        if selected_entry is None:
            raise RouterError(f"{location} requires federation entry '{entry_id}'")
        entry_kind = spec["entry_kind"]
        owner_repo = spec["owner_repo"]
        if ensure_string(selected_entry.get("kind"), f"{location}.entry_kind") != entry_kind:
            raise RouterError(f"{location} must stay aligned with entry kind '{entry_kind}'")
        if ensure_string(selected_entry.get("owner_repo"), f"{location}.owner_repo") != owner_repo:
            raise RouterError(f"{location} must stay aligned with owner repo '{owner_repo}'")
        capsule_repo, capsule_surface = ensure_repo_qualified_ref(
            selected_entry.get("capsule_surface"),
            f"{location}.primary_action",
        )
        if capsule_repo != owner_repo:
            raise RouterError(f"{location}.primary_action must stay inside owner repo '{owner_repo}'")
        ensure_source_surface_exists(
            federation_owner_roots[owner_repo],
            capsule_surface,
            f"{location}.primary_action",
        )
        federation_entry_returns[entry_id] = {
            "entry_kind": entry_kind,
            "owner_repo": owner_repo,
            "supported_return_reasons": list(
                spec.get("supported_return_reasons", RETURN_REASONS_BY_FEDERATION_KIND[entry_kind])
            ),
            "primary_action": build_return_navigation_action(
                verb="inspect",
                target_repo=owner_repo,
                target_surface=capsule_surface,
                match_field=spec.get("primary_match_field"),
                target_value=spec.get("primary_target_value"),
            ),
            "fallback_action": build_return_navigation_action(
                verb="inspect",
                target_repo=PAIRING_SURFACE_REPO,
                target_surface=FEDERATION_ENTRYPOINTS_FILE,
                match_field="id",
                target_value=entry_id,
            ),
            "ownership_note": spec["ownership_note"],
        }

    return {
        "schema_version": "aoa_routing_return_navigation_hints_v2",
        "schema_ref": "mechanics/recurrence/parts/return-navigation/schemas/return-navigation-hints.schema.json",
        "owner_repo": "aoa-routing",
        "surface_kind": "return_navigation_hints",
        "thin_router_returns": thin_router_returns,
        "federation_root_returns": federation_root_returns,
        "federation_kind_returns": federation_kind_returns,
        "federation_entry_returns": federation_entry_returns,
    }


def build_task_to_surface_hints_payload(memo_root: Path) -> dict[str, Any]:
    def action_flags(
        *,
        inspect_enabled: bool,
        surface_file: str | None = None,
        match_field: str | None = None,
        expand_enabled: bool = False,
        expand_surface_file: str | None = None,
        expand_match_field: str | None = None,
        expand_section_key_field: str = "key",
        default_sections: list[str] | None = None,
        supported_sections: list[str] | None = None,
        pick_enabled: bool = True,
        pair_enabled: bool = False,
        pair_surface_repo: str | None = None,
        pair_surface_file: str | None = None,
        pair_match_field: str | None = None,
        recall_enabled: bool = False,
        recall_contract_file: str | None = None,
        recall_default_mode: str | None = None,
        recall_supported_modes: list[str] | None = None,
        recall_contracts_by_mode: dict[str, str] | None = None,
        recall_capsule_surfaces_by_mode: dict[str, str] | None = None,
        recall_parallel_families: dict[str, dict[str, Any]] | None = None,
        second_cut_enabled: bool = False,
        second_cut_surface_repo: str | None = None,
        second_cut_surface_file: str | None = None,
        second_cut_collection_key: str | None = None,
        second_cut_match_field: str | None = None,
        second_cut_selection_axis: str | None = None,
        second_cut_prerequisite_axes: list[str] | None = None,
    ) -> dict[str, dict[str, Any]]:
        inspect: dict[str, Any] = {"enabled": inspect_enabled}
        if inspect_enabled:
            inspect["surface_file"] = surface_file
            inspect["match_field"] = match_field
        expand: dict[str, Any] = {"enabled": expand_enabled}
        if expand_enabled:
            expand["surface_file"] = expand_surface_file
            expand["match_field"] = expand_match_field
            expand["section_key_field"] = expand_section_key_field
            expand["default_sections"] = list(default_sections or [])
            expand["supported_sections"] = list(supported_sections or [])
        pair: dict[str, Any] = {"enabled": pair_enabled}
        if pair_enabled:
            pair["surface_repo"] = pair_surface_repo
            pair["surface_file"] = pair_surface_file
            pair["match_field"] = pair_match_field
        recall: dict[str, Any] = {"enabled": recall_enabled}
        if recall_enabled:
            if recall_contract_file is not None:
                recall["contract_file"] = recall_contract_file
            recall["default_mode"] = recall_default_mode
            recall["supported_modes"] = list(recall_supported_modes or [])
            recall["contracts_by_mode"] = dict(recall_contracts_by_mode or {})
            if recall_capsule_surfaces_by_mode:
                recall["capsule_surfaces_by_mode"] = dict(recall_capsule_surfaces_by_mode)
            if recall_parallel_families:
                recall["parallel_families"] = {
                    family_name: dict(family_payload)
                    for family_name, family_payload in sorted(recall_parallel_families.items())
                }
        actions: dict[str, dict[str, Any]] = {
            "pick": {"enabled": pick_enabled},
            "inspect": inspect,
            "expand": expand,
            "pair": pair,
            "recall": recall,
        }
        if second_cut_enabled:
            actions["second_cut"] = {
                "enabled": True,
                "surface_repo": second_cut_surface_repo,
                "surface_file": second_cut_surface_file,
                "collection_key": second_cut_collection_key,
                "match_field": second_cut_match_field,
                "selection_axis": second_cut_selection_axis,
                "prerequisite_axes": list(second_cut_prerequisite_axes or []),
            }
        return actions

    memo_surfaces = load_memo_catalog_surfaces(memo_root)
    (
        recall_default_mode,
        recall_supported_modes,
        recall_contracts_by_mode,
        recall_capsule_surfaces_by_mode,
    ) = (
        load_router_ready_memo_recall_contracts(memo_root, memo_surfaces)
    )
    recall_parallel_families = load_optional_parallel_memo_recall_families(memo_root)
    recall_contract_file = None
    if recall_default_mode is not None:
        recall_contract_file = recall_contracts_by_mode[recall_default_mode]

    return {
        "version": 1,
        "hints": [
            {
                "kind": "technique",
                "enabled": True,
                "source_repo": "aoa-techniques",
                "use_when": "need a reusable engineering practice or minimal technique selection",
                "actions": action_flags(
                    inspect_enabled=True,
                    surface_file="generated/technique_capsules.json",
                    match_field="id",
                    expand_enabled=True,
                    expand_surface_file="generated/technique_sections.full.json",
                    expand_match_field="id",
                    default_sections=[
                        "intent",
                        "when_to_use",
                        "inputs",
                        "outputs",
                        "core_procedure",
                        "contracts",
                        "risks",
                        "validation",
                    ],
                    supported_sections=[
                        "intent",
                        "when_to_use",
                        "when_not_to_use",
                        "inputs",
                        "outputs",
                        "core_procedure",
                        "contracts",
                        "risks",
                        "validation",
                        "adaptation_notes",
                        "public_sanitization_notes",
                        "example",
                        "checks",
                        "promotion_history",
                        "future_evolution",
                    ],
                    pair_enabled=True,
                    pair_surface_repo=PAIRING_SURFACE_REPO,
                    pair_surface_file=PAIRING_SURFACE_FILE,
                    pair_match_field="id",
                    second_cut_enabled=True,
                    second_cut_surface_repo=TECHNIQUE_KIND_SECOND_CUT_SOURCE_REPO,
                    second_cut_surface_file=TECHNIQUE_KIND_SECOND_CUT_SURFACE_FILE,
                    second_cut_collection_key=TECHNIQUE_KIND_SECOND_CUT_COLLECTION_KEY,
                    second_cut_match_field=TECHNIQUE_KIND_SECOND_CUT_MATCH_FIELD,
                    second_cut_selection_axis=TECHNIQUE_KIND_SECOND_CUT_SELECTION_AXIS,
                    second_cut_prerequisite_axes=list(
                        TECHNIQUE_KIND_SECOND_CUT_PREREQUISITE_AXES
                    ),
                ),
            },
            {
                "kind": "skill",
                "enabled": True,
                "source_repo": "aoa-skills",
                "use_when": "need one current callable skill bundle; use the capability graph for modes, typed relations, and deeper retrieval",
                "actions": action_flags(
                    inspect_enabled=True,
                    surface_file="generated/agent_skill_catalog.min.json",
                    match_field="name",
                    expand_enabled=True,
                    expand_surface_file="generated/capability_graph.json",
                    expand_match_field="id",
                    expand_section_key_field="id",
                    default_sections=[],
                    supported_sections=[],
                    pair_enabled=False,
                ),
            },
            {
                "kind": "eval",
                "enabled": True,
                "source_repo": "aoa-evals",
                "use_when": "need a bounded proof or quality-check surface",
                "actions": action_flags(
                    inspect_enabled=True,
                    surface_file="generated/eval_capsules.json",
                    match_field="name",
                    expand_enabled=True,
                    expand_surface_file="generated/eval_sections.full.json",
                    expand_match_field="name",
                    default_sections=[
                        "bounded_claim",
                        "trigger_boundary",
                        "inputs",
                        "scoring_or_verdict_logic",
                        "outputs",
                        "blind_spots",
                        "interpretation_guidance",
                        "verification",
                    ],
                    supported_sections=[
                        "intent",
                        "object_under_evaluation",
                        "bounded_claim",
                        "trigger_boundary",
                        "inputs",
                        "fixtures_and_case_surface",
                        "scoring_or_verdict_logic",
                        "baseline_or_comparison_mode",
                        "execution_contract",
                        "outputs",
                        "failure_modes",
                        "blind_spots",
                        "interpretation_guidance",
                        "verification",
                        "technique_traceability",
                        "skill_traceability",
                        "adaptation_points",
                    ],
                    pair_enabled=True,
                    pair_surface_repo=PAIRING_SURFACE_REPO,
                    pair_surface_file=PAIRING_SURFACE_FILE,
                    pair_match_field="id",
                ),
            },
            {
                "kind": "memo",
                "enabled": True,
                "source_repo": "aoa-memo",
                "use_when": "need bounded recall or memory-layer doctrine surfaces without copying memo truth into routing",
                "actions": action_flags(
                    inspect_enabled=True,
                    surface_file=MEMO_INSPECT_SURFACE_FILE,
                    match_field="id",
                    expand_enabled=True,
                    expand_surface_file=MEMO_EXPAND_SURFACE_FILE,
                    expand_match_field="id",
                    expand_section_key_field="section_id",
                    default_sections=[],
                    supported_sections=[],
                    recall_enabled=bool(recall_supported_modes),
                    recall_contract_file=recall_contract_file,
                    recall_default_mode=recall_default_mode,
                    recall_supported_modes=recall_supported_modes,
                    recall_contracts_by_mode=recall_contracts_by_mode,
                    recall_capsule_surfaces_by_mode=recall_capsule_surfaces_by_mode,
                    recall_parallel_families=recall_parallel_families,
                ),
            },
        ],
    }


def build_pairing_hints_payload(
    registry_entries: list[dict[str, Any]],
    source_catalog: str,
    technique_catalog_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    index = {(entry["kind"], entry["id"]): entry for entry in registry_entries}
    pairings: dict[tuple[str, str], list[dict[str, str]]] = {
        (entry["kind"], entry["id"]): []
        for entry in registry_entries
        if entry["kind"] in PAIRABLE_KINDS
    }
    seen_pairs: dict[tuple[str, str], set[tuple[str, str, str]]] = {
        key: set() for key in pairings
    }

    def add_pair(source_key: tuple[str, str], target_kind: str, target_id: str, relation: str) -> None:
        if source_key[0] not in PAIRABLE_KINDS:
            return
        if target_kind == "memo":
            raise RouterError("memo entries must not appear in bounded pairing hints")
        if target_kind not in PAIRABLE_KINDS:
            raise RouterError(f"{target_kind} is not supported in the bounded pairing surface")
        if target_kind == "technique" and is_pending_technique_id(target_id):
            return
        if target_kind == source_key[0]:
            if source_key[0] != "technique":
                raise RouterError(
                    f"same-kind pairing is not allowed for {source_key[0]}:{source_key[1]} -> {target_id}"
                )
            if source_key[1] not in KAG_SOURCE_LIFT_TECHNIQUE_SET or target_id not in KAG_SOURCE_LIFT_TECHNIQUE_SET:
                raise RouterError(
                    f"same-kind pairing must stay within the KAG/source-lift family: {source_key[1]} -> {target_id}"
                )
            if relation not in DIRECT_RELATION_TYPES_SET:
                raise RouterError(
                    f"same-kind pairing for {source_key[1]} -> {target_id} must use a supported direct relation"
                )
        elif relation not in {RELATION_REQUIRES, RELATION_REQUIRED_BY}:
            raise RouterError(
                f"cross-kind pairing for {source_key[0]}:{source_key[1]} -> {target_kind}:{target_id} must use requires/required_by"
            )
        if (target_kind, target_id) not in index:
            raise RouterError(
                f"unresolved pairing target: {source_key[0]}:{source_key[1]} -> {target_kind}:{target_id}"
            )
        pair_key = (target_kind, target_id, relation)
        if pair_key in seen_pairs[source_key]:
            return
        seen_pairs[source_key].add(pair_key)
        pairings[source_key].append(
            {"kind": target_kind, "id": target_id, "relation": relation}
        )

    for entry in registry_entries:
        source_key = (entry["kind"], entry["id"])
        if entry["kind"] == "skill":
            for dependency_id in entry["attributes"]["technique_dependencies"]:
                add_pair(source_key, "technique", dependency_id, RELATION_REQUIRES)
                if ("technique", dependency_id) in pairings:
                    add_pair(("technique", dependency_id), "skill", entry["id"], RELATION_REQUIRED_BY)
        elif entry["kind"] == "eval":
            for dependency_id in entry["attributes"]["technique_dependencies"]:
                add_pair(source_key, "technique", dependency_id, RELATION_REQUIRES)
                if ("technique", dependency_id) in pairings:
                    add_pair(("technique", dependency_id), "eval", entry["id"], RELATION_REQUIRED_BY)
            for dependency_name in entry["attributes"]["skill_dependencies"]:
                add_pair(source_key, "skill", dependency_name, RELATION_REQUIRES)
                if ("skill", dependency_name) in pairings:
                    add_pair(("skill", dependency_name), "eval", entry["id"], RELATION_REQUIRED_BY)

    techniques_by_id: dict[str, dict[str, Any]] = {}
    for index_value, item in enumerate(technique_catalog_entries):
        location = f"generated/technique_catalog.min.json.techniques[{index_value}]"
        technique = ensure_mapping(item, location)
        require_keys(technique, ("id",), location)
        technique_id = ensure_string(technique["id"], f"{location}.id")
        techniques_by_id[technique_id] = technique

    for technique_id in KAG_SOURCE_LIFT_TECHNIQUE_IDS:
        selected_technique = techniques_by_id.get(technique_id)
        if selected_technique is None or ("technique", technique_id) not in pairings:
            continue
        raw_relations = selected_technique.get("relations", [])
        if raw_relations is None:
            raw_relations = []
        relations = ensure_list(
            raw_relations,
            f"generated/technique_catalog.min.json.techniques[{technique_id}].relations",
        )
        for relation_index, raw_relation in enumerate(relations):
            relation_location = (
                f"generated/technique_catalog.min.json.techniques[{technique_id}].relations[{relation_index}]"
            )
            relation = ensure_mapping(raw_relation, relation_location)
            require_keys(relation, ("type", "target"), relation_location)
            relation_type = ensure_string(relation["type"], f"{relation_location}.type")
            target_id = ensure_string(relation["target"], f"{relation_location}.target")
            add_pair(("technique", technique_id), "technique", target_id, relation_type)

    payload_entries = []
    for entry in sort_registry_entries(list(registry_entries)):
        if entry["kind"] not in PAIRABLE_KINDS:
            continue
        key = (entry["kind"], entry["id"])
        payload_entries.append(
            {
                "kind": entry["kind"],
                "id": entry["id"],
                "pairs": sort_hops(pairings[key]),
            }
        )
    return {
        "version": 1,
        "source_inputs": {
            "registry_surface": "generated/cross_repo_registry.min.json",
            "kag_relation_source_repo": "aoa-techniques",
            "kag_relation_source_catalog": source_catalog,
        },
        "entries": payload_entries,
    }


def build_tiny_model_entrypoints_payload(
    registry_entries: list[dict[str, Any]],
    hints_payload: dict[str, Any],
    federation_payload: dict[str, Any],
) -> dict[str, Any]:
    registry_index = {(entry["kind"], entry["id"]): entry for entry in registry_entries}
    available_kinds = {entry["kind"] for entry in registry_entries}
    hints = ensure_list(hints_payload.get("hints"), "task_to_surface_hints.json.hints")
    federation_root_entries = ensure_list(
        federation_payload.get("root_entries"),
        "federation_entrypoints.min.json.root_entries",
    )
    federation_entries = ensure_list(
        federation_payload.get("entrypoints"),
        "federation_entrypoints.min.json.entrypoints",
    )
    active_entry_kinds = ensure_string_list(
        federation_payload.get("active_entry_kinds"),
        "federation_entrypoints.min.json.active_entry_kinds",
    )
    memo_recall_supported_modes: list[str] = []
    memo_parallel_recall_modes: dict[str, list[str]] = {}
    queries: list[dict[str, Any]] = [
        {
            "verb": "pick",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": "generated/aoa_router.min.json",
            "match_key": "kind",
            "allowed_kinds": list(ACTIVE_KINDS),
        }
    ]

    for index, raw_hint in enumerate(hints):
        location = f"task_to_surface_hints.json.hints[{index}]"
        hint = ensure_mapping(raw_hint, location)
        kind = ensure_string(hint["kind"], f"{location}.kind")
        source_repo = ensure_string(hint["source_repo"], f"{location}.source_repo")
        actions = ensure_mapping(hint["actions"], f"{location}.actions")

        inspect = ensure_mapping(actions["inspect"], f"{location}.actions.inspect")
        if inspect.get("enabled") is True:
            queries.append(
                {
                    "verb": "inspect",
                    "source_repo": source_repo,
                    "target_surface": ensure_string(
                        inspect.get("surface_file"),
                        f"{location}.actions.inspect.surface_file",
                    ),
                    "match_key": ensure_string(
                        inspect.get("match_field"),
                        f"{location}.actions.inspect.match_field",
                    ),
                    "allowed_kinds": [kind],
                }
            )

        expand = ensure_mapping(actions["expand"], f"{location}.actions.expand")
        if expand.get("enabled") is True:
            queries.append(
                {
                    "verb": "expand",
                    "source_repo": source_repo,
                    "target_surface": ensure_string(
                        expand.get("surface_file"),
                        f"{location}.actions.expand.surface_file",
                    ),
                    "match_key": ensure_string(
                        expand.get("match_field"),
                        f"{location}.actions.expand.match_field",
                    ),
                    "allowed_kinds": [kind],
                    "section_key_field": ensure_string(
                        expand.get("section_key_field"),
                        f"{location}.actions.expand.section_key_field",
                    ),
                    "default_sections": ensure_string_list(
                        expand.get("default_sections"),
                        f"{location}.actions.expand.default_sections",
                    ),
                }
            )

        pair = ensure_mapping(actions["pair"], f"{location}.actions.pair")
        if pair.get("enabled") is True:
            queries.append(
                {
                    "verb": "pair",
                    "source_repo": ensure_string(
                        pair.get("surface_repo"),
                        f"{location}.actions.pair.surface_repo",
                    ),
                    "target_surface": ensure_string(
                        pair.get("surface_file"),
                        f"{location}.actions.pair.surface_file",
                    ),
                    "match_key": ensure_string(
                        pair.get("match_field"),
                        f"{location}.actions.pair.match_field",
                    ),
                    "allowed_kinds": [kind],
                }
            )

        recall = ensure_mapping(actions["recall"], f"{location}.actions.recall")
        if recall.get("enabled") is True:
            queries.append(
                {
                    "verb": "recall",
                    "source_repo": PAIRING_SURFACE_REPO,
                    "target_surface": "generated/task_to_surface_hints.json",
                    "match_key": "kind",
                    "allowed_kinds": [kind],
                }
            )
            if kind == "memo":
                memo_recall_supported_modes = ensure_string_list(
                    recall.get("supported_modes"),
                    f"{location}.actions.recall.supported_modes",
                )
                parallel_families = recall.get("parallel_families")
                if parallel_families is not None:
                    parallel_family_payloads = ensure_mapping(
                        parallel_families,
                        f"{location}.actions.recall.parallel_families",
                    )
                    for family_name, raw_family in sorted(parallel_family_payloads.items()):
                        family_location = (
                            f"{location}.actions.recall.parallel_families.{family_name}"
                        )
                        family_payload = ensure_mapping(raw_family, family_location)
                        memo_parallel_recall_modes[family_name] = ensure_string_list(
                            family_payload.get("supported_modes"),
                            f"{family_location}.supported_modes",
                        )
                        queries.append(
                            {
                                "verb": "recall",
                                "source_repo": PAIRING_SURFACE_REPO,
                                "target_surface": "generated/task_to_surface_hints.json",
                                "match_key": "kind",
                                "allowed_kinds": [kind],
                                "recall_family": family_name,
                            }
                        )

    starters: list[dict[str, Any]] = [
        {
            "name": "router-root",
            "verb": "pick",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": "generated/aoa_router.min.json",
            "match_key": "kind",
            "allowed_kinds": list(ACTIVE_KINDS),
        }
    ]
    for kind in ACTIVE_KINDS:
        if kind not in available_kinds:
            continue
        starter = {
            "name": f"{kind}-root",
            "verb": "pick",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": "generated/aoa_router.min.json",
            "match_key": "kind",
            "allowed_kinds": [kind],
            "target_kind": kind,
            "target_value": kind,
        }
        starters.append(starter)
    for mode in memo_recall_supported_modes:
        starters.append(
            {
                "name": f"memo-recall-{mode.replace('_', '-')}",
                "verb": "recall",
                "source_repo": PAIRING_SURFACE_REPO,
                "target_surface": "generated/task_to_surface_hints.json",
                "match_key": "kind",
                "allowed_kinds": ["memo"],
                "target_kind": "memo",
                "target_value": "memo",
                "recall_mode": mode,
            }
        )
    for family_name, supported_modes in sorted(memo_parallel_recall_modes.items()):
        starter_prefix = f"memo-{family_name.replace('_', '-')}-recall"
        if family_name == MEMO_OBJECT_RECALL_FAMILY:
            starter_prefix = "memo-object-recall"
        for mode in supported_modes:
            starters.append(
                {
                    "name": f"{starter_prefix}-{mode.replace('_', '-')}",
                    "verb": "recall",
                    "source_repo": PAIRING_SURFACE_REPO,
                    "target_surface": "generated/task_to_surface_hints.json",
                    "match_key": "kind",
                    "allowed_kinds": ["memo"],
                    "target_kind": "memo",
                    "target_value": "memo",
                    "recall_family": family_name,
                    "recall_mode": mode,
                }
            )
    if ("technique", KAG_DEFAULT_ENTRYPOINT_ID) in registry_index:
        starters.append(
            {
                "name": "kag-source-lift-default",
                "verb": "inspect",
                "source_repo": "aoa-techniques",
                "target_surface": "generated/technique_capsules.json",
                "match_key": "id",
                "allowed_kinds": ["technique"],
                "target_kind": "technique",
                "target_value": KAG_DEFAULT_ENTRYPOINT_ID,
            }
        )
        starters.append(
            {
                "name": "kag-source-lift-companions",
                "verb": "pair",
                "source_repo": PAIRING_SURFACE_REPO,
                "target_surface": PAIRING_SURFACE_FILE,
                "match_key": "id",
                "allowed_kinds": ["technique"],
                "target_kind": "technique",
                "target_value": KAG_DEFAULT_ENTRYPOINT_ID,
            }
        )

    root_ids = [
        ensure_string(entry.get("id"), f"federation_entrypoints.min.json.root_entries[{index}].id")
        for index, entry in enumerate(federation_root_entries)
        if isinstance(entry, dict)
    ]
    federation_entry_ids_by_kind: dict[str, list[str]] = {}
    for index, raw_entry in enumerate(federation_entries):
        location = f"federation_entrypoints.min.json.entrypoints[{index}]"
        entry = ensure_mapping(raw_entry, location)
        entry_kind = ensure_string(entry.get("kind"), f"{location}.kind")
        entry_id = ensure_string(entry.get("id"), f"{location}.id")
        federation_entry_ids_by_kind.setdefault(entry_kind, []).append(entry_id)

    if FEDERATION_DEFAULT_AGENT_ENTRY_ID not in federation_entry_ids_by_kind.get("agent", []):
        raise RouterError(
            f"tiny-model federation seam requires agent '{FEDERATION_DEFAULT_AGENT_ENTRY_ID}'"
        )
    if FEDERATION_DEFAULT_TIER_ENTRY_ID not in federation_entry_ids_by_kind.get("tier", []):
        raise RouterError(
            f"tiny-model federation seam requires tier '{FEDERATION_DEFAULT_TIER_ENTRY_ID}'"
        )
    if FEDERATION_DEFAULT_PLAYBOOK_ENTRY_ID not in federation_entry_ids_by_kind.get("playbook", []):
        raise RouterError(
            f"tiny-model federation seam requires playbook '{FEDERATION_DEFAULT_PLAYBOOK_ENTRY_ID}'"
        )
    if FEDERATION_DEFAULT_KAG_VIEW_ENTRY_ID not in federation_entry_ids_by_kind.get("kag_view", []):
        raise RouterError(
            f"tiny-model federation seam requires KAG view '{FEDERATION_DEFAULT_KAG_VIEW_ENTRY_ID}'"
        )
    if FEDERATION_DEFAULT_SOURCE_ROUTE_ENTRY_ID not in federation_entry_ids_by_kind.get("source_route", []):
        raise RouterError(
            f"tiny-model federation seam requires source-route entry '{FEDERATION_DEFAULT_SOURCE_ROUTE_ENTRY_ID}'"
        )
    if (
        FEDERATION_DEFAULT_RUNTIME_SURFACE_ENTRY_ID
        not in federation_entry_ids_by_kind.get("runtime_surface", [])
    ):
        raise RouterError(
            "tiny-model federation seam requires runtime surface "
            f"'{FEDERATION_DEFAULT_RUNTIME_SURFACE_ENTRY_ID}'"
        )
    if (
        FEDERATION_DEFAULT_ORIENTATION_SURFACE_ENTRY_ID
        not in federation_entry_ids_by_kind.get("orientation_surface", [])
    ):
        raise RouterError(
            "tiny-model federation seam requires orientation surface "
            f"'{FEDERATION_DEFAULT_ORIENTATION_SURFACE_ENTRY_ID}'"
        )

    federation_queries: list[dict[str, Any]] = [
        {
            "name": "federation-kind-pick",
            "verb": "pick",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": FEDERATION_ENTRYPOINTS_FILE,
            "match_key": "kind",
            "allowed_entry_kinds": active_entry_kinds,
        },
        {
            "name": "federation-entry-inspect",
            "verb": "inspect",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": FEDERATION_ENTRYPOINTS_FILE,
            "match_key": "id",
            "allowed_entry_kinds": active_entry_kinds,
        },
        {
            "name": "federation-root-inspect",
            "verb": "inspect",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": FEDERATION_ENTRYPOINTS_FILE,
            "match_key": "id",
            "allowed_root_ids": root_ids,
        },
    ]
    federation_starters: list[dict[str, Any]] = [
        {
            "name": "federation-root",
            "verb": "pick",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": FEDERATION_ENTRYPOINTS_FILE,
        },
        {
            "name": "aoa-root",
            "verb": "inspect",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": FEDERATION_ENTRYPOINTS_FILE,
            "match_key": "id",
            "target_value": "aoa-root",
        },
        {
            "name": "tos-root",
            "verb": "inspect",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": FEDERATION_ENTRYPOINTS_FILE,
            "match_key": "id",
            "target_value": "tos-root",
        },
        {
            "name": "agent-root",
            "verb": "inspect",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": FEDERATION_ENTRYPOINTS_FILE,
            "match_key": "id",
            "target_value": FEDERATION_DEFAULT_AGENT_ENTRY_ID,
            "entry_kind": "agent",
        },
        {
            "name": "tier-root",
            "verb": "inspect",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": FEDERATION_ENTRYPOINTS_FILE,
            "match_key": "id",
            "target_value": FEDERATION_DEFAULT_TIER_ENTRY_ID,
            "entry_kind": "tier",
        },
        {
            "name": "playbook-root",
            "verb": "inspect",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": FEDERATION_ENTRYPOINTS_FILE,
            "match_key": "id",
            "target_value": FEDERATION_DEFAULT_PLAYBOOK_ENTRY_ID,
            "entry_kind": "playbook",
        },
        {
            "name": "kag-view-root",
            "verb": "inspect",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": FEDERATION_ENTRYPOINTS_FILE,
            "match_key": "id",
            "target_value": FEDERATION_DEFAULT_KAG_VIEW_ENTRY_ID,
            "entry_kind": "kag_view",
        },
        {
            "name": "source-route-root",
            "verb": "inspect",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": FEDERATION_ENTRYPOINTS_FILE,
            "match_key": "id",
            "target_value": FEDERATION_DEFAULT_SOURCE_ROUTE_ENTRY_ID,
            "entry_kind": "source_route",
        },
        {
            "name": "runtime-surface-root",
            "verb": "inspect",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": FEDERATION_ENTRYPOINTS_FILE,
            "match_key": "id",
            "target_value": FEDERATION_DEFAULT_RUNTIME_SURFACE_ENTRY_ID,
            "entry_kind": "runtime_surface",
        },
        {
            "name": "checkpoint-root",
            "verb": "inspect",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": FEDERATION_ENTRYPOINTS_FILE,
            "match_key": "id",
            "target_value": FEDERATION_DEFAULT_RUNTIME_SURFACE_ENTRY_ID,
            "entry_kind": "runtime_surface",
        },
        {
            "name": "orientation-surface-root",
            "verb": "inspect",
            "source_repo": PAIRING_SURFACE_REPO,
            "target_surface": FEDERATION_ENTRYPOINTS_FILE,
            "match_key": "id",
            "target_value": FEDERATION_DEFAULT_ORIENTATION_SURFACE_ENTRY_ID,
            "entry_kind": "orientation_surface",
        },
    ]

    return {
        "schema_version": "aoa_routing_tiny_model_entrypoints_v2",
        "schema_ref": "routing/core/schemas/tiny-model-entrypoints.schema.json",
        "owner_repo": "aoa-routing",
        "surface_kind": "tiny_model_entrypoints",
        "queries": queries,
        "starters": starters,
        "federation_queries": federation_queries,
        "federation_starters": federation_starters,
    }


def build_task_to_tier_hints_payload(agents_root: Path) -> dict[str, Any]:
    registry_relative_path, tier_index = load_model_tier_registry(agents_root)
    hints: list[dict[str, Any]] = []
    for spec in TASK_TO_TIER_HINT_SPECS:
        preferred_tier = spec["preferred_tier"]
        preferred_entry = tier_index.get(preferred_tier)
        if preferred_entry is None:
            raise RouterError(
                f"task-to-tier hint spec references unknown preferred tier '{preferred_tier}'"
            )

        fallback_tier = spec["fallback_tier"]
        if fallback_tier is not None and fallback_tier not in tier_index:
            raise RouterError(
                f"task-to-tier hint spec references unknown fallback tier '{fallback_tier}'"
            )

        hints.append(
            {
                "task_family": spec["task_family"],
                "preferred_tier": preferred_tier,
                "fallback_tier": fallback_tier,
                "use_when": spec["use_when"],
                "output_artifact": preferred_entry["artifact_requirement"],
            }
        )

    return {
        "version": 1,
        "source_of_truth": {
            "tier_registry_repo": MODEL_TIER_SOURCE_REPO,
            "tier_registry_path": registry_relative_path,
        },
        "hints": hints,
    }


def build_recommended_paths_payload(registry_entries: list[dict[str, Any]]) -> dict[str, Any]:
    index = {(entry["kind"], entry["id"]): entry for entry in registry_entries}
    adjacency: dict[tuple[str, str], dict[str, list[dict[str, str]]]] = {
        (entry["kind"], entry["id"]): {"upstream": [], "downstream": []}
        for entry in registry_entries
    }

    def add_hop(
        source_key: tuple[str, str],
        target_kind: str,
        target_id: str,
    ) -> None:
        if target_kind == source_key[0]:
            raise RouterError(
                f"same-kind hop is not allowed for {source_key[0]}:{source_key[1]} -> {target_id}"
            )
        if target_kind not in RECOMMENDED_HOP_KINDS:
            raise RouterError(f"{target_kind} hops are not supported in the bounded recommended path surface")
        if target_kind == "technique" and is_pending_technique_id(target_id):
            return
        target_key = (target_kind, target_id)
        if target_key not in index:
            raise RouterError(
                f"unresolved dependency: {source_key[0]}:{source_key[1]} -> {target_kind}:{target_id}"
            )
        adjacency[source_key]["upstream"].append(
            {"kind": target_kind, "id": target_id, "relation": RELATION_REQUIRES}
        )
        adjacency[target_key]["downstream"].append(
            {"kind": source_key[0], "id": source_key[1], "relation": RELATION_REQUIRED_BY}
        )

    for entry in registry_entries:
        if entry["kind"] == "skill":
            for dependency_id in entry["attributes"]["technique_dependencies"]:
                add_hop((entry["kind"], entry["id"]), "technique", dependency_id)
        elif entry["kind"] == "eval":
            for dependency_id in entry["attributes"]["technique_dependencies"]:
                add_hop((entry["kind"], entry["id"]), "technique", dependency_id)
            for dependency_name in entry["attributes"]["skill_dependencies"]:
                add_hop((entry["kind"], entry["id"]), "skill", dependency_name)

    payload_entries = []
    for entry in sort_registry_entries(list(registry_entries)):
        key = (entry["kind"], entry["id"])
        payload_entries.append(
            {
                "kind": entry["kind"],
                "id": entry["id"],
                "upstream": sort_hops(adjacency[key]["upstream"]),
                "downstream": sort_hops(adjacency[key]["downstream"]),
            }
        )
    return {
        "version": 1,
        "entries": payload_entries,
    }


def build_kag_source_lift_relation_hints_payload(
    registry_entries: list[dict[str, Any]],
    source_catalog: str,
    technique_catalog_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    registry_index: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in registry_entries:
        kind = entry.get("kind")
        identifier = entry.get("id")
        if not isinstance(kind, str) or not isinstance(identifier, str):
            continue
        registry_index[(kind, identifier)] = entry
    techniques_by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(technique_catalog_entries):
        location = f"generated/technique_catalog.min.json.techniques[{index}]"
        technique = ensure_mapping(item, location)
        require_keys(technique, ("id", "name", "summary"), location)
        technique_id = ensure_string(technique["id"], f"{location}.id")
        if technique_id in techniques_by_id:
            raise RouterError(f"duplicate technique catalog entry for {technique_id}")
        techniques_by_id[technique_id] = technique

    payload_entries: list[dict[str, Any]] = []
    for technique_id in KAG_SOURCE_LIFT_TECHNIQUE_IDS:
        selected_technique = techniques_by_id.get(technique_id)
        if selected_technique is None:
            continue

        registry_entry = registry_index.get(("technique", technique_id))
        if registry_entry is None:
            raise RouterError(f"missing registry entry for technique relation hints {technique_id}")

        raw_relations = selected_technique.get("relations", [])
        if raw_relations is None:
            raw_relations = []
        relations = ensure_list(
            raw_relations,
            f"generated/technique_catalog.min.json.techniques[{technique_id}].relations",
        )
        direct_relations: list[dict[str, str]] = []
        seen_relations: set[tuple[str, str]] = set()
        for relation_index, raw_relation in enumerate(relations):
            relation_location = (
                f"generated/technique_catalog.min.json.techniques[{technique_id}].relations[{relation_index}]"
            )
            relation = ensure_mapping(raw_relation, relation_location)
            require_keys(relation, ("type", "target"), relation_location)
            relation_type = ensure_string(relation["type"], f"{relation_location}.type")
            target_id = ensure_string(relation["target"], f"{relation_location}.target")
            if relation_type not in DIRECT_RELATION_TYPES_SET:
                raise RouterError(f"{relation_location}.type must be a supported direct relation type")
            if target_id == technique_id:
                raise RouterError(f"{relation_location}.target must not point to the same technique")
            if target_id not in KAG_SOURCE_LIFT_TECHNIQUE_SET:
                raise RouterError(
                    f"{relation_location}.target must stay within the KAG/source-lift family"
                )
            if (relation_type, target_id) in seen_relations:
                raise RouterError(
                    f"{relation_location} duplicates a direct relation already seen for {technique_id}"
                )
            if ("technique", target_id) not in registry_index:
                raise RouterError(
                    f"unresolved direct relation target: technique:{technique_id} -> technique:{target_id}"
                )
            seen_relations.add((relation_type, target_id))
            direct_relations.append({"type": relation_type, "target": target_id})

        payload_entries.append(
            {
                "kind": "technique",
                "id": ensure_string(registry_entry.get("id"), f"registry[technique:{technique_id}].id"),
                "name": ensure_string(
                    registry_entry.get("name"),
                    f"registry[technique:{technique_id}].name",
                ),
                "summary": ensure_string(
                    registry_entry.get("summary"),
                    f"registry[technique:{technique_id}].summary",
                ),
                "relations": direct_relations,
            }
        )

    return {
        "version": 1,
        "scope": "kag_source_lift_family",
        "source_repo": "aoa-techniques",
        "source_catalog": source_catalog,
        "family_ids": list(KAG_SOURCE_LIFT_TECHNIQUE_IDS),
        "entries": payload_entries,
    }
