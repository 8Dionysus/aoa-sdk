from __future__ import annotations

import json

import pytest

from aoa_sdk.artifacts import ArtifactsAPI
from aoa_sdk.errors import InvalidSurface
from aoa_sdk.models import (
    ArtifactAffectedReport,
    ArtifactBundleRegistry,
    ArtifactClassificationReport,
    ArtifactDriftState,
    ArtifactRequirementsReport,
    ArtifactProducerProfile,
    ArtifactProducerProfilesReport,
    ArtifactSourceRefStatus,
    ArtifactTrustCoverageReport,
    ArtifactTrustGateReport,
    ArtifactScittReceiptVerification,
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
                "source_refs": ["sdk/distribution/manifests/python_distribution.bundle.json"],
                "bundle_manifest_ref": "sdk/distribution/manifests/python_distribution.bundle.json",
                "producer": "aoa-sdk build backend",
                "producer_command": "python -m build",
                "evidence_refs": ["commit:e89d46184339adc67418025f06b83b002b6d5038"],
                "trust_root_mode": "host_managed",
                "lifecycle_state": "release-ready",
                "latest_eligible": True,
                "terminal_state": False,
                "verifier_versions": {"artifact_bundle_verifier": {"schema": "abyss_machine_artifact_bundle_verify_v1"}},
                "created_at": "2026-06-21T19:36:40Z",
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
                "registry_status": {"has_latest": True, "latest_record_id": "sha256:record"},
                "trust_gate_status": {"checked": True, "verdict": "allow"},
                "consumer": {"intent": "agent", "requires_trust_gate": True},
                "release_rules": {"release_ready_required": True},
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
            "scitt_status": "local_stub_fail_closed_external_v1",
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
        "tuf": {
            "status": "prepared_v1",
            "external_repository_verifier": {"status": "structural_v1"},
        },
        "scitt": {
            "status": "local_stub_fail_closed_external_v1",
            "blocking_v1": False,
            "external_relying_party_mode": {
                "receipt_required": True,
                "missing_receipt_verdict": "deny",
                "binding": "receipt.statement_digest must equal canonical signed statement digest",
                "not_external_service_yet": True,
            },
        },
        "claim_limits": [
            "not a full external TUF repository",
            "local statement/receipt binding stub",
        ],
    }
    scitt_verify_allow_payload = {
        "schema": "abyss_machine_scitt_receipt_verify_v1",
        "ok": True,
        "policy_ref": "manifests/artifact_signature_policy.manifest.json",
        "statement_schema": "abyss_machine_scitt_signed_statement_v1",
        "receipt_schema": "abyss_machine_scitt_receipt_v1",
        "statement_digest": "sha256:statement",
        "statement_class": "release_update_artifact",
        "issuer": "did:web:abyss.example:issuer:release",
        "artifact_digest": "sha256:artifact",
        "external_relying_party": True,
        "receipt_required": True,
        "receipt_present": True,
        "receipt_ok": True,
        "transparency_service": "did:web:transparency.abyss.example",
        "verdict": "allow",
        "known_statement_classes": ["release_update_artifact", "artifact_evidence_record", "eval_report_result"],
        "scitt_policy": {"status": "local_stub_fail_closed_external_v1"},
        "checked": {"expected_statement_class": "release_update_artifact"},
        "errors": [],
        "warnings": [],
        "claim_limits": ["local verifier/stub"],
    }
    scitt_verify_deny_payload = {
        **scitt_verify_allow_payload,
        "ok": False,
        "receipt_schema": None,
        "receipt_present": False,
        "receipt_ok": False,
        "transparency_service": None,
        "verdict": "deny",
        "errors": ["scitt_receipt_required"],
    }
    scitt_verify_inconsistent_payload = {
        **scitt_verify_allow_payload,
        "receipt_present": False,
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
        "raw_changed_paths": ["/srv/AbyssOS/aoa-sdk/src/aoa_sdk/artifacts/api.py"],
        "changed_path_analysis": [
            {
                "raw": "/srv/AbyssOS/aoa-sdk/src/aoa_sdk/artifacts/api.py",
                "normalized": "src/aoa_sdk/artifacts/api.py",
                "source_repo": "aoa-sdk",
                "source_repo_inferred": True,
                "scope": "source_repo_relative",
            }
        ],
        "changed_source_repo": None,
        "changed_source_repo_inferred": "aoa-sdk",
        "changed_source_ref": "commit:e89d46184339adc67418025f06b83b002b6d5038",
        "changed_path_source": {"mode": "explicit"},
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
        "known_drift_statuses": [
            "fresh",
            "missing_durable_evidence",
            "rebuild_required",
            "reverify_required",
            "blocked_missing_sibling",
            "accepted_lag",
            "manual_review_required",
        ],
        "summary": {
            "artifact_classes": 1,
            "affected": 0,
            "status_counts": {"fresh": 1},
            "operationally_blocking": 0,
            "accepted_lag": 0,
        },
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
                "changed_source_repo_inferred": "aoa-sdk",
                "contract_surface_status": "external_subject_or_owner_bundle_required",
                "drift": {
                    "status": "fresh",
                    "known_statuses": [
                        "fresh",
                        "missing_durable_evidence",
                        "rebuild_required",
                        "reverify_required",
                        "blocked_missing_sibling",
                        "accepted_lag",
                        "manual_review_required",
                    ],
                    "operationally_blocking": False,
                    "needs_rebuild": False,
                    "needs_reverify": False,
                    "accepted_lag": False,
                    "lag_policy": "not_accepted",
                    "source_ref_state": "proved_current",
                    "evidence_state": "durable_latest_present",
                    "reason_count": 0,
                    "explanation": "latest durable evidence is current",
                },
                "registry": {
                    "checked": True,
                    "has_latest": True,
                    "latest_source_ref": "sdk/distribution/manifests/python_distribution.bundle.json",
                    "latest_evidence_refs": ["commit:e89d46184339adc67418025f06b83b002b6d5038"],
                },
                "trust_gate": {"checked": True, "verdict": "allow"},
                "source_ref_status": {
                    "required": True,
                    "expected": "commit:e89d46184339adc67418025f06b83b002b6d5038",
                    "matched": True,
                    "matched_ref": "commit:e89d46184339adc67418025f06b83b002b6d5038",
                    "known_refs": [
                        "commit:e89d46184339adc67418025f06b83b002b6d5038",
                        "github:8Dionysus/aoa-sdk/pull/189",
                    ],
                },
                "next_actions": ["abyss-machine artifacts requirements --artifact-class aoa_sdk_python_distribution --json"],
                "claim_limit": "Affected detects declared source/profile drift and closes source-ref drift only when latest durable evidence proves the ref; it does not rebuild or consume artifacts by itself.",
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
    scitt_verify_allow = api.parse_scitt_receipt_verification(scitt_verify_allow_payload)
    scitt_verify_deny = api.parse_scitt_receipt_verification(scitt_verify_deny_payload)
    scitt_verify_inconsistent = api.parse_scitt_receipt_verification(scitt_verify_inconsistent_payload)
    update_verify = api.parse_update_verification(update_verify_payload)
    affected = api.parse_affected(affected_payload)
    trust_coverage = api.parse_trust_coverage(trust_coverage_payload)

    assert isinstance(classification, ArtifactClassificationReport)
    assert classification.identity["owner_repo"] == "aoa-sdk"
    assert isinstance(registry, ArtifactBundleRegistry)
    assert registry.records[0].trust_root_mode == "host_managed"
    assert registry.records[0].source_refs == ["sdk/distribution/manifests/python_distribution.bundle.json"]
    assert registry.records[0].evidence_refs == ["commit:e89d46184339adc67418025f06b83b002b6d5038"]
    assert isinstance(requirements, ArtifactRequirementsReport)
    assert requirements.rows[0].controls["required"] == ["abi_signature", "sbom", "slsa_in_toto"]
    assert requirements.rows[0].registry_status["latest_record_id"] == "sha256:record"
    assert requirements.rows[0].trust_gate_status["verdict"] == "allow"
    assert requirements.rows[0].agent_loop["trust_gate"].startswith("abyss-machine artifacts trust-gate")
    assert isinstance(update_lane, ArtifactUpdateLaneStatus)
    assert update_lane.rows[0].metadata_sidecar == "artifact.update.tuf.json"
    assert update_lane.tuf_status == "prepared_v1"
    assert update_lane.scitt_status == "local_stub_fail_closed_external_v1"
    assert update_lane.has_structural_tuf_repository_verifier is True
    assert update_lane.has_scitt_receipt_binding_stub is True
    assert update_lane.external_relying_party_receipt_required is True
    assert isinstance(scitt_verify_allow, ArtifactScittReceiptVerification)
    assert scitt_verify_allow.external_relying_party_allowed is True
    assert scitt_verify_allow.consumable is True
    assert isinstance(scitt_verify_deny, ArtifactScittReceiptVerification)
    assert scitt_verify_deny.consumable is False
    assert scitt_verify_deny.fail_closed_missing_receipt is True
    assert scitt_verify_inconsistent.consumable is True
    assert scitt_verify_inconsistent.external_relying_party_allowed is False
    assert isinstance(update_verify, ArtifactUpdateMetadataVerification)
    assert update_verify.update_consideration_allowed is True
    assert isinstance(affected, ArtifactAffectedReport)
    assert affected.changed_source_ref == "commit:e89d46184339adc67418025f06b83b002b6d5038"
    assert affected.changed_source_repo_inferred == "aoa-sdk"
    assert affected.changed_path_analysis[0].normalized == "src/aoa_sdk/artifacts/api.py"
    assert affected.known_drift_statuses[-1] == "manual_review_required"
    assert affected.rows[0].verdict == "fresh"
    assert isinstance(affected.rows[0].drift, ArtifactDriftState)
    assert affected.rows[0].drift.status == "fresh"
    assert affected.rows[0].drift.blocks_operation is False
    assert affected.rows[0].operationally_blocking is False
    assert affected.rows[0].lag_accepted is False
    assert isinstance(affected.rows[0].source_ref_status, ArtifactSourceRefStatus)
    assert affected.rows[0].source_ref_status.proven is True
    assert affected.rows[0].source_ref_proven is True
    unrequested_ref = ArtifactSourceRefStatus.model_validate({"required": False, "matched": None})
    assert unrequested_ref.proven is False
    assert isinstance(trust_coverage, ArtifactTrustCoverageReport)
    assert trust_coverage.rows[0].status == "FULLY_COVERED"


def test_artifact_producer_profiles_are_typed_read_model_only(tmp_path) -> None:
    api = ArtifactsAPI()
    payload = {
        "schema": "abyss_machine_artifact_producer_profiles_v1",
        "ok": True,
        "policy_ref": "manifests/artifact_signature_policy.manifest.json",
        "policy_version": "0.2.4",
        "abi_ref": "generated/contract_abi_signatures.min.json",
        "profile_filter": None,
        "owner_repo_filter": None,
        "artifact_class_filter": "public_media_export",
        "summary": {
            "profiles": 2,
            "owner_repos": ["Tree-of-Sophia", "abyss-machine"],
            "artifact_classes": ["public_media_export", "public_source_seed"],
            "artifact_class_count": 2,
        },
        "rows": [
            {
                "profile_id": "Tree-of-Sophia",
                "owner_repo": "Tree-of-Sophia",
                "owner_route_refs": ["AGENTS.md", "ToS/derived-exports"],
                "artifact_classes": ["tree_of_sophia_generated_readmodel_bundle", "public_media_export"],
                "release_export_triggers": ["public PDF, visualization, image, or other media export is published"],
                "validator_commands": ["python scripts/release_check.py"],
                "produced_sidecars": ["artifact.identity.json", "artifact.c2pa"],
                "consumer_expectations": [
                    "media consumers verify C2PA before public use",
                ],
                "owner_boundaries": [
                    "Tree-of-Sophia authored meaning remains stronger than generated readmodels",
                ],
                "trust_root_modes": ["local_dev", "github_oidc", "public_release"],
            },
            {
                "profile_id": "abyss-machine",
                "owner_repo": "abyss-machine",
                "owner_route_refs": ["AGENTS.md", "BOUNDARIES.md"],
                "artifact_classes": ["public_source_seed", "public_media_export"],
                "release_export_triggers": ["public seed or bootstrap release is cut"],
                "validator_commands": ["python scripts/release_check.py", "abyss-machine artifacts validate --json"],
                "produced_sidecars": ["artifact.identity.json", "artifact.verify.json"],
                "consumer_expectations": [
                    "agents consume only after durable registry promotion and trust-gate verdict",
                ],
                "owner_boundaries": [
                    "owns host enforcement, durable registry, trust gates, trust roots, update lane, and public bootstrap seed",
                ],
                "trust_root_modes": ["local_dev", "host_managed", "github_oidc", "oci_registry", "public_release"],
            },
        ],
        "agent_loop": {
            "producer_profiles": "abyss-machine artifacts producer-profiles --artifact-class ARTIFACT_CLASS --json",
            "trust_gate": "abyss-machine artifacts trust-gate --artifact-class ARTIFACT_CLASS --json",
        },
        "claim_limits": [
            "Producer profiles are OS Abyss policy/read-model data; they do not run owner validators or produce sidecars by themselves.",
        ],
        "errors": [],
        "latest": "/var/lib/abyss-machine/artifacts/producer-profiles/latest.json",
    }
    profile_path = tmp_path / "producer-profiles.json"
    profile_path.write_text(json.dumps(payload), encoding="utf-8")

    profiles = api.load_producer_profiles(profile_path)

    assert isinstance(profiles, ArtifactProducerProfilesReport)
    assert profiles.read_model_only is True
    assert profiles.artifact_class_filter == "public_media_export"
    assert profiles.agent_loop["producer_profiles"].startswith("abyss-machine artifacts producer-profiles")
    assert profiles.claim_limits
    assert isinstance(profiles.rows[0], ArtifactProducerProfile)
    assert profiles.rows[0].owner_repo == "Tree-of-Sophia"
    assert "public_media_export" in profiles.rows[0].artifact_classes
    assert profiles.rows[0].trust_root_modes == ["local_dev", "github_oidc", "public_release"]
    assert profiles.for_artifact_class("public_media_export") == profiles.rows
    assert [row.profile_id for row in profiles.for_owner_repo("abyss-machine")] == ["abyss-machine"]
    assert profiles.for_artifact_class("runtime_or_container_artifact") == []
