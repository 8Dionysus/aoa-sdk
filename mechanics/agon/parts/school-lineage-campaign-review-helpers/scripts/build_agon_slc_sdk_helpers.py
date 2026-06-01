#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'config/agon_slc_sdk_helpers.seed.json'
OUT = ROOT / 'generated/agon_slc_sdk_helpers.min.json'
ITEM_KEY = 'sdk_helpers'
REGISTRY_ID = 'agon.slc_sdk_helpers.registry.v1'
SURFACE_ROLE = 'school_lineage_campaign_review_helpers'
REVIEW_DOMAIN = 'schools_lineages_campaigns'

def digest_obj(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def build():
    data = json.loads(SRC.read_text(encoding='utf-8'))
    items = data.get(ITEM_KEY, [])
    return {
        'registry_id': data.get('registry_id', REGISTRY_ID),
        'surface_role': data.get('surface_role', SURFACE_ROLE),
        'review_domain': data.get('review_domain', REVIEW_DOMAIN),
        'runtime_posture': data.get('runtime_posture', 'candidate_only'),
        'count': len(items),
        ITEM_KEY: items,
        'digest': digest_obj(items),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    reg = build()
    txt = json.dumps(reg, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding='utf-8') != txt:
            print('generated registry drift: run builder without --check', file=sys.stderr)
            return 1
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(txt, encoding='utf-8')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
