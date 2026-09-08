# Portable Workspace Bootstrap Validation

Run:

```bash
python -m pytest -q mechanics/runtime-seam/parts/portable-workspace-bootstrap/tests
python -m ruff check src/aoa_sdk/workspace src/aoa_sdk/contracts/workspace.py src/aoa_sdk/cli/workspace.py mechanics/runtime-seam/parts/portable-workspace-bootstrap/tests
python -m mypy src/aoa_sdk/workspace src/aoa_sdk/contracts/workspace.py src/aoa_sdk/cli/workspace.py
```

The focused tests cover portable copy planning plus the OS owner transport:

- default read-only owner plan with opaque payload preservation;
- explicit `--check` failure and malformed/missing/non-object JSON fail-closed;
- bounded stdout/stderr diagnostics and `-B`, `shell=False` subprocess posture;
- repeatable `--source-root OWNER=PATH` and `--os-root` CLI overrides;
- explicit rejection of OS-installer options when a portable profile is chosen.

The live clean-owner canary is kept outside the repository test suite. From the
workspace evidence directory, run
`python3 work/phase1_sdk_owner_execute_check_idempotence.py`; it installs both
real `.aoa` owner links into a temporary destination, runs SDK `execute`, then
runs SDK `check` twice and records the receipt/payload/tree idempotence report.

The repository-wide topology gate is owned by [root `VALIDATION.md`](../../../../VALIDATION.md#focused-repository-checks).
