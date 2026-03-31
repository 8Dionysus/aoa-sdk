from __future__ import annotations

from typing import Any

from ..compatibility import load_surface
from ..errors import SkillNotFound, SurfaceNotFound
from ..loaders import extract_records, find_record
from ..models import SkillDisclosure
from ..workspace.discovery import Workspace

def load_skill_disclosures(workspace: Workspace) -> list[SkillDisclosure]:
    data = load_surface(workspace, "aoa-skills.runtime_disclosure_index")
    records = extract_records(data, preferred_keys=("skills",))
    return [SkillDisclosure.model_validate(item) for item in records]


def resolve_skill_name(workspace: Workspace, skill_name: str) -> str:
    disclosures = load_skill_disclosures(workspace)
    by_name = {skill.name: skill for skill in disclosures}
    if skill_name in by_name:
        return skill_name

    aliases = load_surface(workspace, "aoa-skills.runtime_activation_aliases").get("aliases", [])
    for alias in aliases:
        if skill_name in {
            alias.get("name"),
            alias.get("codex_mention"),
            alias.get("local_slash_alias"),
        }:
            resolved = alias.get("name")
            if resolved:
                return resolved

    raise SkillNotFound(f"Unknown skill: {skill_name}")


def disclose_skill(workspace: Workspace, skill_name: str) -> SkillDisclosure:
    resolved_name = resolve_skill_name(workspace, skill_name)
    records = [skill.model_dump(mode="python") for skill in load_skill_disclosures(workspace)]
    return SkillDisclosure.model_validate(find_record(records, field="name", value=resolved_name))


def load_skill_markdown(workspace: Workspace, disclosure: SkillDisclosure) -> str:
    skill_root = workspace.repo_path("aoa-skills")
    candidates = [
        disclosure.path,
        disclosure.metadata.get("aoa_source_skill_path"),
    ]
    for relative_path in candidates:
        if not relative_path:
            continue
        file_path = skill_root / relative_path
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")

    raise SurfaceNotFound(f"Could not locate skill markdown for {disclosure.name}")


def build_allowlist_paths(disclosure: SkillDisclosure) -> list[str]:
    paths = {disclosure.path, disclosure.skill_dir}
    for values in disclosure.resource_inventory.values():
        for resource_path in values:
            paths.add(f"{disclosure.skill_dir}/{resource_path}")
    return sorted(paths)


def split_frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    if not markdown.startswith("---\n"):
        return {}, markdown

    _, frontmatter_body = markdown.split("---\n", maxsplit=1)
    frontmatter_text, body = frontmatter_body.split("\n---\n", maxsplit=1)
    return parse_frontmatter(frontmatter_text), body.lstrip()


def parse_frontmatter(frontmatter_text: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    current_list_key: str | None = None

    for raw_line in frontmatter_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("- "):
            if current_list_key is None:
                continue
            parsed.setdefault(current_list_key, []).append(stripped[2:].strip())
            continue

        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        current_list_key = None
        if not key:
            continue

        if value == "":
            parsed[key] = []
            current_list_key = key
            continue

        if value.lower() == "true":
            parsed[key] = True
        elif value.lower() == "false":
            parsed[key] = False
        else:
            parsed[key] = value.strip("\"'")

    return parsed
