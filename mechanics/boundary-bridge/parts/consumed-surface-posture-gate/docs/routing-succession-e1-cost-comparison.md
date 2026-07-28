# Routing Succession E1 Process-Cost Comparison

Status: provisional pass pending landed CI observation.

Machine-readable evidence:
[`../evidence/routing-succession-e1-cost-comparison.json`](../evidence/routing-succession-e1-cost-comparison.json).
Raw timing observations:
[`../evidence/routing-succession-e1-process-observations.json`](../evidence/routing-succession-e1-process-observations.json).

## Bounded Question

Did succession reduce the cost of maintaining and consuming routing while
adding the typed Agent OS path, without hiding a regression or pretending that
unavailable telemetry is zero?

For the pinned M3 contour, the answer is yes for structural process cost and
supported process completeness. Direct task-latency, model-token, and landed
CI reliability reductions are not yet proved.

## Repository And CI Result

| Measure | R0 / pre-M3 | Post-M3 |
| --- | ---: | ---: |
| canonical routing producers | 1 | 1 |
| active producer control planes | 2 | 1 |
| physical producer implementations | 1 | 2, of which 1 is active and 1 retained for rollback |
| workflow files in the compared family | 6 | 5 |
| routing-related workflow contours | 6 | 3 |
| sibling checkout actions in those workflows | 73 | 23 |
| SDK checkouts of `aoa-routing` | 4 | 0 |
| predecessor sibling checkout actions | 30 | 0 |
| paired release streams | 2 | 1 |
| active historical pre-G5 wheel probes | 3 | 0 |

The checkout-action reduction is 50 of 73, or 68.5%. It is not a claim that
all remaining 23 federation checkouts are waste: they belong to SDK sibling
drift and cadence duties that still have separate meaning.

The predecessor implementation is deliberately still present. Consumer-zero,
compatibility exit, and rollback retirement have not passed, so counting
physical implementations as `2 -> 1` would be false.

## Agent Process Result

The old route API can answer one manually classified task-family request. In
ten read-only observations it returned advisory role, tier, and artifact
references with a 4.026 ms median. It did not return a `RouteDecision` or
`RunPlan`; intent-to-decision, decision-to-plan, plan-to-session, and
session-to-closeout remained unsupported.

The installed SDK clean-federation verifier exercised:

- `bounded_change_safe`;
- `a2a_summon_return_checkpoint`;
- `runtime_chaos_recovery`.

All ten verifier runs passed without an `aoa-routing` checkout. Each run
started a process, constructed the six-owner clean federation, and performed
repeated deterministic route, bind, and compile checks for all three
scenarios. Median duration was 3.183 seconds and p90 was 3.262 seconds.

Those latency figures are intentionally not divided or compared as an
acceleration claim. The old measurement returns one advisory lookup; the new
measurement verifies three typed compile-ready chains. Cost per equivalent
completed typed result is undefined for the old contour because that result
was unsupported.

Repository context for the measured producer/consumer task falls from an old
15–16-root maintenance lower bound to six owner repositories, a 60–62.5%
reduction. After typed inputs exist, the SDK path requires four public
transformations per compile-ready scenario:
`scenario_ref -> resolve -> bind_scenario -> compile`.

## Quality And Telemetry Ceiling

The E1 comparison reuses the retained T1/G11 evidence:

- eight equal fresh-context compiler observations;
- three golden cases;
- thirteen adversarial categories;
- 16 SDK and 5 runtime-owner cases;
- one 83-event isolated lifecycle ending in `closed`.

This is a bounded no-regression signal, not a central `aoa-evals` verdict.

Neither old nor new retained evidence contains model-token telemetry. The
agent-level tool-call totals are also unavailable. HTTP/process calls are
counted, and serialized byte sizes are retained, but the unlike output
contracts make bytes an invalid token-cost comparison.

## G13 And Remaining E1 Work

G13 is a provisional pass:

- structural maintenance and coordination cost decreased;
- the typed agent process gained supported route, plan, lifecycle, and
  closeout boundaries;
- the retained adversarial contour remains green;
- no direct latency or token reduction is claimed.

E1 stays provisional until the single final landing supplies a comparable
post-landing CI sample for lead time, runner minutes, and failure rate. This
does not block consumer-zero inspection, but it does block a final claim that
the historical 52.3% workflow failure rate has improved.

Consumer-zero, rollback retirement, archive readiness, and archive authority
all remain false.
