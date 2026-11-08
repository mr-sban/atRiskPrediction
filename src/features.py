"""Feature engineering for the OULAD at-risk project.

All functions here assume their inputs have already been truncated by
``src.cutoff``. The only non-truncated input is ``studentInfo`` (used
for the label and for static demographics, both of which are safe).
"""
from __future__ import annotations

from typing import Iterable

import pandas as pd

from .cutoff import (
    CUTOFF_DAY,
    assessments_due_by,
    submissions_by_cutoff,
    truncate_student_vle,
)

# Composite key identifying one student on one module presentation.
KEY = ["id_student", "code_module", "code_presentation"]

# Activity types we treat as "forum-like". Inspect vle.activity_type
# in notebook 01 and adjust if needed (see docs/week09_feature_tradeoffs.md).
FORUM_ACTIVITY_TYPES: tuple[str, ...] = ("forumng",)


# --------------------------------------------------------------------------
# Labels
# --------------------------------------------------------------------------
def build_labels(student_info: pd.DataFrame) -> pd.DataFrame:
    """Binary label from ``final_result``.

    at_risk = 1 if final_result in {Fail, Withdrawn}, else 0.
    """
    labels = student_info[KEY + ["final_result"]].copy()
    labels["at_risk"] = labels["final_result"].isin(["Fail", "Withdrawn"]).astype(int)
    return labels


# --------------------------------------------------------------------------
# Engagement
# --------------------------------------------------------------------------
def engagement_features(
    student_vle_trunc: pd.DataFrame,
    vle: pd.DataFrame,
    cutoff_day: int = CUTOFF_DAY,
) -> pd.DataFrame:
    """Overall engagement plus per-activity-type click totals.

    ``studentVle`` already carries ``code_module`` and ``code_presentation``,
    and ``id_site`` uniquely maps to (module, presentation, activity_type)
    in ``vle``. We therefore pull only ``id_site`` and ``activity_type``
    to avoid merge-suffix collisions on the KEY columns.
    """
    missing = [c for c in KEY if c not in student_vle_trunc.columns]
    if missing:
        raise KeyError(
            f"student_vle_trunc is missing required columns {missing}. "
            f"Present columns: {list(student_vle_trunc.columns)}"
        )

    sv = student_vle_trunc.merge(
        vle[["id_site", "activity_type"]],
        on="id_site",
        how="left",
    )
    sv = sv.dropna(subset=["activity_type"])

    overall = (
        sv.groupby(KEY)
        .agg(
            total_clicks=("sum_click", "sum"),
            active_days=("date", "nunique"),
            mean_clicks_per_active_day=("sum_click", "mean"),
            max_clicks_single_day=("sum_click", "max"),
        )
        .reset_index()
    )
    overall["coverage_ratio"] = overall["active_days"] / cutoff_day

    by_type = sv.pivot_table(
        index=KEY,
        columns="activity_type",
        values="sum_click",
        aggfunc="sum",
        fill_value=0,
    )
    by_type.columns = [f"clicks_{c}" for c in by_type.columns]
    by_type = by_type.reset_index()

    return overall.merge(by_type, on=KEY, how="left")


# --------------------------------------------------------------------------
# Forum activity
# --------------------------------------------------------------------------
def forum_features(
    student_vle_trunc: pd.DataFrame,
    vle: pd.DataFrame,
    forum_types: Iterable[str] = FORUM_ACTIVITY_TYPES,
) -> pd.DataFrame:
    """Click-based proxy for forum engagement."""
    missing = [c for c in KEY if c not in student_vle_trunc.columns]
    if missing:
        raise KeyError(
            f"student_vle_trunc is missing required columns {missing}. "
            f"Present columns: {list(student_vle_trunc.columns)}"
        )

    sv = student_vle_trunc.merge(
        vle[["id_site", "activity_type"]],
        on="id_site",
        how="left",
    )
    forum = sv.loc[sv["activity_type"].isin(forum_types)]
    return (
        forum.groupby(KEY)
        .agg(
            forum_clicks=("sum_click", "sum"),
            forum_active_days=("date", "nunique"),
        )
        .reset_index()
    )


# --------------------------------------------------------------------------
# Early assessment
# --------------------------------------------------------------------------
def early_assessment_features(
    student_assessment_by_cutoff: pd.DataFrame,
    assessments: pd.DataFrame,
    cutoff_day: int = CUTOFF_DAY,
) -> pd.DataFrame:
    """Submission counts, submission rate, and scores for assessments
    that were due by ``cutoff_day`` and submitted by ``cutoff_day``.
    """
    due = assessments_due_by(assessments, cutoff_day)[
        ["id_assessment", "code_module", "code_presentation", "date", "weight"]
    ]
    subs = student_assessment_by_cutoff.merge(due, on="id_assessment", how="inner")

    agg = (
        subs.groupby(KEY)
        .agg(
            early_submitted=("id_assessment", "count"),
            early_mean_score=("score", "mean"),
            early_min_score=("score", "min"),
            early_max_score=("score", "max"),
        )
        .reset_index()
    )

    n_due = (
        due.groupby(["code_module", "code_presentation"])
        .size()
        .rename("early_due")
        .reset_index()
    )
    agg = agg.merge(n_due, on=["code_module", "code_presentation"], how="left")
    agg["early_submission_rate"] = agg["early_submitted"] / agg["early_due"]
    agg["early_missing"] = agg["early_due"] - agg["early_submitted"]
    return agg


# --------------------------------------------------------------------------
# Demographics
# --------------------------------------------------------------------------
def demographic_features(student_info: pd.DataFrame) -> pd.DataFrame:
    cols = KEY + [
        "gender",
        "region",
        "highest_education",
        "imd_band",
        "age_band",
        "disability",
        "num_of_prev_attempts",
        "studied_credits",
    ]
    return student_info[cols].copy()


# --------------------------------------------------------------------------
# Full feature matrix
# --------------------------------------------------------------------------
def build_feature_matrix(
    student_info: pd.DataFrame,
    student_vle: pd.DataFrame,
    vle: pd.DataFrame,
    student_assessment: pd.DataFrame,
    assessments: pd.DataFrame,
    cutoff_day: int = CUTOFF_DAY,
) -> pd.DataFrame:
    """Assemble the day-``cutoff_day`` feature matrix for modelling."""
    sv_trunc = truncate_student_vle(student_vle, cutoff_day)
    sa_trunc = submissions_by_cutoff(student_assessment, cutoff_day)

    base = build_labels(student_info)
    demos = demographic_features(student_info)
    eng = engagement_features(sv_trunc, vle, cutoff_day)
    forum = forum_features(sv_trunc, vle)
    early = early_assessment_features(sa_trunc, assessments, cutoff_day)

    out = (
        base.merge(demos, on=KEY, how="left")
        .merge(eng, on=KEY, how="left")
        .merge(forum, on=KEY, how="left")
        .merge(early, on=KEY, how="left")
    )

    # Students with no VLE / forum / assessment activity appear as NaN
    # after the left joins. Counts and rates default to 0.
    count_like = [
        c
        for c in out.columns
        if any(
            k in c
            for k in (
                "clicks",
                "active_days",
                "total_clicks",
                "max_clicks",
                "forum_clicks",
                "forum_active_days",
                "early_submitted",
                "early_missing",
                "coverage_ratio",
                "mean_clicks_per_active_day",
                "early_submission_rate",
            )
        )
    ]
    out[count_like] = out[count_like].fillna(0)

    return out