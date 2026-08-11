#!/usr/bin/env python3
"""Run the owner-local validation evidence graph and emit a bound receipt."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
import platform
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path, PurePosixPath
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "config" / "validation_graph.json"
SCHEMA_VERSION = "aoa_validation_evidence_graph_v1"
RECEIPT_SCHEMA_VERSION = "aoa_validation_evidence_receipt_v1"
TIERS = {"instant", "fast", "contextual", "semantic", "full", "artifact"}
ROOT_KEYS = {
    "schema_version",
    "graph_id",
    "owner_repo",
    "default_profile",
    "unknown_change_policy",
    "routing_status",
    "instant_budget_seconds",
    "max_workers",
    "claims",
    "profiles",
    "routes",
    "nodes",
}
CLAIM_KEYS = {"id", "risk", "required_evidence"}
ROUTE_KEYS = {"id", "patterns", "claims"}
NODE_KEYS = {
    "id",
    "tier",
    "priority",
    "depends_on",
    "provides_evidence",
    "timeout_seconds",
    "inputs",
    "steps",
}
STEP_KEYS = {"id", "argv"}
TAIL_CHARACTERS = 4_000


class ManifestError(ValueError):
    """Raised when a graph manifest fails closed."""


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Owner repository root whose source, commands, and sufficiency are being validated.",
    )
    parser.add_argument("--profile", help="Named owner claim profile to execute.")
    parser.add_argument(
        "--changed-path",
        action="append",
        default=[],
        help="Changed repo-relative path. Requires --shadow-route.",
    )
    parser.add_argument(
        "--shadow-route",
        action="store_true",
        help="Exercise non-authoritative path routing instead of a named profile.",
    )
    parser.add_argument("--max-workers", type=int)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def _json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"manifest is missing: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"manifest is unreadable or invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ManifestError("manifest root must be a JSON object")
    return payload


def _unknown_keys(value: dict[str, Any], expected: set[str], location: str) -> list[str]:
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    issues = [f"{location}: unknown key {key!r}" for key in unknown]
    issues.extend(f"{location}: missing key {key!r}" for key in missing)
    return issues


def _string_list(value: Any, location: str, *, nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        raise ManifestError(f"{location} must be a{' non-empty' if nonempty else ''} list")
    if any(not isinstance(item, str) or not item for item in value):
        raise ManifestError(f"{location} must contain non-empty strings")
    if len(set(value)) != len(value):
        raise ManifestError(f"{location} must not contain duplicates")
    return value


def _safe_relative_pattern(value: str, location: str) -> None:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\x00" in value:
        raise ManifestError(f"{location} must be a safe repo-relative pattern")


def _topological_order(nodes: list[dict[str, Any]]) -> list[str]:
    by_id = {node["id"]: node for node in nodes}
    indegree = {node_id: 0 for node_id in by_id}
    children: dict[str, list[str]] = {node_id: [] for node_id in by_id}
    for node in nodes:
        for dependency in node["depends_on"]:
            indegree[node["id"]] += 1
            children[dependency].append(node["id"])
    ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
    ordered: list[str] = []
    while ready:
        node_id = ready.pop(0)
        ordered.append(node_id)
        for child in sorted(children[node_id]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready.sort()
    if len(ordered) != len(nodes):
        raise ManifestError("nodes: dependency graph contains a cycle")
    return ordered


def validate_manifest(manifest: dict[str, Any]) -> None:
    issues = _unknown_keys(manifest, ROOT_KEYS, "manifest")
    if issues:
        raise ManifestError("; ".join(issues))
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise ManifestError(f"schema_version must be {SCHEMA_VERSION!r}")
    for key in ("graph_id", "owner_repo", "default_profile"):
        if not isinstance(manifest[key], str) or not manifest[key]:
            raise ManifestError(f"{key} must be a non-empty string")
    if manifest["unknown_change_policy"] != "full":
        raise ManifestError("unknown_change_policy must remain fail-closed as 'full'")
    if manifest["routing_status"] != "shadow_only":
        raise ManifestError("routing_status must remain 'shadow_only' until owner promotion")
    budget = manifest["instant_budget_seconds"]
    if not isinstance(budget, (int, float)) or isinstance(budget, bool) or not 0 < budget <= 1:
        raise ManifestError("instant_budget_seconds must be greater than zero and at most one")
    max_workers = manifest["max_workers"]
    if not isinstance(max_workers, int) or isinstance(max_workers, bool) or not 1 <= max_workers <= 16:
        raise ManifestError("max_workers must be an integer from 1 through 16")

    claims = manifest["claims"]
    if not isinstance(claims, list) or not claims:
        raise ManifestError("claims must be a non-empty list")
    claim_ids: list[str] = []
    claim_evidence: dict[str, list[str]] = {}
    for index, claim in enumerate(claims):
        location = f"claims[{index}]"
        if not isinstance(claim, dict):
            raise ManifestError(f"{location} must be an object")
        issues = _unknown_keys(claim, CLAIM_KEYS, location)
        if issues:
            raise ManifestError("; ".join(issues))
        claim_id = claim["id"]
        if not isinstance(claim_id, str) or not claim_id:
            raise ManifestError(f"{location}.id must be a non-empty string")
        if not isinstance(claim["risk"], str) or not claim["risk"]:
            raise ManifestError(f"{location}.risk must be a non-empty string")
        claim_ids.append(claim_id)
        claim_evidence[claim_id] = _string_list(
            claim["required_evidence"], f"{location}.required_evidence"
        )
    if len(set(claim_ids)) != len(claim_ids):
        raise ManifestError("claims: claim ids must be unique")
    claim_id_set = set(claim_ids)

    profiles = manifest["profiles"]
    if not isinstance(profiles, dict) or not profiles:
        raise ManifestError("profiles must be a non-empty object")
    if manifest["default_profile"] not in profiles:
        raise ManifestError("default_profile must name a declared profile")
    if "full" not in profiles or "instant" not in profiles:
        raise ManifestError("profiles must declare both 'instant' and 'full'")
    for profile_id, profile_claims in profiles.items():
        if not isinstance(profile_id, str) or not profile_id:
            raise ManifestError("profile ids must be non-empty strings")
        values = _string_list(profile_claims, f"profiles.{profile_id}")
        unknown_claims = sorted(set(values) - claim_id_set)
        if unknown_claims:
            raise ManifestError(
                f"profiles.{profile_id}: unknown claims {', '.join(unknown_claims)}"
            )
    if set(profiles["full"]) != claim_id_set:
        raise ManifestError("profiles.full must contain every owner claim")

    routes = manifest["routes"]
    if not isinstance(routes, list) or not routes:
        raise ManifestError("routes must be a non-empty list")
    route_ids: list[str] = []
    for index, route in enumerate(routes):
        location = f"routes[{index}]"
        if not isinstance(route, dict):
            raise ManifestError(f"{location} must be an object")
        issues = _unknown_keys(route, ROUTE_KEYS, location)
        if issues:
            raise ManifestError("; ".join(issues))
        route_id = route["id"]
        if not isinstance(route_id, str) or not route_id:
            raise ManifestError(f"{location}.id must be a non-empty string")
        route_ids.append(route_id)
        patterns = _string_list(route["patterns"], f"{location}.patterns")
        for pattern in patterns:
            _safe_relative_pattern(pattern, f"{location}.patterns")
        routed_claims = _string_list(route["claims"], f"{location}.claims")
        unknown_claims = sorted(set(routed_claims) - claim_id_set)
        if unknown_claims:
            raise ManifestError(f"{location}: unknown claims {', '.join(unknown_claims)}")
    if len(set(route_ids)) != len(route_ids):
        raise ManifestError("routes: route ids must be unique")

    nodes = manifest["nodes"]
    if not isinstance(nodes, list) or not nodes:
        raise ManifestError("nodes must be a non-empty list")
    node_ids: list[str] = []
    evidence_providers: dict[str, str] = {}
    for index, node in enumerate(nodes):
        location = f"nodes[{index}]"
        if not isinstance(node, dict):
            raise ManifestError(f"{location} must be an object")
        issues = _unknown_keys(node, NODE_KEYS, location)
        if issues:
            raise ManifestError("; ".join(issues))
        node_id = node["id"]
        if not isinstance(node_id, str) or not node_id:
            raise ManifestError(f"{location}.id must be a non-empty string")
        node_ids.append(node_id)
        if node["tier"] not in TIERS:
            raise ManifestError(f"{location}.tier must be one of {sorted(TIERS)}")
        priority = node["priority"]
        if not isinstance(priority, int) or isinstance(priority, bool):
            raise ManifestError(f"{location}.priority must be an integer")
        _string_list(node["depends_on"], f"{location}.depends_on", nonempty=False)
        evidence = _string_list(node["provides_evidence"], f"{location}.provides_evidence")
        for evidence_id in evidence:
            previous = evidence_providers.get(evidence_id)
            if previous is not None:
                raise ManifestError(
                    f"evidence {evidence_id!r} has colliding providers {previous!r} and {node_id!r}"
                )
            evidence_providers[evidence_id] = node_id
        timeout = node["timeout_seconds"]
        if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= 3600:
            raise ManifestError(f"{location}.timeout_seconds must be from 1 through 3600")
        inputs = _string_list(node["inputs"], f"{location}.inputs")
        for pattern in inputs:
            _safe_relative_pattern(pattern, f"{location}.inputs")
        steps = node["steps"]
        if not isinstance(steps, list) or not steps:
            raise ManifestError(f"{location}.steps must be a non-empty list")
        step_ids: list[str] = []
        for step_index, step in enumerate(steps):
            step_location = f"{location}.steps[{step_index}]"
            if not isinstance(step, dict):
                raise ManifestError(f"{step_location} must be an object")
            issues = _unknown_keys(step, STEP_KEYS, step_location)
            if issues:
                raise ManifestError("; ".join(issues))
            step_id = step["id"]
            if not isinstance(step_id, str) or not step_id:
                raise ManifestError(f"{step_location}.id must be a non-empty string")
            step_ids.append(step_id)
            argv = _string_list(step["argv"], f"{step_location}.argv")
            if any("\x00" in token for token in argv):
                raise ManifestError(f"{step_location}.argv must not contain NUL")
        if len(set(step_ids)) != len(step_ids):
            raise ManifestError(f"{location}: step ids must be unique within a node")
    if len(set(node_ids)) != len(node_ids):
        raise ManifestError("nodes: node ids must be unique")

    node_id_set = set(node_ids)
    for index, node in enumerate(nodes):
        unknown_dependencies = sorted(set(node["depends_on"]) - node_id_set)
        if unknown_dependencies:
            raise ManifestError(
                f"nodes[{index}].depends_on: unknown nodes {', '.join(unknown_dependencies)}"
            )
        if node["id"] in node["depends_on"]:
            raise ManifestError(f"nodes[{index}]: a node cannot depend on itself")
    _topological_order(nodes)

    required_evidence = {
        evidence_id for values in claim_evidence.values() for evidence_id in values
    }
    missing_providers = sorted(required_evidence - set(evidence_providers))
    if missing_providers:
        raise ManifestError(
            "claims require evidence without providers: " + ", ".join(missing_providers)
        )
    unused_evidence = sorted(set(evidence_providers) - required_evidence)
    if unused_evidence:
        raise ManifestError("nodes provide unclaimed evidence: " + ", ".join(unused_evidence))

    instant_claims = set(profiles["instant"])
    instant_evidence = {
        evidence_id
        for claim_id in instant_claims
        for evidence_id in claim_evidence[claim_id]
    }
    instant_nodes = {evidence_providers[evidence_id] for evidence_id in instant_evidence}
    by_id = {node["id"]: node for node in nodes}
    if any(by_id[node_id]["tier"] != "instant" for node_id in instant_nodes):
        raise ManifestError("profiles.instant may activate only instant-tier evidence nodes")


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = _json_object(path)
    validate_manifest(manifest)
    return manifest


def _matches(path: str, pattern: str) -> bool:
    if pattern == "**":
        return True
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(f"{prefix}/")
    candidate = PurePosixPath(path)
    return candidate.match(pattern)


def select_claims(
    manifest: dict[str, Any],
    *,
    profile: str | None,
    changed_paths: Sequence[str],
    shadow_route: bool,
) -> tuple[list[str], dict[str, Any]]:
    profiles = manifest["profiles"]
    if shadow_route:
        if profile is not None:
            raise ManifestError("--profile and --shadow-route are mutually exclusive")
        if not changed_paths:
            raise ManifestError("--shadow-route requires at least one --changed-path")
        normalized: list[str] = []
        for value in changed_paths:
            path = PurePosixPath(value)
            if path.is_absolute() or ".." in path.parts or "\x00" in value:
                raise ManifestError(f"changed path is not safe and repo-relative: {value!r}")
            normalized.append(path.as_posix())
        selected: set[str] = set(profiles["instant"])
        matched_routes: dict[str, list[str]] = {}
        unmatched: list[str] = []
        for path in normalized:
            matches = [
                route
                for route in manifest["routes"]
                if any(_matches(path, pattern) for pattern in route["patterns"])
            ]
            if not matches:
                unmatched.append(path)
                continue
            matched_routes[path] = [route["id"] for route in matches]
            for route in matches:
                selected.update(route["claims"])
        fallback = bool(unmatched)
        if fallback:
            selected = set(profiles["full"])
        ordered = [claim["id"] for claim in manifest["claims"] if claim["id"] in selected]
        return ordered, {
            "mode": "shadow",
            "authoritative": False,
            "changed_paths": normalized,
            "matched_routes": matched_routes,
            "unmatched_paths": unmatched,
            "fallback_to_full": fallback,
        }

    if changed_paths:
        raise ManifestError("--changed-path is accepted only with --shadow-route")
    selected_profile = profile or manifest["default_profile"]
    if selected_profile not in profiles:
        raise ManifestError(f"unknown profile: {selected_profile!r}")
    return list(profiles[selected_profile]), {
        "mode": "profile",
        "authoritative": selected_profile == "full",
        "profile": selected_profile,
        "changed_paths": [],
        "matched_routes": {},
        "unmatched_paths": [],
        "fallback_to_full": False,
    }


def activate_nodes(manifest: dict[str, Any], claim_ids: Sequence[str]) -> list[str]:
    claims = {claim["id"]: claim for claim in manifest["claims"]}
    unknown = sorted(set(claim_ids) - set(claims))
    if unknown:
        raise ManifestError("unknown requested claims: " + ", ".join(unknown))
    required_evidence = {
        evidence_id
        for claim_id in claim_ids
        for evidence_id in claims[claim_id]["required_evidence"]
    }
    provider = {
        evidence_id: node["id"]
        for node in manifest["nodes"]
        for evidence_id in node["provides_evidence"]
    }
    selected = {provider[evidence_id] for evidence_id in required_evidence}
    by_id = {node["id"]: node for node in manifest["nodes"]}
    pending = list(selected)
    while pending:
        node_id = pending.pop()
        for dependency in by_id[node_id]["depends_on"]:
            if dependency not in selected:
                selected.add(dependency)
                pending.append(dependency)
    return [node["id"] for node in manifest["nodes"] if node["id"] in selected]


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git(args: Sequence[str], repo_root: Path) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    return completed.stdout if completed.returncode == 0 else b""


def require_git_top_level(repo_root: Path) -> None:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        raise ManifestError(f"owner repository root is not a Git checkout: {repo_root}")
    git_top_level = Path(completed.stdout.strip()).resolve()
    if git_top_level != repo_root:
        raise ManifestError(
            "--repo-root must equal the owner Git top-level: "
            f"requested={repo_root} actual={git_top_level}"
        )


def repository_identity(repo_root: Path) -> dict[str, Any]:
    commit = _git(["rev-parse", "HEAD"], repo_root).decode().strip() or None
    tree = _git(["rev-parse", "HEAD^{tree}"], repo_root).decode().strip() or None
    status = _git(["status", "--porcelain=v1", "-z", "--untracked-files=all"], repo_root)
    patch = _git(["diff", "--binary", "HEAD", "--"], repo_root)
    untracked = _git(["ls-files", "--others", "--exclude-standard", "-z"], repo_root)
    untracked_hasher = hashlib.sha256()
    for raw_path in sorted(item for item in untracked.split(b"\0") if item):
        rel_path = os.fsdecode(raw_path)
        path = repo_root / rel_path
        untracked_hasher.update(raw_path)
        untracked_hasher.update(b"\0")
        try:
            if path.is_symlink():
                untracked_hasher.update(os.readlink(path).encode())
            elif path.is_file():
                untracked_hasher.update(path.read_bytes())
        except OSError as exc:
            untracked_hasher.update(f"unreadable:{exc}".encode())
        untracked_hasher.update(b"\0")
    return {
        "git_commit": commit,
        "git_tree": tree,
        "dirty": bool(status),
        "status_sha256": _sha256(status),
        "worktree_patch_sha256": _sha256(patch),
        "untracked_sha256": untracked_hasher.hexdigest(),
    }


def runner_identity() -> dict[str, Any]:
    runner_path = Path(__file__).resolve()
    completed = subprocess.run(
        ["git", "-C", str(runner_path.parent), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    source_root: Path | None = None
    if completed.returncode == 0 and completed.stdout.strip():
        source_root = Path(completed.stdout.strip()).resolve()
    relative_path: str | None = None
    source_identity: dict[str, Any] | None = None
    if source_root is not None:
        try:
            relative_path = runner_path.relative_to(source_root).as_posix()
        except ValueError:
            source_root = None
        else:
            source_identity = repository_identity(source_root)
    return {
        "path": runner_path.as_posix(),
        "relative_path": relative_path,
        "sha256": _sha256(runner_path.read_bytes()),
        "source_root": source_root.as_posix() if source_root is not None else None,
        "source_repository_identity": source_identity,
    }


def input_identity(repo_root: Path, patterns: Sequence[str]) -> dict[str, Any]:
    listing = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    has_git_listing = listing.returncode == 0
    tracked = listing.stdout if has_git_listing else b""
    candidates = {
        os.fsdecode(raw_path).rstrip("/")
        for raw_path in tracked.split(b"\0")
        if raw_path
    }
    for pattern in patterns:
        if pattern == "**":
            if not has_git_listing:
                for path in repo_root.rglob("*"):
                    if ".git" in path.relative_to(repo_root).parts:
                        continue
                    if path.is_file() or path.is_symlink():
                        candidates.add(path.relative_to(repo_root).as_posix())
            continue
        try:
            if pattern.endswith("/**"):
                prefix = pattern[:-3].rstrip("/")
                expansion_root = repo_root / prefix
                expanded = (
                    [expansion_root]
                    if expansion_root.is_file() or expansion_root.is_symlink()
                    else expansion_root.rglob("*")
                )
            else:
                expanded = repo_root.glob(pattern)
            for path in expanded:
                if path.is_file() or path.is_symlink():
                    candidates.add(path.relative_to(repo_root).as_posix())
        except (OSError, ValueError) as exc:
            raise ManifestError(f"cannot expand input pattern {pattern!r}: {exc}") from exc

    selected = sorted(
        path
        for path in candidates
        if any(_matches(path, pattern) for pattern in patterns)
    )
    hasher = hashlib.sha256()
    unreadable: list[str] = []
    nested_repositories: list[dict[str, Any]] = []
    file_count = 0
    for rel_path in selected:
        path = repo_root / rel_path
        hasher.update(rel_path.encode())
        hasher.update(b"\0")
        try:
            if path.is_symlink():
                file_count += 1
                hasher.update(b"symlink\0")
                hasher.update(os.readlink(path).encode())
            elif path.is_file():
                file_count += 1
                hasher.update(b"file\0")
                hasher.update(path.read_bytes())
            elif path.is_dir():
                nested_identity = repository_identity(path)
                if nested_identity["git_commit"] is None:
                    hasher.update(b"unexpected-directory\0")
                    unreadable.append(rel_path)
                else:
                    record = {"path": rel_path, **nested_identity}
                    nested_repositories.append(record)
                    hasher.update(b"nested-git-repository\0")
                    hasher.update(
                        json.dumps(
                            record,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode()
                    )
            else:
                hasher.update(b"missing\0")
                unreadable.append(rel_path)
        except OSError:
            hasher.update(b"unreadable\0")
            unreadable.append(rel_path)
        hasher.update(b"\0")
    return {
        "patterns": list(patterns),
        "file_count": file_count,
        "nested_repository_count": len(nested_repositories),
        "nested_repositories": nested_repositories,
        "sha256": hasher.hexdigest(),
        "unreadable": unreadable,
    }


class InputIdentityCache:
    """Deduplicate identical input hashing within one immutable graph run."""

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._pending: set[tuple[str, ...]] = set()
        self._values: dict[tuple[str, ...], dict[str, Any]] = {}

    def get(self, repo_root: Path, patterns: Sequence[str]) -> dict[str, Any]:
        key = tuple(patterns)
        with self._condition:
            while key in self._pending:
                self._condition.wait()
            cached = self._values.get(key)
            if cached is not None:
                return dict(cached)
            self._pending.add(key)
        try:
            value = input_identity(repo_root, patterns)
        except BaseException:
            with self._condition:
                self._pending.remove(key)
                self._condition.notify_all()
            raise
        with self._condition:
            self._pending.remove(key)
            self._values[key] = value
            self._condition.notify_all()
        return dict(value)


def environment_identity() -> dict[str, Any]:
    packages: dict[str, str | None] = {}
    for name in ("aoa-sdk", "build", "mypy", "pytest", "ruff"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "ci": os.environ.get("CI"),
        "github_runner_os": os.environ.get("RUNNER_OS"),
        "github_runner_arch": os.environ.get("RUNNER_ARCH"),
        "github_runner_image": os.environ.get("ImageOS"),
        "packages": packages,
    }


def _expanded_argv(argv: Sequence[str]) -> list[str]:
    return [sys.executable if token == "{python}" else token for token in argv]


def _tail(value: str) -> str:
    return value[-TAIL_CHARACTERS:]


def _run_step(
    step: dict[str, Any],
    *,
    repo_root: Path,
    timeout_seconds: float,
) -> dict[str, Any]:
    argv = _expanded_argv(step["argv"])
    started = time.monotonic()
    process = subprocess.Popen(
        argv,
        cwd=repo_root,
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=os.name == "posix",
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        stdout, stderr = process.communicate()
    elapsed = time.monotonic() - started
    return {
        "id": step["id"],
        "argv": argv,
        "command_sha256": _sha256(
            json.dumps(argv, ensure_ascii=False, separators=(",", ":")).encode()
        ),
        "status": "timed_out" if timed_out else ("passed" if process.returncode == 0 else "failed"),
        "returncode": process.returncode,
        "timed_out": timed_out,
        "duration_seconds": round(elapsed, 6),
        "stdout_sha256": _sha256(stdout.encode()),
        "stderr_sha256": _sha256(stderr.encode()),
        "stdout_tail": _tail(stdout),
        "stderr_tail": _tail(stderr),
    }


def run_node(
    node: dict[str, Any],
    repo_root: Path,
    input_cache: InputIdentityCache | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    node_input_identity = (
        input_cache.get(repo_root, node["inputs"])
        if input_cache is not None
        else input_identity(repo_root, node["inputs"])
    )
    remaining = float(node["timeout_seconds"])
    step_receipts: list[dict[str, Any]] = []
    status = "passed"
    for step in node["steps"]:
        step_receipt = _run_step(step, repo_root=repo_root, timeout_seconds=remaining)
        step_receipts.append(step_receipt)
        if step_receipt["status"] != "passed":
            status = step_receipt["status"]
            break
        remaining = max(0.001, float(node["timeout_seconds"]) - (time.monotonic() - started))
    return {
        "id": node["id"],
        "tier": node["tier"],
        "status": status,
        "duration_seconds": round(time.monotonic() - started, 6),
        "input_identity": node_input_identity,
        "provides_evidence": node["provides_evidence"] if status == "passed" else [],
        "steps": step_receipts,
    }


def execute_nodes(
    manifest: dict[str, Any],
    activated: Sequence[str],
    *,
    repo_root: Path,
    max_workers: int,
    announce: bool,
) -> list[dict[str, Any]]:
    nodes = {node["id"]: node for node in manifest["nodes"] if node["id"] in activated}
    manifest_order = {node["id"]: index for index, node in enumerate(manifest["nodes"])}
    state = {node_id: "pending" for node_id in nodes}
    results: dict[str, dict[str, Any]] = {}
    running: dict[concurrent.futures.Future[dict[str, Any]], str] = {}
    failure_seen = False
    input_cache = InputIdentityCache()

    def ready_nodes() -> list[str]:
        candidates = [
            node_id
            for node_id, status in state.items()
            if status == "pending"
            and all(state[dependency] == "passed" for dependency in nodes[node_id]["depends_on"])
        ]
        return sorted(
            candidates,
            key=lambda node_id: (-nodes[node_id]["priority"], manifest_order[node_id]),
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        while any(status in {"pending", "running"} for status in state.values()):
            for node_id, status in list(state.items()):
                if status != "pending":
                    continue
                failed_dependencies = [
                    dependency
                    for dependency in nodes[node_id]["depends_on"]
                    if state[dependency]
                    in {"failed", "timed_out", "blocked_dependency", "not_run_after_failure"}
                ]
                if failed_dependencies:
                    state[node_id] = "blocked_dependency"
                    results[node_id] = {
                        "id": node_id,
                        "tier": nodes[node_id]["tier"],
                        "status": "blocked_dependency",
                        "duration_seconds": 0.0,
                        "input_identity": None,
                        "provides_evidence": [],
                        "blocked_by": failed_dependencies,
                        "steps": [],
                    }
            if failure_seen:
                for node_id, status in list(state.items()):
                    if status == "pending":
                        state[node_id] = "not_run_after_failure"
                        results[node_id] = {
                            "id": node_id,
                            "tier": nodes[node_id]["tier"],
                            "status": "not_run_after_failure",
                            "duration_seconds": 0.0,
                            "input_identity": None,
                            "provides_evidence": [],
                            "steps": [],
                        }
            else:
                for node_id in ready_nodes():
                    if len(running) >= max_workers:
                        break
                    state[node_id] = "running"
                    if announce:
                        print(f"[run] {node_id}", flush=True)
                    future = executor.submit(
                        run_node, nodes[node_id], repo_root, input_cache
                    )
                    running[future] = node_id
            if not running:
                if any(status == "pending" for status in state.values()):
                    raise ManifestError("scheduler reached an unresolved dependency state")
                break
            done, _ = concurrent.futures.wait(
                running, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for future in done:
                node_id = running.pop(future)
                result = future.result()
                results[node_id] = result
                state[node_id] = result["status"]
                if announce:
                    print(
                        f"[{result['status']}] {node_id} ({result['duration_seconds']:.3f}s)",
                        flush=True,
                    )
                    if result["status"] != "passed" and result["steps"]:
                        step = result["steps"][-1]
                        if step["stdout_tail"]:
                            print(step["stdout_tail"], flush=True)
                        if step["stderr_tail"]:
                            print(step["stderr_tail"], file=sys.stderr, flush=True)
                if result["status"] != "passed":
                    failure_seen = True
    return [results[node_id] for node_id in activated]


def build_receipt(
    manifest: dict[str, Any],
    *,
    manifest_path: Path,
    claims: Sequence[str],
    activated: Sequence[str],
    route: dict[str, Any],
    node_results: Sequence[dict[str, Any]],
    repo_root: Path,
    max_workers: int,
    started_at: dt.datetime,
    elapsed_seconds: float,
    initial_repository_identity: dict[str, Any],
    initial_manifest_sha256: str,
    initial_environment_identity: dict[str, Any],
    initial_runner_identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    claim_by_id = {claim["id"]: claim for claim in manifest["claims"]}
    required = [
        evidence_id
        for claim_id in claims
        for evidence_id in claim_by_id[claim_id]["required_evidence"]
    ]
    satisfied = {
        evidence_id
        for result in node_results
        if result["status"] == "passed"
        for evidence_id in result["provides_evidence"]
    }
    missing = sorted(set(required) - satisfied)
    final_repository_identity = repository_identity(repo_root)
    if initial_runner_identity is None:
        initial_runner_identity = runner_identity()
    final_runner_identity = runner_identity()
    final_manifest_sha256 = _sha256(manifest_path.read_bytes())
    repository_stable = initial_repository_identity == final_repository_identity
    repository_bound = all(
        identity.get("git_commit") is not None and identity.get("git_tree") is not None
        for identity in (initial_repository_identity, final_repository_identity)
    )
    manifest_stable = initial_manifest_sha256 == final_manifest_sha256
    runner_stable = initial_runner_identity == final_runner_identity
    runner_source_identities = (
        initial_runner_identity.get("source_repository_identity"),
        final_runner_identity.get("source_repository_identity"),
    )
    runner_bound = all(
        isinstance(identity, dict)
        and identity.get("git_commit") is not None
        and identity.get("git_tree") is not None
        for identity in runner_source_identities
    )
    unreadable_inputs = sorted(
        {
            path
            for result in node_results
            if isinstance(result.get("input_identity"), dict)
            for path in result["input_identity"]["unreadable"]
        }
    )
    integrity_blockers: list[str] = []
    if not repository_bound:
        integrity_blockers.append("repository_identity_unavailable")
    if not repository_stable:
        integrity_blockers.append("repository_identity_changed_during_run")
    if not manifest_stable:
        integrity_blockers.append("manifest_changed_during_run")
    if not runner_bound:
        integrity_blockers.append("runner_identity_unavailable")
    if not runner_stable:
        integrity_blockers.append("runner_identity_changed_during_run")
    if unreadable_inputs:
        integrity_blockers.append("node_inputs_unreadable")
    sufficient = (
        not missing
        and not integrity_blockers
        and all(result["status"] == "passed" for result in node_results)
    )
    full_claims = set(manifest["profiles"]["full"])
    full_scope = set(claims) == full_claims and route["mode"] == "profile"
    authoritative = bool(route["authoritative"] and full_scope)
    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "graph_id": manifest["graph_id"],
        "owner_repo": manifest["owner_repo"],
        "graph_manifest": {
            "path": manifest_path.resolve().as_posix(),
            "before_sha256": initial_manifest_sha256,
            "after_sha256": final_manifest_sha256,
            "stable": manifest_stable,
        },
        "repository_identity": {
            "before": initial_repository_identity,
            "after": final_repository_identity,
            "stable": repository_stable,
        },
        "runner_identity": {
            "before": initial_runner_identity,
            "after": final_runner_identity,
            "stable": runner_stable,
        },
        "environment_identity": initial_environment_identity,
        "started_at": started_at.isoformat(),
        "completed_at": dt.datetime.now(dt.UTC).isoformat(),
        "elapsed_seconds": round(elapsed_seconds, 6),
        "routing": route,
        "requested_claims": list(claims),
        "activated_nodes": list(activated),
        "max_workers": max_workers,
        "node_results": list(node_results),
        "evidence": {
            "required": required,
            "satisfied": sorted(satisfied),
            "missing": missing,
            "unreadable_inputs": unreadable_inputs,
        },
        "decision": {
            "sufficient": sufficient,
            "scope": "full-owner-claim-set" if full_scope else "bounded-claim-subset",
            "authoritative_for_owner_gate": authoritative,
            "shadow_routing_never_authoritative": route["mode"] == "shadow",
            "integrity_blockers": integrity_blockers,
        },
        "authority_boundary": (
            "owner-local validation sufficiency only; no central eval verdict, sibling-owner "
            "proof, runtime health, or publication authority"
        ),
    }


def _write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        repo_root = args.repo_root.resolve()
        if not repo_root.is_dir():
            raise ManifestError(f"owner repository root is not a directory: {repo_root}")
        require_git_top_level(repo_root)
        manifest_path = args.manifest.resolve()
        try:
            manifest_path.relative_to(repo_root)
        except ValueError as exc:
            raise ManifestError("manifest must be inside --repo-root") from exc
        manifest = load_manifest(manifest_path)
        if args.validate_only:
            result = {
                "ok": True,
                "schema_version": manifest["schema_version"],
                "graph_id": manifest["graph_id"],
                "owner_repo": manifest["owner_repo"],
                "node_count": len(manifest["nodes"]),
                "claim_count": len(manifest["claims"]),
            }
            print(json.dumps(result, sort_keys=True) if args.json else "validation graph: valid")
            return 0
        claims, route = select_claims(
            manifest,
            profile=args.profile,
            changed_paths=args.changed_path,
            shadow_route=args.shadow_route,
        )
        activated = activate_nodes(manifest, claims)
        max_workers = args.max_workers or manifest["max_workers"]
        if not 1 <= max_workers <= 16:
            raise ManifestError("--max-workers must be from 1 through 16")
    except ManifestError as exc:
        error = {"ok": False, "error": str(exc)}
        print(json.dumps(error, sort_keys=True) if args.json else f"validation graph: {exc}", file=sys.stderr)
        return 2

    started = time.monotonic()
    started_at = dt.datetime.now(dt.UTC)
    try:
        initial_repository_identity = repository_identity(repo_root)
        initial_runner_identity = runner_identity()
        initial_manifest_sha256 = _sha256(manifest_path.read_bytes())
        initial_environment_identity = environment_identity()
        node_results = execute_nodes(
            manifest,
            activated,
            repo_root=repo_root,
            max_workers=max_workers,
            announce=not args.json,
        )
        receipt = build_receipt(
            manifest,
            manifest_path=manifest_path,
            claims=claims,
            activated=activated,
            route=route,
            node_results=node_results,
            repo_root=repo_root,
            max_workers=max_workers,
            started_at=started_at,
            elapsed_seconds=time.monotonic() - started,
            initial_repository_identity=initial_repository_identity,
            initial_manifest_sha256=initial_manifest_sha256,
            initial_environment_identity=initial_environment_identity,
            initial_runner_identity=initial_runner_identity,
        )
    except (ManifestError, OSError, subprocess.SubprocessError) as exc:
        error = {"ok": False, "error": str(exc)}
        print(json.dumps(error, sort_keys=True) if args.json else f"validation graph: {exc}", file=sys.stderr)
        return 2
    if args.receipt is not None:
        _write_receipt(args.receipt, receipt)
    if args.json:
        print(json.dumps(receipt, sort_keys=True, ensure_ascii=False))
    else:
        decision = receipt["decision"]
        print(
            "[decision] "
            f"sufficient={str(decision['sufficient']).lower()} "
            f"scope={decision['scope']} "
            f"elapsed={receipt['elapsed_seconds']:.3f}s",
            flush=True,
        )
        if args.receipt is not None:
            print(f"[receipt] {args.receipt.resolve()}", flush=True)
    return 0 if receipt["decision"]["sufficient"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
