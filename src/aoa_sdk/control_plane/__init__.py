"""Agent OS control-plane implementation families.

The SDK coordinates typed decisions and lifecycle clients. Runtime execution
stays behind external adapter boundaries.
"""

from .api import ControlPlaneAPI
from .agent_tool_routing import (
    AGENT_TOOL_ROUTING_RESOLVER_VERSION,
    default_agent_tool_routing_provenance,
    route_agent_tool_decision,
)
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
    build_agent_incarnation_binding_v2,
    build_obligation_actor_run_plan,
    load_model_realization_ref,
)
from ..contracts.incarnation import (
    AGENT_INCARNATION_BINDING_VERSION,
    AGENT_INCARNATION_BINDING_V2_VERSION,
    AgentIncarnationBinding,
    AgentIncarnationBindingV2,
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
    "AGENT_TOOL_ROUTING_RESOLVER_VERSION",
    "default_agent_tool_routing_provenance",
    "route_agent_tool_decision",
    "EvidenceChainError",
    "EvidenceChainRepository",
    "AGENT_INCARNATION_BINDING_VERSION",
    "AGENT_INCARNATION_BINDING_V2_VERSION",
    "AgentIncarnationBinding",
    "AgentIncarnationBindingV2",
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
    "build_agent_incarnation_binding_v2",
    "build_obligation_actor_run_plan",
    "load_model_realization_ref",
]
