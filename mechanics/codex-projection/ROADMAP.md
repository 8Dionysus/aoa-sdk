# Codex Projection Roadmap

Codex Projection is the SDK route for projecting bounded workspace context into
Codex-facing surfaces. It helps agents inspect the workspace, rollout posture,
and portability boundary without making projections session memory, GitHub
truth, or owner acceptance.

## Current Contour

- Keep workspace MCP, live rollout status readouts, portability boundaries, and
  owner rollout reference handoff routed through active `parts/`.
- Keep rollout readouts lower authority than raw session archives, GitHub
  state, and owner repositories.
- Keep portability boundaries explicit about what can travel and what remains
  local runtime context.
- Keep owner rollout references as handoff routes, not proof that owner work
  landed.

## Next Work

- Tighten projection packets where repeated Codex-facing reads prove a stable
  input, output, owner, and validation route.
- Keep local-first contracts stronger than remote or richer MCP behavior.
- Keep projection helpers visibly derived from source surfaces and generated
  builders.

## When Time Comes

- Add a new projection part when a Codex-facing read need cannot stay inside
  MCP, status, portability, or handoff parts.
- Add richer MCP behavior only after local-first contracts, authorization
  boundaries, and fallback posture remain stable.
- Add remote projection support only when owner evidence can still be inspected
  without trusting the projection as truth.

## Out Of Scope

- Session-memory authority.
- GitHub merge or CI truth.
- Owner rollout acceptance.
- Hidden Codex activation.
- Remote runtime control.
