from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..loaders import load_json
from ..models import SkillActivationRequest
from ..workspace.discovery import Workspace
from .disclosure import disclose_skill, load_skill_markdown, split_frontmatter
from .session import activate_session_skill, ensure_session, save_session

RUNTIME_TOOL_SCHEMAS_SURFACE = "generated/runtime_tool_schemas.json"


def activate_skill(
    workspace: Workspace,
    request: SkillActivationRequest,
) -> dict[str, Any]:
    tool_schemas = load_json(workspace.surface_path("aoa-skills", RUNTIME_TOOL_SCHEMAS_SURFACE))
    _ensure_skill_allowed(tool_schemas, request.skill_name)

    disclosure = disclose_skill(workspace, request.skill_name)
    raw_markdown = load_skill_markdown(workspace, disclosure)
    frontmatter, stripped_markdown = split_frontmatter(raw_markdown)

    session_path: Path | None = None
    session = None
    if request.session_file is not None:
        session_path, session = ensure_session(workspace, request.session_file)
        activated_at = datetime.now(timezone.utc)
        session = activate_session_skill(
            session,
            disclosure=disclosure,
            activated_at=activated_at,
            explicit_handle=request.explicit_handle,
            wrap_mode=request.wrap_mode,
        )
        save_session(session_path, session)

    return {
        "skill": disclosure,
        "wrap_mode": request.wrap_mode,
        "content": _wrap_content(
            disclosure=disclosure,
            raw_markdown=raw_markdown,
            stripped_markdown=stripped_markdown,
            wrap_mode=request.wrap_mode,
        ),
        "frontmatter": frontmatter if request.include_frontmatter else {},
        "session_file": str(session_path) if session_path is not None else None,
        "session": session,
    }


def _ensure_skill_allowed(tool_schemas: dict[str, Any], skill_name: str) -> None:
    tools = tool_schemas.get("tools", [])
    activate_tool = next((tool for tool in tools if tool.get("name") == "activate_skill"), None)
    if activate_tool is None:
        return

    enum_values = (
        activate_tool.get("input_schema", {})
        .get("properties", {})
        .get("skill_name", {})
        .get("enum", [])
    )
    if skill_name not in enum_values:
        return


def _wrap_content(
    *,
    disclosure,
    raw_markdown: str,
    stripped_markdown: str,
    wrap_mode: str,
) -> Any:
    if wrap_mode == "raw":
        return raw_markdown
    if wrap_mode == "markdown":
        return stripped_markdown

    return {
        "instructions_markdown": stripped_markdown,
        "headings_available": disclosure.headings_available,
        "resource_inventory": disclosure.resource_inventory,
        "compatibility": disclosure.compatibility,
        "skill_path": disclosure.path,
    }
