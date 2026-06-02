# AGENTS.md

## Applies to

`mechanics/experience/`.

## Role

Route the shared Experience mechanic for SDK helper contracts. This package
keeps helper shape, examples, docs, and regression checks local to active parts;
it does not own adoption, governance, deployment, office, or release decisions.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/experience/README.md`
- `mechanics/experience/PARTS.md`
- `mechanics/experience/PROVENANCE.md`
- `mechanics/experience/parts/`

## Boundaries

- Stay on the control plane.
- Keep API helper calls as contracts, not operational decisions.
- Keep active Experience artifacts under `mechanics/experience/parts/<part>/`.
- Do not reintroduce root active homes for Experience docs, examples, schemas,
  or tests.
- Do not absorb Experience owner truth into SDK examples or schemas.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/experience/parts/capture-pipeline-helper/tests/test_capture_pipeline_helper.py
python -m pytest -q mechanics/experience/parts/adoption-federation-helper-contracts/tests/test_adoption_federation_helper_contracts.py
python -m pytest -q mechanics/experience/parts/deployment-watchtower-helper-contracts/tests/test_deployment_watchtower_helper_contracts.py
python -m pytest -q mechanics/experience/parts/governance-runtime-helper-contracts/tests/test_governance_runtime_helper_contracts.py
python -m pytest -q mechanics/experience/parts/office-release-train-helper-contracts/tests/test_office_release_train_helper_contracts.py
```

## Closeout

Report which Experience helper contract route changed and which owner decision
layer remains outside SDK.
