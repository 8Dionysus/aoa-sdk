from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from aoa_sdk.release.api import (
    ReleaseAPI,
    ReleaseAuditRepoReport,
    ReleaseAuditResult,
    ReleaseRemoteStateUnknownError,
    _parse_latest_release,
    _gh_release_view,
    _git_fetch_origin,
    build_release_body,
    validate_release_body,
)
from aoa_sdk.workspace.discovery import Workspace


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file() and (parent / "AGENTS.md").is_file():
            return parent
    raise RuntimeError("could not find aoa-sdk repository root")


def _artifact_bundle_validator_module():
    script = (
        _repo_root()
        / "mechanics"
        / "release-support"
        / "parts"
        / "release-audit-publish-helper"
        / "scripts"
        / "validate_abyss_machine_package_artifact_bundle.py"
    )
    spec = importlib.util.spec_from_file_location("aoa_sdk_artifact_bundle_validator", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeArtifactBundles:
    def __init__(self, trust_gate_response: dict[str, Any]) -> None:
        self.trust_gate_response = trust_gate_response
        self.trust_gate_calls: list[dict[str, Any]] = []
        self.materialize_calls: list[dict[str, Any]] = []
        self.records: list[dict[str, Any]] = []

    def trust_gate(self, registry_dir: Path, **kwargs: Any) -> dict[str, Any]:
        self.trust_gate_calls.append({"registry_dir": registry_dir, **kwargs})
        return self.trust_gate_response

    def write_bundle_registry_record(self, bundle_dir: Path, registry_dir: Path, **kwargs: Any) -> dict[str, Any]:
        state = str(kwargs.get("lifecycle_state") or "")
        record = {
            "record_id": f"record-{len(self.records) + 1}",
            "subject_digest": "sha256:" + "1" * 64,
            "lifecycle_state": state,
            "source_repo": kwargs.get("source_repo"),
            "trust_root_mode": kwargs.get("trust_root_mode"),
        }
        self.records.append(record)
        return {"ok": True, "record": record}

    def promote_bundle_evidence(self, bundle_dir: Path, registry_dir: Path, **kwargs: Any) -> dict[str, Any]:
        written = self.write_bundle_registry_record(bundle_dir, registry_dir, **kwargs)
        return {
            "ok": written["ok"],
            "record": written["record"],
            "promotion": {"record_id": written["record"]["record_id"]},
        }

    def read_bundle_registry(self, registry_dir: Path, *, artifact_class: str) -> dict[str, Any]:
        release_ready = [record for record in self.records if record.get("lifecycle_state") == "release-ready"]
        latest_record = release_ready[-1] if release_ready else None
        if self.records and self.records[-1].get("lifecycle_state") == "revoked":
            latest_record = None
        if latest_record and os.environ.get("ABYSS_MACHINE_ARTIFACT_SUBJECT_STORE_ROOT"):
            latest_record["artifact_subject_store"] = {"ok": True}
        return {"latest_by_artifact_class": {artifact_class: latest_record} if latest_record else {}}

    def materialize_artifact_subjects(
        self,
        bundle_dir: Path,
        *,
        store_root: Path,
        registry_dir: Path,
        manifest_ref: Path,
        consumer_intent: str,
        expected_source_repo: str,
        expected_trust_root_mode: str,
        repo_root: Path,
    ) -> dict[str, Any]:
        self.materialize_calls.append(
            {
                "bundle_dir": bundle_dir,
                "store_root": store_root,
                "registry_dir": registry_dir,
                "manifest_ref": manifest_ref,
                "consumer_intent": consumer_intent,
                "expected_source_repo": expected_source_repo,
                "expected_trust_root_mode": expected_trust_root_mode,
                "repo_root": repo_root,
            }
        )
        return {"ok": True, "aggregate_digest": "sha256:" + "3" * 64}


def allow_gate_response() -> dict[str, Any]:
    return {
        "ok": True,
        "verdict": "allow",
        "decision": {"model": "fail_closed_consumer_admission", "allow": True},
        "inspected_claims": {
            "registry_latest": {"selected_record_is_latest": True},
            "controls": {"required_controls_missing": []},
            "source": {"source_repo_matched": True},
            "trust_root": {"trust_root_mode_matched": True},
            "artifact_subject_store": {"ok": True},
        },
    }


def deny_missing_subject_store_gate_response() -> dict[str, Any]:
    return {
        "ok": False,
        "verdict": "deny",
        "decision": {
            "model": "fail_closed_consumer_admission",
            "allow": False,
            "blockers": ["required_artifact_subject_store_not_verified"],
        },
        "inspected_claims": {
            "registry_latest": {"selected_record_is_latest": True},
            "controls": {"required_controls_missing": []},
            "source": {"source_repo_matched": True},
            "trust_root": {"trust_root_mode_matched": True},
            "artifact_subject_store": {"ok": False, "required": True},
        },
    }


def deny_terminal_gate_response() -> dict[str, Any]:
    return {
        "ok": True,
        "verdict": "deny",
        "decision": {"model": "fail_closed_consumer_admission", "allow": False},
        "inspected_claims": {"lifecycle": {"terminal_state": True}},
    }


def _init_repo(repo_root: Path, remote_root: Path) -> None:
    repo_root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "--bare", str(remote_root)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "init", "-b", "main", str(repo_root)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "config", "user.name", "Codex"], check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "config", "user.email", "codex@example.invalid"],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(["git", "-C", str(repo_root), "remote", "add", "origin", str(remote_root)], check=True, capture_output=True, text=True)


def _write_release_surfaces(
    repo_root: Path,
    *,
    repo_name: str,
    version: str,
    summary: list[str] | None = None,
    package_repo: bool = False,
) -> None:
    summary = summary or ["Keep releases small and legible."]
    (repo_root / "docs").mkdir(parents=True, exist_ok=True)
    (repo_root / "scripts").mkdir(parents=True, exist_ok=True)
    readme = (
        f"# {repo_name}\n\n"
        f"> Current release: `v{version}`. See [CHANGELOG](CHANGELOG.md) for release notes.\n"
    )
    (repo_root / "README.md").write_text(readme, encoding="utf-8")
    changelog = "\n".join(
        [
            "# Changelog",
            "",
            "## [Unreleased]",
            "",
            f"## [{version}] - 2026-04-10",
            "",
            "### Summary",
            *(f"- {line}" for line in summary),
            "",
            "### Validation",
            "- `python scripts/release_check.py`",
            "",
            "### Notes",
            "- release contract stays bounded to repo-owned surfaces.",
            "",
        ]
    )
    (repo_root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    (repo_root / "docs" / "RELEASING.md").write_text(
        f"# Releasing `{repo_name}`\n\nUse `python scripts/release_check.py` before tagging or publishing.\n",
        encoding="utf-8",
    )
    (repo_root / "scripts" / "release_check.py").write_text(
        "#!/usr/bin/env python3\nfrom __future__ import annotations\n\nraise SystemExit(0)\n",
        encoding="utf-8",
    )
    if package_repo:
        (repo_root / "src" / "aoa_sdk" / "cli").mkdir(parents=True, exist_ok=True)
        (repo_root / "pyproject.toml").write_text(
            "\n".join(
                [
                    "[build-system]",
                    'requires = ["setuptools>=68"]',
                    'build-backend = "setuptools.build_meta"',
                    "",
                    "[project]",
                    'name = "aoa-sdk"',
                    f'version = "{version}"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (repo_root / "src" / "aoa_sdk" / "cli" / "main.py").write_text(
            f'print("aoa-sdk {version}")\n',
            encoding="utf-8",
        )


def _commit_and_push(repo_root: Path, version: str) -> None:
    subprocess.run(["git", "-C", str(repo_root), "add", "."], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "commit", "-m", "release surfaces"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "push", "-u", "origin", "main"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "tag", "-a", f"v{version}", "-m", f"v{version}"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "push", "origin", f"refs/tags/v{version}"], check=True, capture_output=True, text=True)


def _workspace_for(repo_name: str, repo_root: Path, workspace_root: Path) -> Workspace:
    return Workspace(
        root=workspace_root,
        federation_root=workspace_root,
        federation_root_source="test",
        manifest_path=None,
        repo_roots={repo_name: repo_root},
        repo_origins={repo_name: "test"},
    )


def _fresh_release_payload(repo_name: str, version: str, body: str) -> dict[str, str]:
    published_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "tagName": f"v{version}",
        "body": body,
        "url": f"https://github.com/8Dionysus/{repo_name}/releases/tag/v{version}",
        "publishedAt": published_at,
    }


def test_package_artifact_manifest_keeps_consumer_trust_gate_contract() -> None:
    repo_root = _repo_root()
    manifest = json.loads(
        (repo_root / "sdk" / "distribution" / "manifests" / "python_distribution.bundle.json").read_text(encoding="utf-8")
    )
    helper_readme = (
        repo_root / "mechanics" / "release-support" / "parts" / "release-audit-publish-helper" / "README.md"
    ).read_text(encoding="utf-8")

    consumer_contract = manifest["consumer_contract"]
    consumer_commands = "\n".join(manifest["consumer_command"])

    assert "trust-gate" in consumer_contract["stable_interface"]
    assert "trust-gate allow/warn" in consumer_contract["consumer_expectation"]
    assert "abyss-machine artifacts evidence-promote" in consumer_commands
    assert "abyss-machine artifacts materialize-subjects" in consumer_commands
    assert "abyss-machine artifacts trust-gate" in consumer_commands
    assert "abyss-machine artifacts registry-latest" in consumer_commands
    assert "--consumer-ref aoa-sdk:release-audit-publish-helper" in consumer_commands
    assert "--source-repo aoa-sdk" in consumer_commands
    assert "--trust-root-mode host_managed" in consumer_commands
    assert consumer_contract["subject_store_required"] is True
    assert consumer_contract["admission_gate"] == "fail_closed_consumer_admission"
    assert "materializes the package subject store" in helper_readme
    assert "host-managed trust-root metadata" in helper_readme
    assert "revoked-record" in helper_readme
    assert "unverified latest" in helper_readme


def test_package_artifact_bundle_validator_reports_external_paths(tmp_path: Path) -> None:
    validator = _artifact_bundle_validator_module()

    assert validator._path_ref(_repo_root() / "dist" / "bundle") == "dist/bundle"
    assert validator._path_ref(tmp_path / "bundle") == str((tmp_path / "bundle").resolve())


def test_package_artifact_trust_gate_requires_fail_closed_latest_controls_and_source(tmp_path: Path) -> None:
    validator = _artifact_bundle_validator_module()
    fake = FakeArtifactBundles(allow_gate_response())
    registry_roundtrip = {"promoted": {"record": {"subject_digest": "sha256:" + "2" * 64}}}

    result = validator._trust_gate_allow_latest(fake, tmp_path, registry_roundtrip)

    assert result["ok"] is True
    assert fake.trust_gate_calls == [
        {
            "registry_dir": tmp_path,
            "artifact_class": "aoa_sdk_python_distribution",
            "subject_digest": "sha256:" + "2" * 64,
            "consumer_intent": "agent",
            "expected_source_repo": "aoa-sdk",
            "expected_trust_root_mode": "host_managed",
        }
    ]

    for mutated_claim in (
        {"decision": {"model": "shape_only", "allow": True}},
        {"inspected_claims": {"registry_latest": {"selected_record_is_latest": False}}},
        {"inspected_claims": {"controls": {"required_controls_missing": ["sbom"]}}},
        {"inspected_claims": {"source": {"source_repo_matched": False}}},
        {"inspected_claims": {"trust_root": {"trust_root_mode_matched": False}}},
        {"inspected_claims": {"artifact_subject_store": {"ok": False}}},
    ):
        response = allow_gate_response()
        for key, value in mutated_claim.items():
            if key == "inspected_claims":
                response[key].update(value)
            else:
                response[key] = value
        assert validator._trust_gate_allow_latest(FakeArtifactBundles(response), tmp_path, registry_roundtrip)["ok"] is False


def test_package_artifact_pre_materialization_gate_denies_only_missing_subject_store(tmp_path: Path) -> None:
    validator = _artifact_bundle_validator_module()
    fake = FakeArtifactBundles(deny_missing_subject_store_gate_response())
    registry_roundtrip = {"promoted": {"record": {"subject_digest": "sha256:" + "2" * 64}}}

    result = validator._trust_gate_denies_only_missing_subject_store(fake, tmp_path, registry_roundtrip)

    assert result["ok"] is True
    assert result["expected_blocker"] == "required_artifact_subject_store_not_verified"
    assert fake.trust_gate_calls == [
        {
            "registry_dir": tmp_path,
            "artifact_class": "aoa_sdk_python_distribution",
            "subject_digest": "sha256:" + "2" * 64,
            "consumer_intent": "agent",
            "expected_source_repo": "aoa-sdk",
            "expected_trust_root_mode": "host_managed",
        }
    ]

    for mutated_claim in (
        {"decision": {"model": "fail_closed_consumer_admission", "allow": True, "blockers": []}},
        {
            "decision": {
                "model": "fail_closed_consumer_admission",
                "allow": False,
                "blockers": ["wrong_blocker"],
            }
        },
        {"verdict": "allow"},
        {"inspected_claims": {"registry_latest": {"selected_record_is_latest": False}}},
        {"inspected_claims": {"controls": {"required_controls_missing": ["sbom"]}}},
        {"inspected_claims": {"source": {"source_repo_matched": False}}},
        {"inspected_claims": {"trust_root": {"trust_root_mode_matched": False}}},
        {"inspected_claims": {"artifact_subject_store": {"ok": True, "required": True}}},
    ):
        response = deny_missing_subject_store_gate_response()
        for key, value in mutated_claim.items():
            if key == "inspected_claims":
                response[key].update(value)
            else:
                response[key] = value
        assert (
            validator._trust_gate_denies_only_missing_subject_store(FakeArtifactBundles(response), tmp_path, registry_roundtrip)["ok"]
            is False
        )


def test_package_artifact_terminal_registry_state_requires_revoked_gate_deny(tmp_path: Path) -> None:
    validator = _artifact_bundle_validator_module()

    denied = validator._verify_terminal_registry_state(
        FakeArtifactBundles(deny_terminal_gate_response()),
        tmp_path,
        tmp_path,
        _repo_root() / "sdk" / "distribution" / "manifests" / "python_distribution.bundle.json",
        tmp_path,
    )
    assert denied["ok"] is True
    assert denied["revoked_trust_gate"]["verdict"] == "deny"

    allowed = validator._verify_terminal_registry_state(
        FakeArtifactBundles(allow_gate_response()),
        tmp_path,
        tmp_path,
        _repo_root() / "sdk" / "distribution" / "manifests" / "python_distribution.bundle.json",
        tmp_path,
    )
    assert allowed["ok"] is False
    assert allowed["revoked_trust_gate"]["verdict"] == "allow"


def test_package_artifact_materialized_subject_store_requires_trusted_source_scoped_subject(
    tmp_path: Path,
) -> None:
    validator = _artifact_bundle_validator_module()
    fake = FakeArtifactBundles(allow_gate_response())
    manifest = _repo_root() / "sdk" / "distribution" / "manifests" / "python_distribution.bundle.json"

    result = validator._verify_materialized_subject_store(
        fake,
        manifest,
        tmp_path,
        tmp_path / "registry",
        tmp_path,
        tmp_path,
    )

    assert result["ok"] is True
    assert fake.materialize_calls == [
        {
            "bundle_dir": tmp_path,
            "store_root": tmp_path / "subject-store",
            "registry_dir": tmp_path / "registry",
            "manifest_ref": manifest,
            "consumer_intent": "agent",
            "expected_source_repo": "aoa-sdk",
            "expected_trust_root_mode": "host_managed",
            "repo_root": tmp_path,
        }
    ]
    assert fake.trust_gate_calls[-1] == {
        "registry_dir": tmp_path / "registry",
        "artifact_class": "aoa_sdk_python_distribution",
        "subject_digest": "sha256:" + "3" * 64,
        "consumer_intent": "agent",
        "expected_source_repo": "aoa-sdk",
        "expected_trust_root_mode": "host_managed",
    }

    fake = FakeArtifactBundles({**allow_gate_response(), "verdict": "warn"})
    assert (
        validator._verify_materialized_subject_store(
            fake,
            manifest,
            tmp_path,
            tmp_path / "registry",
            tmp_path,
            tmp_path,
        )["ok"]
        is True
    )


def test_parse_latest_release_extracts_summary_validation_and_notes() -> None:
    release = _parse_latest_release(
        "\n".join(
            [
                "# Changelog",
                "",
                "## [Unreleased]",
                "",
                "## [0.2.0] - 2026-04-10",
                "",
                "### Summary",
                "- one",
                "  still one",
                "- two",
                "",
                "### Validation",
                "- green",
                "",
                "### Notes",
                "- bounded",
                "",
            ]
        )
    )

    assert release.version == "0.2.0"
    assert release.tag == "v0.2.0"
    assert release.summary_bullets == ["one still one", "two"]
    assert release.has_validation is True
    assert release.has_notes is True


def test_build_release_body_uses_full_summary_bullets() -> None:
    release = _parse_latest_release(
        "\n".join(
            [
                "# Changelog",
                "",
                "## [Unreleased]",
                "",
                "## [0.2.0] - 2026-04-10",
                "",
                "### Summary",
                "- one",
                "  still one",
                "",
                "### Validation",
                "- green",
                "",
                "### Notes",
                "- bounded",
                "",
            ]
        )
    )

    body = build_release_body("Agents-of-Abyss", release)
    assert "- one still one" in body


def test_validate_release_body_requires_canonical_shape() -> None:
    release = _parse_latest_release(
        "\n".join(
            [
                "# Changelog",
                "",
                "## [Unreleased]",
                "",
                "## [0.2.0] - 2026-04-10",
                "",
                "### Summary",
                "- one",
                "",
                "### Validation",
                "- green",
                "",
                "### Notes",
                "- bounded",
                "",
            ]
        )
    )

    checks = validate_release_body("Agents-of-Abyss", release, build_release_body("Agents-of-Abyss", release))
    assert all(check.passed for check in checks)

    broken = validate_release_body("Agents-of-Abyss", release, "Released: 2026-04-10\n")
    assert any(not check.passed for check in broken)


def test_preflight_fails_when_package_version_mismatches(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    repo_root = workspace_root / "aoa-sdk"
    remote_root = tmp_path / "aoa-sdk-origin.git"
    _init_repo(repo_root, remote_root)
    _write_release_surfaces(repo_root, repo_name="aoa-sdk", version="0.2.0", package_repo=True)
    (repo_root / "pyproject.toml").write_text(
        (repo_root / "pyproject.toml").read_text(encoding="utf-8").replace('version = "0.2.0"', 'version = "0.1.9"'),
        encoding="utf-8",
    )
    _commit_and_push(repo_root, "0.2.0")

    api = ReleaseAPI(_workspace_for("aoa-sdk", repo_root, workspace_root))
    result = api.audit(workspace_root=workspace_root, phase="preflight", repo="aoa-sdk", include_all=False, strict=True)

    assert result.passed is False
    assert any(check.name == "pyproject-version" and not check.passed for check in result.repo_reports[0].checks)


def test_cadence_marks_repo_due_when_public_surface_drift_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace_root = tmp_path / "workspace"
    repo_root = workspace_root / "Agents-of-Abyss"
    remote_root = tmp_path / "aoa-origin.git"
    _init_repo(repo_root, remote_root)
    _write_release_surfaces(repo_root, repo_name="Agents-of-Abyss", version="0.2.0")
    _commit_and_push(repo_root, "0.2.0")
    (repo_root / "docs" / "EXTRA.md").write_text("new public drift\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_root), "add", "docs/EXTRA.md"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "commit", "-m", "public drift"], check=True, capture_output=True, text=True)

    api = ReleaseAPI(_workspace_for("Agents-of-Abyss", repo_root, workspace_root))
    release = _parse_latest_release((repo_root / "CHANGELOG.md").read_text(encoding="utf-8"))
    payload = _fresh_release_payload("Agents-of-Abyss", "0.2.0", build_release_body("Agents-of-Abyss", release))
    monkeypatch.setattr("aoa_sdk.release.api._gh_release_view", lambda repo, tag, cwd: payload)

    result = api.audit(workspace_root=workspace_root, phase="cadence", repo="Agents-of-Abyss", include_all=False, strict=False)

    assert result.repo_reports[0].due is True
    assert "public-surface drift" in result.repo_reports[0].blocked_reason


def test_git_fetch_origin_times_out_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    remote_root = tmp_path / "origin.git"
    _init_repo(repo_root, remote_root)
    original_run = subprocess.run

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
        timeout: float | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if command[:5] == ["git", "-C", str(repo_root), "fetch", "--tags"]:
            raise subprocess.TimeoutExpired(command, timeout)
        return original_run(
            command,
            cwd=cwd,
            env=env,
            check=check,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
        )

    monkeypatch.setattr("aoa_sdk.release.api.subprocess.run", fake_run)

    passed, detail = _git_fetch_origin(repo_root)

    assert passed is False
    assert "timed out" in detail


def test_publish_dry_run_skips_postpublish_audit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace_root = tmp_path / "workspace"
    repo_root = workspace_root / "Agents-of-Abyss"
    remote_root = tmp_path / "aoa-origin.git"
    _init_repo(repo_root, remote_root)
    _write_release_surfaces(repo_root, repo_name="Agents-of-Abyss", version="0.2.0")
    _commit_and_push(repo_root, "0.2.0")

    api = ReleaseAPI(_workspace_for("Agents-of-Abyss", repo_root, workspace_root))
    release = _parse_latest_release((repo_root / "CHANGELOG.md").read_text(encoding="utf-8"))

    preflight = ReleaseAuditResult(
        workspace_root=str(workspace_root),
        phase="preflight",
        strict=True,
        passed=True,
        repo_reports=[
            ReleaseAuditRepoReport(
                repo="Agents-of-Abyss",
                repo_root=str(repo_root),
                phase="preflight",
                passed=True,
                expected_version=release.version,
                latest_tag=release.tag,
                checks=[],
            )
        ],
    )

    monkeypatch.setattr(api, "audit", lambda **kwargs: preflight)
    monkeypatch.setattr(api, "_publish_repo", lambda *args, **kwargs: (["reuse existing tag v0.2.0"], "https://example.invalid/release"))

    def fail_postpublish(*args: object, **kwargs: object) -> object:
        raise AssertionError("dry-run publish should not call postpublish audit")

    monkeypatch.setattr(api, "_audit_postpublish", fail_postpublish)

    result = api.publish(workspace_root=workspace_root, repo="Agents-of-Abyss", dry_run=True)

    assert result.passed is True
    assert result.repo_reports[0].postpublish_passed is False


def test_publish_aborts_before_tag_push_when_release_view_times_out(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "workspace"
    repo_root = workspace_root / "Agents-of-Abyss"
    remote_root = tmp_path / "aoa-origin.git"
    _init_repo(repo_root, remote_root)
    _write_release_surfaces(repo_root, repo_name="Agents-of-Abyss", version="0.2.0")
    _commit_and_push(repo_root, "0.2.0")
    old_tag_commit = subprocess.run(
        ["git", "-C", str(repo_root), "rev-list", "-n", "1", "v0.2.0"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    (repo_root / "docs" / "AFTER_TAG.md").write_text("new release-prep commit\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_root), "add", "docs/AFTER_TAG.md"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(repo_root), "commit", "-m", "release prep"], check=True, capture_output=True, text=True)
    head_commit = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert old_tag_commit != head_commit

    api = ReleaseAPI(_workspace_for("Agents-of-Abyss", repo_root, workspace_root))
    release = _parse_latest_release((repo_root / "CHANGELOG.md").read_text(encoding="utf-8"))
    preflight = ReleaseAuditResult(
        workspace_root=str(workspace_root),
        phase="preflight",
        strict=True,
        passed=True,
        repo_reports=[
            ReleaseAuditRepoReport(
                repo="Agents-of-Abyss",
                repo_root=str(repo_root),
                phase="preflight",
                passed=True,
                expected_version=release.version,
                latest_tag=release.tag,
                checks=[],
            )
        ],
    )
    original_run = subprocess.run

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
        timeout: float | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if command[:3] == ["gh", "release", "view"]:
            raise subprocess.TimeoutExpired(command, timeout)
        if command[:4] == ["git", "-C", str(repo_root), "push"]:
            raise AssertionError("publish must not push tags when remote release state is unknown")
        if command[:4] == ["git", "-C", str(repo_root), "tag"] and "-fa" in command:
            raise AssertionError("publish must not move tags when remote release state is unknown")
        return original_run(
            command,
            cwd=cwd,
            env=env,
            check=check,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
        )

    monkeypatch.setattr(api, "audit", lambda **kwargs: preflight)
    monkeypatch.setattr("aoa_sdk.release.api.subprocess.run", fake_run)

    result = api.publish(workspace_root=workspace_root, repo="Agents-of-Abyss", dry_run=False)
    tag_after = original_run(
        ["git", "-C", str(repo_root), "rev-list", "-n", "1", "v0.2.0"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    assert result.passed is False
    assert result.repo_reports[0].actions == [
        "GitHub Release lookup for Agents-of-Abyss v0.2.0 timed out after 60s"
    ]
    assert tag_after == old_tag_commit
    assert tag_after != head_commit


def test_release_view_timeout_is_distinct_from_missing_release(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    remote_root = tmp_path / "origin.git"
    _init_repo(repo_root, remote_root)

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
        timeout: float | None = None,
    ) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(command, timeout)

    monkeypatch.setattr("aoa_sdk.release.api.subprocess.run", fake_run)

    with pytest.raises(ReleaseRemoteStateUnknownError, match="timed out"):
        _gh_release_view("Agents-of-Abyss", "v0.2.0", cwd=repo_root)


@pytest.mark.parametrize(
    ("repo_name", "version", "package_repo"),
    [
        ("Agents-of-Abyss", "0.2.0", False),
        ("aoa-skills", "0.3.0", False),
        ("aoa-stats", "0.1.0", False),
        ("aoa-sdk", "0.2.0", True),
    ],
)
def test_preflight_passes_for_release_archetypes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    repo_name: str,
    version: str,
    package_repo: bool,
) -> None:
    workspace_root = tmp_path / "workspace"
    repo_root = workspace_root / repo_name
    remote_root = tmp_path / f"{repo_name}-origin.git"
    _init_repo(repo_root, remote_root)
    _write_release_surfaces(repo_root, repo_name=repo_name, version=version, package_repo=package_repo)
    _commit_and_push(repo_root, version)

    api = ReleaseAPI(_workspace_for(repo_name, repo_root, workspace_root))
    result = api.audit(workspace_root=workspace_root, phase="preflight", repo=repo_name, include_all=False, strict=True)

    assert result.passed is True
    assert result.repo_reports[0].passed is True


def test_postpublish_passes_when_release_body_matches_changelog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace_root = tmp_path / "workspace"
    repo_root = workspace_root / "Agents-of-Abyss"
    remote_root = tmp_path / "aoa-origin.git"
    _init_repo(repo_root, remote_root)
    _write_release_surfaces(repo_root, repo_name="Agents-of-Abyss", version="0.2.0")
    _commit_and_push(repo_root, "0.2.0")

    api = ReleaseAPI(_workspace_for("Agents-of-Abyss", repo_root, workspace_root))
    release = _parse_latest_release((repo_root / "CHANGELOG.md").read_text(encoding="utf-8"))
    body = build_release_body("Agents-of-Abyss", release)
    payload = _fresh_release_payload("Agents-of-Abyss", "0.2.0", body)
    monkeypatch.setattr("aoa_sdk.release.api._gh_release_view", lambda repo, tag, cwd: payload)
    monkeypatch.setattr(
        "aoa_sdk.release.api._gh_release_list",
        lambda repo, cwd: [{"tagName": "v0.2.0", "isLatest": True}],
    )

    result = api.audit(workspace_root=workspace_root, phase="postpublish", repo="Agents-of-Abyss", include_all=False, strict=True)

    assert result.passed is True
    assert result.repo_reports[0].release_url == payload["url"]
