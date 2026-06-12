# AGENTS.md

Local route card for `aoa-sdk/evals/`.

This skeleton port captures future SDK eval pressure without moving SDK helper
contracts into proof authority.

`aoa-evals` owns central verdict, scoring, regression, and proof doctrine
authority. Keep typed helper truth in `aoa-sdk`; route proof adoption to
`aoa-evals`.

Validation:

```bash
python ../aoa-evals/scripts/validate_local_eval_port.py --target-root .
```
