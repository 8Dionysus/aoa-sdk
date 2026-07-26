#!/usr/bin/env python3
"""Verify an installed SDK wheel can run and restore the C3 reference lifecycle."""

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--installed-probe", action="store_true")
    parser.add_argument("--fixture", type=Path)
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


def _installed_probe(fixture_path: Path) -> int:
    from aoa_sdk import AoASDK
    from aoa_sdk.contracts.control_plane import (
        ApprovalDecision,
        ProvenanceRef,
        RouteDecision,
        ScenarioBinding,
        StartCommand,
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

    import aoa_sdk.control_plane.runner.core as runner_module
    import aoa_sdk.control_plane.runner.reference as reference_module

    module_paths = (
        Path(runner_module.__file__).resolve(),
        Path(reference_module.__file__).resolve(),
    )
    if any(REPO_ROOT.resolve() in module_path.parents for module_path in module_paths):
        raise SystemExit(
            f"probe imported Runner from checkout: {[str(path) for path in module_paths]}"
        )
    public_sdk = AoASDK.from_workspace(Path.cwd())
    if not isinstance(public_sdk.runner, AoARunner):
        raise SystemExit("installed AoASDK does not expose AoARunner")

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    plan = compile_run_plan(
        RouteDecision.model_validate(fixture["decision"]),
        ScenarioBinding.model_validate(fixture["scenario_binding"]),
        reference_runtime_profile(),
        load_plan_compilation_snapshot(),
    )
    now = datetime(2026, 7, 26, 18, 0, tzinfo=timezone.utc)
    runner = AoARunner(clock=lambda: now, id_factory=lambda: "installed-wheel")
    adapter = DeterministicReferenceAdapter(clock=lambda: now)
    session = runner.prepare(plan)
    command = StartCommand(
        command_id="command:installed-wheel:start",
        idempotency_key="idempotency:installed-wheel:start",
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        expected_revision=0,
        issued_at=now,
        issued_by=ProvenanceRef(
            owner_repo="installed-wheel-probe",
            artifact_ref="probe/start-command",
            source_ref="installed-wheel",
            artifact_digest="sha256:" + "0" * 64,
            schema_ref="probe",
            schema_version="v1",
        ),
        reason="verify the installed non-executing Runner lifecycle",
    )
    status = runner.start(session, adapter, command)
    if status.state != "awaiting_approval":
        raise SystemExit("installed Runner did not stop before approval")
    request = runner.approval_requests(session)[0]
    approval = ApprovalDecision(
        decision_id="approval:installed-wheel",
        request_id=request.request_id,
        requirement_id=request.requirement_id,
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        plan_digest=session.plan_digest,
        snapshot_digest=session.snapshot_digest,
        verdict="approved",
        approval_authority=request.approval_authority,
        decided_by=command.issued_by,
        decided_at=now,
        reason="approve the installed reference lifecycle only",
    )
    if runner.approve(session, approval).state != "running":
        raise SystemExit("installed Runner did not enter running after approval")
    adapter.advance(
        session,
        trigger="runtime_completed",
        at=now,
    )
    if runner.sync(session, adapter).state != "completed":
        raise SystemExit("installed Runner did not reconcile completion")
    outcome = runner.outcome(session)
    if outcome is None or outcome.execution_status != "succeeded":
        raise SystemExit("installed reference adapter did not return RunOutcome")
    restored = AoARunner(clock=lambda: now, id_factory=lambda: "unused")
    if restored.restore(plan, session, adapter) != runner.status(session):
        raise SystemExit("installed Runner restore changed runtime status")
    if restored.events(session) != runner.events(session):
        raise SystemExit("installed Runner restore changed append-only events")
    if adapter.executes_plan_steps is not False:
        raise SystemExit("reference adapter claims plan-step execution")
    print(
        json.dumps(
            {
                "event_count": len(runner.events(session)),
                "executes_plan_steps": adapter.executes_plan_steps,
                "module_paths": [str(path) for path in module_paths],
                "package_version": version("aoa-sdk"),
                "plan_digest": plan.plan_digest,
                "restored_state": restored.status(session).state,
                "runtime_owner": plan.runtime_profile.runtime_owner,
                "session_id": session.session_id,
            },
            sort_keys=True,
        )
    )
    return 0


def _outer_probe(wheel: Path) -> int:
    if not C2_FIXTURE.is_file():
        raise SystemExit("C2 installed-wheel input fixture is missing")
    with tempfile.TemporaryDirectory(prefix="aoa-sdk-runner-wheel-") as temp_dir:
        probe_root = Path(temp_dir)
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
            ],
            cwd=probe_root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise SystemExit(
                "installed wheel C3 Runner probe failed:\n"
                f"{completed.stdout}{completed.stderr}"
            )
        if any(path.name == "aoa-playbooks" for path in probe_root.iterdir()):
            raise SystemExit("clean Runner wheel probe unexpectedly contains aoa-playbooks")
        print(completed.stdout.strip())
    print(
        "[ok] installed wheel ran and restored the deterministic C3 lifecycle "
        "without executing a plan step or requiring an aoa-playbooks checkout"
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.installed_probe:
        if args.fixture is None:
            raise SystemExit("--installed-probe requires --fixture")
        return _installed_probe(args.fixture.resolve())
    return _outer_probe(_wheel_path(args.wheel))


if __name__ == "__main__":
    raise SystemExit(main())
