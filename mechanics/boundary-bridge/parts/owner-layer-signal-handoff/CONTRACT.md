# Owner-Layer Signal Handoff Contract

- Every owner-layer item remains a non-executable candidate or reviewed
  handoff input, including explicit skill-layer requests.
- Lexical matches are low-confidence topic hints with empty `signals`, no
  harvest target, and no promotion hint. They do not become checkpoint action
  events or candidate clusters merely by passing through another classifier.
- `requested_owner_layers` carries explicit caller requests using exact owner
  repo names. `declared_signals` carries caller assertions using the existing
  signal ids. Neither input proves occurrence, acceptance, or execution.
- Positive intent is not inferred by a negation dictionary, language-specific
  parser, or mandatory new model service. A semantic caller can use the same
  typed route for any source language.
- Stats regrounding reads only exact `consumed_stats_surfaces`; text such as
  `summary` or `stats` is not evidence of consumption. Missing or incompatible
  explicitly consumed surfaces fail rather than silently becoming clear.
- Surface detection does not read host skill availability, skill runtime
  sessions, activation receipts, or generic skill-routing results.
- Session-local receipts never become owner truth or execution evidence here.
- Retired `aoa-skills` shortlist refs become visible inspection gaps rather
  than fallback routes.
- `aoa surfaces handoff` requires reviewed routes.
- The SDK may preserve owner-layer evidence and next-read hints; it must not
  select a skill, claim execution, or claim the owner verdict.
