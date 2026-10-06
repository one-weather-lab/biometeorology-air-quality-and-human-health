# Biometeorology, Air Quality and Human Health

## Notebooks

| # | Title | Core topics |
|---|-------|-------------|
| 01 | direct_thermal_indices | **Direct thermal indices** computed from the latest ECMWF open-data forecast and mapped over Europe, with recent METAR observations overlaid: apparent temperature (Steadman, 1984), heat index, humidex, discomfort index, simplified wet-bulb globe temperature (WBGT), net effective temperature and wind chill temperature |

Notebook 01 was adapted from `examples/thermofeel-earthkit-demo.ipynb` in [ecmwf/thermofeel](https://github.com/ecmwf/thermofeel), release 2.3.0 (Apache-2.0, Copyright 1996- ECMWF). The first cell of the notebook states the changes made to it.

## Running the Notebooks

Two execution paths are available.

### Option A: Binder (no installation)

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/one-weather-lab/biometeorology-air-quality-and-human-health/HEAD)

Open the notebook and run cells sequentially.
The environment builds automatically. No local setup is required. The notebook downloads the latest ECMWF open-data forecast and recent METAR reports, so it needs internet access.

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
