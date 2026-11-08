# OULAD data dictionary (columns used in this project)

Grain: **one row per (id_student, code_module, code_presentation)** in the
feature matrix. Each source table below is listed with its native grain
and the columns used.

## `studentInfo.csv`
One row per student–module–presentation.

| Column | Type | Notes |
|---|---|---|
| id_student | int | key |
| code_module | str | key |
| code_presentation | str | key |
| gender | str | M / F |
| region | str | 13 categories |
| highest_education | str | 5 categories, some NaN |
| imd_band | str | 10 bands, some NaN |
| age_band | str | 0-35 / 35-55 / 55<= |
| num_of_prev_attempts | int | 0+ |
| studied_credits | int | 30–655 |
| disability | str | Y / N |
| final_result | str | Distinction / Pass / Fail / Withdrawn — **label source** |

## `studentRegistration.csv`
One row per student–module–presentation.

| Column | Type | Notes |
|---|---|---|
| date_registration | int | days relative to module start (often negative) |
| date_unregistration | int / NaN | days relative to module start; NaN = still enrolled |

Only used for exploratory analysis; `final_result == Withdrawn` already
encodes the outcome.

## `courses.csv`
One row per module–presentation.

| Column | Notes |
|---|---|
| code_module, code_presentation | keys |
| module_presentation_length | days of the presentation |

## `assessments.csv`
One row per assessment.

| Column | Notes |
|---|---|
| id_assessment | key |
| code_module, code_presentation | keys |
| assessment_type | TMA / CMA / Exam |
| date | deadline in days relative to module start |
| weight | % contribution to final grade |

## `studentAssessment.csv`
One row per student–assessment submission.

| Column | Notes |
|---|---|
| id_student, id_assessment | keys |
| date_submitted | days relative to module start |
| is_banked | 1 = result carried over from previous attempt |
| score | 0–100, NaN if not graded |

## `vle.csv`
One row per VLE resource.

| Column | Notes |
|---|---|
| id_site | key |
| code_module, code_presentation | keys |
| activity_type | forumng, oucontent, homepage, quiz, resource, etc. |
| week_from, week_to | weeks the resource was active (often NaN) |

## `studentVle.csv`
One row per student–site–day interaction.

| Column | Notes |
|---|---|
| id_student, id_site | keys |
| code_module, code_presentation | keys |
| date | days relative to module start (may be negative) |
| sum_click | number of clicks that day |

**This is the largest table; never join it to the feature matrix directly — always aggregate first.**

---

## Engineered columns in `features_day28.parquet`

| Column | Source | Meaning |
|---|---|---|
| at_risk | studentInfo.final_result | 1 if Fail or Withdrawn |
| total_clicks | studentVle | sum of `sum_click` over the window |
| active_days | studentVle | distinct dates with any click |
| mean_clicks_per_active_day | derived | density of engagement |
| max_clicks_single_day | studentVle | peak daily activity |
| coverage_ratio | derived | active_days / CUTOFF_DAY |
| clicks_<activity_type> | studentVle + vle | per-activity click totals |
| forum_clicks | studentVle + vle | clicks on forum-like activity |
| forum_active_days | studentVle + vle | days with any forum click |
| early_submitted | studentAssessment | submissions by cutoff |
| early_due | assessments | assessments due by cutoff for that module–presentation |
| early_submission_rate | derived | early_submitted / early_due |
| early_missing | derived | early_due − early_submitted |
| early_mean_score | studentAssessment.score | mean score on early submissions |
| early_min_score | studentAssessment.score | min score on early submissions |
| early_max_score | studentAssessment.score | max score on early submissions |
| + demographics | studentInfo | see table above |