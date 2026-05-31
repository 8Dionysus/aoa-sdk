# Skill Routing Parts

## Candidate Parts

| Part | Current surfaces | Future payload condition |
| --- | --- | --- |
| discovery | `.agents/skills/`, `src/aoa_sdk/skills/discovery.py` | only if export indexing needs package-local manifests |
| disclosure | `src/aoa_sdk/skills/disclosure.py` | only if disclosure contracts become reusable schemas |
| activation | `src/aoa_sdk/skills/activation.py` | only if activation receipts become mechanic artifacts |
| phase-dispatch | `src/aoa_sdk/skills/detector.py`, `src/aoa_sdk/cli/main.py` | only if phase rules outgrow CLI tests |
| runtime-session | `src/aoa_sdk/skills/session.py` | only if session files need public schema examples |
