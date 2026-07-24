"""Validate SDK shadow routing outputs against the predecessor contract."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .core import REPO_ROOT, RouterError, default_dependency_root
from .producer import build_outputs


SCHEMA_ROOT = Path(__file__).resolve().parent / "schemas"
OUTPUT_SCHEMA_NAMES = {
    "cross_repo_registry.min.json": "cross-repo-registry.schema.json",
    "aoa_router.min.json": "aoa-router.schema.json",
    "task_to_surface_hints.json": "task-to-surface-hints.schema.json",
    "task_to_tier_hints.json": "task-to-tier-hints.schema.json",
    "quest_dispatch_hints.min.json": "quest-dispatch-hints.schema.json",
    "federation_entrypoints.min.json": "federation-entrypoints.schema.json",
    "return_navigation_hints.min.json": "return-navigation-hints.schema.json",
    "recommended_paths.min.json": "recommended-paths.schema.json",
    "kag_source_lift_relation_hints.min.json": (
        "kag-source-lift-relation-hints.schema.json"
    ),
    "composite_stress_route_hints.min.json": (
        "composite-stress-route-hints.schema.json"
    ),
    "stats_regrounding_hints.min.json": "stats-regrounding-hints.schema.json",
    "owner_layer_shortlist.min.json": "owner-layer-shortlist.schema.json",
    "pairing_hints.min.json": "pairing-hints.schema.json",
    "tiny_model_entrypoints.json": "tiny-model-entrypoints.schema.json",
}
SOURCE_OWNED_PAYLOAD_KEYS = {
    "content_markdown",
    "sections",
    "technique_path",
    "skill_path",
    "eval_path",
    "one_line_intent",
    "use_when_short",
    "do_not_use_short",
    "inputs_short",
    "outputs_short",
    "core_contract_short",
    "main_risk_short",
    "validation_short",
    "trigger_boundary_short",
    "workflow_short",
    "main_anti_patterns_short",
    "verification_short",
    "bounded_claim_short",
    "blind_spot_short",
    "what_this_does_not_prove",
}


@dataclass(frozen=True)
class ValidationIssue:
    location: str
    message: str


@lru_cache(maxsize=None)
def load_schema(schema_name: str) -> dict[str, Any]:
    schema_path = SCHEMA_ROOT / Path(schema_name).name
    try:
        payload = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RouterError(f"could not load schema {schema_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RouterError(f"schema {schema_path} must contain an object")
    return payload


@lru_cache(maxsize=None)
def get_schema_registry() -> Registry:
    resources: list[tuple[str, Resource[Any]]] = []
    for schema_path in sorted(SCHEMA_ROOT.glob("*.json")):
        schema = load_schema(schema_path.name)
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id.strip():
            raise RouterError(f"{schema_path.name} is missing a usable $id")
        resources.append((schema_id, Resource.from_contents(schema)))
    return Registry().with_resources(resources)


@lru_cache(maxsize=None)
def get_schema_validator(schema_name: str) -> Draft202012Validator:
    return Draft202012Validator(
        load_schema(schema_name),
        registry=get_schema_registry(),
        format_checker=FormatChecker(),
    )


def _format_schema_path(path_parts: Iterable[Any]) -> str:
    rendered = ""
    for part in path_parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered.removeprefix(".")


def _validate_schema(
    payload: dict[str, Any],
    *,
    filename: str,
    issues: list[ValidationIssue],
) -> None:
    validator = get_schema_validator(OUTPUT_SCHEMA_NAMES[filename])
    errors = sorted(
        validator.iter_errors(payload),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    for error in errors:
        path = _format_schema_path(error.absolute_path)
        prefix = f" at {path}" if path else ""
        issues.append(
            ValidationIssue(
                filename,
                f"schema violation{prefix}: {error.message}",
            )
        )


def _contains_source_owned_key(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in SOURCE_OWNED_PAYLOAD_KEYS:
                return key
            match = _contains_source_owned_key(nested)
            if match is not None:
                return match
    elif isinstance(value, list):
        for nested in value:
            match = _contains_source_owned_key(nested)
            if match is not None:
                return match
    return None


def _load_outputs(
    generated_dir: Path,
    issues: list[ValidationIssue],
) -> dict[str, dict[str, Any]]:
    outputs: dict[str, dict[str, Any]] = {}
    for filename in OUTPUT_SCHEMA_NAMES:
        path = generated_dir / filename
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            issues.append(ValidationIssue(filename, "missing output"))
            continue
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(ValidationIssue(filename, f"unreadable JSON: {exc}"))
            continue
        if not isinstance(payload, dict):
            issues.append(ValidationIssue(filename, "output must be a JSON object"))
            continue
        outputs[filename] = payload
    return outputs


def validate_generated_outputs(
    generated_dir: Path,
    techniques_root: Path,
    skills_root: Path,
    evals_root: Path,
    memo_root: Path,
    stats_root: Path,
    agents_root: Path,
    aoa_root: Path,
    playbooks_root: Path,
    kag_root: Path,
    tos_root: Path,
    sdk_root: Path,
    source_route_root: Path,
    profile_root: Path,
    abyss_stack_root: Path,
    routing_root: Path | None = None,
) -> list[ValidationIssue]:
    """Validate schema, exact rebuild parity, projection safety, and ABI identity."""

    issues: list[ValidationIssue] = []
    outputs = _load_outputs(generated_dir.resolve(), issues)
    try:
        expected_outputs = build_outputs(
            techniques_root.resolve(),
            skills_root.resolve(),
            evals_root.resolve(),
            memo_root.resolve(),
            stats_root.resolve(),
            agents_root.resolve(),
            aoa_root.resolve(),
            playbooks_root.resolve(),
            kag_root.resolve(),
            tos_root.resolve(),
            sdk_root.resolve(),
            source_route_root.resolve(),
            profile_root.resolve(),
            abyss_stack_root.resolve(),
            (routing_root or REPO_ROOT).resolve(),
        )
    except RouterError as exc:
        issues.append(ValidationIssue("generated", f"rebuild failed: {exc}"))
        return issues

    for filename, payload in outputs.items():
        _validate_schema(payload, filename=filename, issues=issues)
        if payload != expected_outputs[filename]:
            issues.append(
                ValidationIssue(
                    filename,
                    "output does not match the deterministic rebuild",
                )
            )
        forbidden_key = _contains_source_owned_key(payload)
        if forbidden_key is not None:
            issues.append(
                ValidationIssue(
                    filename,
                    f"output copies source-owned payload key {forbidden_key!r}",
                )
            )

    registry = outputs.get("cross_repo_registry.min.json")
    router = outputs.get("aoa_router.min.json")
    recommended = outputs.get("recommended_paths.min.json")
    if registry is not None and router is not None and recommended is not None:
        counts = {
            len(registry.get("entries", [])),
            len(router.get("entries", [])),
            len(recommended.get("entries", [])),
        }
        if len(counts) != 1:
            issues.append(
                ValidationIssue(
                    "routing-family",
                    "registry, thin router, and recommended paths counts differ",
                )
            )
    if router is not None:
        identity = router.get("artifact_identity")
        if not isinstance(identity, dict):
            issues.append(
                ValidationIssue("aoa_router.min.json", "artifact_identity must be an object")
            )
        else:
            if identity.get("owner_repo") != "aoa-routing":
                issues.append(
                    ValidationIssue(
                        "aoa_router.min.json",
                        "shadow embedded owner must stay aoa-routing before G5",
                    )
                )
            if identity.get("abi_epoch") != "aoa_routing_thin_router_v1":
                issues.append(
                    ValidationIssue(
                        "aoa_router.min.json",
                        "routing ABI epoch drifted",
                    )
                )
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate SDK shadow routing outputs.")
    dependency_args = (
        ("techniques", "aoa-techniques"),
        ("skills", "aoa-skills"),
        ("evals", "aoa-evals"),
        ("memo", "aoa-memo"),
        ("stats", "aoa-stats"),
        ("agents", "aoa-agents"),
        ("aoa", "Agents-of-Abyss"),
        ("playbooks", "aoa-playbooks"),
        ("kag", "aoa-kag"),
        ("tos", "Tree-of-Sophia"),
        ("sdk", "aoa-sdk"),
        ("source-route", "Dionysus"),
        ("profile", "8Dionysus"),
        ("abyss-stack", "abyss-stack"),
    )
    for argument, repo_name in dependency_args:
        parser.add_argument(
            f"--{argument}-root",
            type=Path,
            default=default_dependency_root(repo_name),
        )
    parser.add_argument("--generated-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues = validate_generated_outputs(
        args.generated_dir,
        args.techniques_root,
        args.skills_root,
        args.evals_root,
        args.memo_root,
        args.stats_root,
        args.agents_root,
        args.aoa_root,
        args.playbooks_root,
        args.kag_root,
        args.tos_root,
        args.sdk_root,
        args.source_route_root,
        args.profile_root,
        args.abyss_stack_root,
    )
    if issues:
        for issue in issues:
            print(f"[error] {issue.location}: {issue.message}")
        return 1
    print("[ok] validated SDK shadow routing outputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
