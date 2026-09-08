# Portable Workspace Bootstrap Contract

## Guarantees

- An explicit portable profile continues through the SDK copy planner. It
  loads one exact owner-authored profile through compatibility rules, copies
  user-scoped entries into the explicit or host-selected user root, verifies
  full tree parity after `--execute`, and reports conflicts unless
  `--overwrite` is explicit.
- The default `os-user-default` path invokes
  `aoa-skills/scripts/install_os_skill_profile.py` with `--format json` and
  transports its plan or receipt as an opaque `owner_payload`. The SDK does
  not rebuild the owner's profile, resolve owner links, or infer skill
  readiness/admission from the payload.
- The OS adapter supplies discovered owner roots as explicit
  `--source-root OWNER=PATH` arguments. Callers may add repeatable overrides
  and an explicit `--os-root` for a disposable or clean checkout trial.
- The OS adapter uses the owner's read-only plan by default. `--check` is an
  explicit installed-state verification; `--execute` is an explicit owner
  mutation. A valid preview is not reported as verified, and missing,
  malformed, or non-object owner JSON leaves execution/verification unknown.
- Owner subprocesses run with `shell=False`, bounded capture diagnostics, and
  Python `-B`; no `--owner-repo` or owner-link operation is synthesized.
- Repository-scoped portable profiles are rejected without planning or
  applying repository projection steps.
- Workspace `AGENTS.md`, workspace-wide skill projections, repository homes,
  and legacy copies remain untouched by the SDK adapter.

## Non-Goals

- It does not create source-owned sibling repo content.
- It does not infer or build a repository skill home.
- It does not make workspace bootstrap a host deployment system.
- It does not make copied skill files stronger than the owning skill repo.
- It does not claim a successful owner transport proves prompt visibility,
  routing, runtime health, selection, execution, or use in a live session.
