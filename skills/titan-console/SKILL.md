---
name: titan-console
description: Titan approval queue or record, console witness, unsent app-server plan, or receipt; aoa-sdk witnesses only.
---

# titan-console

Preserve the useful console, approval, plan, and receipt procedures behind one
high-signal Titan front door. Every helper artifact is a local witness; no
helper authenticates operator intent or performs runtime work.

## Owner-source return

Resolve the canonical `aoa-sdk` root before reading or running owner helpers:

1. Record `<bundle_dir>` as the directory containing this loaded `SKILL.md`.
2. In one tool turn, inspect only
   `<bundle_dir>/.aoa-skill-source.json`. If it exists, require
   `aoa_skill_source_receipt_v1`, bundle `titan-console`, owner `aoa-sdk`, an
   existing absolute `owner_root`, safe relative `source_path`, and a matching
   `<owner_root>/<source_path>/SKILL.md`. An invalid present handle is terminal.
3. Only when the handle is absent, run exactly
   `git -C <bundle_dir> rev-parse --show-toplevel` and use that result as
   `<owner_root>`.
4. In a later tool turn, read only
   `<owner_root>/skills/port.manifest.json`. Require owner `aoa-sdk`, this
   bundle name, and path `skills/titan-console`.
5. Stop with `blocked_missing_owner_source` on any mismatch. Do not scan for a
   substitute checkout.

Report the source route and provenance. Installation metadata does not prove
owner parity or helper execution.

## Select exactly one mode

Read `references/contract.yaml` to EOF, then load only the selected mode:

| Mode | Select when | Read |
|---|---|---|
| `console` | Create, inspect, update, digest, close, or validate visible console state. | `references/console.md` |
| `approval-witness` | An explicit external operator decision must be recorded against one Forge or Delta gate in a console, receipt, or bridge witness. | `references/approval-witness.md` |
| `approval-queue` | Inspect one app-server approval request, or record an exact externally supplied decision. | `references/approval-queue.md` |
| `plan` | Prepare a Titan app-server plan without starting or emitting anything. | `references/plan.md` |
| `receipt` | Create, validate, annotate, or close one Titan receipt witness. | `references/receipt.md` |

Do not preload neighboring modes. If the request spans modes, build a
task-local DAG and load each mode only when its inputs are ready.

## Common contract

- Require explicit Titan intent, bounded paths, named lane, and source refs.
- Keep Forge mutation and Delta judgment distinct.
- Never infer approval from helper defaults, queue state, silence, or a
  plausible plan.
- Never claim that `titanctl summon` launched a child, that an app-server plan
  was sent, or that a console gate enforces runtime.
- Validate every written helper artifact with its owning helper.
- Return `titan-console-result-v1`: selected mode, source return, inputs,
  helper actions, witness artifacts, gate state, execution state, actual
  effects, verification, next owner route, and stop line.
- Before the final response, materialize every required
  `output_abi.required` key from `references/contract.yaml`. A shortened
  summary must not be labelled `titan-console-result-v1`.

## Stop

Stop after one verified witness result, an unsent plan, a truthful no-change,
an owner handoff, or an explicit blocker. Operator consent, runtime activation,
agent execution, proof, and durable memory remain outside this skill.
