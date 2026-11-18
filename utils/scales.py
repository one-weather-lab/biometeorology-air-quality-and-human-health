"""
Script Name: scales.py
Purpose: Thermal-stress assessment scales (PET/mPET and UTCI) and vectorized
         classification helpers.
Author(s): Christos Giannaros, One Weather Lab, UoI <chris.giannaros@uoi.gr>
Last updated: 2026-11-17
Version: 0.2.0
License: MIT
"""

from __future__ import annotations

# --- Imports ---
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


# --- Classes ---
@dataclass(frozen=True)
class ScaleBand:
    """Single interval definition in a thermal-stress assessment scale."""

    label: str
    lower: float
    upper: float
    lower_inclusive: bool
    upper_inclusive: bool
    color: str
    sensation: str = ""

    def matches(self, values: np.ndarray) -> np.ndarray:
        """Evaluate elementwise membership in this thermal-stress band.

        Parameters
        ----------
        values : numpy.ndarray
            Numeric array of thermal index values [degC].

        Returns
        -------
        numpy.ndarray
            Boolean mask matching ``values`` shape.
        """
        lower_ok = values >= self.lower if self.lower_inclusive else values > self.lower
        upper_ok = values <= self.upper if self.upper_inclusive else values < self.upper
        return lower_ok & upper_ok

    def format_range(self) -> str:
        """Format the band's numeric threshold for figure legends.

        Returns
        -------
        str
            Human-readable threshold span in degrees Celsius.
        """
        if np.isneginf(self.lower):
            return f"< {self.upper:g} °C"
        if np.isposinf(self.upper):
            return f"> {self.lower:g} °C"
        left = f"{self.lower:g}"
        right = f"{self.upper:g}"
        return f"{left} to {right} °C"


@dataclass(frozen=True)
class ThermalScale:
    """Ordered collection of contiguous, non-overlapping thermal-stress bands."""

    name: str
    bands: tuple[ScaleBand, ...]

    @property
    def labels(self) -> tuple[str, ...]:
        """Return ordered stress-class labels from coldest to warmest.

        Returns
        -------
        tuple of str
            Ordered class names.
        """
        return tuple(band.label for band in self.bands)


# --- Configuration ---
# PET/mPET thermal stress scale:
# Matzarakis, A. et al. (1999). Applications of a universal thermal index:
# physiological equivalent temperature. https://doi.org/10.1007/s004840050119
PET_SCALE = ThermalScale(
    name="PET / mPET",
    bands=(
        ScaleBand("Extreme cold stress", -np.inf, 4.0, False, False, "#2b4c7e", "Very cold"),
        ScaleBand("Strong cold stress", 4.0, 8.0, True, False, "#4575b4", "Cold"),
        ScaleBand("Moderate cold stress", 8.0, 13.0, True, False, "#74add1", "Cool"),
        ScaleBand("Slight cold stress", 13.0, 18.0, True, False, "#abd9e9", "Slightly cool"),
        ScaleBand("No thermal stress", 18.0, 23.0, True, True, "#e6f5d0", "Comfortable"),
        ScaleBand("Slight heat stress", 23.0, 29.0, False, True, "#fee090", "Slightly warm"),
        ScaleBand("Moderate heat stress", 29.0, 35.0, False, True, "#fdae61", "Warm"),
        ScaleBand("Strong heat stress", 35.0, 41.0, False, True, "#f46d43", "Hot"),
        ScaleBand("Extreme heat stress", 41.0, np.inf, False, False, "#a50026", "Very hot"),
    ),
)

# UTCI thermal stress scale:
# Bröde, P. et al. (2012). Deriving the operational procedure for the Universal
# Thermal Climate Index (UTCI). https://doi.org/10.1007/s00484-011-0454-1
UTCI_SCALE = ThermalScale(
    name="UTCI",
    bands=(
        ScaleBand("Extreme cold stress", -np.inf, -40.0, False, False, "#1a237e"),
        ScaleBand("Very strong cold stress", -40.0, -27.0, True, False, "#2b4c7e"),
        ScaleBand("Strong cold stress", -27.0, -13.0, True, False, "#4575b4"),
        ScaleBand("Moderate cold stress", -13.0, 0.0, True, False, "#74add1"),
        ScaleBand("Slight cold stress", 0.0, 9.0, True, False, "#abd9e9"),
        ScaleBand("No thermal stress", 9.0, 26.0, True, True, "#e6f5d0"),
        ScaleBand("Moderate heat stress", 26.0, 32.0, False, True, "#fee090"),
        ScaleBand("Strong heat stress", 32.0, 38.0, False, True, "#fdae61"),
        ScaleBand("Very strong heat stress", 38.0, 46.0, False, True, "#f46d43"),
        ScaleBand("Extreme heat stress", 46.0, np.inf, False, False, "#a50026"),
    ),
)

# PET has no "very strong" classes, so its open-ended extremes are compared with both the
# UTCI very strong and extreme classes.
UTCI_TO_PET_CLASS = {
    "Very strong cold stress": "Extreme cold stress",
    "Very strong heat stress": "Extreme heat stress",
}

# Operational UTCI polynomial validity bounds:
# Bröde, P. et al. (2012). Deriving the operational procedure for the Universal
# Thermal Climate Index (UTCI). https://doi.org/10.1007/s00484-011-0454-1
UTCI_VALIDITY_BOUNDS = {
    "ta": (-50.0, 50.0),
    "ws10": (0.5, 17.0),
    "tmrt_minus_ta": (-30.0, 70.0),
    "vp": (0.0, 50.0),
}


# --- Functions ---
# [Internal helpers]
def _align_utci_to_pet_classes(utci_classes: pd.Series) -> pd.Series:
    """Rename the UTCI very strong classes to the PET extreme classes they are compared with.

    Parameters
    ----------
    utci_classes : pandas.Series
        UTCI stress-category labels from ``classify`` with ``UTCI_SCALE``.

    Returns
    -------
    pandas.Series
        The same labels with ``UTCI_TO_PET_CLASS`` applied, for comparison with PET classes.
    """
    return utci_classes.replace(UTCI_TO_PET_CLASS)


# [Classification]
def classify(values: Any, scale: ThermalScale) -> np.ndarray | pd.Series:
    """Classify numeric thermal-index values into stress-class labels.

    Parameters
    ----------
    values : array-like or pandas.Series
        Numeric index values [degC], 1D or multidimensional. Non-finite
        entries (``NaN``, ``inf``, ``-inf``) are preserved as ``np.nan``.
    scale : ThermalScale
        Assessment scale (``PET_SCALE`` or ``UTCI_SCALE``) defining the
        band thresholds and labels.

    Returns
    -------
    numpy.ndarray or pandas.Series
        Object-dtype array (or Series preserving the input index when given a
        ``pandas.Series``) of stress-class names with ``np.nan`` for
        non-finite inputs.
    """
    if not isinstance(scale, ThermalScale) or not scale.bands:
        raise ValueError("scale must be a non-empty ThermalScale instance")

    is_series = isinstance(values, pd.Series)
    arr = np.asarray(values, dtype=float)
    finite = np.isfinite(arr)

    # Object array preserves float np.nan alongside string class names without 'nan' coercion.
    out = np.full(arr.shape, np.nan, dtype=object)
    for band in scale.bands:
        mask = finite & band.matches(arr)
        out[mask] = band.label

    if is_series:
        return pd.Series(out, index=values.index, name=values.name, dtype=object)
    return out


# [Validity masking]
def mask_utci_inputs(
    ta: Any,
    tmrt: Any,
    ws10: Any,
    vp: Any,
) -> np.ndarray:
    """Screen meteorological inputs against operational UTCI validity bounds.

    Parameters
    ----------
    ta : array-like
        Air temperature [degC]; valid in ``[-50, 50]``.
    tmrt : array-like
        Mean radiant temperature [degC]; ``tmrt - ta`` valid in ``[-30, 70]`` K.
    ws10 : array-like
        Wind speed at 10 m above ground [m/s]; valid in ``[0.5, 17]``.
    vp : array-like
        Vapor pressure [hPa]; valid in ``[0, 50]``.

    Returns
    -------
    numpy.ndarray
        Boolean array matching input shape where ``True`` indicates all inputs
        are finite and inside operational UTCI bounds.
    """
    ta_arr = np.asarray(ta, dtype=float)
    tmrt_arr = np.asarray(tmrt, dtype=float)
    ws10_arr = np.asarray(ws10, dtype=float)
    vp_arr = np.asarray(vp, dtype=float)

    shapes = {ta_arr.shape, tmrt_arr.shape, ws10_arr.shape, vp_arr.shape}
    if len(shapes) != 1:
        raise ValueError(
            f"Input arrays must share identical shapes; got {ta_arr.shape}, "
            f"{tmrt_arr.shape}, {ws10_arr.shape}, {vp_arr.shape}"
        )

    finite = np.isfinite(ta_arr) & np.isfinite(tmrt_arr) & np.isfinite(ws10_arr) & np.isfinite(vp_arr)
    ta_low, ta_high = UTCI_VALIDITY_BOUNDS["ta"]
    ws_low, ws_high = UTCI_VALIDITY_BOUNDS["ws10"]
    dt_low, dt_high = UTCI_VALIDITY_BOUNDS["tmrt_minus_ta"]
    vp_low, vp_high = UTCI_VALIDITY_BOUNDS["vp"]

    delta_tmrt = np.where(finite, tmrt_arr - ta_arr, np.nan)
    return (
        finite
        & (ta_arr >= ta_low)
        & (ta_arr <= ta_high)
        & (ws10_arr >= ws_low)
        & (ws10_arr <= ws_high)
        & (delta_tmrt >= dt_low)
        & (delta_tmrt <= dt_high)
        & (vp_arr >= vp_low)
        & (vp_arr <= vp_high)
    )
