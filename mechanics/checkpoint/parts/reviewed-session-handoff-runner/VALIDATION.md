# Reviewed Session Handoff Runner Validation

Run:

```bash
python -m pytest -q mechanics/checkpoint/parts/reviewed-session-handoff-runner/tests/test_reviewed_session_handoff_runner.py
python scripts/validate_mechanics_topology.py
```

For the part-local operator scripts, also smoke import the script paths:

```bash
python mechanics/checkpoint/parts/reviewed-session-handoff-runner/scripts/process_closeout_inbox.py --help
python mechanics/checkpoint/parts/reviewed-session-handoff-runner/scripts/install_closeout_units.py --help
```
