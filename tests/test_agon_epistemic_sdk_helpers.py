from __future__ import annotations
import json, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]

def test_generated_registry_shape():
    reg = json.loads((ROOT / 'generated/agon_epistemic_sdk_helpers.min.json').read_text(encoding='utf-8'))
    assert reg['wave'] == 'XV'
    assert reg['runtime_posture'] in ('candidate_only', 'pre_protocol_candidate_only')
    assert reg['count'] == 7
    assert len(reg['helpers']) == 7
    for item in reg['helpers']:
        assert item['live_protocol'] is False
        assert 'auto_doctrine_rewrite' in item.get('forbidden_effects', [])

def test_builder_check_and_validator():
    assert subprocess.run([sys.executable, str(ROOT / 'scripts/build_agon_epistemic_sdk_helpers.py'), '--check'], cwd=ROOT).returncode == 0
    assert subprocess.run([sys.executable, str(ROOT / 'scripts/validate_agon_epistemic_sdk_helpers.py')], cwd=ROOT).returncode == 0
