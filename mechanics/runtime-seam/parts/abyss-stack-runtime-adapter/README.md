# abyss-stack Runtime Adapter

This part owns the SDK-side typed client for the first production runtime
adapter. The client binds one exact `RunPlan`, `RuntimeProfile`, request
artifact, source/ABI delivery map, and caller-supplied transport.

`load_abyss_stack_runtime_profile()` materializes the runtime profile only
from an explicit absolute owner-descriptor path and an exact set of delivered
constraint artifacts. It hashes both before constructing the typed profile.

`abyss-stack` remains the stronger owner of the bridge ABI, runtime policy,
durable lifecycle state, approvals, real plan-step execution, evidence, and
runtime outcome.

The SDK client performs no adapter discovery, shell invocation, goal
inference, policy evaluation, model/tool execution, or fallback. The provided
subprocess transport invokes one absolute executable path with `shell=False`.
Python bridges additionally bind one absolute interpreter and use isolated
mode, so inherited source routing cannot replace the installed SDK ABI.

See [CONTRACT](CONTRACT.md) and [VALIDATION](VALIDATION.md).
