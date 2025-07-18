
# Real Estate Pricing ETL Pipeline

This repository contains a robust ETL pipeline for ingesting, transforming, validating, and loading housing price data into both local and Azure SQL Server environments. Observability and data quality monitoring are embedded throughout the process to ensure trust and traceability.

## Overview

### Pipeline Components

- Source File: `housing.csv` containing raw pricing and housing attribute data.
- Transformation Script: [`etl_pricing.py`](etl_pricing.py)
- Observability Module: [`observability.py`](observability.py)

## ETL Workflow

### 1. Extract
- Loads raw housing data from a CSV file
- Converts column names to lowercase with underscores
- Logs source load event to both local and cloud SQL instances

### 2. Validate
- Checks for nulls in required fields:  
  `['price', 'area', 'bedrooms', 'bathrooms', 'stories', 'parking']`
- Logs null presence or absence per table

### 3. Transform
- Converts yes/no columns to boolean
- Creates new features:
  - `price_per_sqft`
  - `has_aircon_and_heat`
- Logs transformed column names

### 4. Schema Validation
- Compares the DataFrame schema against a strict expected schema (column order and type)
- Logs success or failure to SQL event log

### 5. Load
- Truncates existing data in the `pricing` table (both environments)
- Inserts transformed rows using efficient batch inserts
- Logs insertion count and row delta

## Observability Features

All key events are logged to the `event_log` table, including:

- Source file load
- Null checks
- Transformation stages
- Schema validation
- Row insert counts
- Pre/post row tallies
- Error tracking (with stage context)

## Requirements

- Python 3.8+
- `pandas`, `numpy`, `pyodbc`
- Local + Azure SQL Server access
- `event_log` table in both SQL environments

## Running the Pipeline

Update the file path in `etl_pricing.py`:

```python
file_path = r"C:\Repos\WS_Dev\data\housing.csv"
```

Then run:

```bash
python etl_pricing.py
```

Make sure your `event_log` table exists in both databases beforehand.

## Use Cases

- Real estate pricing dashboards
- Model-ready data for ML experiments (e.g., price prediction, clustering)
- Audit trails for data engineering workflows
