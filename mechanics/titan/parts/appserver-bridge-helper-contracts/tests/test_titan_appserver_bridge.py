from aoa_sdk.titans.appserver_bridge import (
    AppServerJsonRpcBuilder,
    BRIDGE_TITAN_ROSTER,
    TitanAppServerBridgeSession,
)


def test_builder_and_session():
    b = AppServerJsonRpcBuilder()
    assert b.initialize()["method"] == "initialize"
    assert (
        b.thread_start(cwd="/srv/AbyssOS")["params"]["sandboxPolicy"]["networkAccess"] is False
    )
    s = TitanAppServerBridgeSession.new("/srv/AbyssOS")
    s.ingest({"jsonrpc": "2.0", "id": 1, "result": {"threadId": "t1"}})
    s.ingest({"method": "turn/started", "params": {"threadId": "t1", "turnId": "u1"}})
    s.ingest(
        {
            "method": "item/approval/requested",
            "params": {"requestId": "r1", "type": "command", "summary": "run"},
        }
    )
    assert s.metrics()["approvals_pending"] == 1
    s.decide_approval("r1", "decline", "no")
    assert s.metrics()["approvals_pending"] == 0
    try:
        s.unlock("Forge", "judgment", "wrong")
    except ValueError as e:
        assert "requires gate 'mutation'" in str(e)
    else:
        raise AssertionError("wrong gate accepted")
    s.unlock("Forge", "mutation", "ok")
    s.unlock("Delta", "judgment", "ok")
    assert not s.validate()


def test_from_dict_copies_default_titan_roster() -> None:
    first = TitanAppServerBridgeSession.from_dict(
        {"session_id": "s1", "workspace_root": "/srv/AbyssOS"}
    )
    first.unlock("Forge", "mutation", "ok")

    second = TitanAppServerBridgeSession.from_dict(
        {"session_id": "s2", "workspace_root": "/srv/AbyssOS"}
    )

    assert next(titan for titan in BRIDGE_TITAN_ROSTER if titan["name"] == "Forge")["state"] == "locked"
    assert next(titan for titan in second.titans if titan["name"] == "Forge")["state"] == "locked"


def test_validate_reports_missing_titans_without_crashing() -> None:
    session = TitanAppServerBridgeSession.from_dict(
        {
            "session_id": "s1",
            "workspace_root": "/srv/AbyssOS",
            "titans": [{"name": "Atlas", "role": "architect", "state": "active"}],
        }
    )

    errors = session.validate()

    assert "missing titan Forge" in errors
    assert "missing titan Delta" in errors
