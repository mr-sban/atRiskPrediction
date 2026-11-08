"""Load OULAD tables from data/raw/.

Keeping loading in one place makes the modelling pipeline in Week 11
easy to swap onto the processed feature table.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

TABLE_NAMES = (
    "courses",
    "assessments",
    "vle",
    "studentInfo",
    "studentRegistration",
    "studentAssessment",
    "studentVle",
)


def load_table(name: str) -> pd.DataFrame:
    """Load a single OULAD CSV by table name (no .csv extension)."""
    path = DATA_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Download OULAD into {DATA_DIR} first."
        )
    return pd.read_csv(path)


def load_all() -> Dict[str, pd.DataFrame]:
    """Load every OULAD table into a dict keyed by table name."""
    return {name: load_table(name) for name in TABLE_NAMES}