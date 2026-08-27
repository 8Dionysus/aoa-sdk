# Programmatic Tool Execution

This part owns the provider-neutral SDK contract for one direct or
programmatic tool execution. It carries stable tool handles, an explicit
sandbox/effect ceiling, exact plan and runtime-profile bindings, explicit
activation, and observation requirements.

It also exposes an optional provider-neutral intent bridge that binds an exact
upstream dashboard action-intent ref and Goal correlation to the request while
retaining explicit downstream receipt missingness. The bridge is deferred and
non-executing by default; it does not create an app-server operation or runtime
admission.

The contract is data-only. `aoa-sdk` does not discover providers, launch a
runtime, execute tools, choose models, or issue eval verdicts. Runtime
execution and durable runtime receipts remain owned by `abyss-stack`.

See [CONTRACT](CONTRACT.md) and [VALIDATION](VALIDATION.md).
