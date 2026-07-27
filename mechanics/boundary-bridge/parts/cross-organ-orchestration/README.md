# Cross-Organ Orchestration

## Role

This Boundary Bridge part makes one OS Abyss organ chain explicit:

```text
KAG evidence
  -> memo candidate
  -> eval request
  -> eval result
  -> owner acceptance or rejection
```

It is a deterministic SDK state machine over host-supplied artifacts and
receipts. It never calls an MCP server, writes memory, computes a verdict,
accepts source, or executes runtime work.

## Inputs

- one expiring orchestration request;
- exact owner schema identities and source revisions for all five stages;
- one owner-qualified stage observation at a time;
- one host-visible, content-addressed receipt per transition;
- explicit owner evidence, freshness, effect state, next owner, and stop state.

## Outputs

- an immutable, content-addressed partial or terminal run;
- an exact input/output and previous-snapshot chain;
- explicit `accepted`, `rejected`, `stopped`, or `denied` terminal posture;
- machine-visible negative authority flags.

## Owner split

`aoa-sdk` owns only the contract and deterministic transition validation.
`aoa-kag` owns retrieved evidence meaning, `aoa-memo` owns memory candidates
and reviewed landing, `aoa-evals` owns eval pressure and verdict meaning, and
`abyss-stack` or another explicit host owns calls, ordering, receipt issuance,
runtime lifecycle, credentials, and rollback.

The state machine is deliberately absent from the workspace MCP. The host must
invoke each owner independently and then pass the resulting observation into
the SDK.

## Start route

Read [the contract](CONTRACT.md), [the research basis](docs/research-basis.md),
and [the usage route](docs/cross-organ-orchestration.md). Use
[VALIDATION.md](VALIDATION.md) before relying on a generated schema or example.

The accepted example proves contract shape only. It is not evidence that any
owner accepted a live memory object.
