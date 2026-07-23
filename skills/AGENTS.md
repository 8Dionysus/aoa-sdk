# AGENTS.md

## Applies To

This card applies to the canonical `aoa-sdk/skills/` owner home.

## Role

This home owns callable procedures over SDK-owned Titan helper contracts. It
does not turn helper state into Titan runtime, operator, role, memory, proof,
or playbook authority.

## Read Before Editing

Read root `AGENTS.md`, `skills/README.md`, `skills/port.manifest.json` when it
exists, the selected bundle and admission decision, then only the Titan helper
owners named by that bundle.

## Boundaries

- Keep the three manually justified Titan front doors bundled by trigger,
  contract, and composition: console, app-server bridge, and memory loom.
- Do not create skills for unavailable mutation, runtime-transition, or
  thread-turn enforcement.
- Do not create `titan-closeout` until `aoa-playbooks` has an executable MCP
  owner.
- Keep summon in `aoa-agents` and durable retention decisions in `aoa-memo`.
- Treat console, receipt, approval, bridge, replay, and memory helper outputs
  as witnesses or candidates. They cannot authenticate operator intent or
  prove runtime execution.
- Do not add technique runtime dependencies, raw trials, task-local DAGs,
  temporary rubrics, session traces, runtime state, or generated owner facts.
- Global exposure comes from the single OS user profile. Do not add a duplicate
  `.agents/skills` projection for globally installed bundles.

## Validation

Manual isolated, negative, baseline, coexistence, binding-failure, and
bounded-effect trials decide usefulness. `skill-creator` quick validation and
the `aoa-skills` home-port check prove package shape only. Existing Titan
helper tests prove helper behavior only.

## Closeout

Report manual cases, selected modes, owner contracts, actual effects, blocked
runtime claims, global-profile status, checks, and removed session-only
material.
