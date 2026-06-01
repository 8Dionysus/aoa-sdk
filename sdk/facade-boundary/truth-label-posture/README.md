# Truth Label Posture

Role: route the SDK vocabulary for source, generated, candidate, manual,
reviewed, activated, and advisory truth labels.

Input: label fields, model aliases, route prose, checkpoint and closeout label
changes, and owner-acceptance wording.

Output: model implementation route, boundary doc update, mechanic route,
decision record, or stronger-owner handoff.

Owner: `sdk/facade-boundary/AGENTS.md` and
`sdk/source_home.manifest.json#truth_label_posture`.

Next route: `src/aoa_sdk/models.py`, `docs/boundaries.md`,
`mechanics/boundary-bridge/parts/owner-layer-signal-handoff/`, and
`mechanics/checkpoint/parts/reviewed-closeout-context-carry/`.

Stop line: do not let labels imply owner acceptance without owner proof.
