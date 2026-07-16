from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from shutil import copytree

import pytest


@dataclass(frozen=True)
class SkillEnvironmentFixture:
    workspace_root: Path
    owner_root: Path
    repo_root: Path
    user_root: Path


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_skill(root: Path, name: str, body: str) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    return skill_dir


@pytest.fixture()
def skill_environment_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> SkillEnvironmentFixture:
    workspace_root = tmp_path / "workspace"
    owner_root = workspace_root / "aoa-skills"
    repo_root = workspace_root / "repo-home"
    user_root = tmp_path / "user-skills"
    owner_root.mkdir(parents=True)
    repo_root.mkdir(parents=True)
    (owner_root / "README.md").write_text("# aoa-skills\n", encoding="utf-8")
    (repo_root / "README.md").write_text("# repo-home\n", encoding="utf-8")

    source_skill = _write_skill(
        owner_root / ".agents" / "skills",
        "aoa-decision",
        "---\nname: aoa-decision\ndescription: Route durable decisions.\n---\n",
    )
    (source_skill / "agents").mkdir()
    (source_skill / "agents" / "openai.yaml").write_text(
        'interface:\n  display_name: "AoA Decision"\n',
        encoding="utf-8",
    )
    copytree(source_skill, user_root / "aoa-decision")
    _write_skill(
        user_root,
        "foreign-owner-skill",
        "---\nname: foreign-owner-skill\ndescription: Owned elsewhere.\n---\n",
    )

    repo_source = _write_skill(
        repo_root / "skills",
        "repo-home",
        "---\nname: repo-home\ndescription: Repository-owned procedure.\n---\n",
    )
    copytree(repo_source, repo_root / ".agents" / "skills" / "repo-home")
    _write_json(
        repo_root / "skills" / "port.manifest.json",
        {
            "schema_version": "aoa_skill_home_port_v1",
            "contract_ref": "repo:repo-home/skills/README.md",
            "owner_repo": "repo-home",
            "owner_ref": "repo:repo-home",
            "bundles": [
                {
                    "name": "repo-home",
                    "path": "skills/repo-home",
                    "version": "1",
                    "lifecycle": "active",
                    "visibility": "repo",
                    "admission_ref": "repo:repo-home/skills/README.md",
                }
            ],
            "projection": {
                "runtime": "codex",
                "scope": "repo",
                "root": ".agents/skills",
                "mode": "generated-copy",
                "skills": ["repo-home"],
            },
        },
    )
    _write_skill(
        workspace_root / ".agents" / "skills",
        "aoa-decision",
        "---\nname: aoa-decision\ndescription: Stale workspace copy.\n---\n",
    )

    profile_entry = {
        "name": "aoa-decision",
        "source_path": ".agents/skills/aoa-decision/SKILL.md",
        "target_path": "aoa-decision/SKILL.md",
        "openai_config_path": ".agents/skills/aoa-decision/agents/openai.yaml",
        "allow_implicit_invocation": True,
        "implicit_activation_policy": "allow",
        "trust_posture": "owner-reviewed",
    }
    _write_json(
        owner_root / "generated" / "skill_pack_profiles.resolved.json",
        {
            "schema_version": 2,
            "profile": "skill-pack-profiles",
            "source_config": "config/skill-pack-profiles.yaml",
            "profiles": {
                "user-default": {
                    "description": "Curated user profile.",
                    "scope": "user",
                    "install_mode": "copy",
                    "install_root": "${CODEX_HOME}/skills",
                    "skills": [profile_entry],
                },
                "repo-default": {
                    "description": "Repository profile.",
                    "scope": "repo",
                    "install_mode": "copy",
                    "install_root": ".agents/skills",
                    "skills": [profile_entry],
                },
            },
        },
    )
    _write_json(
        owner_root / "generated" / "agent_skill_catalog.json",
        {
            "catalog_version": 2,
            "profile": "agent-skills",
            "root": ".agents/skills",
            "source_repo": "aoa-skills",
            "source_of_truth": {"skills": "skills/"},
            "skills": [
                {
                    "name": "aoa-decision",
                    "display_name": "AoA Decision",
                    "description": "Route durable decisions.",
                    "short_description": "Route decisions.",
                    "path": ".agents/skills/aoa-decision/SKILL.md",
                    "scope": "shared",
                    "status": "active",
                    "invocation_mode": "implicit",
                    "implicit_activation_policy": "allow",
                    "allow_implicit_invocation": True,
                    "manual_invocation_required": False,
                    "candidate_only": False,
                    "source_skill_path": "skills/aoa-decision/SKILL.md",
                    "trust_posture": "owner-reviewed",
                    "mutation_surface": "none",
                }
            ],
        },
    )
    _write_json(
        owner_root / "generated" / "portable_export_map.json",
        {
            "export_version": 2,
            "profile": "portable-export",
            "root": ".agents/skills",
            "source_repo": "aoa-skills",
            "source_of_truth": {"skills": "skills/"},
            "exports": [],
        },
    )
    _write_json(
        owner_root / "generated" / "mcp_dependency_manifest.json",
        {
            "schema_version": 2,
            "profile": "mcp-dependencies",
            "skills": [],
        },
    )
    _write_json(
        owner_root / "generated" / "capability_graph.json",
        {
            "schema_version": "aoa-capability-graph-v1",
            "authority": False,
            "source": {
                "root": "capabilities/",
                "family_files": [],
                "referenced_files": [],
                "content_hash": "fixture",
            },
            "roots": ["operations.continuity"],
            "nodes": [
                {
                    "id": "operations.continuity",
                    "kind": "capability",
                    "contract_level": "navigation",
                    "primary_parent": None,
                    "source_family": "operations",
                    "source_path": "capabilities/operations.yaml",
                    "owner": {
                        "authority": "aoa-skills",
                        "repo": "aoa-skills",
                        "surface": "capabilities/operations.yaml",
                    },
                    "lifecycle": {
                        "state": "active",
                        "visibility": "shared",
                    },
                },
                {
                    "id": "workflow.operations.checkpoint-closeout",
                    "kind": "workflow",
                    "contract_level": "executable",
                    "primary_parent": "operations.continuity",
                    "source_family": "operations",
                    "source_path": "capabilities/operations.yaml",
                    "owner": {
                        "authority": "external-authority",
                        "repo": "aoa-playbooks",
                        "surface": "playbooks/checkpoint-closeout/PLAYBOOK.md",
                    },
                    "lifecycle": {
                        "state": "active",
                        "visibility": "shared",
                    },
                },
            ],
            "relations": [
                {
                    "kind": "primary-parent",
                    "source": "workflow.operations.checkpoint-closeout",
                    "target": "operations.continuity",
                    "source_path": "capabilities/operations.yaml",
                }
            ],
            "retrieval_documents": [],
        },
    )

    monkeypatch.setenv("AOA_SDK_FEDERATION_ROOT", str(workspace_root))
    monkeypatch.setenv("AOA_SDK_REPO_PATH_AOA_SKILLS", str(owner_root))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    return SkillEnvironmentFixture(
        workspace_root=workspace_root,
        owner_root=owner_root,
        repo_root=repo_root,
        user_root=user_root,
    )
