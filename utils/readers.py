"""
Script Name: readers.py
Purpose: Load and validate thermal-index CSV datasets.
Author(s): Christos Giannaros, One Weather Lab, UoI <chris.giannaros@uoi.gr>
Last updated: 2026-11-18
Version: 0.3.0
License: MIT
"""

from __future__ import annotations

# --- Imports ---
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# --- Classes ---
@dataclass(frozen=True)
class PopulationGroup:
    """One population group of the 2012 hourly mPET dataset.

    Parameters
    ----------
    column : str
        Name of the mPET column in the dataset.
    name : str
        Group name, such as ``Female senior`` or ``Male worker, light labor``.
    sex : str
        ``Female`` or ``Male``.
    kind : str
        ``senior``, ``adult`` or ``worker``.
    age_years : int
        Age [years].
    height_m : float
        Body height [m].
    weight_kg : float
        Body weight [kg].
    activity_w : int
        Metabolic rate from activity [W].
    """

    column: str
    name: str
    sex: str
    kind: str
    age_years: int
    height_m: float
    weight_kg: float
    activity_w: int

    @property
    def label(self) -> str:
        """Return the group name with its age, height, weight and activity.

        Returns
        -------
        str
            Text such as ``Female senior (70 y, 1.65 m, 60 kg, 50 W)``.
        """
        return f"{self.name} ({self.age_years} y, {self.height_m:.2f} m, {self.weight_kg:g} kg, {self.activity_w} W)"

    @property
    def short_label(self) -> str:
        """Return the group name with its activity.

        Returns
        -------
        str
            Text such as ``Female senior, 50 W``.
        """
        return f"{self.name}, {self.activity_w} W"



# --- Configuration ---
FOUR_DAYS_FILENAME = "ioannina_2012_four_seasonal_days.csv"
FOUR_DAYS_COLUMNS = ("time_utc", "ta", "vp", "ws1_1", "ws10", "tmrt")
NUMERIC_COLUMNS = ("ta", "vp", "ws1_1", "ws10", "tmrt")
WIND_COLUMNS = ("ws1_1", "ws10")
UTC_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M UTC"

MPET_FILENAME = "ioannina_2012_hourly_mpet.csv"
POPULATION_GROUPS = {
    "f_adult": PopulationGroup("mpet_f_adult", "Female adult", "Female", "adult", 35, 1.65, 65, 80),
    "m_adult": PopulationGroup("mpet_m_adult", "Male adult", "Male", "adult", 35, 1.75, 75, 80),
    "f_senior": PopulationGroup("mpet_f_senior", "Female senior", "Female", "senior", 70, 1.65, 60, 50),
    "m_senior": PopulationGroup("mpet_m_senior", "Male senior", "Male", "senior", 70, 1.75, 70, 50),
    "f_worker_1": PopulationGroup("mpet_f_worker_1", "Female worker, light labor", "Female", "worker", 35, 1.65, 65, 110),
    "m_worker_1": PopulationGroup("mpet_m_worker_1", "Male worker, light labor", "Male", "worker", 35, 1.75, 75, 110),
    "f_worker_2": PopulationGroup("mpet_f_worker_2", "Female worker, moderate labor", "Female", "worker", 35, 1.65, 65, 210),
    "m_worker_2": PopulationGroup("mpet_m_worker_2", "Male worker, moderate labor", "Male", "worker", 35, 1.75, 75, 210),
    "f_worker_3": PopulationGroup("mpet_f_worker_3", "Female worker, heavy labor", "Female", "worker", 35, 1.65, 65, 310),
    "m_worker_3": PopulationGroup("mpet_m_worker_3", "Male worker, heavy labor", "Male", "worker", 35, 1.75, 75, 310),
}
CORE_GROUPS = tuple(
    POPULATION_GROUPS[key]
    for key in ("f_senior", "m_senior", "f_adult", "m_adult", "f_worker_2", "m_worker_2")
)
ACTIVITY_GROUPS = tuple(POPULATION_GROUPS[key] for key in ("m_worker_1", "m_worker_2", "m_worker_3"))
MPET_COLUMNS = (
    "time_utc",
    "ta",
    "vp",
    "ws1_1",
    "tmrt",
    *(group.column for group in POPULATION_GROUPS.values()),
)
MPET_NUMERIC_COLUMNS = MPET_COLUMNS[1:]
MPET_WIND_COLUMNS = ("ws1_1",)


# --- Functions ---
# [Internal helpers]
def _format_utc_timestamp(timestamp) -> str:
    """Format a timestamp as a UTC string for user-facing output.

    Parameters
    ----------
    timestamp : pandas.Timestamp or datetime.datetime
        Timestamp in UTC.

    Returns
    -------
    str
        Timestamp formatted with ``UTC_TIMESTAMP_FORMAT``, such as ``2012-04-26 07:00 UTC``.
    """
    return timestamp.strftime(UTC_TIMESTAMP_FORMAT)


def _read_validated_csv(
    data_dir: str | Path | None,
    filename: str,
    description: str,
    columns: tuple[str, ...],
    numeric_columns: tuple[str, ...],
    wind_columns: tuple[str, ...],
) -> pd.DataFrame:
    """Read an hourly CSV file and validate its schema, timestamps and numeric fields.

    Parameters
    ----------
    data_dir : str or pathlib.Path or None
        Directory containing the file. When None, ``<repo>/data`` relative to this module.
    filename : str
        Name of the CSV file inside ``data_dir``.
    description : str
        Dataset name used at the start of the file-not-found message.
    columns : tuple of str
        Required columns, starting with ``time_utc``; all other columns are dropped.
    numeric_columns : tuple of str
        Columns that must be finite numbers.
    wind_columns : tuple of str
        Wind speed columns [m/s] that must not be negative.

    Returns
    -------
    pandas.DataFrame
        Chronologically sorted DataFrame holding ``columns``, with ``time_utc``
        as UTC timestamps and the numeric columns as floats.
    """
    base_dir = Path(data_dir) if data_dir is not None else Path(__file__).resolve().parents[1] / "data"
    if not base_dir.is_dir():
        raise FileNotFoundError(f"Data directory not found: {base_dir}")

    csv_path = base_dir / filename
    if not csv_path.is_file():
        raise FileNotFoundError(f"{description} dataset not found: {csv_path}")

    # Load raw CSV and verify schema
    df = pd.read_csv(csv_path, encoding="utf-8")
    missing_cols = [col for col in columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns {missing_cols}: {csv_path.name}")
    if df.empty:
        raise ValueError(f"Dataset contains no rows: {csv_path.name}")

    # Parse UTC timestamps and validate numeric fields
    df = df.loc[:, list(columns)].copy()
    df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True, errors="raise")
    if df["time_utc"].isna().any():
        raise ValueError(f"Dataset contains missing timestamps: {csv_path.name}")
    if df["time_utc"].duplicated().any():
        raise ValueError(f"Dataset contains duplicate timestamps: {csv_path.name}")

    for col in numeric_columns:
        series = pd.to_numeric(df[col], errors="raise").astype(float)
        if series.isna().any() or not np.isfinite(series.to_numpy()).all():
            raise ValueError(f"Dataset contains NaN or non-finite values in column '{col}'")
        df[col] = series

    # Sub-0.5 m/s winds remain untouched so UTCI masking can exclude them explicitly.
    for col in wind_columns:
        if (df[col] < 0.0).any():
            raise ValueError(f"Dataset contains negative wind speed in column '{col}'")
    if (df["vp"] < 0.0).any():
        raise ValueError("Dataset contains negative vapor pressure in column 'vp'")

    return df.sort_values("time_utc").reset_index(drop=True)


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
    return _read_validated_csv(
        data_dir=data_dir,
        filename=FOUR_DAYS_FILENAME,
        description="Four-seasonal-days",
        columns=FOUR_DAYS_COLUMNS,
        numeric_columns=NUMERIC_COLUMNS,
        wind_columns=WIND_COLUMNS,
    )


def read_hourly_mpet(data_dir: str | Path | None = None) -> pd.DataFrame:
    """Read and validate the 2012 hourly mPET CSV dataset.

    Parameters
    ----------
    data_dir : str or pathlib.Path or None, optional
        Directory containing ``ioannina_2012_hourly_mpet.csv``. Defaults
        to ``<repo>/data`` relative to this module.

    Returns
    -------
    pandas.DataFrame
        Chronologically sorted DataFrame with columns ``time_utc``
        [UTC timestamp], ``ta`` [degC, 2 m air temperature], ``vp``
        [hPa, vapor pressure], ``ws1_1`` [m/s, 1.1 m wind speed],
        ``tmrt`` [degC, mean radiant temperature] and one ``mpet_<sex>_<group>``
        column [degC, mPET] for each of the ten population groups.
    """
    return _read_validated_csv(
        data_dir=data_dir,
        filename=MPET_FILENAME,
        description="Hourly mPET",
        columns=MPET_COLUMNS,
        numeric_columns=MPET_NUMERIC_COLUMNS,
        wind_columns=MPET_WIND_COLUMNS,
    )
