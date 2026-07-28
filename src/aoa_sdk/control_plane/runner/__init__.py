"""AoARunner lifecycle client and deterministic non-executing adapter."""

from .core import (
    AOA_RUNNER_VERSION,
    AoARunner,
    AoARunnerError,
    RunnerCommandRejected,
    RunnerSessionNotFound,
    default_runner_provenance,
)
from .reference import (
    REFERENCE_ADAPTER_VERSION,
    DeterministicReferenceAdapter,
    ReferenceAdapterError,
    ReferenceAdapterUnavailable,
    default_reference_adapter_provenance,
    reference_runtime_profile,
)

__all__ = [
    "AOA_RUNNER_VERSION",
    "REFERENCE_ADAPTER_VERSION",
    "AoARunner",
    "AoARunnerError",
    "DeterministicReferenceAdapter",
    "ReferenceAdapterError",
    "ReferenceAdapterUnavailable",
    "RunnerCommandRejected",
    "RunnerSessionNotFound",
    "default_reference_adapter_provenance",
    "default_runner_provenance",
    "reference_runtime_profile",
]
