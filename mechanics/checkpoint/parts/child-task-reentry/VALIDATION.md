# Child-Task Reentry Validation

Run:

```bash
python -m pytest -q mechanics/checkpoint/parts/child-task-reentry/tests/test_a2a_sdk_api.py mechanics/checkpoint/parts/child-task-reentry/tests/test_a2a_transport_contract.py mechanics/checkpoint/parts/child-task-reentry/tests/test_a2a_assessment.py mechanics/checkpoint/parts/child-task-reentry/tests/test_a2a_checkpoint_and_return.py mechanics/checkpoint/parts/child-task-reentry/tests/test_a2a_owner_handoff.py mechanics/checkpoint/parts/child-task-reentry/tests/test_a2a_e2e_fixture.py
```

Before retaining schema or packet regressions, manually build one request,
result, return plan, and owner-handoff fixture; validate both schemas and verify
`capability_execution_claimed=false`.
