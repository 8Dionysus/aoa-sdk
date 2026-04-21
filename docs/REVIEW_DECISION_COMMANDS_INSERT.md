# Review Decision Commands Insert

After generating a queue:

```bash
aoa recur review decision-template .aoa/recurrence/review-queues/latest.json \
  --item-ref review-item:0001 \
  --decision defer \
  --json
```

Fallback script before CLI merge:

```bash
python scripts/review_decision_closure.py --workspace-root /srv/workspace template \
  --queue .aoa/recurrence/review-queues/latest.json \
  --item-ref review-item:0001 \
  --decision defer \
  --output .aoa/recurrence/review-decisions/decision.example.json
```

Close a queue with one or more owner decisions:

```bash
aoa recur review close .aoa/recurrence/review-queues/latest.json \
  --decision .aoa/recurrence/review-decisions/decision.example.json \
  --json
```

The close command writes a close report, decision ledger, and suppression memory. Unresolved queue items remain explicit.
