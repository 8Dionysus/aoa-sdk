# Optional CLI Insert

Add an `agents` subgroup under `aoa recur` only with read-only commands:

```python
agents = recur_subparsers.add_parser("agents")
agents_sub = agents.add_subparsers(dest="agents_command")

# readiness
# boundary-check
# projection-candidates
```

Do not add:

```text
spawn
run
summon
open-arena
```

Wire commands to:

```python
from aoa_sdk.recurrence.agent_readiness import (
    build_recursor_readiness_projection,
    build_recursor_boundary_scan_report,
    build_recursor_projection_candidates,
)
```
