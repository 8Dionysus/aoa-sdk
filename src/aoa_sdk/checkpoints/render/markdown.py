"""Markdown renderers for checkpoint notes."""

from __future__ import annotations

from ...models import SessionCheckpointNote
from ..timestamps import with_local_timestamp_default


def render_checkpoint_note_markdown(note: SessionCheckpointNote, *, repo_label: str) -> str:
    lines = [
        "# Session Checkpoint Note",
        "",
        f"Session ref: `{note.session_ref}`",
        *([f"Runtime session id: `{note.runtime_session_id}`"] if note.runtime_session_id else []),
        f"Repo label: `{repo_label}`",
        f"State: `{note.state}`",
        f"Review status: `{note.review_status}`",
        f"Promotion recommendation: `{note.promotion_recommendation}`",
        f"Carry until session closeout: `{'yes' if note.carry_until_session_closeout else 'no'}`",
        f"Session-end recommendation: `{note.session_end_recommendation}`",
        f"Stats refresh recommended at closeout: `{'yes' if note.stats_refresh_recommended else 'no'}`",
        f"Agent checkpoint review: `{note.agent_review_status}`",
        "",
        "## Repo Scope",
        "",
    ]
    lines.extend(f"- `{scope}`" for scope in note.repo_scope)
    if note.harvest_candidate_ids:
        lines.extend(["", "## Harvest Candidates", ""])
        lines.extend(f"- `{candidate_id}`" for candidate_id in note.harvest_candidate_ids)
    if note.progression_candidate_ids:
        lines.extend(["", "## Progression Candidates", ""])
        lines.extend(f"- `{candidate_id}`" for candidate_id in note.progression_candidate_ids)
    if note.progression_axis_signals:
        lines.extend(["", "## Provisional Progression Axes", ""])
        for signal in note.progression_axis_signals:
            lines.append(
                f"- `{signal.axis}` -> `{signal.movement}`"
                + (
                    f" from {', '.join(f'`{candidate_id}`' for candidate_id in signal.candidate_ids)}"
                    if signal.candidate_ids
                    else ""
                )
            )
            lines.append(f"  - {signal.why}")
    if note.upgrade_candidate_ids:
        lines.extend(["", "## Upgrade Candidates", ""])
        lines.extend(f"- `{candidate_id}`" for candidate_id in note.upgrade_candidate_ids)
    if note.agent_reviews:
        lines.extend(["", "## Semantic Review Carry", ""])
        lines.extend(
            [
                f"- review refs: {', '.join(f'`{ref}`' for ref in note.review_refs) or '`none`'}",
                "- auto observation refs: "
                + (", ".join(f"`{ref}`" for ref in note.auto_observation_refs) or "`none`"),
                "- related capability refs: "
                + (
                    ", ".join(f"`{ref}`" for ref in note.related_capability_refs)
                    or "`none`"
                ),
            ]
        )
        for label, values in (
            ("summaries", note.summaries),
            ("findings", note.findings),
            ("candidate notes", note.candidate_notes),
            ("stats hints", note.stats_hints),
            ("mechanic hints", note.mechanic_hints),
            ("closeout questions", note.closeout_questions),
        ):
            if values:
                lines.append(f"- {label}:")
                lines.extend(f"  - {value}" for value in values)
        lines.extend(["", "## Agent Checkpoint Reviews", ""])
        for review in note.agent_reviews:
            lines.extend(
                [
                    f"### {review.commit_short_sha or review.commit_ref}",
                    "",
                    f"- review id: `{review.review_id}`",
                    f"- auto observation ref: `{review.auto_observation_ref or 'none'}`",
                    f"- summary: {review.summary}",
                    "- related capability refs: "
                    + (
                        ", ".join(f"`{ref}`" for ref in review.related_capability_refs)
                        or "`none`"
                    ),
                    f"- defer until closeout: `{'yes' if review.defer_until_closeout else 'no'}`",
                ]
            )
            for label, values in (
                ("findings", review.findings),
                ("candidate notes", review.candidate_notes),
                ("stats hints", review.stats_hints),
                ("mechanic hints", review.mechanic_hints),
                ("closeout questions", review.closeout_questions),
            ):
                if values:
                    lines.append(f"- {label}:")
                    lines.extend(f"  - {value}" for value in values)
            if review.evidence_refs:
                lines.append("- evidence refs:")
                lines.extend(f"  - `{ref}`" for ref in review.evidence_refs)
            lines.append("")
    lines.extend(["", "## Candidate Intelligence", ""])
    lines.append(
        "Generated route evidence only; not reviewed memory, proof, owner verdict, "
        "accepted wrapper, automation, or promotion."
    )
    if note.action_signatures:
        lines.append("- action signatures:")
        lines.extend(
            f"  - `{signature.signature_id}` -> `{signature.wrapper_family_hint}` "
            f"({signature.confidence})"
            for signature in note.action_signatures
        )
    else:
        lines.append("- action signatures: `none`")
    if note.repetition_clusters:
        lines.append("- repetition clusters:")
        lines.extend(
            f"  - `{cluster.cluster_id}` repeat `{cluster.repeat_count}`; "
            f"draftability `{cluster.wrapper_readiness.draftability}`; "
            f"fit `{cluster.existing_wrapper_fit.fit_status}`"
            for cluster in note.repetition_clusters
        )
    else:
        lines.append("- repetition clusters: `none`")
    if note.wrapper_gap_candidates:
        lines.append("- wrapper gaps:")
        lines.extend(
            f"  - `{gap.candidate_id}` -> `{gap.proposed_wrapper_family}` "
            f"({gap.draftability})"
            for gap in note.wrapper_gap_candidates
        )
    else:
        lines.append("- wrapper gaps: `none`")
    lines.extend(["", "## Candidate Clusters", ""])
    if not note.candidate_clusters:
        lines.append("- none")
    for cluster in note.candidate_clusters:
        lines.extend(
            [
                f"### {cluster.display_name}",
                "",
                f"- candidate id: `{cluster.candidate_id}`",
                f"- kind: `{cluster.candidate_kind}`",
                f"- owner hint: `{cluster.owner_hint}`",
                f"- checkpoint hits: `{cluster.checkpoint_hits}`",
                f"- confidence: `{cluster.confidence}`",
                f"- review status: `{cluster.review_status}`",
                f"- source surface: `{cluster.source_surface_ref}`",
                f"- session-end targets: {', '.join(f'`{target}`' for target in cluster.session_end_targets) or '`none`'}",
            ]
        )
        if cluster.progression_axis_signals:
            lines.append("- provisional progression axes:")
            lines.extend(
                f"  - `{signal.axis}` -> `{signal.movement}`: {signal.why}"
                for signal in cluster.progression_axis_signals
            )
        if cluster.blocked_by:
            lines.append("- blocked by: " + ", ".join(f"`{item}`" for item in cluster.blocked_by))
        if cluster.defer_reason:
            lines.append(f"- defer reason: {cluster.defer_reason}")
        if cluster.evidence_refs:
            lines.append("- evidence refs:")
            lines.extend(f"  - `{ref}`" for ref in cluster.evidence_refs)
        if cluster.promote_if:
            lines.append("- promote if:")
            lines.extend(f"  - {item}" for item in cluster.promote_if)
        if cluster.next_owner_moves:
            lines.append("- next owner moves:")
            lines.extend(f"  - {item}" for item in cluster.next_owner_moves)
        lines.append("")
    lines.extend(["## Checkpoint History", ""])
    for entry in note.checkpoint_history:
        observed_at = entry.observed_at.isoformat().replace("+00:00", "Z")
        observed_at_local, observed_tz = with_local_timestamp_default(
            utc_value=entry.observed_at,
            local_value=entry.observed_at_local,
            tz_name=entry.observed_tz,
        )
        if observed_at_local:
            observed_at += f" (local {observed_at_local}"
            if observed_tz:
                observed_at += f" {observed_tz}"
            observed_at += ")"
        lines.append(
            f"- `{entry.checkpoint_kind}` at `{observed_at}` -> "
            + (", ".join(cluster.candidate_id for cluster in entry.candidate_clusters) or "no surviving candidates")
        )
        if entry.agent_review_status != "not_required":
            lines.append(f"  - agent review: `{entry.agent_review_status}`")
        if entry.auto_observation is not None:
            lines.append(f"  - auto observation: {entry.auto_observation.summary}")
            if entry.auto_observation.related_capability_refs:
                lines.append(
                    "  - related capability refs: "
                    + ", ".join(
                        f"`{ref}`" for ref in entry.auto_observation.related_capability_refs
                    )
                )
            for label, values in (
                ("auto findings", entry.auto_observation.findings),
                ("auto candidate notes", entry.auto_observation.candidate_notes),
                ("auto stats hints", entry.auto_observation.stats_hints),
                ("auto mechanic hints", entry.auto_observation.mechanic_hints),
                ("auto closeout questions", entry.auto_observation.closeout_questions),
            ):
                if values:
                    lines.append(f"  - {label}:")
                    lines.extend(f"    - {value}" for value in values)
    if note.blocked_by:
        lines.extend(["", "## Blocked By", ""])
        lines.extend(f"- `{item}`" for item in note.blocked_by)
    if note.next_owner_moves:
        lines.extend(["", "## Next Owner Moves", ""])
        lines.extend(f"- {item}" for item in note.next_owner_moves)
    return "\n".join(lines).rstrip() + "\n"
