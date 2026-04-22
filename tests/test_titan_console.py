from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "titan_console.py"
def run(*args, check=True): return subprocess.run([sys.executable, str(SCRIPT), *args], text=True, capture_output=True, check=check)
def test_new_validate_and_gates(tmp_path):
    state=tmp_path/'state.json'; run('new','--workspace',str(tmp_path),'--operator','tester','--out',str(state)); run('validate','--state',str(state))
    bad=run('gate','--state',str(state),'--titan','Forge','--gate','judgment','--reason','wrong',check=False); assert bad.returncode!=0
    run('gate','--state',str(state),'--titan','Forge','--gate','mutation','--reason','bounded patch')
    run('gate','--state',str(state),'--titan','Delta','--gate','judgment','--reason','regression verdict')
    run('validate','--state',str(state)); data=json.loads(state.read_text()); assert data['titans']['Forge']['active'] is True and data['titans']['Delta']['active'] is True
def test_appserver_plan(tmp_path):
    prompt=tmp_path/'prompt.md'; prompt.write_text('Summon Atlas, Sentinel, and Mneme.', encoding='utf-8'); out=tmp_path/'plan.jsonl'
    run('appserver-plan','--workspace',str(tmp_path),'--prompt-file',str(prompt),'--out',str(out)); lines=[json.loads(x) for x in out.read_text().splitlines()]
    assert [x['method'] for x in lines] == ['initialize','initialized','thread/start','turn/start']
