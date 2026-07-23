# Admit the Titan Helper Skill Family

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0070
- Original date: 2026-07-23
- Surface classes: owner skill home, user exposure, compatibility, validation
- SDK facets: control-plane, Titan helpers, operator-visible witnesses
- Mechanic parents: titan
- Guard families: operator approval, runtime boundary, memory retention, manual admission
- Posture: accepted

## Context

The retired flat catalog exposed fifteen Titan-named skills, but those names
mixed SDK helper procedures with runtime execution, operator authority, memory
ownership, and playbook sequencing. Restoring all names mechanically would
advertise capabilities that the SDK does not own. Collapsing the family to a
few empty aliases would lose the useful console, approval, bridge, replay,
receipt, recall, and retention procedures.

Manual fresh-agent trials also showed that the existing helpers were not safe
enough to wrap unchanged. New console and bridge records labelled declared
roster members as active, omitted explicit witness and transport semantics,
accepted ambiguous local actor attribution, supplied a generic app-server
prompt and model by default, conflated queue inspection with queue decisions,
and failed to preserve external decision references in the written approval
records. Those defects were found through task execution before their
structural assertions were retained in existing tests and schemas.

## Decision

Admit three owner-authored bundles under `skills/`:

- `titan-console` owns console, gate-approval witness, app-server approval
  queue, unsent plan, and receipt modes;
- `titan-appserver-bridge` owns visible bridge and replay modes;
- `titan-memory-loom` owns candidate ingest, bounded recall, and effect-free
  retention-handoff modes.

Each bundle uses one compact prompt-visible front door and conditionally loads
only the selected procedure. All helper artifacts remain witness-only or
candidate-only. They do not authenticate an operator, launch a Titan or agent,
send app-server traffic, enforce a runtime gate, prove an outcome, or accept
durable memory.

Expose the owner packages once through the v2 `os-user-default` skill profile.
Do not create same-name `.agents/skills` copies. Keep the semantic tree and
typed relations derived from the owner contracts, and keep any multi-skill
execution graph task-local.

Titan summon execution remains with `aoa-agents`. Titan closeout remains a
playbook route and does not become a skill before `aoa-playbooks-mcp` exists.
Mutation enforcement, runtime gating, and thread-turn binding remain
unavailable bindings rather than fictional SDK skills.

## Manual Evidence Summary

- Fresh agents selected the console, plan, receipt, bridge/replay, ingest,
  recall, and retention modes for their distinct tasks and returned their
  complete typed output contracts.
- A receipt-to-ingest-to-recall task composed `titan-console` and
  `titan-memory-loom` as a small task-local DAG while preserving candidate-only
  memory meaning.
- Queue-only requests selected `titan-console` without co-activating the
  neighboring bridge bundle after the applicability boundary was corrected.
- Read-only queue inspection worked without an external decision reference;
  decision writes remained blocked without one.
- Positive console, queue, receipt-ledger, and bridge-ledger decision trials
  preserved the exact external decision reference and explicitly
  unauthenticated attribution in the witness artifact itself.
- A bridge-to-approval task composed `titan-appserver-bridge` and
  `titan-console` as a task-local DAG. The trial exposed source-provenance loss
  across the bridge helper read-write cycle; the owner helper was then changed
  to require and preserve the exact source kind and ref without a manual patch.
- Receipt and bridge gate helpers now reject missing decision provenance.
  Receipt Forge and Delta payloads must also be explicit rather than
  helper-invented placeholders.
- Retention preparation left the candidate index unchanged and did not call a
  redact helper or implicitly submit to `aoa-memo`.
- All exercised app-server plans, bridge records, and console records retained
  `not_run`, `not_sent`, and witness-only semantics.

These cases establish bounded usefulness and corrected failure behavior. They
do not establish universal model, host, routing, latency, token, runtime, or
operator-authority superiority.

## Options Considered

- Restore fifteen global names: rejected because several names have no SDK
  execution binding and would increase routing interference.
- Remove the whole Titan family: rejected because ten legacy procedures map to
  useful SDK-owned helper behavior.
- Publish every internal mode as a separate skill: rejected because the modes
  share owners, contracts, stop-lines, and tools and have not shown independent
  composition value.
- Admit three focused owner bundles: chosen because it preserves the exercised
  procedures without pretending that helper state is runtime truth.

## Consequences

- Ten legacy helper procedures remain reachable through three focused bundles.
- Five legacy names receive explicit dispositions instead of nominal
  compatibility: summon routes to `aoa-agents`, closeout waits for its MCP-backed
  playbook route, and three runtime guards remain unavailable.
- Approval provenance is now replayable from the artifact rather than existing
  only in an agent response.
- The OS-profile catalog still needs system-level budget and coexistence work;
  owner admission alone does not prove final global installation.
- No trial transcript, prompt, task-local DAG, new validator, or new test file
  is retained in the owner repository.

## Source Surfaces

- `skills/README.md`
- `skills/port.manifest.json`
- `skills/titan-console/`
- `skills/titan-appserver-bridge/`
- `skills/titan-memory-loom/`
- `mechanics/titan/parts/operator-console-helper-contracts/`
- `mechanics/titan/parts/appserver-bridge-helper-contracts/`
- `mechanics/titan/parts/incarnation-identity-runtime-helper-contracts/`

## Follow-Up Route

Route summon execution to `aoa-agents`, durable retention decisions to
`aoa-memo`, playbook sequencing to the future MCP-backed playbook owner, and
global selection, coexistence, and catalog budget to the `aoa-skills`
OS-profile assembly.

## Verification

Manual isolated, negative, coexistence, provenance, retention, and task-local
DAG trials are the admission authority. Use the generic skill package checker,
shared owner-home port validator, existing Titan helper tests and schemas,
decision-index parity, mechanics topology, and repository release gates only
as structural follow-up.
