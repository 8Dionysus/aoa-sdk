# Insert: Manifest Compatibility Gate

Add this insert to `RECURRENCE_CONTROL_PLANE.md` or the local recurrence landing note.

Before recurrence expands into graph closure, run a manifest compatibility scan:

```bash
aoa recur manifest-scan --root /srv/workspace --json
python scripts/validate_recurrence_manifests.py --workspace-root /srv/workspace --json
```

The scan is successful when:

- component manifests load;
- hook/review/wiring/rollout manifests are recognised as known foreign shapes;
- Agon-shaped files are carried as adapter-required observation-only diagnostics;
- invalid JSON and invalid component shapes appear as diagnostics instead of process failures.

Treat high diagnostics as a blocking landing issue. Treat medium adapter diagnostics as review-required, not as automatic mutation permission.
