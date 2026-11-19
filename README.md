# Biometeorology, Air Quality and Human Health

The notebooks in this repository accompany the course "Biometeorology, Air Quality and Human Health" (M216) of the Postgraduate Studies Program ["Atmospheric Sciences and Environment"](https://atmos-physics-uoi.gr/en/home/) at the Department of Physics, University of Ioannina, Greece.

## Notebooks

| # | Title | Core topics |
|---|---|---|
| 01 | 01_direct_thermal_indices | **Direct thermal indices** computed from the latest or a past ECMWF open-data forecast and mapped over Europe. These include apparent temperature, heat index, humidex, discomfort index, simplified wet-bulb globe temperature, net effective temperature and wind chill temperature |
| 02 | 02_thermophysiological_indices | **Thermo-physiological indices** computed for four days spanning the four seasons of 2012 in Ioannina (PET and UTCI) and mapped over Europe as gridded UTCI from ECMWF open-data forecasts (Part 1), followed by mPET compared across six population groups for the same four days and summarised in monthly thermal bioclimate diagrams for 2012 (Part 2) |

Notebook 01 was adapted from `examples/thermofeel-earthkit-demo.ipynb` in [ecmwf/thermofeel](https://github.com/ecmwf/thermofeel), release 2.3.0 (Apache-2.0, Copyright 1996- ECMWF), while Notebook 02 adapts the European open-data retrieval and mapping workflow from the same Apache-2.0 release in its Section 4, through `utils/europe.py`. The first cell of Notebook 01 and the header of `utils/europe.py` state the changes made.

## Running the Notebooks

Two execution paths are available.

### Option A: Binder (no installation)

**Run the notebooks via Binder:**

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/one-weather-lab/biometeorology-air-quality-and-human-health/HEAD)

Open a notebook from `notebooks/` and run its cells sequentially.
The environment builds automatically, and no local setup is required.

### Option B: Local machine (Linux and macOS)

Clone the repository:

```bash
git clone https://github.com/one-weather-lab/biometeorology-air-quality-and-human-health.git
cd biometeorology-air-quality-and-human-health
```

Create and activate the conda environment:

```bash
conda env create -f environment.yml
conda activate biometeorology-air-quality-and-human-health
```

Launch Jupyter Lab:

```bash
jupyter lab notebooks/
```

If you prefer pip over conda, use `pip install -r requirements.txt`.

## Data Credits

- **Ioannina four-day subset** (`data/ioannina_2012_four_seasonal_days.csv`) contains 96 hourly records for four clear-sky days in 2012 at Ioannina, with air temperature, vapour pressure, and 1.1 m and 10 m wind speeds from the Copernicus Climate Change Service (C3S) CERRA reanalysis alongside mean radiant temperature computed through RayMan Pro.
- **Ioannina 2012 mPET subset** (`data/ioannina_2012_hourly_mpet.csv`) comprises 8,784 hourly records across 2012 at Ioannina from the HEAT-ALARM mPET dataset, with vapour pressure in place of relative humidity (Giannaros et al., 2024, *Scientific Data* 11:76, `https://doi.org/10.1038/s41597-024-02923-y`; Zenodo `https://doi.org/10.5281/zenodo.10893914`, CC BY 4.0).
- **European forecast fields** are retrieved at runtime from ECMWF open data under CC BY 4.0 (Copyright ECMWF).
