# SDK Shape

`sdk/` names the SDK organ.

It exists because `aoa-sdk` needs a visible source-home for its own posture,
not because the Python package needs another implementation path.

## Shape Rule

`sdk/` is tree-shaped:

```text
sdk/
  public-interface/
  facade-boundary/
  runtime-entry/
  distribution/
```

Each branch has a local `AGENTS.md` and `README.md`. Leaf directories explain
one source-home family and route to the implementation, mechanic, docs,
release, or validator surface that owns behavior.

## Authority Split

| Surface | Owns |
| --- | --- |
| `sdk/` | SDK posture, source-home branch topology, and route shape |
| `src/aoa_sdk/` | importable Python implementation and CLI behavior |
| `mechanics/` | repeatable SDK operation topology and part-local payload |
| `docs/` | public route doors, decisions, boundaries, and release explanation |
| `generated/` | compact derived companions |
| sibling repos | source meaning for their domains |

## Naming Rule

Branch names should tell an agent the operational posture:

- `public-interface`: what consumers may call or import;
- `facade-boundary`: what the SDK may read without owning meaning;
- `runtime-entry`: what the SDK may enter or inspect without becoming runtime;
- `distribution`: what the SDK may promise, build, release, or support.

Do not name branches after Python module layout unless that branch is actually
about public SDK posture.

## Stop Lines

- Do not add `PARTS.md`; mechanic parts belong under `mechanics/`.
- Do not move Python modules into `sdk/`.
- Do not hide schemas, tests, generated readers, or mechanic payload here.
- Do not use `sdk/` as a replacement for decisions or validators.
- Do not let a public-interface note become stronger than implementation
  tests.
