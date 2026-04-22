from __future__ import annotations

from aoa_sdk.titans.memory_loom import new_index, make_record, add_record, recall, redact, digest, validate_index


def test_memory_loom_candidate_recall_and_redaction():
    idx = new_index('/srv', 'Dionysus')
    rec = make_record(titan='Mneme', kind='note', text='Atlas mapped the memory route.', source_kind='test', tags=['memory'])
    add_record(idx, rec)
    hits = recall(idx, 'Atlas memory')
    assert hits
    assert hits[0]['authority_note'] == 'candidate_only'
    redact(idx, rec['record_id'], 'mask', 'test mask')
    assert idx['records'][0]['status'] == 'redacted'
    d = digest(idx)
    assert d['record_count'] == 1
    assert not validate_index(idx)


def test_forge_and_delta_gate_metadata_allowed_only_when_expected():
    idx = new_index('/srv', 'Dionysus')
    forge = make_record(titan='Forge', kind='mutation_note', text='Patch approved.', source_kind='test', lineage={'gate': 'mutation'})
    delta = make_record(titan='Delta', kind='verdict_note', text='Judgment approved.', source_kind='test', lineage={'gate': 'judgment'})
    add_record(idx, forge)
    add_record(idx, delta)
    assert not validate_index(idx)
