# Return Re-entry Seam

Return is the concrete re-entry seam for recurrence.

Wave one keeps return small and reviewed:

- take a propagation plan that has already been inspected
- preserve the smallest owner-boundary target for each direct component
- preserve the first rollback anchor for bounded recovery
- preserve downstream route, summary, regrounding, or playbook targets only as follow-through pointers
- keep unresolved items visible

## Output packet

`aoa recur handoff ...` emits `aoa_return_handoff_v1`.

The packet keeps:

- reviewed status
- surviving fields that should not be lost
- owner-facing target surfaces
- unresolved edges and open questions

## Non-goals

Wave one return does not:

- reopen mutation automatically
- decide retry budgets
- assign agents
- hide unresolved downstream seams
- replace owner refresh laws or playbook doctrine
