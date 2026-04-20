# Recurrence Wiring Plan

This note defines the reviewable wiring plan for the planted recurrence control-plane.

## Core rule

The plan tells you where recurrence may be wired. It does not wire the system by itself.

## Scope

The plan may emit snippet targets for:

- Codex `SessionStart`
- Codex `UserPromptSubmit`
- Codex `Stop`
- git `pre-commit`
- git `pre-push`
- CI

## Boundary

A wiring plan is a map, not a hidden installer. Keep every copied snippet reviewable and source-owned by the repo that adopts it.
