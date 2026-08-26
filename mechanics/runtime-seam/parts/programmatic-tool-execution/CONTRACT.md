# Contract

`aoa_programmatic_tool_execution_v1` is the shared, provider-neutral ABI for
comparing ordinary direct tool calling with a programmatic tool execution
mode.

## SDK-owned shape

- `ProgrammaticExecutionRequest` binds one execution and correlation identity,
  mode, plan, runtime profile, input, tool handles, effect ceiling, explicit
  activation, and observation requirements.
- `ProgrammaticToolHandle` gives each tool a stable identity and binds input
  and output schemas plus its effect class.
- `ProgrammaticEffectCeiling` names the admitted sandbox and tool-effect
  classes. Tool-call limits are effect-surface limits, not token budgets.
- `ProgrammaticActivationRequirements` binds the exact plan and runtime
  profile and keeps `default_enabled=false`. `ProgrammaticActivation` can be
  admitted only with an explicit evidence ref and timestamp.
- `ProgrammaticExecutionObservation` records execution status, tool calls,
  intermediate value refs, failures, economy counters, and dimension-level
  missingness. Economy counters are observations, never predeclared limits.

`assert_programmatic_execution_observation()` checks the exact request digest,
identity, handle set, effect ceiling, observation dimensions, and missingness
policy. It does not decide whether a baseline is ready or whether a result is
correct.

## Boundaries

The SDK contract does not own provider discovery, model selection, runtime
launch, tool implementation, sandbox enforcement, eval meaning, memory,
closeout, or owner acceptance. A runtime adapter must revalidate this contract
before execution and retain the returned observation as runtime evidence.
