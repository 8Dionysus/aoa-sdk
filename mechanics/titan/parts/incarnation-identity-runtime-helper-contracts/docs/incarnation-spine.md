# Titan Incarnation Spine

The incarnation spine carries Titan bearer identity through runtime records.

Every active or locked Titan in a session must carry:

```text
session_id
incarnation_id
bearer_id
titan_name
role_key
role_class
state
thread_id / turn_id when available
source_ref when available
```

Forge and Delta are locked until gates provide structured payloads.
