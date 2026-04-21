#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config' / 'agon_sdk_state_packet_bindings.seed.json'
OUT = ROOT / 'generated' / 'agon_sdk_state_packet_bindings.min.json'


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def build(seed: dict) -> dict:
    return {
        'registry_id': seed['registry_id'],
        'version': seed['version'],
        'status': seed['status'],
        'wave': seed['wave'],
        'home_repo': seed['home_repo'],
        'live_protocol': False,
        'runtime_effect': 'none',
        'binding_count': len(seed['bindings']),
        'binding_ids': [b['binding_id'] for b in seed['bindings']],
        'bindings': [
            {
                'binding_id': b['binding_id'],
                'helper_kind': b['helper_kind'],
                'reads': b['reads'],
                'writes': b['writes'],
                'live_protocol': False,
                'runtime_effect': 'none',
            }
            for b in seed['bindings']
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    expected = build(load_json(CONFIG))
    text = json.dumps(expected, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
    if args.check:
        if not OUT.exists():
            raise SystemExit(f'missing generated registry: {OUT}')
        if OUT.read_text(encoding='utf-8') != text:
            raise SystemExit('generated/agon_sdk_state_packet_bindings.min.json is out of date')
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
