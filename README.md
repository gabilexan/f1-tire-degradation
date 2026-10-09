# 🏎️ F1 Race Intelligence - Tire Degradation Analytics Platform

This interactive Data Science web platform analyzes and projects **tire thermal and mechanical degradation** in Formula 1, utilizing real-telemetry data sourced from the official FIA servers. 

Mirroring the telemetry tools used by high-level racing teams, this project identifies non-linear behavior in race pace caused by compound wear, visually estimating optimal pitstop windows.

---

## 🚀 Architecture & Technical Capabilities

The project is built under a comprehensive, end-to-end engineering approach:

1. **Data Engineering & Ingestion (`scripts/get_f1_data.py`):**
   * Establishes a remote connection to the FIA API via the `fastf1` library.
   * Implements a structured local caching system (`f1_cache/`) to optimize data transfer times and API performance.
   * Features a `Pandas` data-cleaning pipeline to remove telemetry anomalies and outliers (laps under Safety Car, Virtual Safety Car, or pit lane entries).
2. **Statistical Modeling & Trend Analysis:**
   * Integrates Ordinary Least Squares (OLS) regression models using `statsmodels` to plot accurate grip-loss trendlines per lap.
3. **Interactive Visualization Layer (`app.py`):**
   * Features a dynamic telemetry dashboard developed with `Streamlit`.
   * Displays analytical, interactive charts rendered through `Plotly Express`.

---

## 📁 Project Structure

```text
├── data/               # Processed and indexed CSV datasets
├── f1_cache/           # FastF1 disk cache for raw telemetry (Git-ignored)
├── notebooks/          # Workspace for exploratory data analysis (EDA)
├── scripts/
│   ├── f1_data_engine.py # Dynamic FastF1 API ingestion, cleaning & strategy engine
│   └── get_f1_data.py    # Offline dataset extraction script
├── app.py              # Main interactive Streamlit analytics dashboard
├── .gitignore          # Rules to prevent uploading heavy cache files
└── requirements.txt    # Project dependencies configuration

---

## 💡 Key Features Implemented

- **Dynamic GP & Season Selection:** Ingests live or cached race telemetry from any Grand Prix (2022 - 2024 seasons).
- **Single Driver Wear Rate Breakdown:** Fits regression models per stint to calculate degradation slope (\(s / \text{lap}\)) and base pace.
- **Head-to-Head Pace Comparison:** Contrast race pace and tire degradation rates between any two drivers in real-time.
- **Pitstop Window Estimator:** Simulates cumulative wear overhead against pit stop loss penalties to highlight optimal pit windows.
- **🔮 Win Probability Predictor (Singapore GP 2026):** Monte Carlo stochastic engine (up to 10,000 simulations) factoring street circuit pace deltas, tire thermal degradation, qualifying track position weighting, and Safety Car probabilities.
- **F1 Official Compound Palette:** Dynamic visual styling matching Soft (Red), Medium (Yellow), Hard (White), Inter, and Wet compounds.

---

---

## 👤 Author

Developed by **Karen**

* **LinkedIn:** [karen-monsalve-699072136](https://www.linkedin.com/in/karen-monsalve-699072136)
* **GitHub:** [@gabilexan](https://github.com/gabilexan)

*Feel free to reach out for collaboration or questions regarding race intelligence data engineering!*