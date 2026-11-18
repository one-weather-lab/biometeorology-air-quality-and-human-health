"""
Script Name: visualization.py
Purpose: Plot diurnal PET and UTCI time series, index comparisons, and
         European UTCI maps.
Author(s): Christos Giannaros, One Weather Lab, UoI <chris.giannaros@uoi.gr>
Last updated: 2026-11-18
Version: 0.2.3
License: MIT
"""

from __future__ import annotations

# --- Imports ---
import logging
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

from .scales import ThermalScale, classify

# --- Configuration ---
FIG_DPI = 300
FIG_DPI_OVERVIEW = 200
INLINE_DISPLAY_DPI = 95
HOUR_TICKS = (0, 3, 6, 9, 12, 15, 18, 21)
SEASON_COLORS = ("#2b83ba", "#1b9e77", "#d95f02", "#7570b3")

# --- Logging ---
LOG = logging.getLogger("owl.m216.visualization")


# --- Functions ---
# [Internal helpers]
def _resolve_season_labels(
    dates: list[str],
    season_labels: dict[str, str] | None,
) -> dict[str, str]:
    """Map ISO date strings to readable seasonal subplot labels.

    Parameters
    ----------
    dates : list of str
        Sorted date strings formatted as ``YYYY-MM-DD``.
    season_labels : dict of str to str or None
        Optional mapping from ``YYYY-MM-DD`` strings to labels; a date without
        an entry is shown as its date string.

    Returns
    -------
    dict of str to str
        Mapping containing a display label for every date in ``dates``.
    """
    labels = season_labels or {}
    return {d: labels.get(d, d) for d in dates}


def _plot_index_diurnal(
    df: pd.DataFrame,
    index_col: str,
    index_label: str,
    scale: ThermalScale,
    output_path: str | Path,
    title: str,
    season_labels: dict[str, str] | None = None,
) -> Path:
    """Build and save a 2x2 seasonal diurnal figure over shaded thermal-stress bands.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly DataFrame containing ``time_utc``, ``ta``, ``tmrt``, and ``index_col``.
    index_col : str
        Column name of the thermal index to plot [degC].
    index_label : str
        Legend display name for the thermal index.
    scale : ThermalScale
        Thermal-stress scale defining shaded background bands and class ranges.
    output_path : str or pathlib.Path
        Destination PNG file path.
    title : str
        Figure super-title shown above the four seasonal panels.
    season_labels : dict of str to str or None, optional
        Optional mapping from ``YYYY-MM-DD`` strings to subplot titles.

    Returns
    -------
    pathlib.Path
        Path to the saved PNG figure.

    Raises
    ------
    ValueError
        If ``index_col`` is absent from ``df``.
    """
    if index_col not in df.columns:
        raise ValueError(f"DataFrame missing index column '{index_col}'")

    work = df.copy()
    work["date_str"] = work["time_utc"].dt.strftime("%Y-%m-%d")
    work["hour_utc"] = work["time_utc"].dt.hour
    dates = sorted(work["date_str"].unique().tolist())
    labels = _resolve_season_labels(dates=dates, season_labels=season_labels)

    # Shared y-range across panels
    all_vals = np.concatenate(
        [
            work["ta"].to_numpy(dtype=float),
            work["tmrt"].to_numpy(dtype=float),
            work[index_col].to_numpy(dtype=float),
        ]
    )
    finite_vals = all_vals[np.isfinite(all_vals)]
    y_min = float(np.floor(finite_vals.min() / 5.0) * 5.0 - 2.0)
    y_max = float(np.ceil(finite_vals.max() / 5.0) * 5.0 + 2.0)

    fig, axes = plt.subplots(2, 2, figsize=(13.0, 8.5), sharex=True, sharey=True)
    axes_flat = axes.ravel()

    # Draw stress bands and diurnal curves per seasonal day
    visible_bands = []
    for band in scale.bands:
        band_low = y_min if np.isneginf(band.lower) else max(band.lower, y_min)
        band_high = y_max if np.isposinf(band.upper) else min(band.upper, y_max)
        if band_high > band_low:
            visible_bands.append((band, band_low, band_high))

    for ax, date_str in zip(axes_flat, dates):
        sub = work[work["date_str"] == date_str].sort_values("hour_utc")
        for band, band_low, band_high in visible_bands:
            ax.axhspan(band_low, band_high, color=band.color, alpha=0.30, zorder=0)

        hours = sub["hour_utc"].to_numpy()
        ax.plot(hours, sub["ta"], color="#333333", linestyle="--", linewidth=1.4, label="$T_a$")
        ax.plot(hours, sub["tmrt"], color="#8c510a", linestyle="-.", linewidth=1.4, label="$T_{mrt}$")
        ax.plot(
            hours,
            sub[index_col],
            color="#111111",
            linestyle="-",
            linewidth=2.2,
            marker="o",
            markersize=3.2,
            label=index_label,
        )

        # Mark blank/masked hours explicitly without interpolating across the gap.
        blank_hours = sub.loc[sub[index_col].isna(), "hour_utc"].tolist()
        for blank_hr in blank_hours:
            ax.axvline(blank_hr, color="#777777", linestyle=":", linewidth=1.2, zorder=2)
            ax.text(
                blank_hr + 0.4,
                y_min + 0.06 * (y_max - y_min),
                f"{blank_hr:02d} UTC blank",
                fontsize=10.5,
                color="#444444",
            )

        ax.set_title(labels[date_str], fontsize=12.5, fontweight="bold")
        ax.set_xticks(HOUR_TICKS)
        ax.tick_params(axis="both", labelsize=11.5)
        ax.set_xlim(-0.5, 23.5)
        ax.set_ylim(y_min, y_max)
        ax.grid(True, linestyle=":", alpha=0.35, color="#666666")

    for ax in axes_flat[len(dates) :]:
        ax.set_visible(False)

    axes[1, 0].set_xlabel("Hour (UTC)", fontsize=12.5)
    axes[1, 1].set_xlabel("Hour (UTC)", fontsize=12.5)
    axes[0, 0].set_ylabel("Temperature (°C)", fontsize=12.5)
    axes[1, 0].set_ylabel("Temperature (°C)", fontsize=12.5)

    # Combined curve and thermal-stress band legend
    curve_handles = [
        Line2D([0], [0], color="#111111", linewidth=2.2, marker="o", markersize=4.5, label=index_label),
        Line2D([0], [0], color="#333333", linestyle="--", linewidth=1.4, label="Air temperature ($T_a$)"),
        Line2D([0], [0], color="#8c510a", linestyle="-.", linewidth=1.4, label="Mean radiant temp. ($T_{mrt}$)"),
    ]
    band_handles = [
        Patch(
            facecolor=band.color,
            alpha=0.45,
            edgecolor="#666666",
            linewidth=0.5,
            label=f"{band.label} ({band.format_range()})",
        )
        for band, _, _ in visible_bands
    ]
    fig.suptitle(title, fontsize=14.5, fontweight="bold", y=0.99)
    fig.legend(
        handles=curve_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.955),
        ncol=3,
        frameon=False,
        fontsize=11.5,
    )
    fig.legend(
        handles=band_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.015),
        ncol=3,
        frameon=False,
        fontsize=10.5,
        title=f"{scale.name} stress classes",
        title_fontsize=11.0,
    )
    fig.tight_layout(rect=(0.0, 0.02, 1.0, 0.92), h_pad=1.2, w_pad=1.0)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=FIG_DPI_OVERVIEW, bbox_inches="tight")
    plt.show()
    plt.close(fig)
    return out


# [Diurnal plot builders]
def plot_pet_diurnal(
    df: pd.DataFrame,
    scale: ThermalScale,
    output_path: str | Path,
    *,
    season_labels: dict[str, str] | None = None,
) -> Path:
    """Render and save the 2x2 seasonal diurnal PET figure over shaded stress bands.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly DataFrame containing ``time_utc``, ``ta``, ``tmrt``, and ``pet``.
    scale : ThermalScale
        PET stress scale defining background bands and legend labels.
    output_path : str or pathlib.Path
        Destination PNG file path.
    season_labels : dict of str to str or None, optional
        Mapping from ``YYYY-MM-DD`` date strings to subplot titles.

    Returns
    -------
    pathlib.Path
        Path to the saved PNG figure.
    """
    return _plot_index_diurnal(
        df=df,
        index_col="pet",
        index_label="PET",
        scale=scale,
        output_path=output_path,
        title="Hourly PET, Air Temperature, and Mean Radiant Temperature (Ioannina, 2012)",
        season_labels=season_labels,
    )


def plot_utci_diurnal(
    df: pd.DataFrame,
    scale: ThermalScale,
    output_path: str | Path,
    *,
    season_labels: dict[str, str] | None = None,
) -> Path:
    """Render and save the 2x2 seasonal diurnal UTCI figure leaving blank hours unplotted.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly DataFrame containing ``time_utc``, ``ta``, ``tmrt``, and ``utci``.
    scale : ThermalScale
        UTCI stress scale defining background bands and legend labels.
    output_path : str or pathlib.Path
        Destination PNG file path.
    season_labels : dict of str to str or None, optional
        Mapping from ``YYYY-MM-DD`` date strings to subplot titles.

    Returns
    -------
    pathlib.Path
        Path to the saved PNG figure.
    """
    return _plot_index_diurnal(
        df=df,
        index_col="utci",
        index_label="UTCI",
        scale=scale,
        output_path=output_path,
        title="Hourly UTCI, Air Temperature, and Mean Radiant Temperature (Ioannina, 2012)",
        season_labels=season_labels,
    )


# [Comparison builders]
def plot_pet_utci_comparison(
    df: pd.DataFrame,
    output_path: str | Path,
    *,
    season_labels: dict[str, str] | None = None,
) -> Path:
    """Render and save the two-panel PET vs UTCI scatter and diurnal difference figure.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly DataFrame containing ``time_utc``, ``pet``, and ``utci``.
    output_path : str or pathlib.Path
        Destination PNG file path.
    season_labels : dict of str to str or None, optional
        Mapping from ``YYYY-MM-DD`` date strings to legend labels.

    Returns
    -------
    pathlib.Path
        Path to the saved PNG figure.
    """
    for required_col in ("time_utc", "pet", "utci"):
        if required_col not in df.columns:
            raise ValueError(f"DataFrame missing required column '{required_col}'")

    work = df.copy()
    work["date_str"] = work["time_utc"].dt.strftime("%Y-%m-%d")
    work["hour_utc"] = work["time_utc"].dt.hour
    work["pet_minus_utci"] = work["pet"] - work["utci"]
    dates = sorted(work["date_str"].unique().tolist())
    labels = _resolve_season_labels(dates=dates, season_labels=season_labels)

    valid = work.dropna(subset=["pet", "utci"])
    low_lim = float(np.floor(min(valid["pet"].min(), valid["utci"].min()) / 5.0) * 5.0 - 2.0)
    high_lim = float(np.ceil(max(valid["pet"].max(), valid["utci"].max()) / 5.0) * 5.0 + 2.0)

    fig, (ax_scatter, ax_diff) = plt.subplots(1, 2, figsize=(13.0, 5.4))

    # Left panel: paired PET against UTCI and 1:1 reference line
    for idx, date_str in enumerate(dates):
        color = SEASON_COLORS[idx % len(SEASON_COLORS)]
        sub_valid = valid[valid["date_str"] == date_str]
        ax_scatter.scatter(
            sub_valid["utci"],
            sub_valid["pet"],
            color=color,
            s=36,
            alpha=0.85,
            edgecolors="#222222",
            linewidths=0.4,
            label=labels[date_str],
        )

        sub_all = work[work["date_str"] == date_str].sort_values("hour_utc")
        ax_diff.plot(
            sub_all["hour_utc"],
            sub_all["pet_minus_utci"],
            color=color,
            marker="o",
            markersize=3.5,
            linewidth=1.8,
            label=labels[date_str],
        )

    ax_scatter.plot([low_lim, high_lim], [low_lim, high_lim], color="#333333", linestyle="--", linewidth=1.2, label="1:1 line")
    ax_scatter.set_xlim(low_lim, high_lim)
    ax_scatter.set_ylim(low_lim, high_lim)
    ax_scatter.set_aspect("equal", adjustable="box")
    ax_scatter.set_xlabel("UTCI (°C)")
    ax_scatter.set_ylabel("PET (°C)")
    ax_scatter.set_title("PET vs UTCI (valid hours)")
    ax_scatter.grid(True, linestyle=":", alpha=0.35, color="#666666")
    ax_scatter.legend(frameon=False, fontsize=8.5, loc="upper left")

    # Right panel: diurnal PET - UTCI difference curves
    ax_diff.axhline(0.0, color="#333333", linestyle="--", linewidth=1.1)
    ax_diff.set_xticks(HOUR_TICKS)
    ax_diff.set_xlim(-0.5, 23.5)
    ax_diff.set_xlabel("Hour (UTC)")
    ax_diff.set_ylabel("PET − UTCI (K)")
    ax_diff.set_title("Diurnal Difference (PET − UTCI)")
    ax_diff.grid(True, linestyle=":", alpha=0.35, color="#666666")
    ax_diff.legend(frameon=False, fontsize=8.5, loc="upper right")

    fig.suptitle("Comparison of PET and UTCI (Ioannina, Four Seasonal Days, 2012)", fontsize=13.0, fontweight="bold")
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=FIG_DPI_OVERVIEW, bbox_inches="tight")
    plt.show()
    plt.close(fig)
    return out


# [Gridded Europe map builders]
def plot_europe_utci_map(
    utci_c: np.ndarray,
    lat2d: np.ndarray,
    lon2d: np.ndarray,
    scale: ThermalScale,
    output_path: str | Path,
    *,
    valid_label: str | None = None,
) -> Path | None:
    """Plot a classified European UTCI map leaving masked cells blank.

    Parameters
    ----------
    utci_c : numpy.ndarray
        2D gridded UTCI values [degC] with ``NaN`` at masked or out-of-domain
        grid cells.
    lat2d : numpy.ndarray
        2D latitude meshgrid matching ``utci_c`` shape [deg].
    lon2d : numpy.ndarray
        2D longitude meshgrid matching ``utci_c`` shape [deg].
    scale : ThermalScale
        Assessment scale (typically ``UTCI_SCALE``) defining categories and
        fill colors.
    output_path : str or pathlib.Path
        Destination PNG file path.
    valid_label : str or None, optional
        Optional valid timestamp text shown in parentheses in the map title.

    Returns
    -------
    pathlib.Path or None
        Path to the saved PNG figure, or ``None`` when no finite grid cell is
        present.
    """
    utci_arr = np.asarray(utci_c, dtype=float)
    lat_arr = np.asarray(lat2d, dtype=float)
    lon_arr = np.asarray(lon2d, dtype=float)

    if utci_arr.ndim != 2:
        raise ValueError(f"utci_c must be a 2D array; got shape {utci_arr.shape}")
    if lat_arr.shape != utci_arr.shape or lon_arr.shape != utci_arr.shape:
        raise ValueError(
            f"lat2d and lon2d must match utci_c shape {utci_arr.shape}; "
            f"got {lat_arr.shape} and {lon_arr.shape}"
        )
    if not isinstance(scale, ThermalScale) or not scale.bands:
        raise ValueError("scale must be a non-empty ThermalScale instance")

    classified = classify(values=utci_arr, scale=scale)
    if not np.isfinite(utci_arr).any():
        LOG.info("Europe UTCI map skipped (no valid grid cells).")
        return None

    # Deferred import keeps time-series sections runnable without earthkit installed.
    import io

    import earthkit.plots as ekp
    from matplotlib.colors import ListedColormap

    try:
        from IPython.display import Image, display
    except ImportError:
        Image = None
        display = None

    chart = ekp.Map(domain="Europe")
    for band in scale.bands:
        in_class = (classified == band.label).astype(float)
        if in_class.any():
            # Contour at 0.5 on the binary mask to shade each category without interpolating across levels.
            chart.contourf(
                in_class,
                x=lon_arr,
                y=lat_arr,
                style=ekp.styles.Style(
                    colors=ListedColormap([band.color]),
                    levels=[0.5, 1.5],
                    legend_style=None,
                ),
            )

    chart.coastlines()
    chart.borders()
    chart.gridlines()
    title = scale.name
    if valid_label:
        title = f"{title} ({valid_label})"
    chart.title(title)

    handles = [
        Patch(
            facecolor=band.color,
            edgecolor="#555555",
            linewidth=0.5,
            label=f"{band.label} ({band.format_range()})",
        )
        for band in scale.bands
    ]
    chart.fig.canvas.draw()
    map_bbox = chart.fig.axes[0].get_tightbbox(chart.fig.canvas.get_renderer())
    legend_y = map_bbox.transformed(chart.fig.transFigure.inverted()).y0 - 0.01
    chart.fig.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, legend_y),
        ncol=2,
        frameon=False,
        fontsize=9.5,
        title=f"{scale.name} stress categories (masked cells left blank)",
        title_fontsize=10.0,
    )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    chart.fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight")

    if display is not None and Image is not None:
        # Display via IPython Image and close the figure so earthkit-plots renders once without figure leaks.
        buffer = io.BytesIO()
        chart.fig.savefig(buffer, format="png", dpi=INLINE_DISPLAY_DPI, bbox_inches="tight")
        plt.close(chart.fig)
        display(Image(data=buffer.getvalue()))
    else:
        plt.close(chart.fig)
    return out