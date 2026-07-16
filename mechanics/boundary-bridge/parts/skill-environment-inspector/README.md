# Skill Environment Inspector

## Role

`skill-environment-inspector` exposes a passive typed view of owner-authored
skill bundles, install profiles, portable exports, MCP dependencies, exact
capability nodes, and the distinct roots visible to one repository.

It answers what exists, where it came from, whether an admitted copy matches
its owner source, and which duplicate scopes are present. It does not decide
which capability applies to a task.

## Input

- current `aoa-skills` catalog, resolved profiles, export map, MCP dependency
  manifest, and capability graph;
- an explicit repository root;
- an optional host-selected user skill root;
- an admitted repository `skills/port.manifest.json`, when that repository owns
  home skills.

## Output

- exact typed owner surfaces;
- exact-node capability neighborhoods;
- separate source-export, user, repository, unowned-repository, and legacy
  workspace observations;
- current, drift, missing, unmanaged, duplicate, and admission warnings.

## Owner

`aoa-sdk` owns the read model and scope-preserving inspection. `aoa-skills`
owns shared bundle meaning and install profiles. Each repository owns its
admitted home skill source and projection. The host owns user installation and
runtime selection; KAG and the executing agent own retrieval and task-local
composition.

## Next Route

Use the exact owner profile for user installation. Use a repository's own port
builder for repository projection. Route semantic retrieval to KAG and runtime
execution to the host.
