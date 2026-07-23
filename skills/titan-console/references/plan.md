# Plan mode

Prepare inspectable app-server launch data without sending, spawning, or
starting anything.

1. Require explicit Titan planning intent, workspace, output path, source refs,
   and a bounded prompt that faithfully names the requested target and action.
   Reject a request to execute; hand it to the runtime owner.
2. Run:

   `python <owner_root>/mechanics/titan/parts/operator-console-helper-contracts/scripts/titan_console.py appserver-plan --workspace <workspace> --out <plan> --prompt-file <bounded-prompt-file> [--model <model>]`

   A task-local prompt file or `/dev/stdin` is acceptable. The helper has no
   generic default prompt; do not synthesize one from Titan vocabulary.

3. Inspect every JSONL row. Record referenced workspace, command, state,
   approval, receipt, and validation surfaces.
4. Do not call the bridge `emit` command, a process launcher, or a child-agent
   interface.
5. Return the plan path and digest with
   `execution_state: not_run`, `transport_state: unsent`, actual effect limited
   to the plan file, required external gates, and next runtime-owner route.

A valid plan is data, not execution evidence.
