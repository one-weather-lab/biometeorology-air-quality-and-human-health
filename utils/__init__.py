"""
Script Name: __init__.py
Purpose: Public exports of the utils package for the notebooks in this repository.
Author(s): Christos Giannaros, One Weather Lab, UoI <chris.giannaros@uoi.gr>
Last updated: 2026-11-18
Version: 0.4.0
License: MIT
"""

from __future__ import annotations

from .europe import compute_europe_utci, fetch_open_data_fields, format_europe_summary
from .indices import compute_pet, compute_utci
from .readers import read_four_seasonal_days, read_hourly_mpet
from .reports import (
    format_activity_spread,
    format_comparison,
    format_mpet_daily_table,
    format_pet_class_counts,
    format_pet_daily_table,
    format_radiative_load,
    format_utci_class_counts,
    format_utci_screening,
)
from .scales import (
    PET_SCALE,
    UTCI_SCALE,
    UTCI_TO_PET_CLASS,
    UTCI_VALIDITY_BOUNDS,
    ScaleBand,
    ThermalScale,
    class_frequencies,
    classify,
    group_class_frequencies,
    mask_utci_inputs,
)
from .visualization import (
    plot_europe_utci_map,
    plot_mpet_bioclimate,
    plot_mpet_groups_diurnal,
    plot_mpet_worker_activity,
    plot_pet_diurnal,
    plot_pet_utci_comparison,
    plot_utci_diurnal,
)

__all__ = [
    "PET_SCALE",
    "ScaleBand",
    "ThermalScale",
    "UTCI_SCALE",
    "UTCI_TO_PET_CLASS",
    "UTCI_VALIDITY_BOUNDS",
    "class_frequencies",
    "classify",
    "compute_europe_utci",
    "compute_pet",
    "compute_utci",
    "fetch_open_data_fields",
    "format_activity_spread",
    "format_comparison",
    "format_europe_summary",
    "format_mpet_daily_table",
    "format_pet_class_counts",
    "format_pet_daily_table",
    "format_radiative_load",
    "format_utci_class_counts",
    "format_utci_screening",
    "group_class_frequencies",
    "mask_utci_inputs",
    "plot_europe_utci_map",
    "plot_mpet_bioclimate",
    "plot_mpet_groups_diurnal",
    "plot_mpet_worker_activity",
    "plot_pet_diurnal",
    "plot_pet_utci_comparison",
    "plot_utci_diurnal",
    "read_four_seasonal_days",
    "read_hourly_mpet",
]
