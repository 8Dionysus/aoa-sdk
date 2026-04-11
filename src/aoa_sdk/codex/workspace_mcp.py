from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[import-not-found, no-redef]

from ..workspace.config import load_workspace_config
from ..workspace.discovery import Workspace
from ..workspace.roots import KNOWN_REPOS

LOGGER = logging.getLogger(__name__)

MARKER_FILE = "AOA_WORKSPACE_ROOT"
CONTROL_PLANE_RELATIVE_PATH = "generated/workspace_control_plane.min.json"
PROJECT_CODEX_CONFIG_RELATIVE_PATH = ".codex/config.toml"
PROJECT_HOOKS_RELATIVE_PATH = ".codex/hooks.json"

REPO_HINTS: dict[str, dict[str, Any]] = {
    "8Dionysus": {
        "role": "profile-route-map",
        "surface": "public profile, route map, and glossary surfaces",
        "entry_candidates": ["README.md", "GLOSSARY.md"],
    },
    "aoa-sdk": {
        "role": "control-plane",
        "surface": "workspace discovery, compatibility posture, and bounded control-plane helpers",
        "entry_candidates": [
            CONTROL_PLANE_RELATIVE_PATH,
            "docs/workspace-layout.md",
            ".aoa/workspace.toml",
        ],
    },
    "aoa-routing": {
        "role": "routing-canon",
        "surface": "federation routing hints and owner-layer shortlist surfaces",
        "entry_candidates": ["README.md", "generated/federation_entrypoints.min.json"],
    },
    "aoa-skills": {
        "role": "workflow-canon",
        "surface": "canonical skills, exports, and runtime discovery indexes",
        "entry_candidates": ["SKILL_INDEX.md", "generated/runtime_discovery_index.min.json", "skills"],
    },
    "aoa-agents": {
        "role": "role-canon",
        "surface": "agent profiles, role posture, and orchestration seams",
        "entry_candidates": ["profiles", "README.md"],
    },
    "aoa-playbooks": {
        "role": "launcher-canon",
        "surface": "playbook launchers and reviewed run surfaces",
        "entry_candidates": ["README.md", "generated/playbook_registry.min.json"],
    },
    "aoa-memo": {
        "role": "memory-derived",
        "surface": "memory catalogs and writeback governance surfaces",
        "entry_candidates": ["README.md", "generated/memory_catalog.min.json"],
    },
    "aoa-evals": {
        "role": "evaluation-canon",
        "surface": "eval bundles, scorers, and report surfaces",
        "entry_candidates": ["README.md", "generated/eval_catalog.min.json"],
    },
    "aoa-kag": {
        "role": "retrieval-derived",
        "surface": "KAG registries and retrieval-oriented derived bundles",
        "entry_candidates": ["README.md", "generated/kag_registry.min.json"],
    },
    "aoa-stats": {
        "role": "derived-observability",
        "surface": "summary catalogs and derived observability views",
        "entry_candidates": ["generated/summary_surface_catalog.min.json", "README.md"],
        "launcher": "scripts/aoa_stats_mcp_server.py",
    },
    "aoa-techniques": {
        "role": "technique-canon",
        "surface": "technique references and promotion-readiness surfaces",
        "entry_candidates": ["README.md", "docs/README.md"],
    },
    "Agents-of-Abyss": {
        "role": "federation-center",
        "surface": "ecosystem rules, constitutional center, and method spine",
        "entry_candidates": ["ECOSYSTEM_MAP.md", "README.md", "docs/README.md"],
    },
    "Tree-of-Sophia": {
        "role": "tree-canon",
        "surface": "tree, lineage, and synthesis structures",
        "entry_candidates": ["README.md", "docs/AGENTS.md"],
    },
    "Dionysus": {
        "role": "seed-garden",
        "surface": "seed staging, route maps, and planting follow-through",
        "entry_candidates": ["generated/seed_route_map.min.json", "seed-registry.yaml", "README.md"],
        "launcher": "scripts/dionysus_mcp_server.py",
    },
    "abyss-stack": {
        "role": "runtime-substrate-source",
        "surface": "runtime substrate source checkout and diagnostic surfaces",
        "entry_candidates": ["generated/diagnostic_surface_catalog.min.json", "README.md"],
    },
}

SURFACE_CROSSWALK: list[dict[str, str]] = [
    {
        "need": "repo law, conventions, and persistent posture",
        "primary_surface": "AGENTS.md",
        "fallback": "repo README.md and owner source files",
        "notes": "use workspace-root guidance first, then the nearest repo-local guidance",
    },
    {
        "need": "repeatable bounded workflow",
        "primary_surface": "skills",
        "fallback": "repo-local source files",
        "notes": "skills carry workflow shape; owner repos keep semantic authority",
    },
    {
        "need": "role specialization or delegation posture",
        "primary_surface": "subagents",
        "fallback": "skills",
        "notes": "role posture is not the same thing as workflow canon",
    },
    {
        "need": "cross-repo orientation and next-surface choice",
        "primary_surface": "project-level MCP",
        "fallback": "workspace AGENTS.md",
        "notes": "use the workspace MCP to orient, not to replace repo-local truth",
    },
    {
        "need": "derived metrics, receipts overview, or summary views",
        "primary_surface": "repo-local MCP: aoa-stats",
        "fallback": "owner repo source files",
        "notes": "aoa-stats remains derived-only when semantics matter",
    },
    {
        "need": "seed staging, route map, and planting follow-through",
        "primary_surface": "repo-local MCP: dionysus",
        "fallback": "owner repo source files",
        "notes": "staging and route maps do not outrank planted owner objects",
    },
]


@dataclass(slots=True)
class AoAWorkspaceMCPState:
    start_path: Path
    workspace: Workspace

    @classmethod
    def discover(cls, start: str | Path | None = None) -> "AoAWorkspaceMCPState":
        start_path = Path(start or Path.cwd()).expanduser().resolve()
        return cls(start_path=start_path, workspace=Workspace.discover(start_path))

    @property
    def workspace_root(self) -> Path:
        return self.workspace.federation_root

    def build_workspace_resolution(self) -> dict[str, Any]:
        repos: dict[str, dict[str, str | None]] = {}
        for repo in KNOWN_REPOS:
            path = self.workspace.repo_roots.get(repo)
            repos[repo] = {
                "path": str(path) if path is not None else None,
                "origin": self.workspace.repo_origins.get(repo),
            }
        return {
            "root": str(self.workspace.root),
            "federation_root": str(self.workspace.federation_root),
            "federation_root_source": self.workspace.federation_root_source,
            "manifest": str(self.workspace.manifest_path) if self.workspace.manifest_path else None,
            "repos": repos,
        }

    def build_health(self) -> dict[str, Any]:
        workspace_marker = self.workspace_root / MARKER_FILE
        control_plane_surface = self.workspace.surface_path("aoa-sdk", CONTROL_PLANE_RELATIVE_PATH)
        project_codex = self._project_codex_details()

        repo_rows: dict[str, Any] = {}
        for repo in KNOWN_REPOS:
            repo_root = self.workspace.repo_roots.get(repo)
            repo_rows[repo] = {
                "present": repo_root is not None,
                "path": str(repo_root) if repo_root is not None else None,
                "origin": self.workspace.repo_origins.get(repo),
                "entrypoint_count": len(self._existing_entrypoints(repo)),
            }

        return {
            "workspace_root": str(self.workspace_root),
            "control_plane_root": str(self.workspace.root),
            "workspace_manifest": {
                "path": str(self.workspace.manifest_path) if self.workspace.manifest_path else None,
                "exists": self.workspace.manifest_path is not None,
                "federation_root_source": self.workspace.federation_root_source,
            },
            "workspace_marker": {
                "path": str(workspace_marker),
                "present": workspace_marker.exists(),
            },
            "project_codex": project_codex,
            "control_plane_surface": {
                "path": str(control_plane_surface),
                "exists": control_plane_surface.exists(),
            },
            "available_repo_count": sum(1 for repo in KNOWN_REPOS if self.workspace.has_repo(repo)),
            "known_repo_count": len(KNOWN_REPOS),
            "repos": repo_rows,
        }

    def build_repo_map(self) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        config = load_workspace_config(self.workspace.root)
        for repo in KNOWN_REPOS:
            hint = REPO_HINTS.get(repo, {})
            repo_root = self.workspace.repo_roots.get(repo)
            repo_config = config.repo_configs.get(repo)
            manifest_role = repo_config.role if repo_config is not None else None
            rows.append(
                {
                    "repo": repo,
                    "present": repo_root is not None,
                    "path": str(repo_root) if repo_root is not None else None,
                    "origin": self.workspace.repo_origins.get(repo),
                    "manifest_role": manifest_role,
                    "role": hint.get("role") or manifest_role or "repo-local-surface",
                    "surface": hint.get("surface") or "owner-local source and generated surfaces",
                    "preferred_entrypoints": self._existing_entrypoints(repo),
                }
            )
        return {
            "workspace_root": str(self.workspace_root),
            "repos": rows,
        }

    def build_surface_crosswalk(self) -> dict[str, Any]:
        return {
            "workspace_root": str(self.workspace_root),
            "crosswalk": SURFACE_CROSSWALK,
        }

    def build_runtime_entrypoints(self) -> dict[str, Any]:
        entries = [
            {
                "name": "workspace_marker",
                "scope": "workspace",
                "path": MARKER_FILE,
                "need": "anchor sibling-workspace project detection",
            },
            {
                "name": "project_codex_config",
                "scope": "workspace",
                "path": PROJECT_CODEX_CONFIG_RELATIVE_PATH,
                "need": "project-level Codex wiring and MCP server declarations",
            },
            {
                "name": "workspace_control_plane",
                "scope": "aoa-sdk",
                "path": CONTROL_PLANE_RELATIVE_PATH,
                "need": "compact control-plane capsule for workspace posture",
            },
            {
                "name": "ecosystem_map",
                "scope": "Agents-of-Abyss",
                "path": "ECOSYSTEM_MAP.md",
                "need": "federation-center map and constitutional entrypoint",
            },
            {
                "name": "skill_index",
                "scope": "aoa-skills",
                "path": "SKILL_INDEX.md",
                "need": "canonical skill catalog entrypoint",
            },
            {
                "name": "skill_runtime_discovery",
                "scope": "aoa-skills",
                "path": "generated/runtime_discovery_index.min.json",
                "need": "generated skill discovery index",
            },
            {
                "name": "agent_profiles",
                "scope": "aoa-agents",
                "path": "profiles",
                "need": "role profiles for future projection",
            },
            {
                "name": "stats_catalog",
                "scope": "aoa-stats",
                "path": "generated/summary_surface_catalog.min.json",
                "need": "derived observability catalog",
            },
            {
                "name": "seed_route_map",
                "scope": "Dionysus",
                "path": "generated/seed_route_map.min.json",
                "need": "seed route orientation",
            },
            {
                "name": "abyss_stack_diagnostic_catalog",
                "scope": "abyss-stack",
                "path": "generated/diagnostic_surface_catalog.min.json",
                "need": "runtime-substrate diagnostic summary",
            },
        ]
        return {
            "workspace_root": str(self.workspace_root),
            "entrypoints": [self._resolve_entrypoint(entry) for entry in entries],
        }

    def load_skill_index(self, mode: str = "preview", limit: int = 80) -> dict[str, Any]:
        return self._text_payload("aoa-skills", "SKILL_INDEX.md", mode=mode, limit=limit, label="skill_index")

    def load_agent_profiles(self) -> dict[str, Any]:
        repo_root = self.workspace.repo_roots.get("aoa-agents")
        profiles_dir = repo_root / "profiles" if repo_root is not None else None
        profiles: list[dict[str, Any]] = []
        if profiles_dir is not None and profiles_dir.exists():
            for path in sorted(profiles_dir.glob("*.profile.json")):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    data = {}
                profiles.append(
                    {
                        "file": path.name,
                        "name": data.get("name"),
                        "description": data.get("description"),
                        "model": data.get("model"),
                        "role": data.get("role"),
                    }
                )
        return {
            "workspace_root": str(self.workspace_root),
            "profile_count": len(profiles),
            "profiles": profiles,
        }

    def _project_codex_details(self) -> dict[str, Any]:
        config_path = self.workspace_root / PROJECT_CODEX_CONFIG_RELATIVE_PATH
        hooks_path = self.workspace_root / PROJECT_HOOKS_RELATIVE_PATH
        config, config_error = self._load_toml(config_path)

        markers: list[str] = []
        mcp_servers: dict[str, Any] = {}
        if isinstance(config, dict):
            raw_markers = config.get("project_root_markers")
            if isinstance(raw_markers, list):
                markers = [item for item in raw_markers if isinstance(item, str)]
            raw_servers = config.get("mcp_servers")
            if isinstance(raw_servers, dict):
                mcp_servers = raw_servers

        server_config = mcp_servers.get("aoa_workspace") if isinstance(mcp_servers.get("aoa_workspace"), dict) else None

        return {
            "config_path": str(config_path),
            "config_exists": config_path.exists(),
            "config_parse_error": config_error,
            "hooks_path": str(hooks_path),
            "hooks_exists": hooks_path.exists(),
            "project_root_markers": markers,
            "aoa_workspace_server": {
                "configured": server_config is not None,
                "command": server_config.get("command") if server_config is not None else None,
                "args": server_config.get("args") if server_config is not None else None,
                "cwd": server_config.get("cwd") if server_config is not None else None,
            },
        }

    def _existing_entrypoints(self, repo: str) -> list[dict[str, str]]:
        repo_root = self.workspace.repo_roots.get(repo)
        if repo_root is None:
            return []
        hint = REPO_HINTS.get(repo, {})
        entries: list[dict[str, str]] = []
        for rel_path in hint.get("entry_candidates", []):
            candidate = repo_root / rel_path
            if candidate.exists():
                entries.append(
                    {
                        "path": rel_path,
                        "abs_path": str(candidate),
                    }
                )
        launcher = hint.get("launcher")
        if isinstance(launcher, str):
            launcher_path = repo_root / launcher
            if launcher_path.exists():
                entries.append(
                    {
                        "path": launcher,
                        "abs_path": str(launcher_path),
                    }
                )
        return entries

    def _resolve_entrypoint(self, entry: dict[str, str]) -> dict[str, Any]:
        scope = entry["scope"]
        rel_path = entry["path"]
        abs_path: Path | None
        if scope == "workspace":
            abs_path = self.workspace_root / rel_path
        else:
            repo_root = self.workspace.repo_roots.get(scope)
            abs_path = (repo_root / rel_path) if repo_root is not None else None
        return {
            **entry,
            "exists": abs_path.exists() if abs_path is not None else False,
            "abs_path": str(abs_path) if abs_path is not None else None,
        }

    def _text_payload(
        self,
        repo: str,
        relative_path: str,
        *,
        mode: str,
        limit: int,
        label: str,
    ) -> dict[str, Any]:
        repo_root = self.workspace.repo_roots.get(repo)
        path = repo_root / relative_path if repo_root is not None else None
        if path is None or not path.exists():
            return {
                "label": label,
                "path": str(path) if path is not None else None,
                "exists": False,
                "mode": mode,
                "content": None,
            }

        text = path.read_text(encoding="utf-8")
        content = text if mode == "full" else "\n".join(text.splitlines()[:limit])
        return {
            "label": label,
            "path": str(path),
            "exists": True,
            "mode": mode,
            "content": content,
        }

    def _load_toml(self, path: Path) -> tuple[dict[str, Any] | None, str | None]:
        if not path.exists():
            return None, None
        try:
            return tomllib.loads(path.read_text(encoding="utf-8")), None
        except Exception as exc:  # pragma: no cover - defensive
            return None, str(exc)


def build_server(start: str | Path | None = None) -> Any:
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency 'mcp'. Install with: python -m pip install -e '.[mcp]'"
        ) from exc

    start_path = Path(start or Path.cwd()).expanduser().resolve()
    mcp = FastMCP("aoa-workspace", json_response=True)

    def current_state() -> AoAWorkspaceMCPState:
        return AoAWorkspaceMCPState.discover(start_path)

    @mcp.tool()
    def workspace_resolution() -> dict[str, Any]:
        """Return the resolved aoa-sdk workspace payload with path origins."""
        return current_state().build_workspace_resolution()

    @mcp.tool()
    def workspace_health() -> dict[str, Any]:
        """Return a narrow health bundle for workspace marker, project config, and repo presence."""
        return current_state().build_health()

    @mcp.tool()
    def workspace_repo_map() -> dict[str, Any]:
        """Return the repo-role map using aoa-sdk workspace discovery plus advisory entrypoints."""
        return current_state().build_repo_map()

    @mcp.tool()
    def workspace_surface_crosswalk() -> dict[str, Any]:
        """Return the Codex surface-selection crosswalk for the workspace."""
        return current_state().build_surface_crosswalk()

    @mcp.tool()
    def workspace_runtime_entrypoints() -> dict[str, Any]:
        """Return curated runtime entrypoints across the workspace."""
        return current_state().build_runtime_entrypoints()

    @mcp.tool()
    def workspace_skill_index(mode: str = "preview", limit: int = 80) -> dict[str, Any]:
        """Return aoa-skills/SKILL_INDEX.md as preview text or full text."""
        return current_state().load_skill_index(mode=mode, limit=limit)

    @mcp.tool()
    def workspace_agent_profiles() -> dict[str, Any]:
        """Return compact aoa-agents profile metadata."""
        return current_state().load_agent_profiles()

    @mcp.resource("aoa-workspace://resolution")
    def resolution_resource() -> str:
        return json.dumps(current_state().build_workspace_resolution(), ensure_ascii=False, indent=2)

    @mcp.resource("aoa-workspace://health")
    def health_resource() -> str:
        return json.dumps(current_state().build_health(), ensure_ascii=False, indent=2)

    @mcp.resource("aoa-workspace://repo-map")
    def repo_map_resource() -> str:
        return json.dumps(current_state().build_repo_map(), ensure_ascii=False, indent=2)

    @mcp.resource("aoa-workspace://surface-crosswalk")
    def crosswalk_resource() -> str:
        return json.dumps(current_state().build_surface_crosswalk(), ensure_ascii=False, indent=2)

    @mcp.resource("aoa-workspace://runtime-entrypoints")
    def runtime_entrypoints_resource() -> str:
        return json.dumps(current_state().build_runtime_entrypoints(), ensure_ascii=False, indent=2)

    @mcp.resource("aoa-workspace://skill-index")
    def skill_index_resource() -> str:
        return json.dumps(current_state().load_skill_index(mode="preview", limit=80), ensure_ascii=False, indent=2)

    @mcp.resource("aoa-workspace://agent-profiles")
    def agent_profiles_resource() -> str:
        return json.dumps(current_state().load_agent_profiles(), ensure_ascii=False, indent=2)

    @mcp.prompt()
    def orient_in_aoa_workspace() -> str:
        """Prompt recipe for first orientation in the AoA workspace."""
        return (
            "Use workspace_resolution, then workspace_repo_map, then workspace_surface_crosswalk. "
            "Name the strongest next surface for the task, one fallback surface, and one owner boundary you must not cross."
        )

    @mcp.prompt()
    def choose_codex_surface(task: str) -> str:
        """Prompt recipe for choosing the right Codex surface."""
        return (
            f"Task: {task}\n"
            "Use workspace_surface_crosswalk first. Then say whether the next move belongs in AGENTS.md, "
            "skills, subagents, project-level MCP, repo-local MCP, or repo-local source files. "
            "Name one primary choice and one fallback."
        )

    LOGGER.info("AoA workspace MCP server ready at federation root: %s", current_state().workspace_root)
    return mcp


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    server = build_server()
    server.run(transport="stdio")
