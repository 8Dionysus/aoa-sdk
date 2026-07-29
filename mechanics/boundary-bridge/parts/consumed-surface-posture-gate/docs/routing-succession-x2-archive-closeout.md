# Routing Succession X2 Archive Closeout

X2 is the final SDK-owned receipt for the operator-approved hosting succession
of `8Dionysus/aoa-routing`. Its machine-readable source is
[`../evidence/routing-succession-x2-archive-closeout.json`](../evidence/routing-succession-x2-archive-closeout.json).

## What X2 closes

X1 proved consumer-zero, compatibility exit, SDK-only operational rollback,
and archive readiness. X2 does not revise that evidence. It pins the exact X1
bytes and then records the later actions that X1 was intentionally forbidden
to authorize:

- the operator approval naming repository ID `1186624390`, node ID
  `R_kgDORrpzhg`, and `8Dionysus/aoa-routing`;
- the final predecessor PR and its exact-head and post-merge validation;
- the public `v0.4.0` deprecation release at the landed main commit;
- the repository About metadata and preserved historical topics;
- the GitHub archive state, with deletion and rename still forbidden;
- public availability of the repository, README, and final release;
- continued SDK-canonical route and RAG runtime health after archival.

The predecessor remains a public historical source. Archival ends active
development; it does not erase ABI history, releases, decisions, or KAG
provenance.

## Historical authority is not rewritten

The X1 receipt remains byte-pinned with `archive_authorized=false` and
`github_archive_executed=false`. Those fields describe the authority and
observations available when X1 was issued. Likewise, the live runtime mirror
still carries `g5_authority.archive_authorized=false` because it preserves the
earlier owner-switch receipt. Neither historical record is the authority for
the later operator-approved GitHub action.

X2 is the separate subsequent receipt. This avoids turning a current outcome
into a retroactive claim about earlier evidence.

## Runtime result

The live routing path remains owned by `abyss-stack` at execution time and by
`aoa-sdk` for the routing producer and ABI:

- route API and RAG API are healthy;
- all seven route layers are ready;
- the router exposes 170 entries with `artifact_identity.owner_repo=aoa-sdk`;
- the mirror is `sdk_canonical` under `authorized_live_cutover`;
- the exact runtime trust record remains `allow`;
- neither runtime container mounts nor requires the predecessor checkout.

Archive execution therefore did not become a runtime cutover and did not
change execution ownership.

## KAG residual

`AOA-KAG-D-0020` and `aoa-kag` PR
[`#180`](https://github.com/8Dionysus/aoa-kag/pull/180) already removed
`aoa-routing` from the active provider registry and route current routing work
to `aoa-sdk`.

The mutable KAG runtime projection still contains a July 14 historical
`aoa-routing` slice. After the canonical provider succession landed, MCP marks
that slice `source_unavailable` and returns a degraded result with provenance.
X2 classifies this honestly as `derived_projection_refresh_pending`.

That residual is not:

- an active provider;
- a direct checkout consumer;
- a routing producer;
- a runtime mount;
- an operational rollback dependency.

Refreshing that large mutable projection belongs to the `abyss-stack` KAG
runtime lifecycle. X2 does not hide the residual and does not widen the SDK
control-plane boundary to mutate it.

## Verdict

The routing succession is complete: `aoa-sdk` is the sole canonical routing
owner, the live runtime uses its trusted artifact, active predecessor checkout
consumers are zero, the final release is public, and the exact predecessor is
preserved and archived within operator scope. No delete or rename action was
taken.
