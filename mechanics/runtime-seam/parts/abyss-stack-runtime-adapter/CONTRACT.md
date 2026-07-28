# Contract

## Exact caller inputs

- one `RuntimeProfile` whose owner is `abyss-stack` and whose adapter ID is
  `abyss_stack_agent_os_adapter_v1`;
- one `AbyssStackRuntimeBinding` for the exact plan digest and scenario;
- one runtime request provenance ref already present either in the scenario's
  untyped `input_refs` or typed `input_artifact_bindings`, and bound to at
  least one admitted step;
- one absolute request delivery path;
- exact absolute delivery coordinates for every source and ABI in the plan
  snapshot;
- one explicit transport instance.

The binding contract ref must equal the runtime profile provenance. Source and
ABI location keys must cover the plan snapshot exactly, without missing or
extra observations.

`load_abyss_stack_runtime_profile()` is the supported construction route for
the runtime profile. It requires one absolute descriptor coordinate and an
exact owner/artifact location for every declared runtime constraint. It does
not discover `abyss-stack`, a policy file, or an executable. When the caller
supplies an exact `scenario_id`, the loader also projects only that
compatibility entry's runtime-owned approval requirements into the profile;
it grants none of them.

## Transport

`AbyssStackSubprocessTransport` invokes:

```text
<absolute executable> <operation> --state-root <absolute state root>
```

For a Python bridge, the caller must also bind the interpreter explicitly:

```text
<absolute python interpreter> -I <absolute executable> <operation> --state-root <absolute state root>
```

The isolated interpreter form prevents `PYTHONPATH`, user-site packages, and
the bridge shebang from silently selecting another SDK control-plane ABI. The
interpreter environment remains an explicit deployment input; it may carry
ordinary runtime configuration, but it must not be relied on for SDK package
selection.

Both forms send one canonical JSON payload on stdin, never invoke a shell,
never search `PATH`, and accept only
`abyss_stack_agent_os_bridge_response_v1`.

## Authority

The SDK adapter is a transport-only implementation of
`RuntimeAdapterProtocol`. Its `executes_plan_steps=true` declaration means the
selected runtime adapter can cause real execution through its runtime-owner
bridge; it does not mean the SDK client executes a step. `execution_owner`
remains `abyss-stack`.

Runtime completion may carry runtime evidence. It does not synthesize
`aoa-evals` verdicts, `aoa-memo` receipts, checkpoint acceptance, or final
closeout.
