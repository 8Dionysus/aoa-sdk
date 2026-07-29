"""Deterministic addressing for owner-authored organ-result reviews."""

from __future__ import annotations

from ..contracts.control_plane import canonical_digest
from ..contracts.organs import (
    OwnerResultReviewReceipt,
    OwnerResultReviewStatement,
)
from ..errors import AoASDKError


class OwnerResultReviewError(AoASDKError, ValueError):
    """An owner-result review receipt is not bound to its exact statement."""


def materialize_owner_result_review(
    statement: OwnerResultReviewStatement,
) -> OwnerResultReviewReceipt:
    """Address an already owner-authored statement without deciding its meaning."""

    payload = statement.model_dump(mode="json")
    return OwnerResultReviewReceipt.model_validate(
        {
            **payload,
            "review_id": canonical_digest(statement),
        }
    )


def assert_owner_result_review(
    receipt: OwnerResultReviewReceipt,
) -> OwnerResultReviewReceipt:
    """Reject receipt identity drift without upgrading the owner's assessment."""

    statement = OwnerResultReviewStatement.model_validate(
        receipt.model_dump(mode="json", exclude={"review_id"})
    )
    expected = canonical_digest(statement)
    if receipt.review_id != expected:
        raise OwnerResultReviewError(
            f"owner result review digest mismatch: expected {expected}, "
            f"got {receipt.review_id}"
        )
    return receipt
