# Manifest Compatibility CLI Route

Manifest compatibility precedes graph closure. The executable scan is owned by
the recurrence CLI and the part-local manifest validator; its canonical
operator and test route is `../VALIDATION.md`.

The scan is successful when:

- component manifests load;
- hook/review/wiring/rollout manifests are recognised as known foreign shapes;
- Agon-shaped files are carried as adapter-required observation-only diagnostics;
- invalid JSON and invalid component shapes appear as diagnostics instead of process failures.

Treat high diagnostics as a blocking landing issue. Treat medium adapter diagnostics as review-required, not as automatic mutation permission.
