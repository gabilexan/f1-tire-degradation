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
f1-tire-degradation/
├── data/               # Processed and indexed CSV files
├── f1_cache/           # Local storage for raw telemetry data (Git-ignored)
├── notebooks/          # Workspace for experimental exploratory data analysis (EDA)
├── scripts/
│   └── get_f1_data.py  # Data ingestion and preprocessing pipeline
├── app.py              # Main web interface application
├── .gitignore          # Rules to prevent uploading heavy data or virtual environments
└── requirements.txt    # Project dependencies configuration

---

## 👤 Author

Developed by **Nicole** [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/TU_PERFIL_LINKEDIN)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/gabilexan)

*Feel free to reach out for collaboration or questions regarding race intelligence data engineering!*