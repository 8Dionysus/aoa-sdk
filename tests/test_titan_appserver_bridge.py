from aoa_sdk.titans.appserver_bridge import AppServerJsonRpcBuilder, TitanAppServerBridgeSession

def test_builder_and_session():
    b=AppServerJsonRpcBuilder(); assert b.initialize()['method']=='initialize'
    assert b.thread_start(cwd='/srv')['params']['sandboxPolicy']['networkAccess'] is False
    s=TitanAppServerBridgeSession.new('/srv')
    s.ingest({'jsonrpc':'2.0','id':1,'result':{'threadId':'t1'}})
    s.ingest({'method':'turn/started','params':{'threadId':'t1','turnId':'u1'}})
    s.ingest({'method':'item/approval/requested','params':{'requestId':'r1','type':'command','summary':'run'}})
    assert s.metrics()['approvals_pending']==1
    s.decide_approval('r1','decline','no')
    assert s.metrics()['approvals_pending']==0
    try: s.unlock('Forge','judgment','wrong')
    except ValueError as e: assert "requires gate 'mutation'" in str(e)
    else: raise AssertionError('wrong gate accepted')
    s.unlock('Forge','mutation','ok'); s.unlock('Delta','judgment','ok')
    assert not s.validate()
