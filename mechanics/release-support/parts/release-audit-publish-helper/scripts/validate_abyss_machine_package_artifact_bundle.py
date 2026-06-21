#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


def _find_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file() and (parent / "AGENTS.md").is_file():
            return parent
    raise RuntimeError("could not find aoa-sdk repository root")


REPO_ROOT = _find_repo_root()
DEFAULT_MANIFEST = REPO_ROOT / "sdk" / "distribution" / "manifests" / "python_distribution.bundle.json"
DEFAULT_BUNDLE_DIR = REPO_ROOT / "dist" / "abyss-artifact-bundle"
DEFAULT_REGISTRY_DIR = REPO_ROOT / "dist" / "abyss-artifact-registry"
ARTIFACT_CLASS = "aoa_sdk_python_distribution"
EXPECTED_REQUIRED_CONTROLS = ["abi_signature", "sbom", "slsa_in_toto"]


def _candidate_abyss_machine_roots() -> list[Path]:
    candidates: list[Path] = []
    env_root = os.environ.get("ABYSS_MACHINE_REPO_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend(
        [
            REPO_ROOT.parent / "abyss-machine",
            Path("/home/dionysus/src/abyss-machine"),
            Path("/srv/AbyssOS/abyss-machine"),
        ]
    )
    return candidates


def _public_seed_root() -> Path:
    return Path(os.environ.get("ABYSS_MACHINE_PUBLIC_SEED_ROOT", "/usr/local/share/abyss-machine")).expanduser()


def _import_from_package_root(package_root: Path) -> tuple[Any, Path, str] | None:
    root = package_root.expanduser().resolve()
    if (root / "abyss_machine" / "artifact_bundles.py").is_file():
        sys.path.insert(0, str(root))
        return importlib.import_module("abyss_machine.artifact_bundles"), _public_seed_root(), str(root)
    return None


def _import_artifact_bundles() -> tuple[Any, Path | None, str | None]:
    package_root = os.environ.get("ABYSS_MACHINE_PACKAGE_ROOT")
    if package_root:
        imported = _import_from_package_root(Path(package_root))
        if imported is not None:
            return imported
    for candidate in _candidate_abyss_machine_roots():
        root = candidate.expanduser().resolve()
        module_root = root / "src"
        if (module_root / "abyss_machine" / "artifact_bundles.py").is_file():
            sys.path.insert(0, str(module_root))
            return importlib.import_module("abyss_machine.artifact_bundles"), root, None
    installed = _import_from_package_root(Path("/usr/local/libexec"))
    if installed is not None:
        return installed
    artifact_bundles = importlib.import_module("abyss_machine.artifact_bundles")
    return artifact_bundles, getattr(artifact_bundles, "REPO_ROOT", None), None


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _path_ref(path: Path) -> str:
    resolved = path.expanduser().resolve()
    try:
        return resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _default_tmp_root() -> Path | None:
    for raw in (os.environ.get("ABYSS_MACHINE_TMP_ROOT"), "/srv/abyss-machine/tmp"):
        if not raw:
            continue
        path = Path(raw)
        if path.is_dir():
            return path
    return None


def _assert_dist_subjects_exist() -> None:
    wheel_subjects = sorted((REPO_ROOT / "dist").glob("aoa_sdk-*.whl"))
    sdist_subjects = sorted((REPO_ROOT / "dist").glob("aoa_sdk-*.tar.gz"))
    missing: list[str] = []
    if not wheel_subjects:
        missing.append("dist/aoa_sdk-*.whl")
    if not sdist_subjects:
        missing.append("dist/aoa_sdk-*.tar.gz")
    if missing:
        raise FileNotFoundError(
            "built package artifacts are required before OS Abyss bundle verification: "
            + ", ".join(missing)
        )


def _assert_public_sidecars_do_not_leak_local_roots(bundle_dir: Path, abyss_machine_root: Path | None) -> None:
    forbidden = [str(REPO_ROOT.resolve())]
    if abyss_machine_root is not None:
        forbidden.append(str(abyss_machine_root.resolve()))
    leaks: list[str] = []
    for path in sorted(bundle_dir.iterdir()):
        if path.is_file() and path.suffix in {".json", ".jsonl"}:
            text = path.read_text(encoding="utf-8")
            if any(item and item in text for item in forbidden):
                leaks.append(path.name)
    if leaks:
        raise ValueError("public artifact sidecars leak local repo roots: " + ", ".join(leaks))


def _assert_public_registry_does_not_leak_local_roots(registry_dir: Path, abyss_machine_root: Path | None) -> None:
    forbidden = [str(REPO_ROOT.resolve())]
    if abyss_machine_root is not None:
        forbidden.append(str(abyss_machine_root.resolve()))
    leaks: list[str] = []
    for path in sorted(registry_dir.rglob("*")) if registry_dir.exists() else []:
        if path.is_file() and path.suffix in {".json", ".jsonl"}:
            text = path.read_text(encoding="utf-8")
            if any(item and item in text for item in forbidden):
                leaks.append(path.name)
    if leaks:
        raise ValueError("public artifact registry leaks local repo roots: " + ", ".join(leaks))


def _assert_expected_controls(verify: dict[str, Any]) -> None:
    required = verify.get("required_controls")
    verified = verify.get("verified_controls")
    if required != EXPECTED_REQUIRED_CONTROLS:
        raise ValueError(f"unexpected required controls: {required!r}")
    if verified != EXPECTED_REQUIRED_CONTROLS:
        raise ValueError(f"unexpected verified controls: {verified!r}")


def _copy_bundle(bundle_dir: Path, target: Path) -> Path:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(bundle_dir, target)
    return target


def _registry_roundtrip(
    artifact_bundles: Any,
    bundle_dir: Path,
    registry_dir: Path,
    *,
    lifecycle_state: str,
    evidence_ref: str,
) -> dict[str, Any]:
    registered = artifact_bundles.write_bundle_registry_record(
        bundle_dir,
        registry_dir,
        lifecycle_state=lifecycle_state,
        consumer_refs=["aoa-sdk:release-audit-publish-helper"],
        evidence_refs=[evidence_ref],
    )
    latest = artifact_bundles.read_bundle_registry(registry_dir, artifact_class=ARTIFACT_CLASS)
    latest_record = latest.get("latest_by_artifact_class", {}).get(ARTIFACT_CLASS)
    return {
        "ok": bool(
            registered.get("ok")
            and isinstance(latest_record, dict)
            and latest_record.get("record_id") == registered.get("record", {}).get("record_id")
            and latest_record.get("lifecycle_state") == lifecycle_state
        ),
        "registered": registered,
        "latest": latest,
    }


def _trust_gate_allow_latest(artifact_bundles: Any, registry_dir: Path, registry_roundtrip: dict[str, Any]) -> dict[str, Any]:
    record = registry_roundtrip.get("registered", {}).get("record", {})
    trust_gate = artifact_bundles.trust_gate(
        registry_dir,
        artifact_class=ARTIFACT_CLASS,
        subject_digest=str(record.get("subject_digest") or ""),
        consumer_intent="agent",
        expected_source_repo="aoa-sdk",
    )
    inspected_claims = trust_gate.get("inspected_claims", {})
    return {
        "ok": bool(
            trust_gate.get("ok")
            and trust_gate.get("verdict") in {"allow", "warn"}
            and trust_gate.get("decision", {}).get("model") == "fail_closed_consumer_admission"
            and trust_gate.get("decision", {}).get("allow") is True
            and inspected_claims.get("registry_latest", {}).get("selected_record_is_latest") is True
            and inspected_claims.get("controls", {}).get("required_controls_missing") == []
            and inspected_claims.get("source", {}).get("source_repo_matched") is True
        ),
        "trust_gate": trust_gate,
    }


def _verify_missing_sbom(artifact_bundles: Any, abyss_repo_root: Path, bundle_dir: Path, tmp_root: Path) -> dict[str, Any]:
    candidate = _copy_bundle(bundle_dir, tmp_root / "missing-sbom")
    for name in (artifact_bundles.SBOM_CYCLONEDX_SIDECAR, artifact_bundles.SBOM_SPDX_SIDECAR):
        path = candidate / name
        if path.exists():
            path.unlink()
    verification = artifact_bundles.verify_bundle(candidate, repo_root=abyss_repo_root)
    return {
        "ok": verification.get("ok") is False and bool(verification.get("missing")),
        "verification": verification,
    }


def _verify_wrong_slsa_subject(
    artifact_bundles: Any,
    abyss_repo_root: Path,
    bundle_dir: Path,
    tmp_root: Path,
) -> dict[str, Any]:
    candidate = _copy_bundle(bundle_dir, tmp_root / "wrong-slsa-subject")
    path = candidate / artifact_bundles.SLSA_INTOTO_SIDECAR
    statement = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    statement["subject"][0]["digest"]["sha256"] = "0" * 64
    path.write_text(json.dumps(statement, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    verification = artifact_bundles.verify_bundle(candidate, repo_root=abyss_repo_root)
    return {
        "ok": verification.get("ok") is False
        and any("SLSA/in-toto sidecar does not cover artifact subject digests" in item for item in verification.get("errors", [])),
        "verification": verification,
    }


def _verify_private_path_leak(bundle_dir: Path, tmp_root: Path) -> dict[str, Any]:
    candidate = _copy_bundle(bundle_dir, tmp_root / "private-path-leak")
    identity = candidate / "artifact.identity.json"
    payload = _load_json(identity)
    payload["private_path_negative"] = str(REPO_ROOT.resolve())
    identity.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    try:
        _assert_public_sidecars_do_not_leak_local_roots(candidate, None)
    except ValueError as exc:
        return {"ok": "public artifact sidecars leak local repo roots" in str(exc), "error": str(exc)}
    return {"ok": False, "error": "private path leak was not detected"}


def _verify_unverified_latest_rejected(artifact_bundles: Any, bundle_dir: Path, tmp_root: Path) -> dict[str, Any]:
    candidate = _copy_bundle(bundle_dir, tmp_root / "unverified-latest")
    for name in (artifact_bundles.SBOM_CYCLONEDX_SIDECAR, artifact_bundles.SBOM_SPDX_SIDECAR):
        path = candidate / name
        if path.exists():
            path.unlink()
    registered = artifact_bundles.write_bundle_registry_record(
        candidate,
        tmp_root / "unverified-registry",
        lifecycle_state="release-ready",
    )
    return {
        "ok": registered.get("ok") is False
        and any("successful bundle verification" in item for item in registered.get("errors", [])),
        "registered": registered,
    }


def _verify_terminal_registry_state(artifact_bundles: Any, bundle_dir: Path, tmp_root: Path) -> dict[str, Any]:
    registry_dir = tmp_root / "terminal-registry"
    release_ready = _registry_roundtrip(
        artifact_bundles,
        bundle_dir,
        registry_dir,
        lifecycle_state="release-ready",
        evidence_ref="terminal-state-rehearsal",
    )
    revoked = artifact_bundles.write_bundle_registry_record(
        bundle_dir,
        registry_dir,
        lifecycle_state="revoked",
        revocation_reason="aoa-sdk package artifact terminal-state rehearsal",
    )
    revoked_gate = artifact_bundles.trust_gate(
        registry_dir,
        artifact_class=ARTIFACT_CLASS,
        record_id=str(release_ready.get("registered", {}).get("record", {}).get("record_id") or ""),
        consumer_intent="agent",
    )
    after_revoke = artifact_bundles.read_bundle_registry(registry_dir, artifact_class=ARTIFACT_CLASS)
    return {
        "ok": bool(
            release_ready.get("ok")
            and revoked.get("ok")
            and revoked_gate.get("verdict") == "deny"
            and revoked_gate.get("decision", {}).get("allow") is False
            and revoked_gate.get("inspected_claims", {}).get("lifecycle", {}).get("terminal_state") is True
            and not after_revoke.get("latest_by_artifact_class")
        ),
        "release_ready": release_ready,
        "revoked": revoked,
        "revoked_trust_gate": revoked_gate,
        "after_revoke": after_revoke,
    }


def _run_adversarial_checks(artifact_bundles: Any, abyss_repo_root: Path, bundle_dir: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="aoa-sdk-artifact-negative-", dir=_default_tmp_root()) as tmp:
        tmp_root = Path(tmp)
        checks = {
            "missing_sbom": _verify_missing_sbom(artifact_bundles, abyss_repo_root, bundle_dir, tmp_root),
            "wrong_slsa_subject": _verify_wrong_slsa_subject(artifact_bundles, abyss_repo_root, bundle_dir, tmp_root),
            "private_path_leak": _verify_private_path_leak(bundle_dir, tmp_root),
            "unverified_latest_rejected": _verify_unverified_latest_rejected(artifact_bundles, bundle_dir, tmp_root),
            "terminal_registry_state": _verify_terminal_registry_state(artifact_bundles, bundle_dir, tmp_root),
        }
    return {
        "ok": all(bool(item.get("ok")) for item in checks.values()),
        "checks": checks,
    }


def validate_bundle(manifest: Path, bundle_dir: Path, registry_dir: Path, *, clean: bool) -> dict[str, Any]:
    artifact_bundles, abyss_machine_root, package_root = _import_artifact_bundles()
    _assert_dist_subjects_exist()
    if clean and bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    if clean and registry_dir.exists():
        shutil.rmtree(registry_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    abyss_repo_root = abyss_machine_root or artifact_bundles.REPO_ROOT
    build = artifact_bundles.build_sidecars(
        bundle_dir,
        manifest_ref=manifest,
        repo_root=abyss_repo_root,
        producer_command=(
            "python mechanics/release-support/parts/release-audit-publish-helper/scripts/"
            "validate_abyss_machine_package_artifact_bundle.py"
        ),
    )
    sign = artifact_bundles.sign_bundle(bundle_dir, repo_root=abyss_repo_root)
    verify = artifact_bundles.verify_bundle(bundle_dir, repo_root=abyss_repo_root)
    release_check = artifact_bundles.release_check(bundle_dir, repo_root=abyss_repo_root)
    _assert_expected_controls(verify)
    _assert_public_sidecars_do_not_leak_local_roots(bundle_dir, abyss_machine_root)
    registry = _registry_roundtrip(
        artifact_bundles,
        bundle_dir,
        registry_dir,
        lifecycle_state="release-ready",
        evidence_ref=f"{_path_ref(bundle_dir)}/artifact.verify.json",
    )
    trust_gate = _trust_gate_allow_latest(artifact_bundles, registry_dir, registry)
    _assert_public_registry_does_not_leak_local_roots(registry_dir, abyss_machine_root)
    adversarial = _run_adversarial_checks(artifact_bundles, abyss_repo_root, bundle_dir)

    manifest_payload = _load_json(manifest)
    payload = {
        "ok": bool(
            build.get("ok")
            and sign.get("ok")
            and verify.get("ok")
            and release_check.get("ok")
            and registry.get("ok")
            and trust_gate.get("ok")
            and adversarial.get("ok")
        ),
        "schema": "aoa_sdk_abyss_machine_package_artifact_bundle_validation_v1",
        "manifest_ref": _path_ref(manifest),
        "bundle_dir": _path_ref(bundle_dir),
        "registry_dir": _path_ref(registry_dir),
        "artifact_class": manifest_payload.get("artifact_class"),
        "required_controls": verify.get("required_controls"),
        "verified_controls": verify.get("verified_controls"),
        "abyss_machine_repo_root": str(abyss_repo_root),
        "abyss_machine_package_root": package_root,
        "registry": registry,
        "trust_gate": trust_gate,
        "adversarial_checks": adversarial,
        "steps": {
            "build_sidecars": build,
            "sign": sign,
            "verify": verify,
            "release_check": release_check,
        },
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate aoa-sdk package artifacts through abyss-machine bundles.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--bundle-dir", type=Path, default=DEFAULT_BUNDLE_DIR)
    parser.add_argument("--registry-dir", type=Path, default=DEFAULT_REGISTRY_DIR)
    parser.add_argument("--no-clean", action="store_true", help="do not remove the previous generated bundle directory first")
    parser.add_argument("--json", action="store_true", help="print the full validation payload")
    args = parser.parse_args()

    manifest = args.manifest if args.manifest.is_absolute() else REPO_ROOT / args.manifest
    bundle_dir = args.bundle_dir if args.bundle_dir.is_absolute() else REPO_ROOT / args.bundle_dir
    registry_dir = args.registry_dir if args.registry_dir.is_absolute() else REPO_ROOT / args.registry_dir
    payload = validate_bundle(manifest, bundle_dir, registry_dir, clean=not args.no_clean)
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    elif payload["ok"]:
        print(
            "[ok] abyss-machine package artifact bundle verified: "
            f"{payload['bundle_dir']} ({', '.join(payload['verified_controls'])}; registry={payload['registry_dir']})"
        )
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
