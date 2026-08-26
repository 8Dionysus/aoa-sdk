# Programmatic Tool Execution

This part owns the provider-neutral SDK contract for one direct or
programmatic tool execution. It carries stable tool handles, an explicit
sandbox/effect ceiling, exact plan and runtime-profile bindings, explicit
activation, and observation requirements.

The contract is data-only. `aoa-sdk` does not discover providers, launch a
runtime, execute tools, choose models, or issue eval verdicts. Runtime
execution and durable runtime receipts remain owned by `abyss-stack`.

See [CONTRACT](CONTRACT.md) and [VALIDATION](VALIDATION.md).
