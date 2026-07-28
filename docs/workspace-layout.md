# Workspace Layout

`aoa-sdk` assumes a local-first workspace where source repositories and deployed runtime mirrors are not the same thing.

## Default topology

- `/srv/<repo>` is the normal source-checkout location for the AoA federation repositories.
- `~/src/abyss-stack` is the source checkout for `abyss-stack`.
- `/srv/AbyssOS/abyss-stack` is a deployed runtime mirror and should not be treated as the authored source checkout.

## Machine-readable contract

The repository tracks its workspace expectations in `.aoa/workspace.toml`.
`Workspace.discover()` loads that manifest automatically and uses it before falling back to generic ancestor scanning.

The current manifest expresses five things:

- the expected federation root is the parent of the `aoa-sdk` checkout
- additional source checkouts may exist under `~/src`
- `abyss-stack` should prefer `~/src/abyss-stack`
- C1 route resolution reads the explicit deployed SDK-canonical routing bundle
  under the `abyss-stack` runtime mirror
- organ discovery reads exactly one OS-private registry source under the
  workspace-owned `.aoa/organ-access/` directory; a missing, invalid, stale, or
  expired instance fails closed and cannot authorize activation

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
- `AOA_SDK_ROUTING_BUNDLE_ROOT`
  Force the explicit SDK-canonical routing runtime bundle used by C1.
- `AOA_SDK_ROUTING_SOURCE_LOCK`
  Replace the packaged canonical source lock for an explicit bounded test or
  rehearsal. The override is still subject to canonical path, owner, ref,
  digest, receipt, and trust checks.
- `AOA_SDK_ORGAN_REGISTRY`
  Select one explicit OS-private organ-registry source. The source contains no
  credential values, remains outside this public repository, and is still
  subject to strict schema, expiry, admission, compatibility, and maturity
  validation.

Repo names in env vars are normalized to uppercase with non-alphanumeric characters replaced by `_`.

Workspace discovery overrides in `aoa-sdk` are not a substitute for
Codex Projection deployment regeneration. When the live public workspace root
changes, rerender the source-owned `8Dionysus/.codex/` deployment surfaces
from the shared Codex projection manifest/profile pair instead of patching SDK
discovery code or MCP server names ad hoc. For the owner split, see
`mechanics/codex-projection/parts/portability-boundary/docs/portability-boundary.md`
and `8Dionysus/docs/CODEX_PLANE_REGENERATION.md`.

## Inspection

Use the workspace inspection route owned by the SDK CLI and listed in root
`AGENTS.md#verify` to confirm what the SDK will actually resolve.

This prints the workspace root, federation root, manifest path, every resolved
repository path, and the selected routing bundle/source-lock origins.

C1 remains fail closed when no routing bundle is configured. It does not scan
for `aoa-routing`, and the packaged source lock pins the exact `aoa-skills`
capability graph ref consumed during resolution.
