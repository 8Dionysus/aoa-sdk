# aoa-sdk blueprint

## 1. Charter

`aoa-sdk` is the typed Python consumer and orchestration spine for the AoA federation.

It **loads source-owned generated surfaces** from sibling AoA repositories and exposes stable Python APIs for:

- routing
- skill discovery and activation
- session compaction
- role/phase handoff
- playbook activation
- memo recall
- eval hookup
- bounded orchestration

It does **not** become:
- a new owner of AoA meaning
- a replacement for `aoa-routing`
- a content store for skills/evals/memo
- a runtime service platform
- a hidden monolith swallowing adjacent repos

North star:

> *control plane, not content plane*  
> *typed nerve system, not new brain*

---

## 2. Why a separate repo

A separate repo keeps the ownership boundaries clean:

- `aoa-routing` stays the thin navigation layer
- `aoa-skills` stays the execution canon
- `aoa-agents` stays the role-contract and handoff canon
- `aoa-playbooks` stays the scenario/composition canon
- `aoa-memo` stays the memory and recall canon
- `aoa-evals` stays the proof canon
- `Dionysus` stays the seed garden, not the runtime home

So `aoa-sdk` becomes a **consumer/orchestrator** of published surfaces rather than a new claimant to meaning.

---

## 3. Design laws

1. **Generated-first**
   Read `generated/*.json` surfaces first.
   Fall back to authored markdown only for bounded expansion or debugging.

2. **Source repos own meaning**
   The SDK owns loading, typing, execution glue, and orchestration.
   It does not reinterpret neighboring layers into a new authority.

3. **Artifacts over fog**
   Every meaningful step returns a typed artifact:
   - route decision
   - bounded plan
   - work result
   - verification result
   - transition decision
   - deep synthesis note
   - distillation pack
   - skill activation packet
   - session compaction packet

4. **Local-first**
   The first version should work from local filesystem clones and local generated surfaces.

5. **Policy-aware**
   Trust posture, invocation mode, mutation surface, and approval boundaries are first-class.

6. **Adapters, not lock-in**
   Keep transport and environment concerns behind adapters:
   local FS now, MCP/A2A later.

---

## 4. Proposed names

Repo:
- `aoa-sdk`  ← recommended
- `abyss-agent-sdk`
- `aoa-python`

Python package:
- `aoa_sdk`

CLI:
- `aoa`

Recommendation:
- repo = `aoa-sdk`
- package = `aoa_sdk`
- CLI = `aoa`

---

## 5. Top-level architecture

```text
AoA source repos
  ├─ aoa-routing        -> routing ABI, task/surface hints
  ├─ aoa-skills         -> runtime discovery, disclosure, activation, session
  ├─ aoa-agents         -> phase bindings, role/tier/artifact seams
  ├─ aoa-playbooks      -> scenario activation and composition surfaces
  ├─ aoa-memo           -> recall contracts and memory object surfaces
  ├─ aoa-evals          -> proof catalogs, sections, comparison spine
  └─ aoa-kag            -> retrieval/graph-ready derived substrate

                ↓

             aoa-sdk
  ├─ typed loaders
  ├─ pydantic contracts
  ├─ policy engine
  ├─ session/runtime helpers
  ├─ orchestration helpers
  └─ adapter layer

                ↓

Consumers
  ├─ ATM10-Agent
  ├─ local scripts
  ├─ notebooks
  ├─ CI checks
  ├─ wrappers / CLIs
  └─ future MCP/A2A bridges
```

---

## 6. Repository layout

```text
aoa-sdk/
  pyproject.toml
  README.md
  LICENSE
  CHANGELOG.md
  .gitignore
  docs/
    architecture.md
    boundaries.md
    versioning.md
    adapters.md
    quickstart.md
  src/
    aoa_sdk/
      __init__.py
      api.py
      config.py
      errors.py
      types.py
      models.py

      workspace/
        __init__.py
        roots.py
        discovery.py
        bundle.py

      loaders/
        __init__.py
        base.py
        json_file.py
        git_export.py

      routing/
        __init__.py
        hints.py
        picker.py
        expander.py
        pairing.py

      skills/
        __init__.py
        discovery.py
        disclosure.py
        activation.py
        session.py
        compaction.py
        policy.py

      agents/
        __init__.py
        registry.py
        phase_bindings.py
        artifacts.py
        handoff.py

      playbooks/
        __init__.py
        registry.py
        activation.py
        composition.py
        failures.py
        recipes.py

      memo/
        __init__.py
        registry.py
        recall.py
        objects.py
        writeback.py

      evals/
        __init__.py
        registry.py
        comparison.py
        verdicts.py
        evidence.py

      kag/
        __init__.py
        federation.py
        retrieval.py

      policy/
        __init__.py
        approval.py
        trust.py
        mutation.py

      runtime/
        __init__.py
        session_store.py
        orchestrator.py
        transitions.py
        packets.py

      adapters/
        __init__.py
        local_fs.py
        mcp.py
        a2a.py

      cli/
        __init__.py
        main.py
        routing.py
        skills.py
        agents.py
        playbooks.py
        memo.py
        evals.py
  tests/
    test_workspace.py
    test_routing.py
    test_skills.py
    test_agents.py
    test_playbooks.py
    test_memo.py
    test_evals.py
    test_runtime.py
```

---

## 7. Package spine

### `aoa_sdk.api`
Thin public facade.

```python
from aoa_sdk import AoASDK

sdk = AoASDK.from_workspace("/repos/aoa")
```

### `aoa_sdk.workspace`
Finds sibling repo roots and builds a typed view over available generated surfaces.

Responsibilities:
- locate local clones
- validate expected generated files
- cache parsed JSON
- expose version/build metadata when present

### `aoa_sdk.loaders`
Transport-neutral loaders.

Implementations:
- `LocalFSLoader` for local clones
- `GitExportLoader` for exported bundles or checked-out tags
- later: remote read-only adapters

### `aoa_sdk.routing`
Implements the current routing ABI shape.

Operations:
- `pick(kind, query, ...)`
- `inspect(kind, id_or_name)`
- `expand(kind, id_or_name, sections=...)`
- `pair(kind, id_or_name)`
- `recall(mode, query, family=...)`

### `aoa_sdk.skills`
Maps closely to published runtime tools.

Operations:
- `discover(...)`
- `disclose(skill_name)`
- `activate(skill_name, session_file=..., wrap_mode="structured")`
- `session_status(session_file=...)`
- `deactivate(skill_name, session_file=...)`
- `compact(session_file=...)`

### `aoa_sdk.agents`
Consumes the agent role/phase seam.

Operations:
- `bindings()`
- `binding_for_phase("verify")`
- `artifact_type_for_phase("do")`
- `roles_for_phase("transition")`
- `new_artifact(phase=..., payload=...)`

### `aoa_sdk.playbooks`
Runtime-readable playbook surfaces.

Operations:
- `list()`
- `get(playbook_id)`
- `activation_surface(playbook_id)`
- `handoff_contracts(playbook_id)`
- `failure_catalog(playbook_id)`
- `subagent_recipe(playbook_id)`

### `aoa_sdk.memo`
Bounded recall over doctrine and object families.

Operations:
- `inspect(id)`
- `expand(id, sections=...)`
- `recall(mode="semantic", query=...)`
- `recall_object(mode="working", query=...)`
- later: bounded writeback helpers

### `aoa_sdk.evals`
Portable proof surfaces.

Operations:
- `list()`
- `inspect(name)`
- `expand(name, sections=...)`
- `comparison_entries(...)`
- `artifact_to_verdict(...)`

### `aoa_sdk.policy`
Cross-cutting governance helpers.

Responsibilities:
- trust posture checks
- mutation surface checks
- approval gates
- local-vs-remote action policy

### `aoa_sdk.runtime`
Session and orchestration helpers.

Responsibilities:
- skill session state
- artifact envelopes
- phase transitions
- playbook stepping
- compaction packets
- rehydration hints

---

## 8. Core data models

Start with a small pydantic core:

```python
class SurfaceRef(BaseModel):
    repo: str
    path: str
    kind: str

class RouterAction(BaseModel):
    enabled: bool
    surface_file: str | None = None
    match_field: str | None = None
    default_sections: list[str] = []
    supported_sections: list[str] = []

class RoutingHint(BaseModel):
    kind: str
    source_repo: str
    use_when: str
    actions: dict[str, Any]

class SkillCard(BaseModel):
    name: str
    display_name: str
    description: str
    short_description: str
    path: str
    trust_posture: Literal["explicit-risk", "portable-core", "project-overlay"]
    invocation_mode: Literal["explicit-only", "explicit-preferred"]
    allow_implicit_invocation: bool
    mutation_surface: Literal["none", "repo", "runtime", "sharing"]

class SkillActivationRequest(BaseModel):
    skill_name: str
    session_file: str | None = None
    explicit_handle: str | None = None
    include_frontmatter: bool = False
    wrap_mode: Literal["structured", "markdown", "raw"] = "structured"

class ActiveSkillRecord(BaseModel):
    name: str
    activated_at: datetime
    activation_count: int
    protected_from_compaction: bool
    allowlist_paths: list[str]
    compact_summary: str
    must_keep: list[str]
    rehydration_hint: str

class SkillSession(BaseModel):
    schema_version: int
    profile: str
    session_id: str
    created_at: datetime
    updated_at: datetime
    active_skills: list[ActiveSkillRecord]
    activation_log: list[dict[str, Any]]

class PhaseBinding(BaseModel):
    phase: Literal["route", "plan", "do", "verify", "transition", "deep", "distill"]
    tier_id: str
    role_names: list[str]
    artifact_type: str

class ArtifactEnvelope(BaseModel):
    artifact_type: str
    phase: str
    produced_by_role: str | None = None
    produced_at: datetime
    payload: dict[str, Any]
    refs: list[SurfaceRef] = []

class ApprovalDecision(BaseModel):
    allowed: bool
    requires_explicit_approval: bool
    reason: str
    risk_class: str
```

Keep the first release narrow.
Do not model the whole federation at once.

---

## 9. Public Python API

### minimal read-only slice

```python
from aoa_sdk import AoASDK

sdk = AoASDK.from_workspace("/work/aoa")

# routing
skill_route = sdk.routing.pick(kind="skill", query="bounded repo change")
skill_card = sdk.routing.inspect(kind="skill", id_or_name="aoa-change-protocol")
skill_sections = sdk.routing.expand(
    kind="skill",
    id_or_name="aoa-change-protocol",
    sections=["intent", "procedure", "verification"],
)

# skills
candidates = sdk.skills.discover(query="source of truth", mutation_surface="none")
preview = sdk.skills.disclose("aoa-source-of-truth-check")
activation = sdk.skills.activate(
    "aoa-change-protocol",
    session_file=".aoa/skill-runtime-session.json",
    wrap_mode="structured",
)

# agents
verify_binding = sdk.agents.binding_for_phase("verify")
artifact = sdk.agents.new_artifact(
    phase="verify",
    payload={"summary": "contract checks passed", "evidence": ["pytest -q"]},
)

# runtime
status = sdk.runtime.session_status(".aoa/skill-runtime-session.json")
packet = sdk.runtime.compact(".aoa/skill-runtime-session.json")
```

### orchestration slice

```python
run = (
    sdk.runtime
       .start()
       .route("safe bounded change in repo")
       .plan()
       .activate_skill("aoa-change-protocol")
       .do(work=lambda ctx: ctx)
       .verify()
       .distill()
)
```

That fluent API is optional.
The first release can stay function-first.

---

## 10. Runtime flow

The SDK should mirror the published agent seam:

```text
route -> plan -> do -> verify -> transition -> deep -> distill
```

Suggested implementation:

1. resolve route target
2. load required surface(s)
3. activate skill or playbook when needed
4. create typed artifact for the phase
5. validate handoff against the next phase contract
6. persist session state
7. optionally compact/rehydrate

This gives you a **phase-aware orchestrator** without needing a heavyweight framework.

---

## 11. Adapter strategy

### v0
- local filesystem only
- explicit sibling repo roots
- deterministic JSON loading

### later
- git-tag / export-bundle loader
- MCP resource adapter
- A2A outward adapter
- thin HTTP wrapper if needed

Rule:
the adapter layer may change transport, but never ownership.

---

## 12. Version plan

### `v0.1.0` — typed read path
Ship:
- workspace discovery
- routing hints loader
- skill discovery/disclosure/activation API wrappers
- phase bindings loader
- base models
- CLI inspect commands

No orchestration engine yet.
No writeback.
No remote transports.

### `v0.2.0` — session/runtime seam
Ship:
- session file management
- compaction packet helpers
- artifact envelope creation
- approval policy helpers
- local cache

### `v0.3.0` — phase-aware orchestration
Ship:
- route/plan/do/verify/distill runner
- handoff validation
- playbook activation read path
- evidence packet plumbing

### `v0.4.0` — memo + eval hooks
Ship:
- memo recall helpers
- eval comparison / verdict helpers
- evidence-to-verdict bridge helpers
- recurrence / rehydration helpers

### `v0.5.0` — outward integration
Ship:
- MCP resource adapter
- A2A boundary adapter
- export-friendly contracts
- stricter version negotiation

---

## 13. What not to do in v1

Do **not**:
- parse all authored markdown as the primary API
- embed a giant agent framework DSL
- make the SDK a daemon or runtime service
- duplicate catalogs from sibling repos
- put evaluation meaning into orchestration code
- invent hidden memory ranking rules inside the SDK
- let playbook execution swallow the playbook repo’s authority
- hard-code project overlays into portable-core paths

---

## 14. Suggested first commit

```text
aoa-sdk/
  pyproject.toml
  README.md
  src/aoa_sdk/__init__.py
  src/aoa_sdk/api.py
  src/aoa_sdk/models.py
  src/aoa_sdk/errors.py

  src/aoa_sdk/workspace/discovery.py
  src/aoa_sdk/loaders/json_file.py

  src/aoa_sdk/routing/hints.py
  src/aoa_sdk/routing/picker.py
  src/aoa_sdk/routing/expander.py

  src/aoa_sdk/skills/discovery.py
  src/aoa_sdk/skills/disclosure.py
  src/aoa_sdk/skills/activation.py
  src/aoa_sdk/skills/session.py

  src/aoa_sdk/agents/phase_bindings.py
  src/aoa_sdk/agents/artifacts.py

  tests/test_workspace.py
  tests/test_routing_hints.py
  tests/test_skill_discovery.py
  tests/test_skill_activation.py
  tests/test_phase_bindings.py
```

The first commit should already pass on:
- routing hints
- runtime tool schema loading
- runtime discovery parsing
- runtime session parsing
- phase binding parsing

---

## 15. Minimal `pyproject.toml`

```toml
[build-system]
requires = ["hatchling>=1.26"]
build-backend = "hatchling.build"

[project]
name = "aoa-sdk"
version = "0.1.0a1"
description = "Typed Python SDK for the AoA federation"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "Apache-2.0"}
authors = [{name = "8Dionysus"}]
dependencies = [
  "pydantic>=2.8",
  "typing-extensions>=4.12",
  "orjson>=3.10",
  "typer>=0.12",
  "rich>=13.7",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2",
  "pytest-cov>=5.0",
  "ruff>=0.6",
  "mypy>=1.11",
]

[project.scripts]
aoa = "aoa_sdk.cli.main:app"
```

---

## 16. README opening draft

```md
# aoa-sdk

Typed Python SDK for the AoA federation.

`aoa-sdk` loads source-owned generated surfaces from AoA repositories and exposes
stable Python APIs for routing, skill activation, handoff, recall, verification,
and bounded orchestration without taking ownership of meaning away from the
owning repositories.

## What it is
- a typed consumer of published AoA surfaces
- a local-first orchestration helper
- a bridge for downstream tools like ATM10-Agent

## What it is not
- not a replacement for aoa-routing
- not the owner of skills, evals, memo, or playbooks
- not a service runtime
- not a hidden monolith
```

---

## 17. First backlog

1. Workspace root auto-discovery across sibling clones
2. `RoutingHint` pydantic model + loader
3. `SkillCard` model + discovery loader
4. `SkillActivationRequest` + activation wrapper
5. `SkillSession` parsing and save/load
6. `PhaseBinding` model + artifact factory
7. CLI: `aoa route pick`
8. CLI: `aoa skills discover`
9. CLI: `aoa skills activate`
10. CLI: `aoa agents bindings`
11. test fixtures from checked-in sample surfaces
12. version compatibility policy for generated surfaces

---

## 18. Sharp recommendation

Build `aoa-sdk` in this order:

- **first**: typed read path
- **second**: skill session/runtime seam
- **third**: phase-aware artifacts and handoffs
- **fourth**: playbook/memo/eval bridges
- **fifth**: outward protocols

That order lets the SDK grow like a spine, not like ivy.