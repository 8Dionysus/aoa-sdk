"""Protocol-independent direct-owner connection descriptors.

Adapters may prepare a bounded connection descriptor. They deliberately have
no execution method: the SDK control plane does not become an organ gateway.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from ..contracts.organs import EndpointContract, Identifier


class DirectConnectionDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    adapter_id: Identifier
    endpoint: EndpointContract
    credential_class: Identifier
    credential_material_present: bool = False
    execution_authorized: bool = False


@runtime_checkable
class ProtocolIndependentAdapter(Protocol):
    adapter_id: str

    def prepare_connection(
        self,
        endpoint: EndpointContract,
        credential_class: str,
    ) -> DirectConnectionDescriptor: ...
