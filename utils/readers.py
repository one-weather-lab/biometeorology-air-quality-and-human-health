"""
Script Name: readers.py
Purpose: Load and validate committed M216 thermal-index CSV datasets.
Author(s): Christos Giannaros, One Weather Lab, UoI <chris.giannaros@uoi.gr>
Last updated: 2026-11-17
Version: 0.1.2
License: MIT
"""

from __future__ import annotations

# --- Imports ---
from pathlib import Path

import numpy as np
import pandas as pd

# --- Configuration ---
FOUR_DAYS_FILENAME = "ioannina_2012_four_seasonal_days.csv"
FOUR_DAYS_COLUMNS = ("time_utc", "ta", "vp", "ws1_1", "ws10", "tmrt")
NUMERIC_COLUMNS = ("ta", "vp", "ws1_1", "ws10", "tmrt")
WIND_COLUMNS = ("ws1_1", "ws10")


# --- Functions ---
# [Dataset readers]
def read_four_seasonal_days(data_dir: str | Path | None = None) -> pd.DataFrame:
    """Read and validate the 96-hour four-seasonal-days CSV dataset.

    Parameters
    ----------
    data_dir : str or pathlib.Path or None, optional
        Directory containing ``ioannina_2012_four_seasonal_days.csv``. Defaults
        to ``<repo>/data`` relative to this module.

    Returns
    -------
    pandas.DataFrame
        Chronologically sorted DataFrame with columns ``time_utc``
        [UTC timestamp], ``ta`` [degC, 2 m air temperature], ``vp``
        [hPa, vapor pressure], ``ws1_1`` [m/s, 1.1 m wind speed],
        ``ws10`` [m/s, unclipped 10 m wind speed], and ``tmrt``
        [degC, mean radiant temperature].
    """
    base_dir = Path(data_dir) if data_dir is not None else Path(__file__).resolve().parents[1] / "data"
    if not base_dir.is_dir():
        raise FileNotFoundError(f"Data directory not found: {base_dir}")

    csv_path = base_dir / FOUR_DAYS_FILENAME
    if not csv_path.is_file():
        raise FileNotFoundError(f"Four-seasonal-days dataset not found: {csv_path}")

    # Load raw CSV and verify schema
    df = pd.read_csv(csv_path, encoding="utf-8")
    missing_cols = [col for col in FOUR_DAYS_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns {missing_cols}: {csv_path.name}")
    if df.empty:
        raise ValueError(f"Dataset contains no rows: {csv_path.name}")

    # Parse UTC timestamps and validate numeric fields
    df = df.loc[:, list(FOUR_DAYS_COLUMNS)].copy()
    df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True, errors="raise")
    if df["time_utc"].isna().any():
        raise ValueError(f"Dataset contains missing timestamps: {csv_path.name}")
    if df["time_utc"].duplicated().any():
        raise ValueError(f"Dataset contains duplicate timestamps: {csv_path.name}")

    for col in NUMERIC_COLUMNS:
        series = pd.to_numeric(df[col], errors="raise").astype(float)
        if series.isna().any() or not np.isfinite(series.to_numpy()).all():
            raise ValueError(f"Dataset contains NaN or non-finite values in column '{col}'")
        df[col] = series

    # Sub-0.5 m/s winds remain untouched so UTCI masking can exclude them explicitly.
    for col in WIND_COLUMNS:
        if (df[col] < 0.0).any():
            raise ValueError(f"Dataset contains negative wind speed in column '{col}'")
    if (df["vp"] < 0.0).any():
        raise ValueError("Dataset contains negative vapor pressure in column 'vp'")

    return df.sort_values("time_utc").reset_index(drop=True)
