from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..workspace.discovery import Workspace
from ..workspace.roots import KNOWN_REPOS

OWNER_RELEASE_REPOS = tuple(repo for repo in KNOWN_REPOS if repo != "8Dionysus")
README_BANNER_TEMPLATE = "> Current release: `{tag}`. See [CHANGELOG](CHANGELOG.md) for release notes."
PUBLIC_SURFACE_PREFIXES = ("docs/", "generated/", "schemas/", ".github/workflows/")
PUBLIC_SURFACE_FILES = {"README.md", "CHANGELOG.md", "pyproject.toml", "package.json"}
PACKAGE_VERSION_FILES = {
    "aoa-sdk": ("pyproject.toml", "src/aoa_sdk/cli/main.py"),
}
ReleaseAuditPhase = Literal["preflight", "postpublish", "cadence"]
REMOTE_COMMAND_TIMEOUT_SECONDS = 60.0
PUBLISH_COMMAND_TIMEOUT_SECONDS = 120.0


class ReleaseCheck(BaseModel):
    name: str
    passed: bool
    detail: str


class ReleaseAuditRepoReport(BaseModel):
    repo: str
    repo_root: str
    phase: ReleaseAuditPhase
    passed: bool
    expected_version: str | None = None
    latest_tag: str | None = None
    release_url: str | None = None
    published_at: str | None = None
    commits_since_tag: int | None = None
    hours_since_release: float | None = None
    due: bool | None = None
    blocked_reason: str | None = None
    checks: list[ReleaseCheck] = Field(default_factory=list)


class ReleaseAuditResult(BaseModel):
    workspace_root: str
    phase: ReleaseAuditPhase
    strict: bool
    passed: bool
    repo_reports: list[ReleaseAuditRepoReport] = Field(default_factory=list)


class ReleasePublishRepoReport(BaseModel):
    repo: str
    repo_root: str
    tag: str
    version: str
    dry_run: bool
    passed: bool
    postpublish_passed: bool
    release_url: str | None = None
    actions: list[str] = Field(default_factory=list)


class ReleasePublishResult(BaseModel):
    workspace_root: str
    dry_run: bool
    passed: bool
    repo_reports: list[ReleasePublishRepoReport] = Field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ParsedReleaseSection:
    version: str
    tag: str
    date: str
    body: str
    summary_bullets: list[str]
    has_validation: bool
    has_notes: bool


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    check: bool = False,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=check,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _strip(text: str) -> str:
    return text.strip()


def _normalize_markdown(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").strip().split("\n")]
    return "\n".join(lines)


def _banner_for(tag: str) -> str:
    return README_BANNER_TEMPLATE.format(tag=tag)


def _github_repo_slug(repo: str) -> str:
    return f"8Dionysus/{repo}"


def _github_changelog_url(repo: str) -> str:
    return f"https://github.com/{_github_repo_slug(repo)}/blob/main/CHANGELOG.md"


def _git_stdout(repo_root: Path, *args: str) -> str:
    completed = _run(["git", "-C", str(repo_root), *args], cwd=repo_root, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "git command failed")
    return completed.stdout.strip()


def _git_returncode(repo_root: Path, *args: str) -> int:
    return _run(["git", "-C", str(repo_root), *args], cwd=repo_root, check=False).returncode


def _git_fetch_origin(repo_root: Path) -> tuple[bool, str]:
    if _git_returncode(repo_root, "remote", "get-url", "origin") != 0:
        return False, "missing git remote origin"
    try:
        completed = _run(
            ["git", "-C", str(repo_root), "fetch", "--tags", "origin"],
            cwd=repo_root,
            check=False,
            timeout=REMOTE_COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return False, f"git fetch origin timed out after {int(REMOTE_COMMAND_TIMEOUT_SECONDS)}s"
    if completed.returncode != 0:
        detail = _strip(completed.stderr) or _strip(completed.stdout) or "git fetch origin failed"
        return False, detail
    return True, "origin fetched"


def _parse_latest_release(changelog_text: str) -> ParsedReleaseSection:
    match = re.search(r"^## \[(?P<version>\d+\.\d+\.\d+)\] - (?P<date>\d{4}-\d{2}-\d{2})$", changelog_text, re.M)
    if not match:
        raise ValueError("CHANGELOG.md is missing a dated latest tagged release heading")
    start = match.end()
    next_match = re.search(r"^## \[", changelog_text[start:], re.M)
    end = start + next_match.start() if next_match else len(changelog_text)
    body = changelog_text[start:end].strip()
    summary = _extract_section(body, "Summary")
    validation = _extract_section(body, "Validation")
    notes = _extract_section(body, "Notes")
    summary_bullets = _extract_bullets(summary)
    return ParsedReleaseSection(
        version=match.group("version"),
        tag=f"v{match.group('version')}",
        date=match.group("date"),
        body=body,
        summary_bullets=summary_bullets,
        has_validation=validation is not None,
        has_notes=notes is not None,
    )


def _extract_section(body: str, heading: str) -> str | None:
    pattern = re.compile(rf"^### {re.escape(heading)}\s*$", re.M)
    match = pattern.search(body)
    if not match:
        return None
    start = match.end()
    next_match = re.search(r"^### ", body[start:], re.M)
    end = start + next_match.start() if next_match else len(body)
    return body[start:end].strip()


def _extract_bullets(section: str | None) -> list[str]:
    if not section:
        return []
    bullets: list[str] = []
    current: str | None = None
    for raw_line in section.splitlines():
        line = raw_line.rstrip()
        if line.startswith("- "):
            if current is not None:
                bullets.append(current)
            current = line[2:].strip()
            continue
        if current is not None and line.strip():
            current = f"{current} {line.strip()}"
    if current is not None:
        bullets.append(current)
    return bullets


def build_release_body(repo: str, release: ParsedReleaseSection) -> str:
    highlights = "\n".join(f"- {line}" for line in release.summary_bullets)
    chunks = [
        f"Released: {release.date}",
        f"Canonical changelog: [CHANGELOG.md]({_github_changelog_url(repo)})",
        "## Highlights\n" + highlights,
        "## Full Release Notes\n" + release.body,
    ]
    return "\n\n".join(chunks) + "\n"


def validate_release_body(repo: str, release: ParsedReleaseSection, body: str) -> list[ReleaseCheck]:
    normalized = _normalize_markdown(body)
    expected = _normalize_markdown(build_release_body(repo, release))
    canonical_line = f"Canonical changelog: [CHANGELOG.md]({_github_changelog_url(repo)})"
    return [
        ReleaseCheck(
            name="released-line",
            passed=normalized.startswith(f"Released: {release.date}"),
            detail=f"expected Released: {release.date}",
        ),
        ReleaseCheck(
            name="canonical-changelog-link",
            passed=canonical_line in normalized,
            detail=canonical_line,
        ),
        ReleaseCheck(
            name="highlights-section",
            passed="## Highlights" in normalized and len(release.summary_bullets) > 0,
            detail="release body must include highlights built from changelog summary bullets",
        ),
        ReleaseCheck(
            name="full-release-notes-section",
            passed="## Full Release Notes" in normalized,
            detail="release body must include full release notes",
        ),
        ReleaseCheck(
            name="body-sync",
            passed=normalized == expected,
            detail="release body should exactly match the canonical changelog-derived shape",
        ),
    ]


def _gh_release_view(repo: str, tag: str, *, cwd: Path) -> dict[str, Any] | None:
    try:
        completed = _run(
            ["gh", "release", "view", tag, "--repo", _github_repo_slug(repo), "--json", "tagName,body,url,publishedAt"],
            cwd=cwd,
            check=False,
            timeout=REMOTE_COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return None
    if completed.returncode != 0:
        return None
    return json.loads(completed.stdout)


def _gh_release_list(repo: str, *, cwd: Path) -> list[dict[str, Any]]:
    try:
        completed = _run(
            ["gh", "release", "list", "--repo", _github_repo_slug(repo), "--limit", "10", "--json", "tagName,isLatest"],
            cwd=cwd,
            check=False,
            timeout=REMOTE_COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return []
    if completed.returncode != 0:
        return []
    return json.loads(completed.stdout)


def _pyproject_version(repo_root: Path) -> str | None:
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        return None
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return data.get("project", {}).get("version")


def _sdk_cli_version(repo_root: Path) -> str | None:
    main_py = repo_root / "src" / "aoa_sdk" / "cli" / "main.py"
    if not main_py.exists():
        return None
    match = re.search(r'print\("aoa-sdk ([0-9]+\.[0-9]+\.[0-9]+)"\)', main_py.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def _has_exact_readme_banner(repo_root: Path, tag: str) -> bool:
    readme = repo_root / "README.md"
    if not readme.exists():
        return False
    return _banner_for(tag) in readme.read_text(encoding="utf-8")


def _tracked_worktree_dirty(repo_root: Path) -> bool:
    completed = _run(
        ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=no"],
        cwd=repo_root,
        check=False,
    )
    return bool(completed.stdout.strip())


def _public_surface_drift_paths(repo_root: Path, tag: str | None) -> list[str]:
    if tag:
        diff_args = ["git", "-C", str(repo_root), "diff", "--name-only", f"{tag}..HEAD"]
    else:
        diff_args = ["git", "-C", str(repo_root), "ls-files"]
    completed = _run(diff_args, cwd=repo_root, check=False)
    if completed.returncode != 0:
        return []
    changed = []
    for line in completed.stdout.splitlines():
        rel = line.strip()
        if not rel:
            continue
        if rel in PUBLIC_SURFACE_FILES or rel.startswith(PUBLIC_SURFACE_PREFIXES):
            changed.append(rel)
            continue
        if rel in PACKAGE_VERSION_FILES.get(repo_root.name, ()):
            changed.append(rel)
    return changed


def _resolve_workspace_root(root: str | Path) -> tuple[Workspace, Path]:
    candidate = Path(root).expanduser().resolve()
    sdk_root = candidate if (candidate / "src" / "aoa_sdk").exists() else candidate / "aoa-sdk"
    if not (sdk_root / "src" / "aoa_sdk").exists():
        raise FileNotFoundError(f"Could not locate aoa-sdk under {candidate}")
    workspace = Workspace.discover(sdk_root)
    return workspace, workspace.federation_root.resolve()


def _release_doc_path(repo_root: Path) -> Path | None:
    if (repo_root / "docs" / "RELEASING.md").exists():
        return repo_root / "docs" / "RELEASING.md"
    if (repo_root / "RELEASING.md").exists():
        return repo_root / "RELEASING.md"
    return None


class ReleaseAPI:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def audit(
        self,
        *,
        workspace_root: str | Path | None = None,
        phase: ReleaseAuditPhase,
        repo: str | None = None,
        include_all: bool = False,
        strict: bool = False,
    ) -> ReleaseAuditResult:
        selected = self._selected_repos(repo=repo, include_all=include_all)
        reports: list[ReleaseAuditRepoReport] = []
        for repo_name in selected:
            repo_root = self.workspace.repo_path(repo_name)
            if phase == "preflight":
                reports.append(self._audit_preflight(repo_name, repo_root))
            elif phase == "postpublish":
                reports.append(self._audit_postpublish(repo_name, repo_root))
            else:
                reports.append(self._audit_cadence(repo_name, repo_root))
        passed = all(report.passed for report in reports)
        return ReleaseAuditResult(
            workspace_root=str((Path(workspace_root) if workspace_root else self.workspace.federation_root).resolve()),
            phase=phase,
            strict=strict,
            passed=passed,
            repo_reports=reports,
        )

    def publish(
        self,
        *,
        workspace_root: str | Path | None = None,
        repo: str | None = None,
        all_due: bool = False,
        dry_run: bool = True,
    ) -> ReleasePublishResult:
        if repo is None and not all_due:
            raise ValueError("choose one target repo or use --all-due")
        selected = [repo] if repo is not None else [
            report.repo
            for report in self.audit(workspace_root=workspace_root, phase="cadence", include_all=True, strict=False).repo_reports
            if report.due
        ]
        repo_reports: list[ReleasePublishRepoReport] = []
        if not selected:
            return ReleasePublishResult(
                workspace_root=str((Path(workspace_root) if workspace_root else self.workspace.federation_root).resolve()),
                dry_run=dry_run,
                passed=True,
                repo_reports=[],
            )
        preflight = self.audit(
            workspace_root=workspace_root,
            phase="preflight",
            repo=selected[0] if len(selected) == 1 else None,
            include_all=len(selected) > 1,
            strict=True,
        )
        preflight_by_repo = {report.repo: report for report in preflight.repo_reports}
        if not preflight.passed:
            for repo_name in selected:
                repo_root = self.workspace.repo_path(repo_name)
                release = self._read_release(repo_root)
                repo_reports.append(
                    ReleasePublishRepoReport(
                        repo=repo_name,
                        repo_root=str(repo_root),
                        tag=release.tag,
                        version=release.version,
                        dry_run=dry_run,
                        passed=False,
                        postpublish_passed=False,
                        actions=["preflight failed"],
                    )
                )
            return ReleasePublishResult(
                workspace_root=str((Path(workspace_root) if workspace_root else self.workspace.federation_root).resolve()),
                dry_run=dry_run,
                passed=False,
                repo_reports=repo_reports,
            )

        for repo_name in selected:
            repo_root = self.workspace.repo_path(repo_name)
            release = self._read_release(repo_root)
            repo_preflight = preflight_by_repo[repo_name]
            actions, release_url = self._publish_repo(repo_name, repo_root, release, dry_run=dry_run)
            postpublish = None if dry_run else self._audit_postpublish(repo_name, repo_root)
            publish_passed = repo_preflight.passed if dry_run else repo_preflight.passed and postpublish is not None and postpublish.passed
            repo_reports.append(
                ReleasePublishRepoReport(
                    repo=repo_name,
                    repo_root=str(repo_root),
                    tag=release.tag,
                    version=release.version,
                    dry_run=dry_run,
                    passed=publish_passed,
                    postpublish_passed=postpublish.passed if postpublish is not None else False,
                    release_url=release_url or (postpublish.release_url if postpublish is not None else None),
                    actions=actions,
                )
            )
        return ReleasePublishResult(
            workspace_root=str((Path(workspace_root) if workspace_root else self.workspace.federation_root).resolve()),
            dry_run=dry_run,
            passed=all(report.passed for report in repo_reports),
            repo_reports=repo_reports,
        )

    def _selected_repos(self, *, repo: str | None, include_all: bool) -> list[str]:
        if repo is not None:
            if repo == "8Dionysus":
                raise ValueError("8Dionysus is excluded from release mutation and publication")
            if repo not in OWNER_RELEASE_REPOS:
                raise ValueError(f"Unknown owner repo {repo!r}")
            return [repo]
        if include_all:
            return [name for name in OWNER_RELEASE_REPOS if self.workspace.has_repo(name)]
        raise ValueError("choose one repo or pass --all")

    def _read_release(self, repo_root: Path) -> ParsedReleaseSection:
        changelog_path = repo_root / "CHANGELOG.md"
        changelog_text = changelog_path.read_text(encoding="utf-8")
        return _parse_latest_release(changelog_text)

    def _audit_preflight(self, repo: str, repo_root: Path) -> ReleaseAuditRepoReport:
        checks: list[ReleaseCheck] = []
        release_doc = _release_doc_path(repo_root)
        checks.append(
            ReleaseCheck(
                name="release-doc",
                passed=release_doc is not None,
                detail="docs/RELEASING.md must exist",
            )
        )
        release_check_path = repo_root / "scripts" / "release_check.py"
        checks.append(
            ReleaseCheck(
                name="release-check",
                passed=release_check_path.exists(),
                detail="scripts/release_check.py must exist",
            )
        )

        changelog_path = repo_root / "CHANGELOG.md"
        changelog_text = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""
        has_unreleased = "## [Unreleased]" in changelog_text
        checks.append(
            ReleaseCheck(
                name="unreleased-heading",
                passed=has_unreleased,
                detail="CHANGELOG.md must keep [Unreleased]",
            )
        )

        try:
            release = _parse_latest_release(changelog_text)
            checks.extend(
                [
                    ReleaseCheck(
                        name="summary-bullets",
                        passed=len(release.summary_bullets) > 0,
                        detail="latest release section must contain Summary bullets",
                    ),
                    ReleaseCheck(
                        name="validation-section",
                        passed=release.has_validation,
                        detail="latest release section must contain Validation",
                    ),
                    ReleaseCheck(
                        name="notes-section",
                        passed=release.has_notes,
                        detail="latest release section must contain Notes",
                    ),
                    ReleaseCheck(
                        name="readme-banner",
                        passed=_has_exact_readme_banner(repo_root, release.tag),
                        detail=_banner_for(release.tag),
                    ),
                ]
            )
        except ValueError as exc:
            release = ParsedReleaseSection(
                version="",
                tag="",
                date="",
                body="",
                summary_bullets=[],
                has_validation=False,
                has_notes=False,
            )
            checks.append(ReleaseCheck(name="latest-release-section", passed=False, detail=str(exc)))

        dirty_before = _tracked_worktree_dirty(repo_root)
        checks.append(
            ReleaseCheck(
                name="clean-tracked-worktree",
                passed=not dirty_before,
                detail="tracked worktree must be clean before release audit",
            )
        )

        fetched, fetch_detail = _git_fetch_origin(repo_root)
        checks.append(ReleaseCheck(name="origin-fetch", passed=fetched, detail=fetch_detail))
        branch = ""
        head_sha = ""
        origin_main_sha = ""
        if fetched:
            try:
                branch = _git_stdout(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
                head_sha = _git_stdout(repo_root, "rev-parse", "HEAD")
                origin_main_sha = _git_stdout(repo_root, "rev-parse", "refs/remotes/origin/main")
                checks.append(
                    ReleaseCheck(
                        name="main-sync",
                        passed=branch == "main" and head_sha == origin_main_sha,
                        detail="release publication must run from main synced with origin/main",
                    )
                )
            except RuntimeError as exc:
                checks.append(ReleaseCheck(name="main-sync", passed=False, detail=str(exc)))

        if release.tag:
            exact_tag_exists = _git_returncode(repo_root, "show-ref", "--tags", "--verify", f"refs/tags/{release.tag}") == 0
            checks.append(
                ReleaseCheck(
                    name="tag-version-alignment",
                    passed=True if not exact_tag_exists else True,
                    detail=f"expected release tag {release.tag}" if not exact_tag_exists else f"local tag {release.tag} exists",
                )
            )

        if repo == "aoa-sdk" and release.version:
            pyproject_version = _pyproject_version(repo_root)
            cli_version = _sdk_cli_version(repo_root)
            checks.extend(
                [
                    ReleaseCheck(
                        name="pyproject-version",
                        passed=pyproject_version == release.version,
                        detail=f"pyproject version must equal {release.version}",
                    ),
                    ReleaseCheck(
                        name="cli-version",
                        passed=cli_version == release.version,
                        detail=f"CLI version must equal {release.version}",
                    ),
                ]
            )

        if release_check_path.exists():
            completed = _run([sys.executable, str(release_check_path)], cwd=repo_root, env=os.environ.copy(), check=False)
            checks.append(
                ReleaseCheck(
                    name="release-check-green",
                    passed=completed.returncode == 0,
                    detail=_strip(completed.stderr) or _strip(completed.stdout) or "release_check.py passed",
                )
            )
            checks.append(
                ReleaseCheck(
                    name="release-check-drift",
                    passed=not _tracked_worktree_dirty(repo_root),
                    detail="release_check.py must not leave tracked drift behind",
                )
            )

        passed = all(check.passed for check in checks)
        return ReleaseAuditRepoReport(
            repo=repo,
            repo_root=str(repo_root),
            phase="preflight",
            passed=passed,
            expected_version=release.version or None,
            latest_tag=release.tag or None,
            checks=checks,
        )

    def _audit_postpublish(self, repo: str, repo_root: Path) -> ReleaseAuditRepoReport:
        release = self._read_release(repo_root)
        checks: list[ReleaseCheck] = []
        fetched, fetch_detail = _git_fetch_origin(repo_root)
        checks.append(ReleaseCheck(name="origin-fetch", passed=fetched, detail=fetch_detail))
        origin_readme = ""
        if fetched:
            try:
                origin_readme = _git_stdout(repo_root, "show", "refs/remotes/origin/main:README.md")
                checks.append(
                    ReleaseCheck(
                        name="origin-readme-banner",
                        passed=_banner_for(release.tag) in origin_readme,
                        detail="origin/main README must expose the exact current-release banner",
                    )
                )
            except RuntimeError as exc:
                checks.append(ReleaseCheck(name="origin-readme-banner", passed=False, detail=str(exc)))

        remote_tag_exists = False
        if fetched:
            try:
                remote_tag = _run(
                    ["git", "-C", str(repo_root), "ls-remote", "--tags", "origin", f"refs/tags/{release.tag}"],
                    cwd=repo_root,
                    check=False,
                    timeout=REMOTE_COMMAND_TIMEOUT_SECONDS,
                )
                remote_tag_exists = bool(remote_tag.stdout.strip())
            except subprocess.TimeoutExpired:
                remote_tag_exists = False
        checks.append(
            ReleaseCheck(
                name="remote-tag",
                passed=remote_tag_exists,
                detail=f"origin must contain {release.tag}",
            )
        )

        release_view = _gh_release_view(repo, release.tag, cwd=repo_root)
        checks.append(
            ReleaseCheck(
                name="github-release",
                passed=release_view is not None,
                detail=f"GitHub Release must exist for {release.tag}",
            )
        )
        release_url = release_view["url"] if release_view else None
        published_at = release_view["publishedAt"] if release_view else None
        if release_view is not None:
            latest_tag = next((item["tagName"] for item in _gh_release_list(repo, cwd=repo_root) if item.get("isLatest")), None)
            checks.append(
                ReleaseCheck(
                    name="latest-tag",
                    passed=latest_tag == release.tag,
                    detail=f"latest GitHub Release must point at {release.tag}",
                )
            )
            checks.extend(validate_release_body(repo, release, release_view.get("body", "")))

        passed = all(check.passed for check in checks)
        return ReleaseAuditRepoReport(
            repo=repo,
            repo_root=str(repo_root),
            phase="postpublish",
            passed=passed,
            expected_version=release.version,
            latest_tag=release.tag,
            release_url=release_url,
            published_at=published_at,
            checks=checks,
        )

    def _audit_cadence(self, repo: str, repo_root: Path) -> ReleaseAuditRepoReport:
        checks: list[ReleaseCheck] = []
        latest_tag: str | None
        try:
            latest_tag = _git_stdout(repo_root, "describe", "--tags", "--abbrev=0")
        except RuntimeError:
            latest_tag = None

        commits_since_tag = 0
        if latest_tag is not None:
            commits_since_tag = int(_git_stdout(repo_root, "rev-list", "--count", f"{latest_tag}..HEAD"))
        else:
            commits_since_tag = int(_git_stdout(repo_root, "rev-list", "--count", "HEAD"))

        release_view = _gh_release_view(repo, latest_tag, cwd=repo_root) if latest_tag else None
        release_url = release_view["url"] if release_view else None
        published_at = release_view["publishedAt"] if release_view else None
        hours_since_release: float | None = None
        reasons: list[str] = []
        if latest_tag is None:
            reasons.append("missing latest tag")
        if latest_tag is not None and commits_since_tag > 15:
            reasons.append(f"{commits_since_tag} commits since {latest_tag}")
        if published_at is None:
            reasons.append("missing published GitHub release")
        else:
            published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            hours_since_release = (datetime.now(UTC) - published).total_seconds() / 3600
            if hours_since_release > 48:
                reasons.append(f"{hours_since_release:.1f} hours since latest release")
        drift_paths = _public_surface_drift_paths(repo_root, latest_tag)
        if drift_paths:
            reasons.append("public-surface drift since latest tag")
        due = bool(reasons)
        checks.extend(
            [
                ReleaseCheck(name="latest-tag-present", passed=latest_tag is not None, detail="repo should have a latest tag"),
                ReleaseCheck(name="commit-threshold", passed=commits_since_tag <= 15, detail="release becomes due after 15 commits"),
                ReleaseCheck(
                    name="release-age-threshold",
                    passed=hours_since_release is not None and hours_since_release <= 48 if hours_since_release is not None else False,
                    detail="release becomes due after 48 hours",
                ),
                ReleaseCheck(
                    name="public-surface-drift",
                    passed=not drift_paths,
                    detail=", ".join(drift_paths[:8]) if drift_paths else "no public-surface drift since latest tag",
                ),
            ]
        )
        return ReleaseAuditRepoReport(
            repo=repo,
            repo_root=str(repo_root),
            phase="cadence",
            passed=not due,
            latest_tag=latest_tag,
            release_url=release_url,
            published_at=published_at,
            commits_since_tag=commits_since_tag,
            hours_since_release=hours_since_release,
            due=due,
            blocked_reason="; ".join(reasons) if reasons else None,
            checks=checks,
        )

    def _publish_repo(
        self,
        repo: str,
        repo_root: Path,
        release: ParsedReleaseSection,
        *,
        dry_run: bool,
    ) -> tuple[list[str], str | None]:
        actions: list[str] = []
        release_url: str | None = None
        tag_commit = None
        head_commit = _git_stdout(repo_root, "rev-parse", "HEAD")
        if _git_returncode(repo_root, "show-ref", "--tags", "--verify", f"refs/tags/{release.tag}") == 0:
            tag_commit = _git_stdout(repo_root, "rev-list", "-n", "1", release.tag)

        if tag_commit is None:
            actions.append(f"create annotated tag {release.tag}")
        elif tag_commit != head_commit:
            actions.append(f"update annotated tag {release.tag} to HEAD")
        else:
            actions.append(f"reuse existing tag {release.tag}")

        release_view = _gh_release_view(repo, release.tag, cwd=repo_root)
        actions.append("create GitHub Release" if release_view is None else "update GitHub Release")
        actions.append("set GitHub Release as latest")

        if dry_run:
            return actions, release_view["url"] if release_view else None

        if tag_commit is None:
            _run(["git", "-C", str(repo_root), "tag", "-a", release.tag, "-m", release.tag, head_commit], cwd=repo_root, check=True)
            _run(
                ["git", "-C", str(repo_root), "push", "origin", f"refs/tags/{release.tag}"],
                cwd=repo_root,
                check=True,
                timeout=PUBLISH_COMMAND_TIMEOUT_SECONDS,
            )
        elif tag_commit != head_commit:
            _run(["git", "-C", str(repo_root), "tag", "-fa", release.tag, "-m", release.tag, head_commit], cwd=repo_root, check=True)
            _run(
                ["git", "-C", str(repo_root), "push", "--force", "origin", f"refs/tags/{release.tag}"],
                cwd=repo_root,
                check=True,
                timeout=PUBLISH_COMMAND_TIMEOUT_SECONDS,
            )

        notes = build_release_body(repo, release)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
            handle.write(notes)
            notes_path = handle.name
        try:
            if release_view is None:
                _run(
                    [
                        "gh",
                        "release",
                        "create",
                        release.tag,
                        "--repo",
                        _github_repo_slug(repo),
                        "--title",
                        release.tag,
                        "--notes-file",
                        notes_path,
                        "--latest",
                    ],
                    cwd=repo_root,
                    check=True,
                    timeout=PUBLISH_COMMAND_TIMEOUT_SECONDS,
                )
            else:
                _run(
                    [
                        "gh",
                        "release",
                        "edit",
                        release.tag,
                        "--repo",
                        _github_repo_slug(repo),
                        "--title",
                        release.tag,
                        "--notes-file",
                        notes_path,
                        "--latest",
                    ],
                    cwd=repo_root,
                    check=True,
                    timeout=PUBLISH_COMMAND_TIMEOUT_SECONDS,
                )
        finally:
            Path(notes_path).unlink(missing_ok=True)

        refreshed = _gh_release_view(repo, release.tag, cwd=repo_root)
        release_url = refreshed["url"] if refreshed else None
        return actions, release_url
