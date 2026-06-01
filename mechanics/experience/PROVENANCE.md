# Experience Provenance

## Source Surfaces

- `mechanics/experience/parts/capture-pipeline-helper/`
- `mechanics/experience/parts/adoption-federation-helper-contracts/`
- `mechanics/experience/parts/deployment-watchtower-helper-contracts/`
- `mechanics/experience/parts/governance-runtime-helper-contracts/`
- `mechanics/experience/parts/office-release-train-helper-contracts/`

## Stronger Owners

Experience owner surfaces decide the meaning and acceptance of Experience
operations. The SDK owns helper contract readability, typed shape, examples,
and seed regression checks.

## Moved Root Families

- `docs/AGON_WAVE1_EXPERIENCE_CAPTURE_PIPELINE.md` -> `mechanics/experience/parts/capture-pipeline-helper/docs/capture-pipeline-helper.md`
- `schemas/agon-experience-capture-pipeline-helper.schema.json` -> `mechanics/experience/parts/capture-pipeline-helper/schemas/capture-pipeline-helper.schema.json`
- `examples/agon_experience_capture_pipeline_helper.example.json` -> `mechanics/experience/parts/capture-pipeline-helper/examples/capture-pipeline-helper.example.json`
- `tests/test_agon_experience_capture_pipeline_helper.py` -> `mechanics/experience/parts/capture-pipeline-helper/tests/test_capture_pipeline_helper.py`
- `docs/EXPERIENCE_ADOPTION_API.md`, `docs/ADOPTION_*.md`, federation, harvest, pattern, KAG, and ToS dossier docs -> `mechanics/experience/parts/adoption-federation-helper-contracts/docs/`
- adoption/federation helper examples and schemas -> `mechanics/experience/parts/adoption-federation-helper-contracts/{examples,schemas}/`
- `tests/test_experience_wave3_seed_contracts.py` -> `mechanics/experience/parts/adoption-federation-helper-contracts/tests/test_adoption_federation_helper_contracts.py`
- governance, council, appeal, veto, constitution runtime, queue, sealing, and replay docs -> `mechanics/experience/parts/governance-runtime-helper-contracts/docs/`
- governance runtime examples and schemas -> `mechanics/experience/parts/governance-runtime-helper-contracts/{examples,schemas}/`
- `tests/test_experience_wave4_seed_contracts.py` -> `mechanics/experience/parts/governance-runtime-helper-contracts/tests/test_governance_runtime_helper_contracts.py`
- certification, deployment, regression, release, rollback, and watchtower docs -> `mechanics/experience/parts/deployment-watchtower-helper-contracts/docs/`
- deployment/watchtower examples and schemas -> `mechanics/experience/parts/deployment-watchtower-helper-contracts/{examples,schemas}/`
- `tests/test_experience_wave2_seed_contracts.py` -> `mechanics/experience/parts/deployment-watchtower-helper-contracts/tests/test_deployment_watchtower_helper_contracts.py`
- installation, console, sovereign release, handoff graph, office registry, and office train docs -> `mechanics/experience/parts/office-release-train-helper-contracts/docs/`
- office/release-train examples and schemas -> `mechanics/experience/parts/office-release-train-helper-contracts/{examples,schemas}/`
- `tests/test_experience_wave5_seed_contracts.py` -> `mechanics/experience/parts/office-release-train-helper-contracts/tests/test_office_release_train_helper_contracts.py`

## Notes

This shared mechanic name is kept because Experience helper contracts recur
across AoA API topology. Active part names describe SDK helper routes, not
historical landing waves.
