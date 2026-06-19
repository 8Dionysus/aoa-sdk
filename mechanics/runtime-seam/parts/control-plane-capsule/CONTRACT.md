# Control Plane Capsule Contract

## Guarantees

- Publishes only low-context routing refs, not implementation internals.
- Fails validation when generated output diverges from the canonical builder.
- Keeps validation refs explicit and resolvable.
- Publishes `artifact_identity` for the capsule itself: artifact class,
  public surface state, producer, consumer expectation, privacy boundary, ABI
  epoch, trust layer, and verification commands.
- Treats the capsule identity as ABI posture with source-schema validation
  listed under consumer verification, not as release provenance, package
  signing, or runtime deployment proof.

## Non-Goals

- It does not replace design docs, decisions, or mechanics contracts.
- It does not load sibling data or make compatibility decisions by itself.
- It does not publish private host evidence, live service facts, SBOM/SLSA
  release claims, Cosign signatures, TUF metadata, SCITT receipts, or C2PA
  credentials.
