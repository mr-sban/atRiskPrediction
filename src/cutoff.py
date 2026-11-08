"""Simulate the early-assessment cutoff.

All feature functions downstream must be given data that has *already*
been truncated to information available on or before CUTOFF_DAY.
Anything not truncated here is leakage.
"""
from __future__ import annotations

import pandas as pd

CUTOFF_DAY: int = 28


def truncate_student_vle(
    student_vle: pd.DataFrame, cutoff_day: int = CUTOFF_DAY
) -> pd.DataFrame:
    """Keep only VLE interactions on or before the cutoff day."""
    return student_vle.loc[student_vle["date"] <= cutoff_day].copy()


def assessments_due_by(
    assessments: pd.DataFrame, cutoff_day: int = CUTOFF_DAY
) -> pd.DataFrame:
    """Assessments whose *deadline* is on or before the cutoff day."""
    return assessments.loc[assessments["date"] <= cutoff_day].copy()


def submissions_by_cutoff(
    student_assessment: pd.DataFrame, cutoff_day: int = CUTOFF_DAY
) -> pd.DataFrame:
    """Submissions actually *received* on or before the cutoff day.

    This is stricter than ``assessments_due_by``: a student may submit an
    assessment after its deadline, and we must not see that score until
    after the cutoff.
    """
    return student_assessment.loc[
        student_assessment["date_submitted"] <= cutoff_day
    ].copy()