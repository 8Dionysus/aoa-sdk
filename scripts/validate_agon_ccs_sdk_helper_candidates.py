#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config' / 'agon_ccs_sdk_helper_candidates.seed.json'
REGISTRY = ROOT / 'generated' / 'agon_ccs_sdk_helper_candidates.min.json'
REQUIRED_HELPERS = {
    'agon.sdk.ccs.load_law_registry_candidate',
    'agon.sdk.ccs.preview_contradiction_status_candidate',
    'agon.sdk.ccs.preview_closure_eligibility_candidate',
    'agon.sdk.ccs.draft_summon_intent_review_candidate',
}


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def validate() -> None:
    seed = load(CONFIG)
    reg = load(REGISTRY)
    assert seed['live_protocol'] is False
    assert seed['runtime_effect'] == 'none'
    assert reg['live_protocol'] is False
    assert reg['runtime_effect'] == 'none'
    assert reg['helper_count'] == len(seed['helper_candidates'])
    ids = {h['helper_id'] for h in seed['helper_candidates']}
    assert REQUIRED_HELPERS <= ids, f'missing helpers: {sorted(REQUIRED_HELPERS - ids)}'
    for h in seed['helper_candidates']:
        forbidden = set(h['forbidden_effects'])
        assert forbidden, h['helper_id']
        assert 'candidate' in h['helper_id'] or 'candidate' in h['output_candidate'], h['helper_id']
        assert 'runtime' not in h['helper_id'], h['helper_id']
    stop_text = json.dumps(seed['stop_lines'])
    assert 'no_cli_activation' in stop_text
    assert 'no_live_arena_session' in stop_text
    assert 'no_verdict_authority' in stop_text


if __name__ == '__main__':
    validate()
    print('agon CCS SDK helper candidates: ok')
