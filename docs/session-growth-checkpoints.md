# Session Growth Checkpoints

`aoa-sdk` owns the control-plane seam for checkpoint-aware session growth.
It keeps checkpoint capture local-first and reviewable without turning the
existing session-harvest family into an automatic runtime authority.

## Boundary

- `aoa surfaces detect --phase checkpoint` stays additive and read-only
- `aoa skills enter` and `aoa skills guard` stay skill-first; `enter` stays read-only unless `--checkpoint-kind` is explicit, while `guard` can auto-append one local checkpoint note only when checkpoint-phase surface detection finds a real growth signal
- explicit `commit`, `verify-green`, `pr_opened`, `pr_merged`, or `owner_followthrough` intents on a non-`none` mutation surface also count as local growth signals, even when recurring-route heuristics stay quiet
- use `--no-auto-checkpoint` to keep `aoa skills guard` read-only apart from the persisted skill report; `aoa skills enter` is already read-only unless an explicit `--checkpoint-kind` is present
- use `--checkpoint-kind` to override the inferred checkpoint kind when one explicit checkpoint event matters
- `aoa checkpoint mark` is the agent-facing way to record an explicit milestone, and `aoa checkpoint append` remains the lower-level append surface; both write only local note state under `.aoa/`
- plain `git commit` can trigger one active-session-only checkpoint pass through the installed `post-commit` hook and `aoa checkpoint after-commit`; when no active session file already exists, that path exits as `skipped_no_active_session` and does not mint a fresh session just to emit noise
- post-commit kind selection defaults to `auto`; ordinary commits resolve to `commit/code`, explicit `owner_followthrough`, owner-follow-through commit text, or closed-session follow-through resolves to `owner_followthrough/public-share`, and a closed note is never rotated or reopened by the hook
- use `AOA_CHECKPOINT_KIND=owner_followthrough git commit ...` when the commit is the final owner follow-through after reviewed closeout; if the note has already been closed or promoted, `auto` records a report-only follow-through artifact instead of mutating closed ledger state
- a captured post-commit checkpoint starts with `agent_review=pending`; the Codex agent must then apply the checkpoint skill protocol and run `aoa checkpoint review-note` to record real intermediate findings, candidate notes, stats hints, mechanic hints, closeout questions, and evidence refs in the note
- checkpoint capture does not emit `HARVEST_PACKET`
- checkpoint capture does not emit `CORE_SKILL_APPLICATION_RECEIPT`
- promotion remains explicit through `aoa checkpoint promote`
- post-commit checkpoint capture always stays mid-session and reviewable: it may dispatch checkpoint-phase skills, run additive checkpoint surface detection, and append a local reviewable note, but it never runs closeout, promotion, harvest, push, or release logic
- full harvest still belongs to the existing reviewed closeout path
- checkpoint notes carry harvest, progression, and upgrade candidates through the end of the session
- checkpoint notes may also carry provisional lineage hints rooted in
  `cluster_ref`; that carry may name owner hypothesis, owner shape, nearest
  wrong target, evidence refs, axis pressure, supersession metadata, and
  status posture, but it must not mint `candidate_ref`, `seed_ref`, or
  `object_ref`
- reviewed closeout may also carry one separate self-agency continuity hint
  surface rooted in
  `continuity_ref_hint -> revision_window_ref_hint -> anchor_artifact_ref`; it
  may name `reanchor_need` and `continuity_status_hint`, but it must not claim
  reviewed continuity truth or runtime self-agency authority
- checkpoint and reviewed closeout may also carry
  `component_drift_hint` and reviewed
  `component_refresh_followthrough_decision` packets rooted in `component_ref`;
  they may name owner repo, signals, route class, evidence refs, rollback
  anchor, and whether stats or memo follow-through is worth considering, but
  they must not auto-run owner refresh or stand in for owner receipts
- checkpoint notes keep provisional multi-axis movement for `boundary_integrity`, `execution_reliability`, `change_legibility`, `review_sharpness`, `proof_discipline`, `provenance_hygiene`, and `deep_readiness`
- candidate movement and stats refresh stay reviewed-closeout decisions, not
  mid-session auto-promotion; after reviewed closeout, surviving candidates
  should land promptly in tracked owner status surfaces with early, reanchor, or
  thin-evidence posture instead of remaining only in runtime-local `.aoa`
  state

## Local storage

Checkpoint state lives under:

```text
aoa-sdk/.aoa/session-growth/current/<runtime-session-id>/<repo-label>/
  checkpoint-note.jsonl
  checkpoint-note.json
  checkpoint-note.md
  post-commit-report.json
  harvest-handoff.json
  closeout-context.json
  closeout-execution-report.json
```

When no runtime session is available yet, the legacy unscoped fallback remains
`current/<repo-label>/`.
With an active runtime session, `current/<runtime-session-id>/<repo-label>/` is
the live ledger for that repo scope inside one specific session, not a date
bucket.
The unscoped fallback stays only as a migration bridge for a note that has no
`runtime_session_id` yet, or for one that already matches the active runtime
session. If an unscoped ledger explicitly points at a different
`runtime_session_id`, stateful checkpoint flows archive it under
`aoa-sdk/.aoa/session-growth/archive/` so `current/` stops advertising a stale
session as live.
The checkpoint `session_ref` is minted uniquely when a new ledger starts and
now includes a high-resolution timestamp plus the current runtime-session
identity suffix when available, so many same-day sessions do not collapse into
one daily label.
When a note already ended as `closed` or `promoted`, that runtime-scoped
`current` ledger is archived under `aoa-sdk/.aoa/session-growth/archive/`
before the next cycle begins.
When `CODEX_THREAD_ID` is present, the default runtime session store now lives
under `aoa-sdk/.aoa/skill-runtime-sessions/<codex-thread>.json`, so parallel
Codex threads no longer mutate the same singleton session file.
If you use a non-default runtime session file, pass the same `--session-file`
to `aoa checkpoint status`, `aoa checkpoint promote`,
`aoa checkpoint build-closeout-context`, and
`aoa checkpoint execute-closeout-chain` so those commands resolve the same
active checkpoint session.
At reviewed closeout, the builder aggregates every checkpoint ledger under the
same active runtime-session scope before it derives the closeout candidate map.
During that aggregation, stale unscoped ledgers from a different runtime
session are archived out of `current/` instead of lingering beside the live
scope.
The repo-root checkpoint note must still agree with the resolved reviewed
session for the closeout to proceed. This keeps one narrow repo-scoped note
from silently standing in for the whole session and blocks cross-session
mismatch when parallel work is in flight.

The JSONL file is append-only checkpoint history.
The JSON and Markdown files are rebuilt snapshots for current review.
`post-commit-report.json` is the trigger/audit artifact for one plain-commit
capture pass; it is not the authoritative checkpoint ledger.
It records whether the agent-authored review is still `pending` or already
`reviewed`.
When capture skips because no active session file exists, or fails before a
runtime-scoped note is available, the latest fallback status artifact is
written under `aoa-sdk/.aoa/session-growth/post-commit-status/<repo>.latest.json`.
Those rebuilt snapshots now act as the session-local ledger for:

- harvest candidates that should be bundled at reviewed closeout
- progression candidates and provisional axis movement that should feed `aoa-session-progression-lift` only at reviewed closeout
- upgrade candidates that should be reviewed once at closeout before any owner-layer promotion
- the final stats-refresh hint that belongs to the same reviewed closeout moment
- agent-authored intermediate review notes for each commit checkpoint, including what changed, why it matters, where it belongs, and which questions the final closeout must reread against the full session

Machine-facing timestamps stay canonical in UTC with the usual `Z` suffix.
For human review the same checkpoint and explicit closeout surfaces now also
publish local companion fields such as `observed_at_local`, `captured_at_local`,
`built_at_local`, `executed_at_local`, and matching `*_tz` labels so local
operators do not need to mentally convert reviewed session times.

`aoa skills enter` and `aoa skills guard` also surface that ledger directly in
their runtime JSON under `checkpoint_capture.session_end_skill_targets`,
`checkpoint_capture.progression_axis_signals`,
`checkpoint_capture.session_end_next_honest_move`, and
`checkpoint_capture.stats_refresh_recommended`.
At reviewed closeout the explicit bridge skill is
`aoa-checkpoint-closeout-bridge`: it builds `closeout-context.json`, rereads
the reviewed artifact, and then executes donor harvest, progression lift, and
quest harvest in order without refreshing stats inside the bridge itself.
That runtime-session fan-in narrows attention honestly, but it still does not
replace rereading the reviewed artifact itself.
The SDK bridge is a mechanical artifact builder, not proof that an agent has
applied those skills. Its context and execution reports publish
`execution_mode`, `mechanical_bridge_only`, `agent_skill_application_required`,
and the authority contract
`reviewed_artifact_primary_checkpoint_hints_provisional`; the Codex agent must
still use the skill as a protocol, reread the session evidence, and separate
checkpoint hints from final candidates before treating the closeout as a
session analysis.
`docs/CANDIDATE_LINEAGE_CARRY.md` is the canonical note for what the SDK may
and may not carry on that lineage seam.
`docs/COMPONENT_DRIFT_HINTS.md` is the companion note for control-plane
component drift hints and reviewed refresh decisions that stay weaker than
owner refresh law and owner receipts.
`docs/SELF_AGENCY_CONTINUITY_CARRY.md` is the companion note for the narrower
self-agency continuity hint seam that may survive reviewed closeout without
becoming self-agent truth.
When the active runtime session also carries a live Codex rollout path,
closeout now binds that rollout trace into the context and rereads it beside
the reviewed artifact so one narrow checkpoint ledger does not stand in for the
whole runtime thread.
That reviewed closeout context may now also carry one deterministic
`followthrough_decision` naming the next honest kernel class after the reread.
It stays reviewed-only and advisory, and it does not auto-run kernel skills
from the SDK.
When the reread is instead about a drifting owner-owned component,
`docs/COMPONENT_DRIFT_HINTS.md` defines the companion hint and reviewed
decision packets.

## Commands

```bash
aoa skills detect /srv/aoa-sdk --phase checkpoint --intent-text "plan verify a bounded change" --root /srv/aoa-sdk --json
aoa skills enter /srv/aoa-sdk --intent-text "recurring workflow needs better handoff proof and recall" --root /srv/aoa-sdk --json
aoa skills guard /srv/aoa-sdk --intent-text "recurring workflow needs better handoff proof and recall" --mutation-surface code --root /srv/aoa-sdk --json
aoa skills guard /srv/aoa-sdk --intent-text "commit bounded patch" --mutation-surface code --root /srv/aoa-sdk --json
aoa skills guard /srv/aoa-sdk --intent-text "refresh generated contracts" --mutation-surface code --no-auto-checkpoint --root /srv/aoa-sdk --json
aoa surfaces detect /srv/aoa-sdk --phase checkpoint --checkpoint-kind commit --intent-text "recurring owner follow-through after green verify" --root /srv/aoa-sdk --json
aoa surfaces detect /srv/aoa-sdk --phase checkpoint --checkpoint-kind commit --append-note --intent-text "recurring owner follow-through after green verify" --root /srv/aoa-sdk --json
aoa skills guard /srv/aoa-sdk --intent-text "recurring owner follow-through after green verify" --mutation-surface code --checkpoint-kind verify_green --root /srv/aoa-sdk --json
aoa checkpoint mark /srv/aoa-sdk --kind pr_opened --intent-text "opened PR after protected main rejected direct push" --mutation-surface public-share --root /srv/aoa-sdk --json
aoa checkpoint append /srv/aoa-sdk --kind commit --intent-text "recurring owner follow-through after green verify" --root /srv/aoa-sdk --json
aoa checkpoint after-commit /srv/aoa-sdk --commit-ref HEAD --root /srv --json
aoa checkpoint after-commit /srv/aoa-sdk --commit-ref HEAD --kind owner_followthrough --root /srv --json
aoa checkpoint review-note /srv/aoa-sdk --commit-ref HEAD --summary "agent-reviewed checkpoint notes for this commit" --finding "what changed and why it matters" --candidate-note "candidate, owner, and where it should be revisited" --stats-hint "stats to refresh only after reviewed closeout" --mechanic-hint "workflow mechanism to retain" --closeout-question "what to verify when rereading the full session" --applied-skill aoa-change-protocol --root /srv --json
aoa checkpoint install-hook --repo aoa-sdk --root /srv --json
aoa checkpoint hook-status --repo aoa-sdk --root /srv --json
aoa checkpoint build-closeout-context /srv/aoa-sdk --reviewed-artifact /srv/path/to/reviewed_session_artifact.md --root /srv/aoa-sdk --json
aoa checkpoint execute-closeout-chain /srv/aoa-sdk --reviewed-artifact /srv/path/to/reviewed_session_artifact.md --root /srv/aoa-sdk --json
aoa checkpoint status /srv/aoa-sdk --root /srv/aoa-sdk --json
```

## Promotion read

`aoa checkpoint promote --target dionysus-note` writes one lightweight
reviewed snapshot into `Dionysus`.

`aoa checkpoint promote --target harvest-handoff` writes one local reviewed
handoff that can feed the explicit session-harvest family later.

Checkpoint notes stay below harvest verdict authority. They exist to preserve
good mid-session candidates until reviewed promotion is honest.
They should be carried through the session and only moved, harvested, or paired
with stats refresh from the final reviewed closeout path.
Once that reviewed closeout path has run, owner follow-through should not leave
surviving candidates only in `harvest-handoff.json`. If the relevant owner repo
has a tracked status surface, land the candidate there with its early status,
provenance, and blockers preserved, and keep final promotion authority separate
from that early landing.
When progression evidence exists, reviewed closeout should raise
`aoa-session-progression-lift` before `aoa-quest-harvest`, so the final
multi-axis verdict is gathered once from the carried checkpoint evidence instead
of being guessed mid-session.
That reviewed closeout path should be driven through
`aoa-checkpoint-closeout-bridge`, not by silently widening `aoa closeout run`.
