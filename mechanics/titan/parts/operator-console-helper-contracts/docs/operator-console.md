# Titan Operator Console

The console keeps a visible roster, event ledger, gate approvals, digest, and
optional app-server launch plan. It does not rewrite Codex agents and does not
own role truth.

New console states are explicit local witnesses:
`surface_role=titan_console_witness`, `authority=witness_only`,
`runtime_execution_state=not_run`, `transport_state=not_sent`, and
`state_semantics=helper_projection_only`. Ungated roster entries begin
`declared`; gated entries begin `locked`. An `active` helper entry records only
an explicit local gate witness and never proves runtime activation.

The `operator` field is attribution, not authentication. Callers that do not
have an externally supplied operator label use
`unattributed-local-operator`; `operator_field_authenticated` remains false.
Gate witness writes require both `--decision-ref` and `--approved-by`. The
stored approval remains `authority=witness_only` and
`approved_by_authenticated=false`; the helper preserves attribution and
provenance but does not authenticate either.

`appserver-plan` requires an explicit prompt file. It omits the model when the
caller does not select one, leaving runtime/model resolution to the eventual
app-server owner rather than embedding a stale helper default.

Commands: `roster`, `new`, `event`, `gate`, `digest`, `close`, `validate`, `appserver-plan`.
