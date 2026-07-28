#!/usr/bin/env python3
"""Verify an installed SDK wheel composes, stores, and closes one C5 chain."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import tomllib
import venv
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path


PART_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PART_ROOT.parents[3]
C2_FIXTURE = (
    REPO_ROOT
    / "mechanics"
    / "boundary-bridge"
    / "parts"
    / "plan-compilation-control-plane"
    / "examples"
    / "installed-wheel-smoke.inputs.json"
)
NOW = datetime(2026, 7, 26, 22, 0, tzinfo=timezone.utc)
ZERO_DIGEST = "sha256:" + "0" * 64


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--installed-probe", action="store_true")
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--store", type=Path)
    return parser.parse_args()


def _wheel_path(explicit: Path | None) -> Path:
    if explicit is not None:
        wheel = explicit.resolve()
        if not wheel.is_file():
            raise SystemExit(f"wheel does not exist: {wheel}")
        return wheel
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project_version = project["project"]["version"]
    wheels = sorted((REPO_ROOT / "dist").glob(f"aoa_sdk-{project_version}-*.whl"))
    if len(wheels) != 1:
        raise SystemExit(
            f"expected exactly one aoa-sdk {project_version} wheel under dist/, "
            f"found {len(wheels)}"
        )
    return wheels[0].resolve()


def _installed_probe(fixture_path: Path, store: Path) -> int:
    from aoa_sdk.contracts.control_plane import (
        ApprovalDecision,
        CandidateExplanation,
        CloseoutBundleRef,
        ContentRef,
        EvalVerdictRef,
        EvidenceBundleRef,
        MemoryReceiptRef,
        ProvenanceRef,
        RouteDecision,
        RouteExplanation,
        RouteIntent,
        ScenarioBinding,
        StartCommand,
        candidate_explanation_disposition,
        canonical_digest,
    )
    from aoa_sdk.contracts.evidence_chain import CheckpointReceiptRef
    from aoa_sdk.contracts.evidence_chain import EvidenceChain as ContractEvidenceChain
    from aoa_sdk.control_plane.evidence_chain import (
        EvidenceChainRepository,
        assemble_evidence_chain,
        assert_evidence_chain_complete,
    )
    from aoa_sdk.control_plane.planning import (
        compile_run_plan,
        load_plan_compilation_snapshot,
    )
    from aoa_sdk.control_plane.runner import (
        AoARunner,
        DeterministicReferenceAdapter,
        reference_runtime_profile,
    )
    from aoa_sdk.models import EvidenceChain as PublicEvidenceChain

    import aoa_sdk.control_plane.evidence_chain as chain_module
    import aoa_sdk.contracts.evidence_chain as contract_module

    module_paths = (
        Path(chain_module.__file__).resolve(),
        Path(contract_module.__file__).resolve(),
    )
    if any(REPO_ROOT.resolve() in path.parents for path in module_paths):
        raise SystemExit(
            f"probe imported C5 modules from checkout: {[str(path) for path in module_paths]}"
        )
    if PublicEvidenceChain is not ContractEvidenceChain:
        raise SystemExit("installed aoa_sdk.models does not export EvidenceChain")

    def provenance(owner: str, artifact_ref: str) -> ProvenanceRef:
        return ProvenanceRef(
            owner_repo=owner,
            artifact_ref=artifact_ref,
            source_ref="installed-wheel-probe",
            artifact_digest=ZERO_DIGEST,
            schema_ref="probe",
            schema_version="v1",
        )

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    base_decision = RouteDecision.model_validate(fixture["decision"])
    binding = ScenarioBinding.model_validate(fixture["scenario_binding"])
    intent = RouteIntent(
        intent_id=base_decision.intent_ref.object_id,
        correlation_id=base_decision.correlation_id,
        objective="verify installed C5 evidence composition",
        requested_by=binding.agent_refs[0],
        scenario=binding.scenario,
        requested_capability_kinds=(
            base_decision.candidates[0].capability.capability_kind,
        ),
        context_refs=binding.input_refs,
        authored_at=NOW,
        provenance=provenance(
            base_decision.intent_ref.owner_repo,
            "probe/intent.json",
        ),
    )
    decision = base_decision.model_copy(
        update={
            "intent_ref": ContentRef(
                object_id=intent.intent_id,
                owner_repo=intent.provenance.owner_repo,
                schema_version=intent.schema_version,
                digest=canonical_digest(intent),
            )
        }
    )
    decision_ref = ContentRef(
        object_id=decision.decision_id,
        owner_repo=decision.provenance.owner_repo,
        schema_version=decision.schema_version,
        digest=canonical_digest(decision),
    )
    explanation = RouteExplanation(
        explanation_id=f"explanation:{decision.decision_id}",
        correlation_id=decision.correlation_id,
        decision_ref=decision_ref,
        decision_status=decision.status,
        candidate_explanations=tuple(
            CandidateExplanation(
                candidate_id=item.candidate_id,
                disposition=candidate_explanation_disposition(
                    item,
                    selected_candidate_id=decision.selected_candidate_id,
                ),
                reason_codes=item.reason_codes,
                evidence_refs=item.evidence_refs,
            )
            for item in decision.candidates
        ),
        selected_candidate_id=decision.selected_candidate_id,
        ambiguity_codes=tuple(
            item for item in decision.reason_codes if item.startswith("ambiguous_")
        ),
        provenance=provenance("aoa-sdk", "probe/explanation.json"),
    )
    plan = compile_run_plan(
        decision,
        binding.model_copy(update={"decision_ref": decision_ref}),
        reference_runtime_profile(),
        load_plan_compilation_snapshot(),
    )
    runner = AoARunner(clock=lambda: NOW, id_factory=lambda: "c5-wheel")
    adapter = DeterministicReferenceAdapter(clock=lambda: NOW)
    session = runner.prepare(plan)
    start = StartCommand(
        command_id="command:c5-wheel:start",
        idempotency_key="idempotency:c5-wheel:start",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        expected_revision=0,
        issued_at=NOW,
        issued_by=provenance("installed-wheel-probe", "probe/start.json"),
        reason="run the installed no-execution C5 contract probe",
    )
    status = runner.start(session, adapter, start)
    if status.state != "awaiting_approval":
        raise SystemExit("installed Runner did not stop before approval")
    for index, request in enumerate(runner.approval_requests(session)):
        status = runner.approve(
            session,
            ApprovalDecision(
                decision_id=f"approval:c5-wheel:{index}",
                request_id=request.request_id,
                requirement_id=request.requirement_id,
                session_id=session.session_id,
                correlation_id=session.correlation_id,
                plan_digest=session.plan_digest,
                snapshot_digest=session.snapshot_digest,
                verdict="approved",
                approval_authority=request.approval_authority,
                decided_by=provenance(
                    "installed-wheel-probe",
                    f"probe/approval-{index}.json",
                ),
                decided_at=NOW,
                reason="approve only the deterministic installed-wheel probe",
            ),
        )
    if status.state != "running":
        raise SystemExit("installed Runner did not enter running after approvals")
    runtime_refs = tuple(
        EvidenceBundleRef(
            ref_id=f"runtime-evidence:{item.requirement_id}",
            provenance=provenance(
                item.producer_owner,
                f"probe/runtime/{item.requirement_id}.json",
            ),
            satisfies_requirement_ids=(item.requirement_id,),
        )
        for item in plan.evidence_requirements
        if item.terminal_required
    )
    adapter.advance(
        session,
        trigger="runtime_completed",
        at=NOW,
        evidence_bundle_refs=runtime_refs,
    )
    if runner.sync(session, adapter).state != "completed":
        raise SystemExit("installed Runner did not reconcile completion")
    outcome = runner.outcome(session)
    if outcome is None:
        raise SystemExit("installed Runner did not return an outcome")
    assembled_by = provenance(
        "aoa-sdk",
        "src/aoa_sdk/control_plane/evidence_chain.py",
    )
    partial = assemble_evidence_chain(
        intent=intent,
        decision=decision,
        explanation=explanation,
        plan=plan,
        session=session,
        events=runner.events(session),
        runtime_outcome=outcome,
        assembled_at=NOW,
        assembled_by=assembled_by,
    )
    if partial.disposition != "partial":
        raise SystemExit("owner-incomplete installed chain was not partial")

    eval_refs = tuple(
        EvalVerdictRef(
            ref_id=f"eval-verdict:{item.requirement_id}",
            provenance=provenance(
                item.eval_owner_ref.owner_repo,
                f"probe/eval/{item.requirement_id}.json",
            ),
            satisfies_requirement_ids=(item.requirement_id,),
        )
        for item in plan.eval_requirements
    )
    memory_refs = tuple(
        MemoryReceiptRef(
            ref_id=f"memory-receipt:{item.requirement_id}",
            provenance=provenance(
                item.memory_owner_ref.owner_repo,
                f"probe/memo/{item.requirement_id}.json",
            ),
            satisfies_requirement_ids=(item.requirement_id,),
        )
        for item in plan.retention_requirements
    )
    checkpoint_refs = (
        CheckpointReceiptRef(
            ref_id="checkpoint-receipt:c5-wheel",
            provenance=provenance(
                plan.checkpoint_policy.owner.owner_repo,
                "probe/checkpoint/reviewed.json",
            ),
            review_status="reviewed",
            covered_step_ids=plan.checkpoint_policy.required_after_step_ids,
        ),
    )
    closeout_owners = {item.owner_ref.owner_repo for item in plan.closeout_requirements}
    if len(closeout_owners) != 1:
        raise SystemExit("installed probe requires one exact closeout owner")
    closeout = CloseoutBundleRef(
        ref_id="closeout-receipt:c5-wheel",
        provenance=provenance(
            next(iter(closeout_owners)),
            "probe/closeout/bundle.json",
        ),
        satisfies_requirement_ids=tuple(
            item.requirement_id for item in plan.closeout_requirements
        ),
    )
    complete = assemble_evidence_chain(
        intent=intent,
        decision=decision,
        explanation=explanation,
        plan=plan,
        session=session,
        events=runner.events(session),
        runtime_outcome=outcome,
        eval_verdict_refs=eval_refs,
        memory_receipt_refs=memory_refs,
        checkpoint_receipt_refs=checkpoint_refs,
        closeout_bundle_ref=closeout,
        assembled_at=NOW,
        assembled_by=assembled_by,
    )
    assert_evidence_chain_complete(complete)
    repository = EvidenceChainRepository(store.resolve())
    if repository.record(partial).revision != 1:
        raise SystemExit("installed repository did not record partial revision 1")
    if repository.record(complete).revision != 2:
        raise SystemExit("installed repository did not record complete revision 2")
    if repository.resolve_session(session) != complete:
        raise SystemExit("installed repository session lookup changed the chain")
    if repository.resolve_closeout(closeout) != complete:
        raise SystemExit("installed repository closeout lookup changed the chain")
    if runner.closeout(session, outcome, complete).state != "closed":
        raise SystemExit("installed Runner did not close from the complete chain")
    print(
        json.dumps(
            {
                "chain_digest": complete.chain_digest,
                "disposition": complete.disposition,
                "event_count": len(complete.events),
                "module_paths": [str(path) for path in module_paths],
                "package_version": version("aoa-sdk"),
                "repository_revisions": 2,
                "runner_state": runner.status(session).state,
                "session_id": session.session_id,
            },
            sort_keys=True,
        )
    )
    return 0


def _outer_probe(wheel: Path) -> int:
    if not C2_FIXTURE.is_file():
        raise SystemExit("C2 installed-wheel input fixture is missing")
    with tempfile.TemporaryDirectory(prefix="aoa-sdk-evidence-chain-wheel-") as temp:
        probe_root = Path(temp)
        venv_root = probe_root / "venv"
        venv.EnvBuilder(with_pip=True, clear=False).create(venv_root)
        python = venv_root / "bin" / "python"
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "--disable-pip-version-check",
                "install",
                str(wheel),
            ],
            cwd=probe_root,
            env=environment,
            check=True,
        )
        completed = subprocess.run(
            [
                str(python),
                str(Path(__file__).resolve()),
                "--installed-probe",
                "--fixture",
                str(C2_FIXTURE),
                "--store",
                str(probe_root / "chain-store"),
            ],
            cwd=probe_root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise SystemExit(
                "installed wheel C5 evidence-chain probe failed:\n"
                f"{completed.stdout}{completed.stderr}"
            )
        print(completed.stdout.strip())
    print(
        "[ok] installed wheel composed partial and complete C5 revisions, "
        "resolved exact identities, and closed the no-execution Runner"
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.installed_probe:
        if args.fixture is None or args.store is None:
            raise SystemExit("--installed-probe requires --fixture and --store")
        return _installed_probe(args.fixture.resolve(), args.store)
    return _outer_probe(_wheel_path(args.wheel))


if __name__ == "__main__":
    raise SystemExit(main())
