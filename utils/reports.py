"""
Script Name: reports.py
Purpose: Text summaries printed by the thermophysiological indices notebook.
Author(s): Christos Giannaros, One Weather Lab, UoI <chris.giannaros@uoi.gr>
Last updated: 2026-11-17
Version: 0.1.0
License: MIT
"""

from __future__ import annotations

# --- Imports ---
import numpy as np
import pandas as pd

from .indices import BLANK_LABEL, _evaluate_radiative_load
from .readers import _format_utc_timestamp
from .scales import (
    _align_utci_to_pet_classes,
    PET_SCALE,
    UTCI_SCALE,
    UTCI_VALIDITY_BOUNDS,
    ThermalScale,
    mask_utci_inputs,
)


# --- Functions ---
# [Internal helpers]
def _date_strings(df: pd.DataFrame) -> pd.Series:
    """Extract the calendar date of each hourly record.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly records with a datetime column ``time_utc``.

    Returns
    -------
    pandas.Series
        Date of each record formatted as ``YYYY-MM-DD``.
    """
    return df["time_utc"].dt.strftime("%Y-%m-%d")


def _format_minmax(sub: pd.DataFrame, col: str, unit: str) -> str:
    """Format the minimum and maximum of a column with the UTC hour of each.

    Parameters
    ----------
    sub : pandas.DataFrame
        Hourly records of one day with a datetime column ``time_utc``.
    col : str
        Name of the numeric column to summarise.
    unit : str
        Unit label appended to the text.

    Returns
    -------
    str
        Text of the form ``min (HHZ) .. max (HHZ) unit``.
    """
    idx_min = sub[col].idxmin()
    idx_max = sub[col].idxmax()
    h_min = sub.loc[idx_min, "time_utc"].hour
    h_max = sub.loc[idx_max, "time_utc"].hour
    return f"{sub.loc[idx_min, col]:6.2f} ({h_min:02d}Z) .. {sub.loc[idx_max, col]:6.2f} ({h_max:02d}Z) {unit}"


def _format_class_counts(
    df: pd.DataFrame,
    class_column: str,
    scale: ThermalScale,
    season_labels: dict[str, str],
    title: str,
    blank_label: str | None = None,
) -> str:
    """Tabulate class counts per day for one thermal-stress scale.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly records with a datetime column ``time_utc`` and the class column.
    class_column : str
        Name of the column holding each hour's class label.
    scale : ThermalScale
        Scale whose labels set the row order.
    season_labels : dict of str to str
        Mapping from ``YYYY-MM-DD`` date to the column label, in column order.
    title : str
        Heading printed above the table.
    blank_label : str or None, optional
        Label counted as an extra last row for hours with no class (missing values). If None,
        missing values are not counted.

    Returns
    -------
    str
        Title line followed by the table of hour counts, classes in rows and days in columns.
    """
    labels = df[class_column] if blank_label is None else df[class_column].fillna(blank_label)
    order = list(scale.labels) + ([blank_label] if blank_label is not None else [])
    counts = pd.crosstab(labels, _date_strings(df)).reindex(index=order, columns=list(season_labels), fill_value=0)
    counts.columns = [season_labels[d] for d in counts.columns]
    return f"{title}\n{counts.to_string()}"


def _utci_exclusion_reasons(row) -> list[str]:
    """List why an hourly record falls outside the UTCI validity bounds.

    Parameters
    ----------
    row : namedtuple
        One hour from ``DataFrame.itertuples`` with ``ta`` [degC], ``ws10`` [m/s], ``tmrt`` [degC] and ``vp`` [hPa].

    Returns
    -------
    list of str
        One text per violated bound, taken from ``UTCI_VALIDITY_BOUNDS``. The list is empty
        when the record lies inside all bounds.
    """
    ta_low, ta_high = UTCI_VALIDITY_BOUNDS["ta"]
    ws_low, ws_high = UTCI_VALIDITY_BOUNDS["ws10"]
    dt_low, dt_high = UTCI_VALIDITY_BOUNDS["tmrt_minus_ta"]
    vp_low, vp_high = UTCI_VALIDITY_BOUNDS["vp"]
    reasons = []
    if not ta_low <= row.ta <= ta_high:
        reasons.append(f"ta = {row.ta:.2f} C outside [{ta_low:g}, {ta_high:+g}] C")
    if not ws_low <= row.ws10 <= ws_high:
        if row.ws10 < ws_low:
            reasons.append(f"ws10 = {row.ws10:.4f} m/s < {ws_low:.2f} m/s lower bound")
        else:
            reasons.append(f"ws10 = {row.ws10:.4f} m/s > {ws_high:.1f} m/s")
    if not dt_low <= row.tmrt - row.ta <= dt_high:
        reasons.append(f"tmrt - ta = {row.tmrt - row.ta:.2f} K outside [{dt_low:g}, {dt_high:+g}] K")
    if not vp_low <= row.vp <= vp_high:
        reasons.append(f"vp = {row.vp:.2f} hPa outside [{vp_low:g}, {vp_high:g}] hPa")
    return reasons


# [Section 1: PET]
def format_pet_daily_table(df: pd.DataFrame, season_labels: dict[str, str]) -> str:
    """Summarise the inputs and PET of each day as daily minimum and maximum with their hours.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly table with ``time_utc``, ``ta`` [degC], ``tmrt`` [degC], ``ws1_1`` [m/s] and
        ``pet`` [degC].
    season_labels : dict of str to str
        Day label for each date (``YYYY-MM-DD``), in display order.

    Returns
    -------
    str
        Record count line followed by one row per day.
    """
    dates = _date_strings(df)
    lines = [
        f"Loaded {len(df)} hourly records across {dates.nunique()} days in Ioannina.",
        f"{'Day':24s} {'Ta [°C]':27s} {'Tmrt [°C]':28s} {'ws1_1 [m/s]':30s} {'PET [°C]':27s}",
        "-" * 140,
    ]
    for date_str, label in season_labels.items():
        sub = df[dates == date_str]
        lines.append(
            f"{label:24s} "
            f"{_format_minmax(sub, 'ta', '°C'):27s} "
            f"{_format_minmax(sub, 'tmrt', '°C'):28s} "
            f"{_format_minmax(sub, 'ws1_1', 'm/s'):30s} "
            f"{_format_minmax(sub, 'pet', '°C'):27s}"
        )
    return "\n".join(lines)


def format_pet_class_counts(df: pd.DataFrame, season_labels: dict[str, str]) -> str:
    """Count hours per PET stress class and day.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly table with ``time_utc`` and ``pet_class``.
    season_labels : dict of str to str
        Day label for each date (``YYYY-MM-DD``), in display order.

    Returns
    -------
    str
        Title line and a class-by-day count table.
    """
    return _format_class_counts(
        df, "pet_class", PET_SCALE, season_labels, "Hourly PET stress-class counts per day (24 h each):"
    )


# [Section 2: UTCI]
def format_utci_screening(df: pd.DataFrame, season_labels: dict[str, str]) -> str:
    """Report the UTCI validity screening, each excluded hour and the daily UTCI range.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly table with ``time_utc``, ``ta`` [degC], ``tmrt`` [degC], ``ws10`` [m/s],
        ``vp`` [hPa] and ``utci`` [degC, ``NaN`` where blank].
    season_labels : dict of str to str
        Day label for each date (``YYYY-MM-DD``), in display order.

    Returns
    -------
    str
        Screening count, one line per excluded hour with its reasons, the reason for
        leaving such hours blank, and one row per day.
    """
    valid = mask_utci_inputs(ta=df["ta"], tmrt=df["tmrt"], ws10=df["ws10"], vp=df["vp"])
    n_valid = int(valid.sum())
    ws_low, ws_high = UTCI_VALIDITY_BOUNDS["ws10"]
    lines = [f"UTCI screening: {n_valid} / {len(df)} hours within validity bounds; {len(df) - n_valid} blank hour(s)."]
    for row in df[~valid].itertuples(index=False):
        reasons = ", ".join(_utci_exclusion_reasons(row))
        lines.append(f"Excluded timestamp : {_format_utc_timestamp(row.time_utc)} -> {reasons}")
    lines += [
        "",
        f"{'Day':24s} {'Valid':7s} {'ws10 [m/s]':30s} {'UTCI [°C]':27s}",
        "-" * 92,
    ]
    dates = _date_strings(df)
    for date_str, label in season_labels.items():
        sub = df[dates == date_str]
        sub_valid = sub[sub["utci"].notna()]
        lines.append(
            f"{label:24s} "
            f"{len(sub_valid):2d} / {len(sub):2d} "
            f"{_format_minmax(sub, 'ws10', 'm/s'):30s} "
            f"{_format_minmax(sub_valid, 'utci', '°C'):27s}"
        )
    return "\n".join(lines)


def format_utci_class_counts(df: pd.DataFrame, season_labels: dict[str, str]) -> str:
    """Count hours per UTCI stress category and day, blank hours included.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly table with ``time_utc`` and ``utci_class`` (``NaN`` where blank).
    season_labels : dict of str to str
        Day label for each date (``YYYY-MM-DD``), in display order.

    Returns
    -------
    str
        Title line and a category-by-day count table with a blank row.
    """
    return _format_class_counts(
        df, "utci_class", UTCI_SCALE, season_labels, "Hourly UTCI stress-category counts per day:", BLANK_LABEL
    )


# [Section 3: comparison]
def format_comparison(df: pd.DataFrame) -> str:
    """Summarise PET minus UTCI and stress-class agreement over the hours with both indices.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly table with ``time_utc``, ``pet`` and ``utci`` [degC], ``pet_class`` and
        ``utci_class``.

    Returns
    -------
    str
        Paired-hour count, mean, minimum and maximum of PET minus UTCI with their times,
        and the number of hours whose classes agree, PET extreme classes counting as UTCI
        very strong or extreme.
    """
    paired = df[df["pet"].notna() & df["utci"].notna()]
    diff = paired["pet"] - paired["utci"]
    idx_min, idx_max, idx_abs = diff.idxmin(), diff.idxmax(), diff.abs().idxmax()
    same_class = int((paired["pet_class"] == _align_utci_to_pet_classes(paired["utci_class"])).sum())

    def _time_of(idx) -> str:
        return f"{_format_utc_timestamp(paired.loc[idx, 'time_utc'])}"

    return "\n".join([
        f"Paired valid hours          : {len(paired)} / {len(df)}",
        f"Mean (PET - UTCI)           : {diff.mean():+.2f} K",
        f"Min  (PET - UTCI)           : {diff[idx_min]:+.2f} K at {_time_of(idx_min)}",
        f"Max  (PET - UTCI)           : {diff[idx_max]:+.2f} K at {_time_of(idx_max)}",
        f"Max |PET - UTCI|            : {abs(diff[idx_abs]):.2f} K at {_time_of(idx_abs)}",
        f"Stress-class agreement      : {same_class} matching / {len(paired) - same_class} differing "
        f"(out of {len(paired)} hours; PET extreme classes count as UTCI very strong or extreme)",
    ])


def format_radiative_load(df: pd.DataFrame, timestamp: str) -> str:
    """Show PET and UTCI for one hour with its calculated Tmrt and with no radiative load.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly table with ``time_utc``, ``ta`` [degC], ``vp`` [hPa], ``tmrt`` [degC],
        ``ws1_1`` [m/s] and ``ws10`` [m/s].
    timestamp : str
        Hour to evaluate, e.g. ``"2012-07-11 12:00 UTC"``; read as UTC when no zone is given.

    Returns
    -------
    str
        The hour's inputs, a two-row table of both cases and the shift of each index.
    """
    target_utc = pd.Timestamp(timestamp)
    target_utc = target_utc.tz_localize("UTC") if target_utc.tzinfo is None else target_utc.tz_convert("UTC")
    matched = df[df["time_utc"] == target_utc]
    if matched.empty:
        raise KeyError(f"Timestamp {_format_utc_timestamp(target_utc)} not found in df_days.")
    row = matched.iloc[0]
    cases = _evaluate_radiative_load(row)
    calc, no_load = cases.loc["calculated"], cases.loc["no_load"]

    def _utci_text(value: float) -> str:
        return f"{value:9.2f}" if np.isfinite(value) else "      N/A"

    both_valid = np.isfinite(calc["utci"]) and np.isfinite(no_load["utci"])
    utci_shift = f"{no_load['utci'] - calc['utci']:+9.2f}" if both_valid else "      N/A"
    return "\n".join([
        f"Timestamp {_format_utc_timestamp(target_utc)} | "
        f"Ta = {row['ta']:.2f} °C, Tmrt = {row['tmrt']:.2f} °C, VP = {row['vp']:.2f} hPa, "
        f"ws1_1 = {row['ws1_1']:.2f} m/s, ws10 = {row['ws10']:.2f} m/s",
        f"{'Case':48s} {'PET [°C]':>9s} {'PET class':24s} {'UTCI [°C]':>9s} {'UTCI class':24s}",
        "-" * 118,
        f"{'Calculated radiative load (RayMan Tmrt)':48s} {calc['pet']:9.2f} {calc['pet_class']:24s} "
        f"{_utci_text(calc['utci'])} {calc['utci_class']:24s}",
        f"{'No radiative load (Tmrt = Ta, same wind and VP)':48s} {no_load['pet']:9.2f} "
        f"{no_load['pet_class']:24s} {_utci_text(no_load['utci'])} {no_load['utci_class']:24s}",
        f"{'Shift (No load - Calculated)':48s} {no_load['pet'] - calc['pet']:+9.2f} {'':24s} {utci_shift}",
    ])
