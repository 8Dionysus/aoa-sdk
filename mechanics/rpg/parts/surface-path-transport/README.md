# Surface Path Transport

This part owns the SDK route for expected RPG upstream generated transport
paths and fragment refs.

## Role

Input: owner repository names, generated relative paths, collection wrapper
shapes, and item fragment refs.

Output: documented path expectations used by the SDK consumer API and local
compatibility checks.

Owner: `aoa-sdk` owns consumer expectations. Source repositories own generated
files, builder behavior, runtime delivery, and RPG meaning.

## Active Surfaces

- [Surface Path Transport](docs/surface-path-transport.md)
- [Surface Path Transport Test](tests/test_surface_path_transport.py)

## Next Route

Promote path rules into global compatibility only after upstream generated
paths and builders are stable enough.
