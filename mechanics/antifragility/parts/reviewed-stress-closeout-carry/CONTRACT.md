# Reviewed Stress Closeout Carry Contract

## Allowed Outputs

- Reviewed closeout manifest with stress evidence refs.
- Audit-only carry when owner receipts are absent.
- Explicit blocked items and next-step brief.

## Stop-Lines

- Do not auto-promote stress bundles into memo.
- Do not auto-publish stats claims.
- Do not auto-trigger runtime repair.
- Do not treat routing hints as source truth.

## Owner Split

The SDK can preserve a reviewed carry packet. Owner repositories, `aoa-evals`,
`aoa-memo`, stats, routing, and runtime layers keep their own authority.

## External Source Tokens

Example refs may preserve source-owned stress receipt or routing hint tokens
whose historical handle contains `fallback`, such as
`retrieval-only-fallback`.

Those strings are evidence handles owned by the source or routing repository.
They are not SDK-owned active route names. New SDK-owned stress carry fields,
examples, or routes should use explicit degraded, recovery, source-first, or
alternate-path vocabulary.
