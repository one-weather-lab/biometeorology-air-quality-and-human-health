"""
Script Name: __init__.py
Purpose: Public utility package exports for M216 biometeorology notebooks.
Author(s): Christos Giannaros, One Weather Lab, UoI <chris.giannaros@uoi.gr>
Last updated: 2026-11-17
Version: 0.3.0
License: MIT
"""

from __future__ import annotations

from .europe import compute_europe_utci, fetch_open_data_fields, format_europe_summary
from .indices import compute_pet, compute_utci
from .readers import read_four_seasonal_days
from .reports import (
    format_comparison,
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
    classify,
    mask_utci_inputs,
)
from .visualization import (
    plot_europe_utci_map,
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
    "classify",
    "compute_europe_utci",
    "compute_pet",
    "compute_utci",
    "fetch_open_data_fields",
    "format_comparison",
    "format_europe_summary",
    "format_pet_class_counts",
    "format_pet_daily_table",
    "format_radiative_load",
    "format_utci_class_counts",
    "format_utci_screening",
    "mask_utci_inputs",
    "plot_europe_utci_map",
    "plot_pet_diurnal",
    "plot_pet_utci_comparison",
    "plot_utci_diurnal",
    "read_four_seasonal_days",
]
