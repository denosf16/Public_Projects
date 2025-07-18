# NBA Shot Analytics

**NBA Shot Analytics** is an end-to-end machine learning project designed to predict the outcome of NBA shot attempts (make or miss) using contextual and spatial features. The project integrates SQL-based ETL, model training, residual diagnostics, and visual evaluation of spatial shot probability to support analysis, observability, and decision-making in a basketball context.

---

## Project Overview

This project builds a full ML pipeline from raw shot log ingestion to trained model evaluation. It applies logistic regression, random forest, and XGBoost models to predict shot outcomes using contextual features such as defender distance, touch time, shot clock, and player height differential. The system includes:

- Robust data cleaning and filtering logic
- Feature selection and interaction engineering
- Model training with cross-validated hyperparameter tuning
- Performance evaluation via grouped metrics, calibration, residuals, and court overlays
- Streamlit dashboard for model diagnostics and SQL pipeline observability

---

## Project Structure

```
NBA_Shot/
├── models/                 # Training and evaluation scripts
│   ├── trained/            # Saved models (.pkl)
│   ├── output/             # Feature importances, plots, metrics
├── scripts/                # ETL loaders and SQL observability tools
│   └── checks/             # Schema, null, and outlier validation
├── app/                    # Streamlit app modules (modular pages)
├── config/                 # ERD and expected schema
├── output/                 # Generated results and visuals
├── requirements.txt        # Dependencies
└── README.md               # This file
```

---

## SQL ETL and Observability

The project includes a complete ingestion and validation pipeline for shot logs and metadata stored in SQL Server.

**Scripts:**
- `create_db.py`, `create_tables.py`: Database setup
- `load_shots.py`, `load_players.py`, `load_stats.py`, `load_teams.py`: Load cleaned CSVs to SQL tables
- `verify_sql.py`: Orchestrates schema, null, and outlier checks

**Checks implemented:**
- Schema drift vs. expected JSON schema
- Null % by column
- Outlier detection
- Row counts and data freshness
- ERD visualization via `visualize_schema.py`

---

## Feature Engineering

Features were constructed through a combination of domain knowledge and diagnostic tooling.

**Base Features**
- SHOT_DIST
- CLOSE_DEF_DIST
- TOUCH_TIME
- SHOT_CLOCK
- HEIGHT_DIFFERENTIAL

**Engineered Interactions**
- CLOCK_TOUCH = SHOT_CLOCK × TOUCH_TIME
- HEIGHT_CLOSE = HEIGHT_DIFFERENTIAL × CLOSE_DEF_DIST
- DIST_x_DEF = SHOT_DIST × CLOSE_DEF_DIST

**Binary Buckets**
- HAS_HEIGHT_ADVANTAGE
- LOW_CLOCK
- LONG_TOUCH
- HIGH_DRIBBLE

Feature evaluation includes:
- Mutual information scores
- Random forest importances
- Variance inflation factors (VIF)
- Verdict tables for inclusion/exclusion decisions

---

## Models Trained

Seven models were trained and versioned:

```
models/trained/
├── logreg_model.pkl
├── logreg_model_v2.pkl
├── rf_model.pkl
├── rf_model_v2.pkl
├── rf_model_v3.pkl
├── xgb_model.pkl
├── xgb_model_v2.pkl
```

**Training Scripts**
- `train_log.py`: Logistic regression with `GridSearchCV`
- `train_rf.py`: Random forest with tuned depth and feature sets
- `train_xgbv2.py`: XGBoost with interaction terms, bin encoding, and class weighting

Each model is trained on engineered features and evaluated on test data. Class imbalance (especially by distance) is addressed via bin weighting and dummy encoding.

---

## Evaluation and Diagnostics

Evaluation metrics are computed using `model_eval.py` and visualized via `diagnostics.py` and Streamlit.

**Metrics Captured**
- Log Loss
- Accuracy
- ROC AUC

**CSV Outputs**
- `output/model_results.csv`: Summary of model metrics
- `output/model_test_predictions.csv`: Probabilities and predictions
- `output/grouped_eval.csv`: Grouped evaluation by context
- `output/xgb_v2_feature_importance.csv`: Ranked feature importances
- `output/rf_v3_feature_importance.csv`: Random forest scores

**Diagnostic Plots**
- Calibration curves
- Confusion matrices
- Residual histograms
- QQ plots
- Residuals vs. shot distance
- Actual vs. predicted scatterplots

---

## Streamlit Dashboard

The app consists of multiple interactive modules:

| Page | Description |
|------|-------------|
| Home | Overview and navigation |
| SQL Observability | Schema, nulls, outliers, ERD viewer |
| Data Preprocessing | Filters and dataset summary |
| Feature Engineering | Verdict tables, visual diagnostics, feature ranking |
| Model Training | Model equations, hyperparameter grids, log loss comparison |
| Model Evaluation | Global metrics, grouped accuracy, per-model diagnostics |
| Model Reflection | Diagnostic summary, calibration trends, spatial analysis, model recommendations |

---

## Key Findings

- XGBoost (v2) outperforms all models on log loss, calibration, and spatial generalization.
- Random Forest (v3) is robust but less expressive.
- Logistic Regression underfits at the rim and struggles with interaction effects.
- Calibration and residual diagnostics suggest XGBoost is best suited for deployment.

---

## Output Artifacts

All plots and outputs are stored in `output/` and subfolders:

```
confusion_matrix/
residual_analysis/
calibration_curves/
court_overlay/
group_eval/
feature_relationships/
plots/
```

These outputs include:
- Court overlays (predicted FG% heatmaps)
- Residual vs. distance plots
- Model-to-model comparisons
- Feature importance visualizations

---

## Dependencies

See `requirements.txt` for full list. Key packages include:

- Data: `pandas`, `numpy`
- Modeling: `scikit-learn`, `xgboost`, `statsmodels`
- Visualization: `matplotlib`, `seaborn`, `plotly`
- SQL: `pyodbc`, `SQLAlchemy`
- Web UI: `streamlit`
- Utilities: `openpyxl`, `tqdm`, `python-dotenv`

---

## Use Cases

- Evaluate player shot profiles with context-aware probability
- Audit model calibration across distance and matchup types
- Run SQL quality checks before analysis
- Build a live model-serving application with Streamlit or API wrapper

---

## Acknowledgments

- [`nba_api`](https://github.com/swar/nba_api) for data access
- `Streamlit` for interface design
- `scikit-learn` and `xgboost` for modeling tools