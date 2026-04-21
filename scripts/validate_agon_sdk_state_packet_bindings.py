#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config' / 'agon_sdk_state_packet_bindings.seed.json'
REGISTRY = ROOT / 'generated' / 'agon_sdk_state_packet_bindings.min.json'
FORBIDDEN_WRITES = {'arena_session', 'verdict', 'scar', 'retention', 'rank', 'tree_of_sophia'}


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def validate() -> None:
    seed = load(CONFIG)
    reg = load(REGISTRY)
    assert seed['live_protocol'] is False
    assert seed['runtime_effect'] == 'none'
    assert reg['live_protocol'] is False
    assert reg['runtime_effect'] == 'none'
    assert reg['binding_count'] == len(seed['bindings'])
    ids = [b['binding_id'] for b in seed['bindings']]
    assert len(ids) == len(set(ids)), 'duplicate binding ids'
    for binding in seed['bindings']:
        assert binding['binding_id'].startswith('agon.sdk.'), binding['binding_id']
        assert not binding.get('writes'), f"SDK Wave IX binding must not write: {binding['binding_id']}"
        joined = ' '.join(binding.get('writes', []))
        for forbidden in FORBIDDEN_WRITES:
            assert forbidden not in joined, f"forbidden write target {forbidden} in {binding['binding_id']}"
        assert binding.get('forbidden_effects'), f"missing forbidden effects: {binding['binding_id']}"


if __name__ == '__main__':
    validate()
    print('agon sdk state packet bindings: ok')
