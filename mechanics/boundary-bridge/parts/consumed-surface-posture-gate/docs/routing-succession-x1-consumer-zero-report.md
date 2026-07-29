# Routing Succession X1 Consumer-Zero Report

Status: archive ready; exact operator approval still required.

Machine-readable evidence:
[`../evidence/routing-succession-x1-consumer-zero-report.json`](../evidence/routing-succession-x1-consumer-zero-report.json).

## Result

The succession has reached landed direct-checkout consumer-zero. All sixteen
R0 consumers plus the subsequently discovered `aoa-skills` consumer are
accounted for at current `main`: thirteen owner migrations are landed and four
consumers remain unchanged because their predecessor references are bounded
history, fixtures, or provenance rather than executable dependencies. Seven
additional organization repositories have zero predecessor reference. The
final census therefore covers 24 current heads and finds zero active
`aoa-routing` checkout, environment-root, CI clone, generation, runtime, or
release dependencies.

This result does not erase legitimate historical identity. The stable routing
artifact namespace and ABI, predecessor self-identity, accepted decisions,
release and rollback evidence, negative validators, immutable trust and donor
provenance, naming fixtures, and derived KAG projections remain classified
residuals.

## Landed Validation

The thirteen owner migrations are bound to their exact merge refs and owner
PRs. Eight consecutive post-landing `aoa-sdk` main validations passed, and the
landed `aoa-kag` provider succession passed both its pre-merge 23-provider
release audit and post-merge run `30445769702`. The final report records these
as owner evidence; it does not convert them into SDK-owned meaning.

An exact package cycle exercised the preceding `0.8.0` and final `0.9.0`
workflow wheels:

1. clean-install `0.8.0`;
2. upgrade to `0.9.0` and load the packaged admitted trust record;
3. downgrade to `0.8.0`;
4. restore `0.9.0` and reproduce snapshot digest
   `sha256:9c1d0fcf4f9310106f4498f1b55fee21e65b57c03864eb78a0f7cc2f52c277d1`.

Three disposable Agent OS cycles then ran from the exact installed `0.9.0`
workflow wheel
`sha256:e9af2e6674e30bc1fd81d142cd70b3149c12d11dfc6db5d1564d30028ec5d236`
and runtime owner ref
`c779d1413690ec11b5df7b6fc638e2a8b95510a5`. They completed a governed
runtime mutation with evidence-complete closeout, a typed A2A return, and a
degradation pause/restore/resume path. These cycles prove orchestration and
closeout mechanics, not model quality or a stronger-owner eval verdict.

## Immutable-Tag Release Replay

The immutable `v0.9.0` package source is
`b24800bf0e9d2fa8470d7bb674dd33f6ae9e6acb`. Replaying that tag exposed three
workflow defects in succession: shallow release history, verifier lint scope,
and verifier checkout pollution of the source distribution. Each repair
landed through SDK owner review and a green `main` validation before the next
replay.

The final replay, run `30456244099` at workflow head
`956c32cd4db6f49948a0ddeacfafb59fe8807ae7`, passed the full 729-test release
gate, Ruff, mypy, installed-wheel probes, artifact-bundle validation, and
strict postpublish audit. Its wheel contains 268 files and its source
distribution contains 2,172 files with no verifier checkout.

Archive carrier hashes differ between GitHub Actions and the clean local build
because their build environments encode the archives differently. Unpacked
wheel and source-distribution contents are nevertheless byte-identical to the
clean exact-tag build. The exact artifact passes ABI-signature, SBOM, and
SLSA/in-toto controls with agent-consumer trust `allow`. A distinct
public-release-trust-root Python distribution intent remains correctly
`manual_review_required`; neither the live routing runtime nor this X1 result
claims that separate production consumption path.

## Portability Regression and Repair

The first clean installed-wheel cycle exposed a real portability defect: the
admitted `aoa-playbooks` trust record existed only as host-generated
distribution state, so the SDK could not materialize the exact plan source
away from that host state.

`AOA-SDK-D-0091` repaired the boundary by packaging the exact public-safe trust
record as a lower-authority SDK delivery projection. Runtime loading still
fails closed on record identity, digest, lifecycle, subject-store, or control
drift. The full release gate and all three exact-wheel Agent OS cycles passed
after this repair.

## Runtime and Rollback

The live runtime mirror is SDK-canonical and uses the authorized cutover. Both
route and RAG APIs are healthy, the exact 23-file mirror is trust-admitted, and
its manifest records that the predecessor implementation is not operationally
required. SDK-only runtime rollback is the primary operational rollback and
was rehearsed both as a fresh restore and an idempotent already-restored
replay. The live deployment was not rolled back during that rehearsal.

This retires the operational need for predecessor implementation rollback. It
does not delete the historical repository, stable namespace, evidence, or
compatibility records.

## Cost Verdict

E1 is complete with a mixed verdict. The landed topology reduces active
producer control planes from two to one, workflows from six to three, checkout
actions from 73 to 23, release streams from two to one, and the clean
route-bind-compile maintenance context from 15–16 roots to six.

The direct landed CI comparison moved in the opposite direction: the original
four-run E1 comparison has a 210.5-second median, 23.1% slower than the
historical paired 171-second median. Four subsequent green SDK main cycles and
the final immutable-tag replay extend assurance but do not rewrite that
accepted comparison window. The assurance-bearing portable KAG, package,
trust, and control-plane gates are retained. No direct task-latency, token,
long-run failure-rate, or total CI-time reduction is claimed.

## Compatibility Exit and Archive Boundary

All six compatibility-exit criteria are satisfied:

1. every registered consumer is landed and green;
2. active direct-checkout consumer count is zero;
3. clean install, upgrade, downgrade, and restore passed;
4. eight consecutive SDK main validations exceed the required two;
5. the live mirror and trust record identify the SDK canonical producer;
6. the discovered portability regression is repaired with post-repair proof.

Repository `8Dionysus/aoa-routing`, numeric ID `1186624390`, node ID
`R_kgDORrpzhg`, is therefore archive-ready but remains public, unarchived,
preserved, and maintenance-only at `main`
`19c2629a207978a118f7db81d89f44748b2e5235`; its latest release remains
`v0.3.0`. The report deliberately keeps
`archive_authorized=false`, `deprecation_release_executed=false`,
`github_archive_executed=false`, and `irreversible_action_taken=false`.

After this report lands and its post-merge validation passes, the only
remaining external gate is a separate exact operator approval naming
repository ID `1186624390` and the landed X1 report. Without it, no
deprecation release, About-banner mutation, GitHub archive, deletion, rename,
or other irreversible predecessor action is authorized.
