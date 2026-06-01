# Workspace Root Resolution Contract

## Guarantees

- Resolves workspace and federation roots from explicit manifests and
  supported environment overrides.
- Reports the origin for each resolved repo path.
- Prefers source checkouts over runtime mirrors when the manifest says so.

## Non-Goals

- It does not create sibling repo content.
- It does not silently rewrite the workspace manifest.
- It does not make runtime mirror paths stronger than source checkouts.
