# Titan Session Ingress

## Purpose

Define the minimum structured ingress packet for a Titan-backed Codex session.

## Ingress packet

```json
{
  "version": 1,
  "session_kind": "titan_service_cohort",
  "summon_prompt_ref": "8Dionysus/.codex/prompts/titan-summon.service-cohort.v0.md",
  "default_roster": ["Atlas", "Sentinel", "Mneme"],
  "conditional_roster": {
    "Forge": "mutation_intent",
    "Delta": "judgment_intent"
  },
  "boundaries": ["no_hidden_arena", "no_silent_mutation", "no_proof_sovereignty"]
}
```

## Lifecycle

1. Operator summons Atlas, Sentinel, and Mneme.
2. Session records route, risk, and memory posture.
3. Forge can be summoned only with mutation packet.
4. Delta can be summoned only with judgment packet.
5. Closeout produces a receipt candidate.

## Ownership

This SDK surface describes packet shape and control-plane ingress. It does not own role meaning, Codex projection files, or seed garden canon.
