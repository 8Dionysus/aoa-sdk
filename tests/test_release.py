from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aoa_sdk.release.api import (
    ReleaseAPI,
    ReleaseAuditRepoReport,
    ReleaseAuditResult,
    _parse_latest_release,
    _git_fetch_origin,
    build_release_body,
    validate_release_body,
)
from aoa_sdk.workspace.discovery import Workspace


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
