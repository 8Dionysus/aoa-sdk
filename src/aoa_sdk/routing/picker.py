from __future__ import annotations

class RoutingAPI:
    def __init__(self, workspace) -> None:
        self.workspace = workspace

    def pick(self, *, kind: str, query: str) -> dict:
        return {"kind": kind, "query": query, "status": "stub"}

    def inspect(self, *, kind: str, id_or_name: str) -> dict:
        return {"kind": kind, "id_or_name": id_or_name, "status": "stub"}

    def expand(self, *, kind: str, id_or_name: str, sections: list[str] | None = None) -> dict:
        return {
            "kind": kind,
            "id_or_name": id_or_name,
            "sections": sections or [],
            "status": "stub",
        }
