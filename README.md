# NYC Multimodal Transit Recovery Dashboard (2020 - 2025)

---

## Table of Contents
- [NYC Multimodal Transit Recovery Dashboard (2020 - 2025)](#nyc-multimodal-transit-recovery-dashboard-2020---2025)
  - [Table of Contents](#table-of-contents)
  - [Overview \& Visual Design](#overview--visual-design)
  - [Requirements](#requirements)
    - [Prerequisites](#prerequisites)
    - [Python Packages](#python-packages)
  - [How to Run](#how-to-run)
    - [Option 1: Using pip (Standard)](#option-1-using-pip-standard)
    - [Option 2: Using Conda](#option-2-using-conda)
  - [Interaction Guide](#interaction-guide)
  - [Dashboard](#dashboard)

---

## Overview & Visual Design

The dashboard implements **Multiple Coordinated Views (MCV)** using declarative brushing and linking:

1. **VIEW 1: Master Longitudinal Trajectory (Time-Series Line Chart)**
   - **Encodings**: X-axis = `Date` (Temporal), Y-axis = `Recovery_Rate` (% of pre-pandemic baseline), Color = `Transit_Mode`.
   - **Features**: Includes a red dashed reference line at 100% (pre-pandemic level) and an interactive 1D horizontal interval brush (`time_brush`).

2. **VIEW 2: Avg Recovery in Selected Period (Ranked Horizontal Bar Chart)**
   - **Encodings**: X-axis = `Mean Recovery (%)`, Y-axis = `Transit_Mode` (sorted descending), Color = `Transit_Mode`.
   - **Features**: Dynamically linked to View 1; updates in real time to display the mean recovery rate of each transit mode during the selected timeframe.

3. **VIEW 3: Day-of-Week Recovery Matrix (Heatmap)**
   - **Encodings**: X-axis = `Day of Week` (ordered Mon–Sun), Y-axis = `Transit_Mode`, Color/Luminance = `Viridis` scale representing average recovery rate.
   - **Features**: Reveals hybrid-work commuting patterns such as **TWaT** (Tuesday, Wednesday, Thursday peak recovery) versus weekends. Also cross-filtered by the selection in View 1.

---

## Requirements

### Prerequisites
- **Python**: Version `3.9` or higher (tested with Python 3.10 / 3.11 / 3.12).
- Recommended: A virtual environment (such as `conda` or Python `venv`).

### Python Packages
The project relies on the following key dependencies:
- [`streamlit`](https://streamlit.io/) (`>= 1.30.0`): Web application framework and dashboard hosting.
- [`altair`](https://altair-viz.github.io/) (`>= 5.0.0`): Declarative statistical visualization library (powered by Vega-Lite).
- [`pandas`](https://pandas.pydata.org/) (`>= 2.0.0`): Data loading, transformation, and manipulation.

---

## How to Run

### Option 1: Using pip (Standard)

1. **Clone or navigate to the project directory**:
   ```bash
   cd d:/workspace/CS6313InfoVisualization/project
   ```

2. **(Optional) Create and activate a virtual environment**:
   ```bash
   # On macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   
   # On Windows (Command Prompt)
   python -m venv .venv
   .venv\Scripts\activate
   
   # On Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **(Optional) Re-generate the processed tidy dataset**:
   > Note: The cleaned dataset `mta_tidy_data.csv` is already included. You only need to run this step if you have modified the raw dataset or preprocessing logic.
   ```bash
   python prepate_mta_data.py
   ```

5. **Launch the Streamlit dashboard**:
   ```bash
   streamlit run app.py
   ```

6. **View in browser**:
   Once started, Streamlit will open your default browser automatically. If not, visit:
   
   ```
   http://localhost:8501
   ```

---

### Option 2: Using Conda

1. **Create and activate an environment**:
   ```bash
   conda create -n infovis python=3.10 -y
   conda activate infovis
   ```

2. **Install requirements**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the dashboard**:
   ```bash
   streamlit run app.py
   ```

---

## Interaction Guide

- **Drag to Select**: Click and drag horizontally across **View 1** (Time-Series Line Chart) to highlight a specific date range (e.g., Spring 2020 lockdowns, 2021 return-to-office, 2023–2024 stabilization).
- **Linked Cross-Filtering**: As you adjust the brush on View 1, **View 2** (bar chart) and **View 3** (heatmap) will automatically recalculate and re-render their aggregated metrics in real time.
- **Move Selection**: Click inside the highlighted brush box on View 1 and drag to slide the temporal window across different periods.
- **Reset Selection**: Click once anywhere on the background of View 1 outside the active brush box to clear the selection and restore full-range data across all views.
- **Tooltips**: Hover over data marks (lines, bars, or heatmap cells) across all views to inspect exact numeric values and metadata.

---

## Dashboard

![Dashboard](.\assets\Dashboard.png)
