"""Agent OS control-plane implementation families.

The SDK coordinates typed decisions and lifecycle clients. Runtime execution
stays behind external adapter boundaries.
"""

from .api import ControlPlaneAPI
from .evidence_chain import (
    EvidenceChainError,
    EvidenceChainRepository,
    assemble_evidence_chain,
    assert_evidence_chain,
    assert_evidence_chain_complete,
    evidence_chain_digest,
)
from .runner import AoARunner
from .incarnation import (
    IncarnationBindingError,
    agent_incarnation_binding_ref,
    assert_agent_incarnation_binding_digest,
    assert_agent_incarnation_binding_matches_plan,
    build_agent_incarnation_binding,
    load_model_realization_ref,
)
from ..contracts.incarnation import (
    AGENT_INCARNATION_BINDING_VERSION,
    AgentIncarnationBinding,
    ContinuationObligation,
    IncarnationPermissionPosture,
    IncarnationStopCondition,
    IncarnationToolProfile,
    IncarnationUsageMetering,
    WakeCondition,
    WakeEscalationPolicy,
)

__all__ = [
    "AoARunner",
    "ControlPlaneAPI",
    "EvidenceChainError",
    "EvidenceChainRepository",
    "AGENT_INCARNATION_BINDING_VERSION",
    "AgentIncarnationBinding",
    "ContinuationObligation",
    "IncarnationPermissionPosture",
    "IncarnationStopCondition",
    "IncarnationToolProfile",
    "IncarnationUsageMetering",
    "WakeCondition",
    "WakeEscalationPolicy",
    "assemble_evidence_chain",
    "assert_evidence_chain",
    "assert_evidence_chain_complete",
    "evidence_chain_digest",
    "IncarnationBindingError",
    "agent_incarnation_binding_ref",
    "assert_agent_incarnation_binding_digest",
    "assert_agent_incarnation_binding_matches_plan",
    "build_agent_incarnation_binding",
    "load_model_realization_ref",
]
