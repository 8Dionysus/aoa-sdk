# Workspace Layout

`aoa-sdk` assumes a local-first workspace where source repositories and deployed runtime mirrors are not the same thing.

## Default topology

- `/srv/<repo>` is the normal source-checkout location for the AoA federation repositories.
- `~/src/abyss-stack` is the source checkout for `abyss-stack`.
- `/srv/abyss-stack` is a deployed runtime mirror and should not be treated as the authored source checkout.

## Machine-readable contract

The repository tracks its workspace expectations in `.aoa/workspace.toml`.
`Workspace.discover()` loads that manifest automatically and uses it before falling back to generic ancestor scanning.

The current manifest expresses three things:

- the expected federation root is the parent of the `aoa-sdk` checkout
- additional source checkouts may exist under `~/src`
- `abyss-stack` should prefer `~/src/abyss-stack`

## Overrides

For a different machine layout, prefer overrides over code changes.

- `AOA_SDK_WORKSPACE_CONFIG`
  Use a different workspace manifest file.
- `AOA_SDK_FEDERATION_ROOT`
  Force the federation root directory.
- `AOA_SDK_EXTERNAL_ROOTS`
  Add extra repo root search prefixes using the platform path separator.
- `AOA_SDK_REPO_PATH_<REPO>`
  Force a specific repository path.
  Example: `AOA_SDK_REPO_PATH_ABYSS_STACK=/worktrees/abyss-stack`

Repo names in env vars are normalized to uppercase with non-alphanumeric characters replaced by `_`.

Workspace discovery overrides in `aoa-sdk` are not a substitute for
Codex-plane deployment regeneration. When the live public workspace root
changes, rerender the source-owned `8Dionysus/.codex/` deployment surfaces
from the shared Codex-plane manifest/profile pair instead of patching SDK
discovery code or MCP server names ad hoc. For the owner split, see
`docs/CODEX_PLANE_PORTABILITY.md` and `8Dionysus/docs/CODEX_PLANE_REGENERATION.md`.

## Inspection

Use the CLI to confirm what the SDK will actually resolve:

```bash
aoa workspace inspect /srv/aoa-sdk
```

This prints the workspace root, federation root, manifest path, and every resolved repository path.
