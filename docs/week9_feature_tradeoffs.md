# Week 9 — Feature engineering tradeoffs

## Cutoff

`CUTOFF_DAY = 28` (four weeks into the presentation).

**Why day 28.** It is the most commonly used early-warning window in the
OULAD literature, gives every module–presentation at least one due
assessment, and keeps enough VLE signal (~20% of the semester's clicks)
to be informative without leaking most of the term.

**Leakage discipline.**
- VLE features use only `studentVle.date <= 28`.
- Assessment features use only submissions with
  `date_submitted <= 28` — a *stricter* rule than "assessment deadline
  ≤ 28", because late submissions would otherwise leak a score we would
  not have known on day 28.
- Labels come from `studentInfo.final_result`, i.e. end-of-term
  outcomes. Labels are constructed separately from the features and
  never merged into the feature columns before modelling.

**Label definition.** `at_risk = 1` if `final_result ∈ {Fail, Withdrawn}`,
else `0`. This is the standard binary framing for the project.

**Known tension.** Students who unregistered on or before day 28 are
arguably no longer "at risk after an early assessment" — they have
already left. We keep them in Week 9 to preserve class balance and
comparability with the OULAD literature; Week 10 will decide whether to
filter them (as an optional sensitivity check).

## Feature families and tradeoffs

### Engagement (from `studentVle` + `vle`)
| Feature | Tradeoff |
|---|---|
| `total_clicks` | Simple but favours high-volume clickers regardless of usefulness. |
| `active_days` | Robust to long inactive gaps; under-rewards intense bursts. |
| `coverage_ratio = active_days / 28` | Consistency measure; goes to zero for non-engaged learners. |
| `mean_clicks_per_active_day` | Density; noisy for students with 1–2 active days. |
| `max_clicks_single_day` | Captures cramming; sensitive to a single anomalous day. |
| `clicks_<activity_type>` | Separates qualitatively different behaviours (content vs. forum vs. quiz); adds dimensionality. Tree models handle it; linear models may need regularisation. |

### Forum (proxy)
No true forum-post table exists in OULAD — only click-level interactions.
`forum_clicks` and `forum_active_days` therefore measure *reading +
interaction with forum-like resources*, not posting. This is a dataset
limitation, not a pipeline flaw. Activity types considered "forum-like"
are controlled by `FORUM_ACTIVITY_TYPES` in `src/features.py`; after
inspecting `vle.activity_type` in notebook 01, we use `forumng`.

### Early assessment (from `assessments` + `studentAssessment`)
| Feature | Tradeoff |
|---|---|
| `early_mean_score` | Captures performance; NaN for non-submitters, needs imputation in Week 11. |
| `early_min_score` | Penalises one bad early result; sensitive to a single outlier. |
| `early_max_score` | Captures best-case performance. |
| `early_submitted` | Submission *behaviour* is itself a strong risk signal. |
| `early_submission_rate` | Normalises across modules with different assessment counts. |
| `early_missing` | Explicit missingness signal. |

We did **not** use assessment `weight` in `early_mean_score` because
early assessments often have small weights and weighting inflates their
variance. Unweighted mean is more transparent for Week 9; Week 10 can
revisit as a sensitivity check.

### Demographics (from `studentInfo`)
Static, available at registration, safe from leakage. Included because
they improve predictive performance in published baselines, but they
raise fairness concerns — Week 12 will report subgroup performance and
the report will discuss the tradeoff. Categorical columns are **not
encoded yet**; Week 11 handles encoding inside a scikit-learn `ColumnTransformer`.

## Missingness decisions (Week 9)

- **Zero VLE / forum activity** → count features filled with `0`. This is
  a real signal (a student who never clicked), not a data problem.
- **Zero early submissions** → score features (`early_mean_score`,
  `early_min_score`, `early_max_score`) intentionally left as `NaN` so
  Week 11 can choose imputation strategy (median vs. sentinel vs. model-native).
- **Missing demographics** (`highest_education`, `imd_band`) → left as
  `NaN`; Week 11 imputes with a "missing" category (these are
  categorical, not numeric).
- **Withdrawn students** → retained (see "Known tension" above).

## Open questions carried into Week 10

1. Should students with `date_unregistration <= 28` be excluded as an
   optional sensitivity analysis?
2. Should categorical demographics be included in the primary model, or
   only in a fairness-audit model?
3. Do we add time-of-week or time-series shape features (e.g. slope of
   weekly clicks), or keep the feature set static?
4. Which imputation strategy for `early_*_score` fits the class balance
   best after SMOTE?