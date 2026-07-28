#!/usr/bin/env python3
"""Verify the installed wheel carries the explicit abyss-stack adapter client."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import tomllib
import venv
from importlib.metadata import version
from pathlib import Path


PART_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PART_ROOT.parents[3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--installed-probe", action="store_true")
    return parser.parse_args()


def _wheel_path(explicit: Path | None) -> Path:
    if explicit is not None:
        wheel = explicit.resolve()
        if not wheel.is_file():
            raise SystemExit(f"wheel does not exist: {wheel}")
        return wheel
    project = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    project_version = project["project"]["version"]
    wheels = sorted(
        (REPO_ROOT / "dist").glob(f"aoa_sdk-{project_version}-*.whl")
    )
    if len(wheels) != 1:
        raise SystemExit(
            f"expected one aoa-sdk {project_version} wheel, found {len(wheels)}"
        )
    return wheels[0].resolve()


def _installed_probe() -> int:
    from aoa_sdk.contracts.control_plane import ProvenanceRef
    from aoa_sdk.runtime_adapters import (
        ABYSS_STACK_ADAPTER_VERSION,
        AbyssStackRuntimeAdapter,
        AbyssStackRuntimeBinding,
        AbyssStackSubprocessTransport,
        RuntimeArtifactLocation,
        load_abyss_stack_runtime_profile,
    )

    import aoa_sdk.runtime_adapters.abyss_stack as adapter_module

    module_path = Path(adapter_module.__file__).resolve()
    if REPO_ROOT.resolve() in module_path.parents:
        raise SystemExit(f"probe imported adapter from checkout: {module_path}")
    root = Path.cwd()
    policy_path = root / "runtime-policy.yaml"
    policy_path.write_text("enabled: true\n", encoding="utf-8")
    descriptor_path = root / "runtime-profile.v1.json"
    descriptor_path.write_text(
        json.dumps(
            {
                "schema_version": "abyss_stack_agent_os_runtime_profile_v1",
                "profile_id": (
                    "runtime-profile:abyss-stack-governed-execution-v1"
                ),
                "runtime_owner": "abyss-stack",
                "adapter_id": ABYSS_STACK_ADAPTER_VERSION,
                "adapter_protocol_version": "aoa_runtime_adapter_v1",
                "source_ref": ABYSS_STACK_ADAPTER_VERSION,
                "schema_ref": "schemas/agent-os-runtime-profile.schema.json",
                "supported_plan_schema_versions": ["aoa_control_plane_v1"],
                "supported_event_schema_versions": ["aoa_control_plane_v1"],
                "supported_effect_classes": ["read_only", "repo_mutation"],
                "required_constraint_artifacts": [
                    {
                        "owner_repo": "abyss-stack",
                        "artifact_ref": "config/runtime-policy.yaml",
                        "source_ref": "runtime-policy-v1",
                        "schema_ref": "docs/runtime-policy.md",
                        "schema_version": "v1",
                    }
                ],
                "compatibility": [
                    {"scenario_id": "bounded_change_safe"}
                ],
                "boundaries": {
                    "executes_through_governed_runner_only": True
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    profile = load_abyss_stack_runtime_profile(
        descriptor_path,
        constraint_locations=(
            RuntimeArtifactLocation(
                owner_repo="abyss-stack",
                artifact_ref="config/runtime-policy.yaml",
                local_path=str(policy_path),
            ),
        ),
    )
    request_path = root / "request.json"
    request_path.write_text(
        '{"goal":"probe","playbook_id":"AOA-P-0011"}\n',
        encoding="utf-8",
    )
    request_ref = ProvenanceRef(
        owner_repo="wheel-probe",
        artifact_ref="request.json",
        source_ref="wheel-probe",
        artifact_digest="sha256:" + "0" * 64,
        schema_ref="probe",
        schema_version="v1",
    )
    binding = AbyssStackRuntimeBinding(
        binding_id="binding:installed-wheel",
        plan_digest="sha256:" + "1" * 64,
        scenario_id="bounded_change_safe",
        playbook_id="AOA-P-0011",
        request_ref=request_ref,
        request_path=str(request_path),
        source_locations=(
            RuntimeArtifactLocation(
                owner_repo=request_ref.owner_repo,
                artifact_ref=request_ref.artifact_ref,
                local_path=str(request_path),
            ),
        ),
        abi_locations=(),
        adapter_contract_ref=profile.provenance,
    )
    executable = root / "bridge"
    executable.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "payload = json.load(sys.stdin)\n"
        "print(json.dumps({\n"
        "  'schema_version': 'abyss_stack_agent_os_bridge_response_v1',\n"
        "  'ok': True,\n"
        "  'result': {'operation': sys.argv[1], 'payload': payload},\n"
        "}))\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    transport = AbyssStackSubprocessTransport(
        executable,
        state_root=root / "state",
    )
    response = transport.invoke("status", {"probe": True})
    adapter = AbyssStackRuntimeAdapter(
        profile=profile,
        binding=binding,
        transport=transport,
    )
    if response["operation"] != "status" or response["payload"] != {"probe": True}:
        raise SystemExit("installed subprocess transport changed the envelope")
    if (
        adapter.executes_plan_steps is not True
        or adapter.transport_only is not True
        or adapter.execution_owner != "abyss-stack"
    ):
        raise SystemExit("installed adapter authority markers are invalid")
    print(
        json.dumps(
            {
                "adapter_id": profile.adapter_id,
                "execution_owner": adapter.execution_owner,
                "module_path": str(module_path),
                "package_version": version("aoa-sdk"),
                "transport_only": adapter.transport_only,
            },
            sort_keys=True,
        )
    )
    return 0


def _outer_probe(wheel: Path) -> int:
    with tempfile.TemporaryDirectory(
        prefix="aoa-sdk-abyss-stack-adapter-wheel-"
    ) as temp_dir:
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
            ],
            cwd=probe_root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise SystemExit(
                "installed wheel abyss-stack adapter probe failed:\n"
                f"{completed.stdout}{completed.stderr}"
            )
        print(completed.stdout.strip())
    print(
        "[ok] installed wheel exposed the owner-exact profile loader, binding, "
        "authority markers, and no-shell transport without stack imports"
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.installed_probe:
        return _installed_probe()
    return _outer_probe(_wheel_path(args.wheel))


if __name__ == "__main__":
    raise SystemExit(main())
