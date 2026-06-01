# Reviewed Stress Closeout Carry

This part owns the SDK route that lets reviewed closeout carry stress evidence
without creating a new authority center.

## Role

Input: reviewed artifact refs, source receipt refs, runtime degradation refs,
routing hint refs, memo refs, bounded eval refs, and a next-step brief.

Output: a reviewed stress closeout manifest that keeps refs legible and names
what remains blocked or owner-local.

Owner: `aoa-sdk` owns the closeout carry shape and example manifest. Owners
decide repair, proof acceptance, memory promotion, stats publication, and
runtime response.

## Active Surfaces

- [Reviewed Stress Closeout Carry](docs/reviewed-stress-closeout-carry.md)
- [Reviewed Stress Closeout Manifest](examples/reviewed-stress-closeout-manifest.example.json)

## Next Route

Route retained lessons to `aoa-memo`, proof gaps to `aoa-evals`, runtime
degradation to runtime owners, and owner-local repair to the affected repo.
