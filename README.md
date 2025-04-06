# tool-log-analysis
This project simulates manufacturing tool log data and illustrates an end-to-end analytics pipeline — including data cleaning, preprocessing, and dashboard visualization using Python-generated mock data. 
## 📌 Project Overview
In manufacturing, **Tool Logs** capture the real-time status of equipment—such as production, standby,engineering time, scheduled downtime, and unscheduled downtime. Analyzing this data is key to understanding equipment efficiency, maintenance planning, and operational bottlenecks.

This project includes:

- Python scripts to **generate realistic tool log mock data**
- Optional preprocessing scripts for **data cleaning and event merging**
- A **Tableau dashboard** to visualize trends and highlight anomalies

---

## 📁 Project Structure

```
tool-log-analysis/
├── README.md
├── .gitignore
├── data/
│   └── mock_tool_log.csv              # Generated mock data
├── scripts/
│   ├── fina_mock_tool_log_generator.py          # Data generation script
│   └── preprocess.py                  # Data cleaning logic
├── notebook/
│   └── exploratory_analysis.ipynb     # notebook-based EDA
└── tableau/
    └──             # Tableau Public link and screenshot
```

---

## 🧪 Mock Data Logic

The data generation script follows industry-like rules, including:

- Bi-weekly **Scheduled Preventive Maintenance**
- **Post-Maintenance Qual** always follows PM
- **Repair** must follow a productive period, and is followed by qual or delay
- **Supplier/User Maintenance Delays** and their sequence logic
- Special months with increased **Unscheduled Downtime and Delay**
- **No overlapping or missing time gaps** between events
- All 12 status types are included at least once

See: `scripts/fina_mock_tool_log_generator.py`

## 🧹 Repeatable Data Cleaning Scripts

The preprocessing pipeline includes the following key steps:

- **Merge consecutive events** with the same tool status to reduce redundancy
- **Split `tool_status` into three hierarchical levels** (e.g., category / subcategory / detail) for flexible grouping and visualization
- **Add and compute `duration_min`** for each event based on start and end timestamps

See: `scripts/preprocess.py`