# atRiskPrediction
Project for COSC329 using the OULAD dataset to predict at risk students.

Binary classification of students as "at risk" (fail or withdraw) using only
information available up to day 28 of their module presentation.

## Project layout

- `data/raw/` - the 7 original OULAD CSVs (not committed; download from the OU data repository).
- `data/processed/` - engineered feature matrices.
- `src/` - reusable modules imported by notebooks and (later) the modelling pipeline.
- `notebooks/` - Jupyter notebooks containing analysis. 
- `docs/` - data dictionary and week-by-week tradeoff notes.

## Cutoff

`CUTOFF_DAY = 28`. See `docs/week09_feature_tradeoffs.md` for reasoning.
