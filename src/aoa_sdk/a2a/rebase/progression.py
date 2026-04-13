from __future__ import annotations

from .models import CohortPattern, ProgressionOverlay, QuestPassport


DIFFICULTY_ORDER = {
    "d0_probe": 0,
    "d1_patch": 1,
    "d2_slice": 2,
    "d3_seam": 3,
    "d4_architecture": 4,
    "d5_doctrine": 5,
}

RISK_ORDER = {
    "r0_readonly": 0,
    "r1_repo_local": 1,
    "r2_contract": 2,
    "r3_side_effect": 3,
}


def progression_allows(
    passport: QuestPassport,
    cohort: CohortPattern,
    overlay: ProgressionOverlay | None,
) -> tuple[bool, list[str]]:
    if overlay is None:
        return False, ["missing_progression_overlay"]

    reasons: list[str] = []

    max_difficulty = max(
        (DIFFICULTY_ORDER[item] for item in overlay.unlocked_difficulties), default=-1
    )
    if DIFFICULTY_ORDER[passport.difficulty] > max_difficulty:
        reasons.append("difficulty_not_unlocked")

    max_risk = max((RISK_ORDER[item] for item in overlay.unlocked_risks), default=-1)
    if RISK_ORDER[passport.risk] > max_risk:
        reasons.append("risk_not_unlocked")

    if cohort not in overlay.unlocked_cohorts:
        reasons.append("cohort_not_unlocked")

    return not reasons, reasons
