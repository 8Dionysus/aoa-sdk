# Progressive exposure contract

The progressive exposure surface is a provider-neutral, candidate-only bridge
from an explicit organ capability selection to a deterministic model-visible
tool-set snapshot.

The SDK binds:

- the owner-qualified capability identity and source/schema digests;
- freshness, provider watermark, and the bounded TTL;
- the capability effect ceiling, approval lifetime, organ fallback rollback
  route, and ordered primitive-specific rollback bindings;
- the ordered visible tool descriptors; and
- exact rendered bytes, explicitly labelled token counts, expansion reasons,
  and refusal reasons.

`OrgansAPI.compile_exposure` is deny-by-default. It reveals no tool or schema
unless the caller supplies an explicit ordered selection, requests schema
disclosure, supplies an unexpired baseline-ready evidence reference, and the
local feature flag was explicitly enabled. The returned plan still fixes both
`activation_authorized` and `execution_authorized` to `false`.

`OrgansAPI.prepare_exposure_authorization` is only the typed handoff to the
runtime owner. It does not authorize activation, call an owner, issue proof,
or assert acceptance. Runtime materialization and invocation receipts belong
to `abyss-stack`; bounded integrity and economic measurements belong to
`aoa-evals`.

The JSON Schemas are generated into this part's `schemas/` directory by
`generate_organ_access_schemas.py`. A green schema check proves source
contract parity only; it does not prove a baseline gate, live endpoint,
runtime invocation, owner acceptance, or economy effect.
