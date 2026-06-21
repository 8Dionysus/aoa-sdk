from __future__ import annotations

import json

import pytest

from aoa_sdk.artifacts import ArtifactsAPI
from aoa_sdk.errors import InvalidSurface
from aoa_sdk.models import (
    ArtifactAffectedReport,
    ArtifactBundleRegistry,
    ArtifactClassificationReport,
    ArtifactRequirementsReport,
    ArtifactTrustCoverageReport,
    ArtifactTrustGateReport,
    ArtifactUpdateLaneStatus,
    ArtifactUpdateMetadataVerification,
)


def test_artifact_trust_gate_report_is_typed_and_fail_closed() -> None:
    api = ArtifactsAPI()
    allow_payload = {
        "schema": "abyss_machine_artifact_trust_gate_v1",
        "ok": True,
        "artifact_class": "bootstrap_install_bundle",
        "consumer_intent": "installer",
        "verdict": "allow",
        "decision": {
            "allow": True,
            "verdict": "allow",
            "blockers": [],
            "warnings": [],
            "manual_review": [],
            "consumer_intent": "installer",
            "model": "fail_closed_consumer_admission",
        },
        "record_id": "sha256:record",
        "subject_digest": "sha256:subject",
        "inspected_claims": {"trust_root": {"trust_root_mode_actual": "host_managed"}},
    }
    deny_payload = {
        **allow_payload,
        "ok": False,
        "verdict": "deny",
        "decision": {
            **allow_payload["decision"],
            "allow": False,
            "verdict": "deny",
            "blockers": ["missing_required_control:sbom"],
        },
        "blockers": ["missing_required_control:sbom"],
    }

    report = api.parse_trust_gate(allow_payload)

    assert isinstance(report, ArtifactTrustGateReport)
    assert report.consumable is True
    assert report.inspected_claims["trust_root"]["trust_root_mode_actual"] == "host_managed"
    assert api.assert_consumable(report) is report
    with pytest.raises(InvalidSurface, match="missing_required_control:sbom"):
        api.assert_consumable(deny_payload)


def test_artifact_registry_requirements_and_update_surfaces_are_typed(tmp_path) -> None:
    api = ArtifactsAPI()
    classification_payload = {
        "schema": "abyss_machine_artifact_bundle_classification_v1",
        "ok": True,
        "artifact_class": "aoa_sdk_python_distribution",
        "bundle_layout": "abyss_machine_artifact_bundle_v1",
        "target": None,
        "policy_ref": "manifests/artifact_signature_policy.manifest.json",
        "policy_version": "0.2.4",
        "identity": {
            "owner_repo": "aoa-sdk",
            "producer": "aoa-sdk Python build backend from tracked SDK source and package metadata",
            "trust_layer": ["abi_contract_signature", "sbom", "slsa_in_toto"],
        },
        "required_controls": ["abi_signature", "sbom", "slsa_in_toto"],
        "deferred_controls": {"c2pa": {"required": False, "reason": "not public media"}},
        "required_sidecars": {"abi_signature": ["artifact.abi.json"]},
        "signature_required": False,
    }
    registry_payload = {
        "schema": "abyss_machine_artifact_bundle_registry_v1",
        "ok": True,
        "records": [
            {
                "schema": "abyss_machine_artifact_bundle_registry_record_v1",
                "record_id": "sha256:record",
                "artifact_class": "aoa_sdk_python_distribution",
                "subject_digest": "sha256:subject",
                "source_repo": "aoa-sdk",
                "source_ref": "dist/aoa_sdk-0.4.0-py3-none-any.whl",
                "producer": "aoa-sdk build backend",
                "trust_root_mode": "host_managed",
                "lifecycle_state": "release-ready",
                "latest_eligible": True,
                "terminal_state": False,
                "verifier_versions": {"artifact_bundle_verifier": {"schema": "abyss_machine_artifact_bundle_verify_v1"}},
            }
        ],
        "latest_by_artifact_class": {},
        "summary": {"records": 1, "latest": 1},
    }
    requirements_payload = {
        "schema": "abyss_machine_artifact_requirements_v1",
        "ok": True,
        "rows": [
            {
                "schema": "abyss_machine_artifact_requirements_row_v1",
                "artifact_class": "aoa_sdk_python_distribution",
                "owner_repo": "aoa-sdk",
                "controls": {"required": ["abi_signature", "sbom", "slsa_in_toto"]},
                "producer_profile": {"producer": "aoa-sdk Python build backend"},
                "source_route": {"contract_surface_status": "external_subject_or_owner_bundle_required"},
                "trust_roots": {"github_oidc": {"adapter_only": True}},
                "agent_loop": {
                    "requirements": "abyss-machine artifacts requirements --artifact-class aoa_sdk_python_distribution --json",
                    "build_sidecars": "abyss-machine artifacts build-sidecars --artifact-class aoa_sdk_python_distribution --bundle-dir BUNDLE_DIR --json",
                    "trust_gate": "abyss-machine artifacts trust-gate --artifact-class aoa_sdk_python_distribution --json",
                },
                "claim_limits": ["GitHub OIDC is one producer adapter, not the trust plane."],
            }
        ],
        "summary": {"artifact_classes": 1},
    }
    update_lane_payload = {
        "schema": "abyss_machine_update_transparency_lane_status_v1",
        "ok": True,
        "summary": {
            "tuf_status": "prepared_v1",
            "scitt_status": "future_external_accountability_layer",
            "updateable_artifact_classes": 1,
            "blocking_v1": False,
        },
        "rows": [
            {
                "schema": "abyss_machine_update_lane_row_v1",
                "artifact_class": "aoa_sdk_python_distribution",
                "applies": True,
                "consumer_intent": "update_client",
                "metadata_sidecar": "artifact.update.tuf.json",
                "required_when": "package updater consumes the artifact",
                "client_checks": ["artifact_class is updateable by policy"],
                "status": "TUF_REQUIRED_FOR_UPDATE_CLIENT",
            }
        ],
        "tuf": {"status": "prepared_v1"},
        "scitt": {"blocking_v1": False},
        "claim_limits": ["not a full external TUF repository"],
    }
    update_verify_payload = {
        "schema": "abyss_machine_update_metadata_verify_v1",
        "ok": True,
        "verdict": "allow",
        "artifact_class": "aoa_sdk_python_distribution",
        "metadata_sha256": "sha256:metadata",
        "errors": [],
        "warnings": [],
        "checked": {"version": 2},
    }
    affected_payload = {
        "schema": "abyss_machine_artifact_affected_v1",
        "ok": True,
        "policy_ref": "manifests/artifact_signature_policy.manifest.json",
        "abi_ref": "generated/contract_abi_signatures.min.json",
        "artifact_class_filter": None,
        "changed_paths": ["src/aoa_sdk/artifacts/api.py"],
        "changed_source_repo": None,
        "accept_sibling_lag": False,
        "known_verdicts": [
            "fresh",
            "stale",
            "needs_rebuild",
            "needs_reverify",
            "blocked_by_missing_sibling",
            "accepted_lag",
            "manual_review_required",
        ],
        "summary": {"artifact_classes": 1, "affected": 0, "status_counts": {"fresh": 1}},
        "rows": [
            {
                "schema": "abyss_machine_artifact_affected_row_v1",
                "artifact_class": "aoa_sdk_python_distribution",
                "owner_repo": "aoa-sdk",
                "affected": False,
                "verdict": "fresh",
                "freshness": "fresh",
                "reasons": [],
                "matches": [],
                "changed_source_repo": None,
                "contract_surface_status": "external_subject_or_owner_bundle_required",
                "registry": {"checked": True, "has_latest": True},
                "trust_gate": {"checked": True, "verdict": "allow"},
                "next_actions": ["abyss-machine artifacts requirements --artifact-class aoa_sdk_python_distribution --json"],
                "claim_limit": "Affected detects declared source/profile drift; it does not rebuild or consume artifacts by itself.",
            }
        ],
        "errors": [],
    }
    trust_coverage_payload = {
        "schema": "abyss_machine_artifacts_trust_coverage_v1",
        "ok": True,
        "summary": {
            "artifact_classes": 1,
            "fully_covered": 1,
            "status_counts": {"FULLY_COVERED": 1},
            "registry_records": 1,
            "registry_latest": 1,
            "trust_tools_status": "ready",
        },
        "policy_ref": "manifests/artifact_signature_policy.manifest.json",
        "abi_ref": "generated/contract_abi_signatures.min.json",
        "registry": {"summary": {"records": 1}},
        "trust_tools": {"status": "ready", "missing_controls": []},
        "manual_evidence_roots": ["/srv/abyss-machine/tmp"],
        "rows": [
            {
                "schema": "abyss_machine_artifacts_trust_coverage_row_v1",
                "artifact_class": "aoa_sdk_python_distribution",
                "owner": "aoa-sdk",
                "real_artifact": {"surface_state": "publishable_python_distribution"},
                "required_controls": ["abi_signature", "sbom", "slsa_in_toto"],
                "deferred_controls": {"c2pa": {"required": False}},
                "source_verification": ["python scripts/release_check.py"],
                "installed_verification": {"trust_gate_ok": True, "trust_gate_verdict": "allow"},
                "persistent_registry_status": {"has_latest": True},
                "consumer_path": {"trust_gate": "abyss-machine artifacts trust-gate --artifact-class aoa_sdk_python_distribution --json"},
                "manual_positive_evidence": ["/srv/abyss-machine/tmp/positive.json"],
                "manual_negative_evidence": ["/srv/abyss-machine/tmp/negative.json"],
                "external_signature_provenance_status": "local_policy_signature_decision_not_required",
                "claim_limits": ["coverage read-model only"],
                "status": "FULLY_COVERED",
                "remaining_blocker": "",
            }
        ],
        "claim_limits": ["This matrix is a coverage read-model."],
    }
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")

    classification = api.parse_classification(classification_payload)
    registry = api.load_registry(registry_path)
    requirements = api.parse_requirements(requirements_payload)
    update_lane = api.parse_update_lane(update_lane_payload)
    update_verify = api.parse_update_verification(update_verify_payload)
    affected = api.parse_affected(affected_payload)
    trust_coverage = api.parse_trust_coverage(trust_coverage_payload)

    assert isinstance(classification, ArtifactClassificationReport)
    assert classification.identity["owner_repo"] == "aoa-sdk"
    assert isinstance(registry, ArtifactBundleRegistry)
    assert registry.records[0].trust_root_mode == "host_managed"
    assert isinstance(requirements, ArtifactRequirementsReport)
    assert requirements.rows[0].controls["required"] == ["abi_signature", "sbom", "slsa_in_toto"]
    assert requirements.rows[0].agent_loop["trust_gate"].startswith("abyss-machine artifacts trust-gate")
    assert isinstance(update_lane, ArtifactUpdateLaneStatus)
    assert update_lane.rows[0].metadata_sidecar == "artifact.update.tuf.json"
    assert isinstance(update_verify, ArtifactUpdateMetadataVerification)
    assert update_verify.update_consideration_allowed is True
    assert isinstance(affected, ArtifactAffectedReport)
    assert affected.rows[0].verdict == "fresh"
    assert isinstance(trust_coverage, ArtifactTrustCoverageReport)
    assert trust_coverage.rows[0].status == "FULLY_COVERED"
