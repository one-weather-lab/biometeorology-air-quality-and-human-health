"""
Script Name: indices.py
Purpose: Hourly PET and UTCI computation for the thermophysiological indices notebook.
Author(s): Christos Giannaros, One Weather Lab, UoI <chris.giannaros@uoi.gr>
Last updated: 2026-11-17
Version: 0.1.0
License: MIT
"""

from __future__ import annotations

# --- Imports ---
import biometeo
import numpy as np
import pandas as pd

from .scales import PET_SCALE, UTCI_SCALE, classify, mask_utci_inputs

# --- Configuration ---
PET_COLUMNS = ("ta", "vp", "tmrt", "ws1_1")
UTCI_COLUMNS = ("ta", "vp", "tmrt", "ws10")
RADIATIVE_COLUMNS = ("ta", "vp", "tmrt", "ws1_1", "ws10")
BLANK_LABEL = "Blank (out of range)"


# --- Functions ---
# [Internal helpers]
def _require_columns(available, columns: tuple[str, ...]) -> None:
    """Check that every required column is present in the input.

    Parameters
    ----------
    available : iterable of str
        Column names present in the input, such as a DataFrame's columns or a row's index.
    columns : tuple of str
        Column names the calculation requires.

    Returns
    -------
    None
        The function returns nothing when all required columns are present.
    """
    missing = [col for col in columns if col not in available]
    if missing:
        raise ValueError(f"Input missing required columns {missing}")


def _evaluate_radiative_load(row: pd.Series) -> pd.DataFrame:
    """Compute PET and UTCI for one hour with its calculated Tmrt and with Tmrt set to Ta.

    Parameters
    ----------
    row : pandas.Series
        One hour with ``ta`` [degC], ``vp`` [hPa], ``tmrt`` [degC], ``ws1_1`` [m/s] and
        ``ws10`` [m/s].

    Returns
    -------
    pandas.DataFrame
        Two rows indexed ``calculated`` and ``no_load`` (``tmrt = ta``, same wind and vapor
        pressure), with columns ``pet`` [degC], ``pet_class``, ``utci`` [degC, ``NaN`` outside
        the validity bounds] and ``utci_class`` (``"Blank (out of range)"`` where blank).
    """
    _require_columns(row.index, RADIATIVE_COLUMNS)
    cases = pd.DataFrame([row[list(RADIATIVE_COLUMNS)]] * 2, index=["calculated", "no_load"]).astype(float)
    cases.loc["no_load", "tmrt"] = cases.loc["no_load", "ta"]
    result = pd.DataFrame(index=cases.index)
    result["pet"] = compute_pet(cases)
    result["pet_class"] = classify(values=result["pet"], scale=PET_SCALE)
    result["utci"] = compute_utci(cases)
    result["utci_class"] = classify(values=result["utci"], scale=UTCI_SCALE).fillna(BLANK_LABEL)
    return result


# [Index computation]
def compute_pet(df: pd.DataFrame) -> pd.Series:
    """Compute PET for every row of an hourly input table.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly inputs with ``ta`` [degC], ``vp`` [hPa], ``tmrt`` [degC] and ``ws1_1``
        [m/s, 1.1 m wind speed].

    Returns
    -------
    pandas.Series
        PET [degC] named ``pet``, indexed like ``df``.
    """
    _require_columns(df.columns, PET_COLUMNS)
    # biometeo's docstring lists the inputs in a different order from its signature, so pass them by keyword.
    values = [
        float(biometeo.PET(Ta=row.ta, VP=row.vp, Tmrt=row.tmrt, v=row.ws1_1)["PET_v"])
        for row in df.itertuples(index=False)
    ]
    return pd.Series(values, index=df.index, name="pet", dtype=float)


def compute_utci(df: pd.DataFrame) -> pd.Series:
    """Compute UTCI for every row whose inputs fall inside the operational validity bounds.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly inputs with ``ta`` [degC], ``vp`` [hPa], ``tmrt`` [degC] and ``ws10``
        [m/s, 10 m wind speed].

    Returns
    -------
    pandas.Series
        UTCI [degC] named ``utci``, indexed like ``df``, with ``NaN`` where any input is
        outside the bounds of ``UTCI_VALIDITY_BOUNDS``.
    """
    _require_columns(df.columns, UTCI_COLUMNS)
    valid = mask_utci_inputs(ta=df["ta"], tmrt=df["tmrt"], ws10=df["ws10"], vp=df["vp"])
    values = np.full(len(df), np.nan, dtype=float)
    for position, (row, is_valid) in enumerate(zip(df.itertuples(index=False), valid)):
        if is_valid:
            values[position] = float(biometeo.UTCI(Ta=row.ta, VP=row.vp, Tmrt=row.tmrt, v=row.ws10))
    return pd.Series(values, index=df.index, name="utci", dtype=float)
