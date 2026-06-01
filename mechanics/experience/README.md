# Experience Mechanic

Status: active topology with part-local payload.

## Mechanic Card

### Operation

Maintain Experience SDK helper contracts for capture, adoption federation,
deployment/watchtower, governance runtime, and office release-train routes.

### Trigger

Use this mechanic when an Experience helper doc, schema, example, or seed
contract test changes.

### SDK owns

- typed helper contract schemas
- public-safe examples
- seed contract regression tests
- documentation of the SDK helper boundary
- part-local route cards for each active helper family

### Stronger owner split

Experience owners retain operational decisions, adoption authority, federation
meaning, deployment truth, governance truth, watchtower meaning, rollback
authority, office activation, and release acceptance.

### Current source surfaces

- `mechanics/experience/parts/capture-pipeline-helper/`
- `mechanics/experience/parts/adoption-federation-helper-contracts/`
- `mechanics/experience/parts/deployment-watchtower-helper-contracts/`
- `mechanics/experience/parts/governance-runtime-helper-contracts/`
- `mechanics/experience/parts/office-release-train-helper-contracts/`

### Active parts

- capture-pipeline-helper
- adoption-federation-helper-contracts
- deployment-watchtower-helper-contracts
- governance-runtime-helper-contracts
- office-release-train-helper-contracts

### Candidate parts

No active Experience helper family remains in root technical districts. Future
candidate parts must be created only when a real SDK helper contract family
appears that is not owned by the existing active parts.

### Must not claim

This mechanic must not turn a valid SDK helper call into approval to execute an
Experience operation.

### Validation

```bash
python -m pytest -q mechanics/experience/parts/capture-pipeline-helper/tests/test_capture_pipeline_helper.py
python -m pytest -q mechanics/experience/parts/adoption-federation-helper-contracts/tests/test_adoption_federation_helper_contracts.py
python -m pytest -q mechanics/experience/parts/deployment-watchtower-helper-contracts/tests/test_deployment_watchtower_helper_contracts.py
python -m pytest -q mechanics/experience/parts/governance-runtime-helper-contracts/tests/test_governance_runtime_helper_contracts.py
python -m pytest -q mechanics/experience/parts/office-release-train-helper-contracts/tests/test_office_release_train_helper_contracts.py
```

### Next route

Operational meaning routes to the Experience owner; SDK changes stay in
part-local schemas, examples, docs, and tests.
