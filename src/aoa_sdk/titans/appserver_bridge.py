from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
import itertools, json, secrets
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

BRIDGE_TITAN_ROSTER = [
    {'name':'Atlas','role':'architect','state':'active','gate':None,'lane':'structure'},
    {'name':'Sentinel','role':'reviewer','state':'active','gate':None,'lane':'risk'},
    {'name':'Mneme','role':'memory-keeper','state':'active','gate':None,'lane':'memory'},
    {'name':'Forge','role':'coder','state':'locked','gate':'mutation','lane':'implementation'},
    {'name':'Delta','role':'evaluator','state':'locked','gate':'judgment','lane':'verdict'},
]

@dataclass
class AppServerJsonRpcBuilder:
    client_name: str = 'abyss_titan_appserver_bridge'
    client_title: str = 'Abyss Titan App-Server Bridge'
    client_version: str = '0.1.0'
    _ids: Iterable[int] = field(default_factory=lambda: itertools.count(1), repr=False)
    def _id(self) -> int: return next(self._ids)
    def initialize(self) -> Dict[str, Any]:
        return {'method':'initialize','id':0,'params':{'clientInfo':{'name':self.client_name,'title':self.client_title,'version':self.client_version}}}
    def initialized(self) -> Dict[str, Any]: return {'method':'initialized','params':{}}
    def thread_start(self, *, model='gpt-5.4', cwd: Optional[str]=None, approval_policy='unlessTrusted', sandbox='workspaceWrite') -> Dict[str, Any]:
        params={'model':model,'approvalPolicy':approval_policy,'serviceName':self.client_name}
        if cwd: params['cwd']=cwd
        params['sandboxPolicy']={'type':'readOnly'} if sandbox=='readOnly' else {'type':'workspaceWrite','writableRoots':[cwd] if cwd else [],'networkAccess':False}
        return {'method':'thread/start','id':self._id(),'params':params}
    def turn_start(self, *, thread_id: str, text: str, cwd: Optional[str]=None) -> Dict[str, Any]:
        params={'threadId':thread_id,'input':[{'type':'text','text':text}]}
        if cwd: params['cwd']=cwd
        return {'method':'turn/start','id':self._id(),'params':params}
    def turn_steer(self, *, thread_id: str, text: str) -> Dict[str, Any]:
        return {'method':'turn/steer','id':self._id(),'params':{'threadId':thread_id,'input':[{'type':'text','text':text}]}}
    def turn_interrupt(self, *, thread_id: str, turn_id: Optional[str]=None) -> Dict[str, Any]:
        params={'threadId':thread_id}
        if turn_id: params['turnId']=turn_id
        return {'method':'turn/interrupt','id':self._id(),'params':params}

def deep_get(data: Dict[str, Any], *paths: str) -> Optional[Any]:
    for path in paths:
        cur: Any = data
        ok=True
        for part in path.split('.'):
            if isinstance(cur,dict) and part in cur: cur=cur[part]
            else: ok=False; break
        if ok and cur is not None: return cur
    return None

def normalize_appserver_message(message: Dict[str, Any], *, direction='inbound') -> Dict[str, Any]:
    method=str(message.get('method') or '')
    params=message.get('params') if isinstance(message.get('params'),dict) else {}
    result=message.get('result') if isinstance(message.get('result'),dict) else {}
    lower=method.lower()
    category='other'; kind='appserver_message'; summary=method or 'jsonrpc_response'
    thread_id=deep_get(params,'threadId','thread.id') or deep_get(result,'threadId','thread.id','id')
    turn_id=deep_get(params,'turnId','turn.id') or deep_get(result,'turnId','turn.id')
    approval_id=None; approval_type=None
    if 'id' in message and 'result' in message and not method:
        category='rpc_response'; kind='rpc_response'; summary=f"response to request {message.get('id')}"
    elif 'approval' in lower or 'requestuserinput' in lower or ('tool' in lower and 'request' in lower):
        category='approval_request'; kind='approval_requested'
        approval_id=str(deep_get(params,'requestId','approvalId','id','item.id') or 'approval-'+secrets.token_hex(4))
        approval_type=str(deep_get(params,'type','approvalType','item.type') or 'approval')
        summary=str(deep_get(params,'summary','message','item.summary','item.name') or method)
    elif lower.startswith('thread/'):
        category='thread_event'; kind=lower.replace('/','_')
    elif lower.startswith('turn/'):
        category='turn_event'; kind=lower.replace('/','_')
    elif lower.startswith('item/'):
        category='item_event'; kind=lower.replace('/','_')
    return {'timestamp':utc_now(),'direction':direction,'category':category,'kind':kind,'actor':'codex-app-server' if direction=='inbound' else 'titan-bridge','summary':summary,'thread_id':thread_id,'turn_id':turn_id,'approval_id':approval_id,'approval_type':approval_type,'raw':message}

@dataclass
class TitanAppServerBridgeSession:
    session_id: str
    workspace_root: str
    status: str = 'open'
    created_at: str = field(default_factory=utc_now)
    closed_at: Optional[str] = None
    summary: Optional[str] = None
    transport: str = 'stdio'
    thread_id: Optional[str] = None
    turn_id: Optional[str] = None
    titans: List[Dict[str, Any]] = field(default_factory=lambda:[dict(x) for x in BRIDGE_TITAN_ROSTER])
    events: List[Dict[str, Any]] = field(default_factory=list)
    approvals: List[Dict[str, Any]] = field(default_factory=list)
    gates: List[Dict[str, Any]] = field(default_factory=list)
    @classmethod
    def new(cls, workspace_root: str) -> 'TitanAppServerBridgeSession':
        s=cls('titan-bridge-'+secrets.token_hex(8), str(workspace_root)); s.add_event('bridge_opened','operator',f'Titan app-server bridge opened for {workspace_root}'); return s
    @classmethod
    def from_dict(cls,data):
        return cls(data['session_id'],data['workspace_root'],data.get('status','open'),data.get('created_at') or utc_now(),data.get('closed_at'),data.get('summary'),data.get('transport','stdio'),data.get('thread_id'),data.get('turn_id'),list(data.get('titans',BRIDGE_TITAN_ROSTER)),list(data.get('events',[])),list(data.get('approvals',[])),list(data.get('gates',[])))
    @classmethod
    def load(cls,path: Path): return cls.from_dict(json.loads(path.read_text(encoding='utf-8')))
    def save(self,path: Path): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(self.to_dict(),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    def to_dict(self):
        return {'version':1,'session_id':self.session_id,'workspace_root':self.workspace_root,'status':self.status,'created_at':self.created_at,'closed_at':self.closed_at,'summary':self.summary,'transport':self.transport,'thread_id':self.thread_id,'turn_id':self.turn_id,'titans':self.titans,'events':self.events,'approvals':self.approvals,'gates':self.gates}
    def add_event(self,kind,actor,summary,payload=None): self.events.append({'timestamp':utc_now(),'kind':kind,'actor':actor,'summary':summary,'payload':payload or {}})
    def titan(self,name):
        for t in self.titans:
            if t['name'].lower()==name.lower(): return t
        raise ValueError(f'Unknown Titan: {name}')
    def unlock(self,titan_name,gate,reason):
        t=self.titan(titan_name); req=t.get('gate')
        if req is None: raise ValueError(f"{t['name']} is not gated")
        if gate != req: raise ValueError(f"{t['name']} requires gate '{req}', got '{gate}'")
        t['state']='active'; t.setdefault('notes',[]).append(f'Unlocked by {gate} gate: {reason}')
        rec={'timestamp':utc_now(),'titan':t['name'],'gate':gate,'reason':reason}; self.gates.append(rec); self.add_event('gate_unlocked',t['name'],f"{t['name']} unlocked through {gate} gate",rec)
    def ingest(self,message,direction='inbound'):
        e=normalize_appserver_message(message,direction=direction)
        if e.get('thread_id'): self.thread_id=str(e['thread_id'])
        if e.get('turn_id'): self.turn_id=str(e['turn_id'])
        if e['category']=='approval_request': self.approvals.append({'timestamp':e['timestamp'],'request_id':e['approval_id'],'approval_type':e['approval_type'],'status':'pending','summary':e['summary']})
        self.events.append(e); return e
    def decide_approval(self,request_id,decision,summary):
        if decision not in {'accept','acceptForSession','decline','cancel'}: raise ValueError('Unsupported approval decision')
        for a in self.approvals:
            if str(a.get('request_id'))==str(request_id):
                a['status']=decision; a['decided_at']=utc_now(); a['decision_summary']=summary; self.add_event('approval_decision','operator',summary,{'request_id':request_id,'decision':decision}); return
        raise ValueError(f'Unknown approval request: {request_id}')
    def close(self,summary): self.status='closed'; self.closed_at=utc_now(); self.summary=summary; self.add_event('bridge_closed','operator',summary)
    def metrics(self): return {'version':1,'session_id':self.session_id,'status':self.status,'thread_bound':bool(self.thread_id),'turn_bound':bool(self.turn_id),'events':len(self.events),'approvals_total':len(self.approvals),'approvals_pending':sum(1 for a in self.approvals if a.get('status')=='pending'),'gates_opened':len(self.gates),'forge_active':self.titan('Forge')['state']=='active','delta_active':self.titan('Delta')['state']=='active'}
    def validate(self):
        errors=[]; names={t['name'] for t in self.titans}
        for req in ['Atlas','Sentinel','Mneme','Forge','Delta']:
            if req not in names: errors.append(f'missing titan {req}')
        if self.titan('Forge').get('state')=='active' and not any(g.get('titan')=='Forge' and g.get('gate')=='mutation' for g in self.gates): errors.append('Forge active without mutation gate')
        if self.titan('Delta').get('state')=='active' and not any(g.get('titan')=='Delta' and g.get('gate')=='judgment' for g in self.gates): errors.append('Delta active without judgment gate')
        return errors
    def render_text(self):
        lines=[f'Titan App-Server Bridge: {self.session_id}',f'Workspace: {self.workspace_root}',f'Status: {self.status}',f'Thread: {self.thread_id or "-"}',f'Turn: {self.turn_id or "-"}','','Roster:']
        for t in self.titans: lines.append(f"- {t['name']:<8} {t['role']:<14} {t['state']}"+(f" gate={t.get('gate')}" if t.get('gate') else ''))
        lines.append(f"Approvals pending: {self.metrics()['approvals_pending']}"); return '\n'.join(lines)
