# Routing Succession X1 Consumer-Zero Candidate

Status: candidate consumer-zero pending coordinated landing.

Machine-readable evidence:
[`../evidence/routing-succession-x1-consumer-zero-candidate.json`](../evidence/routing-succession-x1-consumer-zero-candidate.json).

## What Is Proved

The exact local migration set accounts for all sixteen R0 consumers plus the
subsequently discovered `aoa-skills` consumer. Thirteen consumers have clean
candidate commits with zero active direct dependency on an `aoa-routing`
checkout. Four consumers need no mutation: `abyss-machine` already carries
the stronger-owner SDK admission, while `Dionysus`, `aoa-session-memory`, and
`ATM10-Agent` retain only classified historical, fixture, or provenance
records.

Seven additional active organization repositories have no direct predecessor
reference at their pinned `origin/main`. The only one whose ref changed after
R0, `aoa-course-connector`, was fetched and rescanned at the new ref.

Literal predecessor references are not blindly deleted. Stable artifact and
ABI names, repository self-identity, historical decisions and reviewed runs,
rollback fixtures, negative assertions, trust and donor provenance, naming
fixtures, and their generated projections remain valid residual classes.
None of them requires the predecessor checkout for active execution.

## What Is Not Proved

The migration commits are not landed. Therefore landed consumer-zero is still
false even though candidate consumer-zero is true. `aoa-kag` must refresh its
exact SDK pin after the SDK commit lands, every repository still needs its
owner CI and review, and post-landing runtime freshness must be observed.

The compatibility window also remains open. The final exit still requires:

1. every registered consumer green on landed SDK-produced artifacts;
2. landed direct checkout consumer-zero;
3. clean install, upgrade, downgrade, and rollback rehearsals;
4. two consecutive SDK main or release validation cycles without predecessor
   generation;
5. a fresh runtime mirror and trust check against the landed SDK ref;
6. no unresolved high-severity compatibility regression.

Post-merge cost telemetry, several real execution/closeout cycles, and proof
that operational rollback no longer needs the predecessor implementation are
also pending.

## Landing Shape

Use one coordinated final wave rather than a PR for every historical step:

1. refresh and land the SDK candidate;
2. bind and regenerate the KAG candidate to that exact landed SDK ref;
3. refresh and land the remaining consumers and the predecessor
   maintenance-only candidate under their owner gates;
4. collect post-merge CI, release, runtime, execution, and closeout evidence;
5. replace this candidate snapshot with a landed consumer-zero and
   archive-readiness verdict.

`aoa-routing` remains the rollback implementation throughout this wave.
Archival, deletion, or another irreversible action is not authorized. Even an
eventual `archive_ready=true` result requires a separate operator approval
that names the exact repository and evidence.
