#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
try:
    from aoa_sdk.titans.appserver_bridge import AppServerJsonRpcBuilder, TitanAppServerBridgeSession
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
    from aoa_sdk.titans.appserver_bridge import AppServerJsonRpcBuilder, TitanAppServerBridgeSession

def load(args):
    p=Path(args.session); return TitanAppServerBridgeSession.load(p), p

def iter_messages(args):
    if getattr(args,'message',None): yield json.loads(args.message)
    if getattr(args,'file',None):
        for line in Path(args.file).read_text(encoding='utf-8').splitlines():
            if line.strip(): yield json.loads(line)

def cmd_init(a):
    s=TitanAppServerBridgeSession.new(a.workspace); s.save(Path(a.out)); print(a.out); return 0

def cmd_render(a): s,_=load(a); print(s.render_text()); return 0

def cmd_emit(a):
    b=AppServerJsonRpcBuilder()
    if a.kind=='initialize': msgs=[b.initialize(),b.initialized()]
    elif a.kind=='thread-start': msgs=[b.thread_start(model=a.model,cwd=a.workspace,approval_policy=a.approval_policy,sandbox=a.sandbox)]
    elif a.kind=='turn-start': msgs=[b.turn_start(thread_id=a.thread_id,text=a.text or 'Render Titan bridge status.',cwd=a.workspace)]
    elif a.kind=='turn-steer': msgs=[b.turn_steer(thread_id=a.thread_id,text=a.text or 'Steer Titan bridge.')]
    else: raise SystemExit('unknown emit kind')
    for m in msgs: print(json.dumps(m,ensure_ascii=False))
    return 0

def cmd_replay(a):
    s,p=load(a); count=0
    for msg in iter_messages(a): s.ingest(msg); count+=1
    s.save(p); print(f'replayed {count} message(s)'); return 0

def cmd_gate(a):
    s,p=load(a); s.unlock(a.titan,a.gate,a.reason); s.save(p); print(f'{a.titan} unlocked through {a.gate}'); return 0

def cmd_approval_decision(a):
    s,p=load(a); s.decide_approval(a.request_id,a.decision,a.summary); s.save(p); print('approval decision recorded'); return 0

def cmd_metrics(a): s,_=load(a); print(json.dumps(s.metrics(),indent=2,ensure_ascii=False)); return 0

def cmd_validate(a):
    s,_=load(a); errors=s.validate()
    if errors:
        for e in errors: print(e,file=sys.stderr)
        return 1
    print('valid'); return 0

def cmd_close(a): s,p=load(a); s.close(a.summary); s.save(p); print(f'closed: {p}'); return 0

def parser():
    p=argparse.ArgumentParser(description='Titan app-server bridge seed CLI'); sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('init'); q.add_argument('--workspace',required=True); q.add_argument('--out',required=True); q.set_defaults(func=cmd_init)
    q=sub.add_parser('render'); q.add_argument('--session',required=True); q.set_defaults(func=cmd_render)
    q=sub.add_parser('emit'); q.add_argument('kind',choices=['initialize','thread-start','turn-start','turn-steer']); q.add_argument('--workspace'); q.add_argument('--model',default='gpt-5.4'); q.add_argument('--approval-policy',default='unlessTrusted'); q.add_argument('--sandbox',default='workspaceWrite',choices=['readOnly','workspaceWrite']); q.add_argument('--thread-id'); q.add_argument('--text'); q.set_defaults(func=cmd_emit)
    q=sub.add_parser('replay'); q.add_argument('--session',required=True); q.add_argument('--file',required=True); q.add_argument('--message'); q.set_defaults(func=cmd_replay)
    q=sub.add_parser('gate'); q.add_argument('--session',required=True); q.add_argument('--titan',required=True,choices=['Atlas','Sentinel','Mneme','Forge','Delta']); q.add_argument('--gate',required=True,choices=['mutation','judgment']); q.add_argument('--reason',required=True); q.set_defaults(func=cmd_gate)
    q=sub.add_parser('approval-decision'); q.add_argument('--session',required=True); q.add_argument('--request-id',required=True); q.add_argument('--decision',required=True,choices=['accept','acceptForSession','decline','cancel']); q.add_argument('--summary',required=True); q.set_defaults(func=cmd_approval_decision)
    q=sub.add_parser('metrics'); q.add_argument('--session',required=True); q.set_defaults(func=cmd_metrics)
    q=sub.add_parser('validate'); q.add_argument('--session',required=True); q.set_defaults(func=cmd_validate)
    q=sub.add_parser('close'); q.add_argument('--session',required=True); q.add_argument('--summary',required=True); q.set_defaults(func=cmd_close)
    return p

def main(argv=None):
    a=parser().parse_args(argv); return a.func(a)
if __name__=='__main__': raise SystemExit(main())
