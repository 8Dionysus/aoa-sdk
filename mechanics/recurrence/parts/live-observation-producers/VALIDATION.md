# Live Observation Producers Validation

```bash
python mechanics/recurrence/parts/live-observation-producers/scripts/collect_live_recurrence_observations.py --workspace-root /srv/AbyssOS --json
python -m pytest -q mechanics/recurrence/parts/live-observation-producers/tests/test_recurrence_live_observation_seed.py
```
