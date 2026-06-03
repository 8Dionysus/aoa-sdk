# Titan Roadmap

Titan is the SDK helper-contract route for Titan-shaped runtime-support
surfaces. It can expose bounded receipts, console, appserver, memory, replay,
and swarm closeout helpers; it cannot claim Titan runtime authority or owner
acceptance.

## Current Contour

- Keep incarnation/runtime receipts, operator console, appserver bridge, memory
  loom and recall, visible session replay, and swarm closeout helper contracts
  routed through active `parts/`.
- Keep receipt and console helpers explicit about evidence limits.
- Keep appserver bridge helpers below runtime owner truth.
- Keep memory, replay, and swarm closeout helpers advisory and source-routed.

## Next Work

- Tighten helper contracts where owner surfaces and validation routes are clear.
- Keep runtime-support helpers separated from deployment, memory acceptance, and
  closeout acceptance.
- Route repeated Titan pressure into the nearest current part before adding new
  helper depth.

## When Time Comes

- Add a new Titan part when repeated helper pressure cannot stay inside receipt,
  console, appserver, memory, replay, or closeout contracts.
- Promote helper behavior only after Titan runtime owners name execution,
  rollback, and acceptance posture.
- Add generated Titan companions only when source records and validation stay
  stronger than the companion.

## Out Of Scope

- Titan runtime authority.
- Appserver deployment truth.
- Durable memory acceptance.
- Swarm execution or closeout acceptance.
- Runtime owner replacement by SDK helper contracts.
