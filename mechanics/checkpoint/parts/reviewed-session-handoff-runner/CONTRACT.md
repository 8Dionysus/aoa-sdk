# Reviewed Session Handoff Runner Contract

## Contract

The part runs only reviewed closeout material. It assembles and processes
manifest-driven handoffs, calls owner-owned publisher scripts, refreshes
`aoa-stats`, and writes reports. It does not infer owner truth or run checkpoint
bridge skills implicitly.

## SDK-Owned Active Names

- part route: `checkpoint/reviewed-session-handoff-runner`
- doc: `docs/reviewed-session-handoff-runner.md`
- operator scripts: `scripts/install_closeout_units.py` and
  `scripts/process_closeout_inbox.py` inside this part
- source module: `src/aoa_sdk/closeout/`

## External Compatibility Inputs

- owner-local publisher scripts in `aoa-skills`, `aoa-evals`, `aoa-playbooks`,
  `aoa-techniques`, and `aoa-memo`
- stats refresh in `aoa-stats`
- part-local `closeout-inbox-user-units/` deployment templates when installed for the local workspace

## Stop-Lines

- Do not run on unreviewed manifests.
- Do not auto-run `aoa-checkpoint-closeout-bridge`.
- Do not auto-run `aoa surfaces handoff`.
- Do not keep reviewed-session handoff runner implementation scripts in root `scripts/`.
