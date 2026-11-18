# (C) Copyright 1996- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
# Modified copy. One Weather Lab adapted this code from examples/thermofeel-earthkit-demo.ipynb in
# ecmwf/thermofeel, release 2.3.0 (Apache-2.0, (C) ECMWF), through the notebook
# 01_direct_thermal_indices.ipynb. The changes include (i) gridded UTCI from ECMWF open-data radiation
# fluxes, taken as 3 h means before the valid time, with the direct radiation estimated with the
# `--approximate-fdir` fallback of thermofeel; (ii) UTCI left blank outside the operational validity bounds; (iii)
# summary statistics for a selectable region; and (iv) the code organised as functions.
"""
Script Name: europe.py
Purpose: Gridded UTCI over Europe from ECMWF open-data forecasts for the thermophysiological indices notebook.
Author(s): Christos Giannaros, One Weather Lab, UoI <chris.giannaros@uoi.gr>
Last updated: 2026-11-17
Version: 0.1.0
License: Apache-2.0
"""

from __future__ import annotations

# --- Imports ---
from datetime import datetime, timedelta
from typing import Any

import numpy as np

from .readers import _format_utc_timestamp
from .scales import mask_utci_inputs

# --- Configuration ---
SURFACE_PARAMS = ["2t", "2d", "10u", "10v"]
RADIATION_PARAMS = ["ssrd", "ssr", "strd", "str"]
SECONDS_PER_HOUR = 3600.0


# --- Functions ---
# [Internal helpers]
def _mean_flux(accumulated_end: np.ndarray, accumulated_start: np.ndarray, window_seconds: float, clamp: bool) -> np.ndarray:
    """Convert two accumulated radiation fields into the mean flux over the window between them.

    Parameters
    ----------
    accumulated_end : numpy.ndarray
        Accumulated field at the end of the window [J/m2].
    accumulated_start : numpy.ndarray
        Accumulated field at the start of the window [J/m2].
    window_seconds : float
        Window length [s].
    clamp : bool
        If True, negative fluxes are set to zero.

    Returns
    -------
    numpy.ndarray
        Mean flux over the window [W/m2].
    """
    # Differencing two accumulations gives the mean flux over the window between them.
    flux = (accumulated_end - accumulated_start) / window_seconds
    return np.maximum(flux, 0.0) if clamp else flux


def _box_mask(lat2d: np.ndarray, lon2d: np.ndarray, bounds: tuple[float, float, float, float]) -> np.ndarray:
    """Flag the grid cells that lie inside a latitude-longitude box.

    Parameters
    ----------
    lat2d : numpy.ndarray
        Latitude of each grid cell [deg N].
    lon2d : numpy.ndarray
        Longitude of each grid cell [deg E].
    bounds : tuple of float
        ``(south, north, west, east)`` limits of the box [deg], edges included.

    Returns
    -------
    numpy.ndarray
        Boolean array with the shape of ``lat2d``, True inside the box.
    """
    south, north, west, east = bounds
    return (lat2d >= south) & (lat2d <= north) & (lon2d >= west) & (lon2d <= east)


# [Open-data retrieval]
def fetch_open_data_fields(
    run_date: str | None,
    run_time: int,
    forecast_step_h: int,
    radiation_window_h: int,
) -> dict[str, Any]:
    """Retrieve ECMWF open-data surface fields and mean radiation fluxes for one forecast step.

    Parameters
    ----------
    run_date : str or None
        Run date as ``"YYYYMMDD"``, read from the Azure mirror; ``None`` reads the latest run
        from the ECMWF server.
    run_time : int
        Forecast cycle hour [UTC], used only when ``run_date`` is set.
    forecast_step_h : int
        Forecast step [h] of the valid time.
    radiation_window_h : int
        Length [h] of the window before the valid time over which radiation is averaged.

    Returns
    -------
    dict
        ``data_source`` (``"ecmwf"`` or ``"azure"``), ``base_time`` and ``valid_time``
        [datetime, UTC], ``forecast_step_h`` and ``radiation_window_h`` [h], ``t2m_k`` and
        ``d2m_k`` [K], ``u10`` and ``v10`` [m/s], ``lat2d`` and ``lon2d`` [deg], and the
        window-mean fluxes ``ssrd_mean``, ``ssr_mean``, ``strd_mean`` and ``str_mean`` [W/m2],
        the last signed.
    """
    if forecast_step_h <= radiation_window_h:
        raise ValueError(
            f"FORECAST_STEP_H ({forecast_step_h}) must exceed RADIATION_WINDOW_H ({radiation_window_h})."
        )
    # Imported here so the station sections run without the gridded forecast packages installed.
    import earthkit.data as ekd

    surface_request = dict(type="fc", stream="oper", levtype="sfc", step=forecast_step_h, param=SURFACE_PARAMS)
    if run_date is None:
        data_source = "ecmwf"
    else:
        data_source = "azure"
        surface_request.update(date=run_date, time=run_time)
    surface = {
        f.metadata("shortName"): f
        for f in ekd.from_source("ecmwf-open-data", source=data_source, request=surface_request).to_fieldlist()
    }
    lat2d, lon2d = surface["2t"].geography.latlons()
    base_time = datetime.fromisoformat(str(surface["2t"].metadata("base_datetime")))
    valid_time = datetime.fromisoformat(str(surface["2t"].metadata("valid_datetime")))

    step_prev = forecast_step_h - radiation_window_h
    radiation_request = dict(
        type="fc",
        stream="oper",
        levtype="sfc",
        param=RADIATION_PARAMS,
        date=base_time.strftime("%Y%m%d"),
        time=base_time.hour,
        step=[step_prev, forecast_step_h],
    )
    radiation = {
        (f.metadata("shortName"), int(f.metadata("step"))): f.to_numpy()
        for f in ekd.from_source("ecmwf-open-data", source=data_source, request=radiation_request).to_fieldlist()
    }
    window_seconds = radiation_window_h * SECONDS_PER_HOUR
    fields = {
        "data_source": data_source,
        "base_time": base_time,
        "valid_time": valid_time,
        "forecast_step_h": forecast_step_h,
        "radiation_window_h": radiation_window_h,
        "t2m_k": surface["2t"].to_numpy(),
        "d2m_k": surface["2d"].to_numpy(),
        "u10": surface["10u"].to_numpy(),
        "v10": surface["10v"].to_numpy(),
        "lat2d": lat2d,
        "lon2d": lon2d,
    }
    for name in RADIATION_PARAMS:
        # Net thermal radiation (str) is signed and typically negative when upward exceeds downward.
        fields[f"{name}_mean"] = _mean_flux(
            radiation[name, forecast_step_h], radiation[name, step_prev], window_seconds, clamp=name != "str"
        )
    return fields


# [Gridded UTCI]
def compute_europe_utci(forecast: dict[str, Any], europe_box: tuple[float, float, float, float]) -> dict[str, Any]:
    """Compute mean radiant temperature and UTCI on the grid cells inside a box.

    Parameters
    ----------
    forecast : dict
        Output of ``fetch_open_data_fields``.
    europe_box : tuple of float
        ``(south, north, west, east)`` bounds [deg] of the computation box.

    Returns
    -------
    dict
        ``europe_box`` (the bounds), ``box_mask`` and ``valid_box`` (cells inside the box, and
        valid cells among them), ``utci_c`` [degC, full grid, ``NaN`` outside the box or the
        validity bounds] and ``valid_grid`` (full-grid validity).
    """
    import thermofeel as tf
    from earthkit.meteo import solar, wind
    from thermofeel.approximations import approximate_fdir_erbs

    lat2d, lon2d, t2m_k = forecast["lat2d"], forecast["lon2d"], forecast["t2m_k"]
    box = _box_mask(lat2d, lon2d, europe_box)
    valid_time = forecast["valid_time"]
    window_start = valid_time - timedelta(hours=forecast["radiation_window_h"])
    cossza = solar.cos_solar_zenith_angle_integrated(window_start, valid_time, lat2d[box], lon2d[box])

    ssrd = forecast["ssrd_mean"][box]
    fdir_flux = approximate_fdir_erbs(ssrd, cossza, doy=valid_time.timetuple().tm_yday)  # [W/m2]
    dsrp_flux = tf.approximate_dsrp(fdir=fdir_flux, cossza=cossza)  # [W/m2]
    mrt_box_k = tf.calculate_mean_radiant_temperature(
        ssrd=ssrd,
        ssr=forecast["ssr_mean"][box],
        dsrp=dsrp_flux,
        strd=forecast["strd_mean"][box],
        fdir=fdir_flux,
        strr=forecast["str_mean"][box],
        cossza=cossza,
    )

    ta_box_c = tf.kelvin_to_celsius(t2m_k[box])
    tmrt_box_c = tf.kelvin_to_celsius(mrt_box_k)
    ws10_box = wind.speed(forecast["u10"][box], forecast["v10"][box])
    vp_box_hpa = tf.calculate_saturation_vapour_pressure(forecast["d2m_k"][box])

    valid_box = mask_utci_inputs(ta=ta_box_c, tmrt=tmrt_box_c, ws10=ws10_box, vp=vp_box_hpa)
    utci_box_c = np.full(ta_box_c.shape, np.nan, dtype=float)
    if valid_box.any():
        utci_box_k = tf.calculate_utci(
            t2_k=t2m_k[box][valid_box],
            va=ws10_box[valid_box],
            mrt=mrt_box_k[valid_box],
            ehPa=vp_box_hpa[valid_box],
        )
        utci_box_c[valid_box] = tf.kelvin_to_celsius(utci_box_k)

    utci_c = np.full(t2m_k.shape, np.nan, dtype=float)
    utci_c[box] = utci_box_c
    valid_grid = np.zeros(t2m_k.shape, dtype=bool)
    valid_grid[box] = valid_box
    return {"europe_box": europe_box, "box_mask": box, "valid_box": valid_box, "utci_c": utci_c, "valid_grid": valid_grid}


# [Summary]
def format_europe_summary(
    forecast: dict[str, Any],
    europe_utci: dict[str, Any],
    region: str,
    regions: dict[str, tuple[float, float, float, float]],
) -> str:
    """Summarise the forecast run, the box validity and UTCI statistics for one region.

    Parameters
    ----------
    forecast : dict
        Output of ``fetch_open_data_fields``.
    europe_utci : dict
        Output of ``compute_europe_utci``.
    region : str
        Key of ``regions`` to summarise.
    regions : dict of str to tuple of float
        ``(south, north, west, east)`` bounds [deg] for each named region.

    Returns
    -------
    str
        Run line, direct-radiation note, box validity line and the region's minimum, mean
        and maximum UTCI [degC] with its valid and masked cell counts.
    """
    if region not in regions:
        raise KeyError(f"Unknown STATS_REGION '{region}'; expected one of {list(regions)}")
    south_box, north_box, west_box, east_box = europe_utci["europe_box"]
    valid_box, box = europe_utci["valid_box"], europe_utci["box_mask"]
    south_reg, north_reg, west_reg, east_reg = regions[region]
    region_mask = _box_mask(forecast["lat2d"], forecast["lon2d"], regions[region])
    region_utci = europe_utci["utci_c"][region_mask]
    region_total = int(region_mask.sum())
    region_valid = int(europe_utci["valid_grid"][region_mask].sum())
    step, window = forecast["forecast_step_h"], forecast["radiation_window_h"]
    lines = [
        f"ECMWF open-data run ({forecast['data_source']}): base {_format_utc_timestamp(forecast['base_time'])}, "
        f"valid {_format_utc_timestamp(forecast['valid_time'])} (+{step} h)",
        "Note: Direct solar radiation (fdir) is missing from ECMWF open data, so it is estimated "
        f"with the thermofeel `--approximate-fdir` fallback from {window} h mean fluxes (forecast hours {step - window}-{step} of the run).",
        f"Europe box ({south_box} to {north_box} N, {west_box} to {east_box} E): "
        f"{int(valid_box.sum())} / {int(box.sum())} valid cells ({int((~valid_box).sum())} masked)",
    ]
    if np.isfinite(region_utci).any():
        lines.append(
            f"{region} ({south_reg} to {north_reg} N, {west_reg} to {east_reg} E): "
            f"min = {np.nanmin(region_utci):.2f} C, mean = {np.nanmean(region_utci):.2f} C, "
            f"max = {np.nanmax(region_utci):.2f} C | "
            f"valid = {region_valid} / {region_total}, masked = {region_total - region_valid}"
        )
    else:
        lines.append(f"{region}: n/a (all {region_total} grid cells masked outside UTCI validity bounds)")
    return "\n".join(lines)
