# Live Observation Producer CLI Route

The recurrence CLI exposes producer discovery and bounded observation modes.
Executable definitions remain under `src/aoa_sdk/recurrence/`; focused
operator and test routes are owned by `../VALIDATION.md`.

The intended pipeline is observation, beacon derivation, then review-queue
construction. Each intermediate packet keeps its own truth posture.

The commands are read-only except for writing recurrence output packets under `.aoa/recurrence` or the explicit `--report-output` path.
