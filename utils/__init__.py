"""
Script Name: __init__.py
Purpose: Public utility package exports for M216 biometeorology notebooks.
Author(s): Christos Giannaros, One Weather Lab, UoI <chris.giannaros@uoi.gr>
Last updated: 2026-11-16
Version: 0.2.0
License: MIT
"""

from __future__ import annotations

from .readers import read_four_seasonal_days
from .scales import (
    PET_SCALE,
    UTCI_SCALE,
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
    "UTCI_VALIDITY_BOUNDS",
    "classify",
    "mask_utci_inputs",
    "plot_europe_utci_map",
    "plot_pet_diurnal",
    "plot_pet_utci_comparison",
    "plot_utci_diurnal",
    "read_four_seasonal_days",
]
