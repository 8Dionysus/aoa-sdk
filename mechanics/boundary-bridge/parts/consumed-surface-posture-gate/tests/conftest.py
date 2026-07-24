from __future__ import annotations

import importlib
import os
import sys
from contextlib import ExitStack
from pathlib import Path


PART_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PART_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))
materialized_fixture_archive = importlib.import_module(
    "routing_shadow_fixture_archive"
).materialized_fixture_archive

_STACK = ExitStack()
_ENV_BY_ARCHIVE = {
    "producer-inputs": "AOA_ROUTING_PRODUCER_FIXTURE_ROOT",
    "inputs": "AOA_ROUTING_HYDRATED_FIXTURE_ROOT",
    "canonical-generated": "AOA_ROUTING_CANONICAL_GENERATED_ROOT",
}


def pytest_configure() -> None:
    for archive_name, env_name in _ENV_BY_ARCHIVE.items():
        root = _STACK.enter_context(materialized_fixture_archive(archive_name))
        os.environ[env_name] = str(root)


def pytest_unconfigure() -> None:
    for env_name in _ENV_BY_ARCHIVE.values():
        os.environ.pop(env_name, None)
    _STACK.close()
