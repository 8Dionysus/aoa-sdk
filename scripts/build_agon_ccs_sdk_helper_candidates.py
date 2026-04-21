#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config' / 'agon_ccs_sdk_helper_candidates.seed.json'
OUT = ROOT / 'generated' / 'agon_ccs_sdk_helper_candidates.min.json'


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def build(seed: dict) -> dict:
    return {
        'registry_id': seed['registry_id'],
        'version': seed['version'],
        'wave': seed['wave'],
        'home_repo': seed['home_repo'],
        'status': seed['status'],
        'live_protocol': False,
        'runtime_effect': 'none',
        'center_registry': seed['center_registry'],
        'helper_count': len(seed['helper_candidates']),
        'helper_ids': [h['helper_id'] for h in seed['helper_candidates']],
        'stop_lines': seed['stop_lines'],
        'helper_candidates': seed['helper_candidates'],
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
            raise SystemExit('generated/agon_ccs_sdk_helper_candidates.min.json is out of date')
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
