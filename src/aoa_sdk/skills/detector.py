from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

from ..closeout import CloseoutAPI
from ..compatibility import load_surface
from ..loaders import load_json
from ..models import (
    KernelNextStepBrief,
    ProjectFoundationProfileSurface,
    SkillCard,
    SkillDetectionReport,
    SkillDispatchItem,
    SkillHostAvailability,
)
from ..workspace.discovery import Workspace
from .session import resolve_session_file


TOKEN_RE = re.compile(r"[a-z0-9_-]+")
STRONG_MATCH_MIN_SCORE = 4
MAX_AUTO_ACTIVATIONS = 3
PHASES = {"ingress", "pre-mutation", "closeout"}
MUTATION_SURFACES = {"none", "code", "repo-config", "infra", "runtime", "public-share"}


def load_project_foundation(workspace: Workspace) -> ProjectFoundationProfileSurface:
    data = load_surface(workspace, "aoa-skills.project_foundation_profile.min")
    return ProjectFoundationProfileSurface.model_validate(data)


def load_tiny_router_bands(workspace: Workspace) -> dict[str, dict[str, Any]]:
    data = load_surface(workspace, "aoa-skills.tiny_router_candidate_bands")
    return {entry["id"]: entry for entry in data.get("bands", [])}


def load_tiny_router_capsules(workspace: Workspace) -> dict[str, dict[str, Any]]:
    data = load_surface(workspace, "aoa-skills.tiny_router_capsules.min")
    return {entry["name"]: entry for entry in data.get("skills", [])}


def load_collision_families(workspace: Workspace) -> dict[str, str | None]:
    data = load_surface(workspace, "aoa-skills.skill_trigger_collision_matrix")
    mapping: dict[str, str | None] = {}
    for family in data.get("families", []):
        family_id = family.get("family")
        for skill_name in family.get("skills", []):
            if isinstance(skill_name, str) and isinstance(family_id, str) and skill_name not in mapping:
                mapping[skill_name] = family_id
    return mapping


def detect_skills(
    workspace: Workspace,
    *,
    repo_root: str | Path,
    phase: Literal["ingress", "pre-mutation", "closeout"],
    intent_text: str = "",
    mutation_surface: Literal["none", "code", "repo-config", "infra", "runtime", "public-share"] = "none",
    closeout_path: str | Path | None = None,
    host_available_skills: list[str] | None = None,
    host_availability_source: Literal[
        "host-manifest",
        "host-skill-list",
        "repo-install",
        "workspace-install",
        "user-install",
        "not-provided",
    ] = "not-provided",
) -> SkillDetectionReport:
    if phase not in PHASES:
        raise ValueError(f"unsupported phase {phase!r}")
    if mutation_surface not in MUTATION_SURFACES:
        raise ValueError(f"unsupported mutation_surface {mutation_surface!r}")

    foundation = load_project_foundation(workspace)
    resolved_repo_root = _resolve_repo_root(workspace, repo_root)
    layer_by_skill = _build_layer_map(foundation)
    collision_by_skill = load_collision_families(workspace)
    host_inventory = _normalize_host_inventory(
        workspace,
        resolved_repo_root=resolved_repo_root,
        host_available_skills=host_available_skills,
        host_availability_source=host_availability_source,
    )

    if phase == "closeout":
        closeout_chain = _load_closeout_chain(workspace, closeout_path)
        closeout_must_confirm = _closeout_must_confirm(
            closeout_chain=closeout_chain,
            layer_by_skill=layer_by_skill,
            collision_by_skill=collision_by_skill,
            host_inventory=host_inventory,
        )
        reasoning = [
            "closeout phase reuses the existing kernel next-step brief instead of rebuilding post-session routing.",
        ]
        if closeout_chain is None:
            reasoning.append("no closeout_chain was available from the supplied path.")
        reasoning.extend(_host_inventory_reasoning(host_inventory))
        return SkillDetectionReport(
            phase=phase,
            repo_root=str(resolved_repo_root),
            foundation_id=foundation.foundation_id,
            activate_now=[],
            must_confirm=closeout_must_confirm,
            suggest_next=[],
            host_inventory_provided=host_inventory.is_provided,
            actionability_gaps=_actionability_gaps(
                activate_now=[],
                must_confirm=closeout_must_confirm,
                suggest_next=[],
            ),
            blocked_actions=[],
            closeout_chain=closeout_chain,
            reasoning=reasoning,
        )

    cards = load_skill_cards(workspace)
    cards_by_name = {card.name: card for card in cards if card.name in set(foundation.skills)}
    capsules_by_name = load_tiny_router_capsules(workspace)
    bands_by_id = load_tiny_router_bands(workspace)
    score_by_skill = _score_foundation_skills(
        cards_by_name=cards_by_name,
        capsules_by_name=capsules_by_name,
        query=intent_text,
    )
    top_band_id, top_band_score = _select_top_band(
        foundation=foundation,
        bands_by_id=bands_by_id,
        score_by_skill=score_by_skill,
    )
    reasoning = [
        f"repo context: {resolved_repo_root.name}",
        f"phase: {phase}",
        f"mutation_surface: {mutation_surface}",
    ]
    if top_band_id is not None:
        reasoning.append(f"top tiny-router band: {top_band_id} (score={top_band_score})")
    else:
        reasoning.append("no tiny-router band scored above zero.")
    reasoning.extend(_host_inventory_reasoning(host_inventory))

    activate_now: list[SkillDispatchItem] = []
    must_confirm: list[SkillDispatchItem] = []
    suggest_next: list[SkillDispatchItem] = []
    blocked_actions: list[str] = []

    if phase == "pre-mutation":
        must_confirm.extend(
            _risk_gate_items(
                mutation_surface=mutation_surface,
                collision_by_skill=collision_by_skill,
                layer_by_skill=layer_by_skill,
                host_inventory=host_inventory,
            )
        )
        blocked_actions.extend(_blocked_actions_for_mutation_surface(mutation_surface))

    if top_band_id is not None and top_band_score >= STRONG_MATCH_MIN_SCORE:
        top_band = bands_by_id[top_band_id]
        activated_families: set[str] = set()
        used_skills: set[str] = {item.skill_name for item in must_confirm}
        for skill_name in top_band.get("skills", []):
            if skill_name not in cards_by_name or skill_name not in foundation.skills:
                continue
            score = score_by_skill.get(skill_name, 0)
            if score <= 0:
                continue
            card = cards_by_name[skill_name]
            family = collision_by_skill.get(skill_name)
            item = SkillDispatchItem(
                skill_name=skill_name,
                layer=layer_by_skill[skill_name],
                collision_family=family,
                reason=f"strong tiny-router match in band {top_band_id} (score={score})",
                host_availability=_host_availability_for_skill(
                    skill_name,
                    host_inventory=host_inventory,
                    manual_fallback_allowed=False,
                ),
            )
            if (
                card.invocation_mode != "explicit-preferred"
                or skill_name in set(top_band.get("manual_only_skills", []))
            ):
                must_confirm.append(item)
                used_skills.add(skill_name)
                continue
            if family is not None and family in activated_families:
                continue
            if len(activate_now) >= MAX_AUTO_ACTIVATIONS:
                continue
            activate_now.append(item)
            used_skills.add(skill_name)
            if family is not None:
                activated_families.add(family)
        if not activate_now:
            reasoning.append("top band was strong, but every matching skill remained explicit-only or otherwise non-auto.")
    else:
        reasoning.append("no strong tiny-router band survived, so detector stayed recommendation-only.")

    scored_skills = sorted(
        (
            name
            for name, score in score_by_skill.items()
            if score > 0 and name in foundation.skills
        ),
        key=lambda name: (-score_by_skill[name], name),
    )
    for skill_name in scored_skills:
        if skill_name in {item.skill_name for item in activate_now} | {item.skill_name for item in must_confirm}:
            continue
        suggest_next.append(
            SkillDispatchItem(
                skill_name=skill_name,
                layer=layer_by_skill[skill_name],
                collision_family=collision_by_skill.get(skill_name),
                reason=f"secondary router signal (score={score_by_skill[skill_name]})",
                host_availability=_host_availability_for_skill(
                    skill_name,
                    host_inventory=host_inventory,
                    manual_fallback_allowed=True,
                ),
            )
        )
        if len(suggest_next) >= MAX_AUTO_ACTIVATIONS:
            break

    activate_now, demoted_activate_now = _demote_non_executable_activate_now(
        activate_now,
        host_inventory=host_inventory,
    )
    if demoted_activate_now:
        must_confirm.extend(demoted_activate_now)
        reasoning.append(
            "host inventory demoted one or more auto-activation candidates into must_confirm because they were router-only for this session."
        )

    must_confirm = _dedupe_items(must_confirm)
    suggest_next = _dedupe_items(suggest_next)
    actionability_gaps = _actionability_gaps(
        activate_now=activate_now,
        must_confirm=must_confirm,
        suggest_next=suggest_next,
    )

    return SkillDetectionReport(
        phase=phase,
        repo_root=str(resolved_repo_root),
        foundation_id=foundation.foundation_id,
        activate_now=activate_now,
        must_confirm=must_confirm,
        suggest_next=suggest_next,
        host_inventory_provided=host_inventory.is_provided,
        actionability_gaps=actionability_gaps,
        blocked_actions=list(dict.fromkeys(blocked_actions)),
        closeout_chain=None,
        reasoning=reasoning,
    )


def dispatch_skills(
    workspace: Workspace,
    *,
    repo_root: str | Path,
    phase: Literal["ingress", "pre-mutation", "closeout"],
    intent_text: str = "",
    mutation_surface: Literal["none", "code", "repo-config", "infra", "runtime", "public-share"] = "none",
    closeout_path: str | Path | None = None,
    session_file: str | Path | None = None,
    host_available_skills: list[str] | None = None,
    host_availability_source: Literal[
        "host-manifest",
        "host-skill-list",
        "repo-install",
        "workspace-install",
        "user-install",
        "not-provided",
    ] = "not-provided",
) -> SkillDetectionReport:
    from .discovery import SkillsAPI

    report = detect_skills(
        workspace,
        repo_root=repo_root,
        phase=phase,
        intent_text=intent_text,
        mutation_surface=mutation_surface,
        closeout_path=closeout_path,
        host_available_skills=host_available_skills,
        host_availability_source=host_availability_source,
    )
    if phase == "closeout" or not report.activate_now:
        return report

    skills_api = SkillsAPI(workspace)
    target_session_file = str(resolve_session_file(workspace, session_file))
    cards = {card.name: card for card in load_skill_cards(workspace)}
    for item in report.activate_now:
        card = cards[item.skill_name]
        skills_api.activate(
            item.skill_name,
            session_file=target_session_file,
            explicit_handle=_explicit_handle(card),
        )
    return report


def load_skill_cards(workspace: Workspace) -> list[SkillCard]:
    data = load_surface(workspace, "aoa-skills.runtime_discovery_index")
    return [SkillCard.model_validate(item) for item in data.get("skills", [])]


def _resolve_repo_root(workspace: Workspace, repo_root: str | Path) -> Path:
    path = Path(repo_root).expanduser()
    if not path.is_absolute():
        path = (workspace.root / path).resolve()
    else:
        path = path.resolve()
    return path


def _build_layer_map(foundation: ProjectFoundationProfileSurface) -> dict[str, Literal["kernel", "outer-ring", "risk-ring"]]:
    mapping: dict[str, Literal["kernel", "outer-ring", "risk-ring"]] = {}
    for skill_name in foundation.kernel_skills:
        mapping[skill_name] = "kernel"
    for skill_name in foundation.outer_ring_skills:
        mapping[skill_name] = "outer-ring"
    for skill_name in foundation.risk_ring_skills:
        mapping[skill_name] = "risk-ring"
    return mapping


def _score_foundation_skills(
    *,
    cards_by_name: dict[str, SkillCard],
    capsules_by_name: dict[str, dict[str, Any]],
    query: str,
) -> dict[str, int]:
    query_text = (query or "").casefold().strip()
    tokens = set(TOKEN_RE.findall(query_text))
    scores: dict[str, int] = {}
    for skill_name, card in cards_by_name.items():
        capsule = capsules_by_name.get(skill_name)
        score = 0
        if query_text and query_text in card.description.casefold():
            score += 2
        if query_text and query_text in card.short_description.casefold():
            score += 2
        for token in tokens:
            if any(token == keyword.casefold() for keyword in card.keywords):
                score += 1
        if capsule is not None:
            cue_phrases = [phrase.casefold() for phrase in capsule.get("cue_phrases", [])]
            cue_tokens = {token.casefold() for token in capsule.get("cue_tokens", [])}
            negative_phrases = [phrase.casefold() for phrase in capsule.get("negative_phrases", [])]
            summary_short = str(capsule.get("summary_short", "")).casefold()
            for phrase in cue_phrases:
                if phrase and phrase in query_text:
                    score += 3
            for token in tokens:
                if token in cue_tokens:
                    score += 2
                elif token and token in summary_short:
                    score += 1
            for phrase in negative_phrases:
                if phrase and phrase in query_text:
                    score -= 2
        scores[skill_name] = max(score, 0)
    return scores


def _select_top_band(
    *,
    foundation: ProjectFoundationProfileSurface,
    bands_by_id: dict[str, dict[str, Any]],
    score_by_skill: dict[str, int],
) -> tuple[str | None, int]:
    foundation_set = set(foundation.skills)
    ranked_bands: list[tuple[int, str]] = []
    for band_id, band in bands_by_id.items():
        band_score = max(
            (score_by_skill.get(skill_name, 0) for skill_name in band.get("skills", []) if skill_name in foundation_set),
            default=0,
        )
        if band_score > 0:
            ranked_bands.append((band_score, band_id))
    if not ranked_bands:
        return None, 0
    ranked_bands.sort(key=lambda item: (-item[0], item[1]))
    score, band_id = ranked_bands[0]
    return band_id, score


def _risk_gate_items(
    *,
    mutation_surface: str,
    collision_by_skill: dict[str, str | None],
    layer_by_skill: dict[str, Literal["kernel", "outer-ring", "risk-ring"]],
    host_inventory: "_HostInventory",
) -> list[SkillDispatchItem]:
    required = ["aoa-approval-gate-check", "aoa-dry-run-first"]
    if mutation_surface == "runtime":
        required.append("aoa-local-stack-bringup")
    if mutation_surface in {"repo-config", "infra", "runtime"}:
        required.append("aoa-safe-infra-change")
    if mutation_surface == "public-share":
        required.append("aoa-sanitized-share")
    return [
        SkillDispatchItem(
            skill_name=skill_name,
            layer=layer_by_skill[skill_name],
            collision_family=collision_by_skill.get(skill_name),
            reason=f"required explicit risk gate for mutation_surface={mutation_surface}",
            host_availability=_host_availability_for_skill(
                skill_name,
                host_inventory=host_inventory,
                manual_fallback_allowed=True,
            ),
        )
        for skill_name in required
    ]


def _blocked_actions_for_mutation_surface(mutation_surface: str) -> list[str]:
    if mutation_surface == "none":
        return []
    blocked = ["mutation_without_explicit_risk_confirmation"]
    if mutation_surface == "runtime":
        blocked.append("runtime_change_without_local_stack_review")
    if mutation_surface in {"repo-config", "infra", "runtime"}:
        blocked.append("operational_change_without_safe_infra_review")
    if mutation_surface == "public-share":
        blocked.append("public_share_without_sanitization_review")
    return blocked


def _load_closeout_chain(
    workspace: Workspace,
    closeout_path: str | Path | None,
) -> KernelNextStepBrief | None:
    if closeout_path is None:
        return None
    resolved_path = Path(closeout_path).expanduser().resolve()
    payload = load_json(resolved_path)
    brief_payload = payload.get("kernel_next_step_brief")
    if brief_payload:
        return KernelNextStepBrief.model_validate(brief_payload)
    if payload.get("audit_only") is True:
        return None
    closeout = CloseoutAPI(workspace)
    manifest = closeout.load_manifest(resolved_path)
    if manifest.audit_only:
        return None
    return closeout._build_kernel_next_step_brief(manifest_path=resolved_path, manifest=manifest)


def _closeout_must_confirm(
    *,
    closeout_chain: KernelNextStepBrief | None,
    layer_by_skill: dict[str, Literal["kernel", "outer-ring", "risk-ring"]],
    collision_by_skill: dict[str, str | None],
    host_inventory: "_HostInventory",
) -> list[SkillDispatchItem]:
    if closeout_chain is None or closeout_chain.suggested_action != "invoke-core-skill":
        return []
    skill_name = closeout_chain.suggested_skill_name
    if skill_name is None or skill_name not in layer_by_skill:
        return []
    return [
        SkillDispatchItem(
            skill_name=skill_name,
            layer=layer_by_skill[skill_name],
            collision_family=collision_by_skill.get(skill_name),
            reason="existing kernel_next_step_brief suggests this as the next explicit post-session step",
            host_availability=_host_availability_for_skill(
                skill_name,
                host_inventory=host_inventory,
                manual_fallback_allowed=True,
            ),
        )
    ]


class _HostInventory:
    def __init__(
        self,
        *,
        available_skills: set[str] | None,
        source: Literal[
            "host-manifest",
            "host-skill-list",
            "repo-install",
            "workspace-install",
            "user-install",
            "not-provided",
        ],
        root: Path | None = None,
    ) -> None:
        self.available_skills = available_skills
        self.source = source
        self.root = root

    @property
    def is_provided(self) -> bool:
        return self.available_skills is not None


def _normalize_host_inventory(
    workspace: Workspace,
    *,
    resolved_repo_root: Path,
    host_available_skills: list[str] | None,
    host_availability_source: Literal[
        "host-manifest",
        "host-skill-list",
        "repo-install",
        "workspace-install",
        "user-install",
        "not-provided",
    ],
) -> _HostInventory:
    if host_available_skills is None:
        return _discover_host_inventory(workspace, resolved_repo_root=resolved_repo_root)
    return _HostInventory(
        available_skills={skill_name for skill_name in host_available_skills if skill_name},
        source="host-skill-list" if host_availability_source == "not-provided" else host_availability_source,
    )


def _host_inventory_reasoning(host_inventory: _HostInventory) -> list[str]:
    if not host_inventory.is_provided:
        return [
            "no explicit host skill inventory was supplied and no canonical install root with skills was found, so recommendation availability stayed unknown."
        ]
    if host_inventory.source in {"repo-install", "workspace-install", "user-install"} and host_inventory.root is not None:
        return [
            f"host skill inventory was auto-discovered from {host_inventory.source} at {host_inventory.root} ({len(host_inventory.available_skills or set())} skills)."
        ]
    return [f"host skill inventory was supplied via {host_inventory.source} ({len(host_inventory.available_skills or set())} skills)."]


def _host_availability_for_skill(
    skill_name: str,
    *,
    host_inventory: _HostInventory,
    manual_fallback_allowed: bool,
) -> SkillHostAvailability:
    if not host_inventory.is_provided:
        return SkillHostAvailability(
            status="unknown",
            source="not-provided",
            manual_fallback_allowed=False,
            reason="no host skill inventory was supplied",
        )
    if skill_name in (host_inventory.available_skills or set()):
        return SkillHostAvailability(
            status="host-executable",
            source=host_inventory.source,
            manual_fallback_allowed=False,
            reason=_inventory_reason_phrase(host_inventory, present=True),
        )
    return SkillHostAvailability(
        status="router-only",
        source=host_inventory.source,
        manual_fallback_allowed=manual_fallback_allowed,
        reason=_inventory_reason_phrase(host_inventory, present=False),
    )


def _discover_host_inventory(
    workspace: Workspace,
    *,
    resolved_repo_root: Path,
) -> _HostInventory:
    candidates: list[tuple[Path, Literal["repo-install", "workspace-install", "user-install"]]] = []
    repo_install_root = resolved_repo_root / ".agents" / "skills"
    if resolved_repo_root != workspace.federation_root:
        candidates.append((repo_install_root, "repo-install"))
    candidates.append((workspace.federation_root / ".agents" / "skills", "workspace-install"))
    candidates.append((Path.home() / ".agents" / "skills", "user-install"))

    seen: set[Path] = set()
    for root, source in candidates:
        resolved_root = root.expanduser().resolve(strict=False)
        if resolved_root in seen:
            continue
        seen.add(resolved_root)
        available_skills = _installed_skill_names(root)
        if available_skills:
            return _HostInventory(
                available_skills=available_skills,
                source=source,
                root=resolved_root,
            )
    return _HostInventory(available_skills=None, source="not-provided")


def _installed_skill_names(install_root: Path) -> set[str]:
    if not install_root.is_dir():
        return set()

    installed: set[str] = set()
    for child in install_root.iterdir():
        if child.name.startswith("."):
            continue
        if (child / "SKILL.md").is_file():
            installed.add(child.name)
    return installed


def _inventory_reason_phrase(host_inventory: _HostInventory, *, present: bool) -> str:
    if host_inventory.source in {"repo-install", "workspace-install", "user-install"}:
        target = "present in" if present else "not present in"
        if host_inventory.root is not None:
            return f"skill is {target} the auto-discovered {host_inventory.source} root at {host_inventory.root}"
        return f"skill is {target} the auto-discovered {host_inventory.source} root"
    target = "present in" if present else "not present in"
    return f"skill is {target} the supplied host inventory"


def _demote_non_executable_activate_now(
    activate_now: list[SkillDispatchItem],
    *,
    host_inventory: _HostInventory,
) -> tuple[list[SkillDispatchItem], list[SkillDispatchItem]]:
    if not host_inventory.is_provided:
        return activate_now, []
    kept: list[SkillDispatchItem] = []
    demoted: list[SkillDispatchItem] = []
    for item in activate_now:
        if item.host_availability.status == "host-executable":
            kept.append(item)
            continue
        demoted.append(
            item.model_copy(
                update={
                    "reason": f"{item.reason}; host inventory is router-only for this skill",
                    "host_availability": item.host_availability.model_copy(
                        update={"manual_fallback_allowed": True}
                    ),
                }
            )
        )
    return kept, demoted


def _actionability_gaps(
    *,
    activate_now: list[SkillDispatchItem],
    must_confirm: list[SkillDispatchItem],
    suggest_next: list[SkillDispatchItem],
) -> list[str]:
    gaps: list[str] = []
    for item in [*activate_now, *must_confirm, *suggest_next]:
        if item.host_availability.status == "router-only":
            gaps.append(item.skill_name)
    return list(dict.fromkeys(gaps))


def _explicit_handle(card: SkillCard) -> str | None:
    codex_handle = card.explicit_handles.get("codex", {})
    mention = codex_handle.get("mention")
    if isinstance(mention, str) and mention:
        return mention
    return None


def _dedupe_items(items: list[SkillDispatchItem]) -> list[SkillDispatchItem]:
    deduped: list[SkillDispatchItem] = []
    seen: set[str] = set()
    for item in items:
        if item.skill_name in seen:
            continue
        seen.add(item.skill_name)
        deduped.append(item)
    return deduped
