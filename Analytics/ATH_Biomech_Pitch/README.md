# ATH Biomech Pitch

**ATH Biomech Pitch** is a modular, end-to-end machine learning project built to predict pitch velocity (`pitch_speed_mph`) using biomechanical motion capture data. The system is designed to serve both predictive and diagnostic purposes, incorporating advanced feature selection, grouped model comparison, and transparent evaluation through coefficients, importances, and error patterns.

---

## Project Overview

The project models pitch velocity from 3D kinematic marker data and force plate metrics collected during athletic assessments. The full ML workflow is implemented in Python and delivered through an interactive Streamlit application. It includes:

- Data validation and filtering for outliers, normality, and collinearity
- Feature selection via mutual information, random forest, and LASSO ensembles
- Grouped modeling across biomechanical domains: full-body, upper-body, lower-body, and force-based
- Transparent diagnostics: VIF, feature scores, model coefficients and importances
- Prediction breakdowns across groups, with R² scores reported globally and by cluster

---

## Project Structure

```
ATH_Biomech_Pitch/
├── app/                      # Streamlit tabs: cleaning, selection, training, evaluation, prediction
├── models/                   # Scripts for training RF, ElasticNet, MLP, GAM models
├── scripts/                  # Data cleaning, preprocessing, and utils
├── output/                   # CSV and PNG diagnostics for model comparison
├── data/                     # Source and merged biomech datasets
├── requirements.txt
└── README.md
```

---

## Streamlit App Navigation

Each tab provides a different role in the workflow:

| Tab | Function |
|-----|----------|
| Home | Project overview and usage instructions |
| Data_Cleaning | Missingness, outliers, skewness, normality summary |
| Feature_Selection | Correlation filter, RF/MI feature scoring, ensemble selection |
| Model_Training | Train RF, ElasticNet, GAM, MLP using selected features or grouped subsets |
| Evaluate | R² scores, residual plots, importances, coefficient comparisons |
| Predict | Upload new biomech data and view predictions with breakdowns |

---

## Feature Engineering and Selection

Features originate from 3D marker data and force plate outputs. The selection pipeline involves:

- Filtering highly correlated predictors (`correlation_heatmap.png`)
- Scoring via mutual information (`mi_importance.png`), random forest (`rf_importance.png`)
- Ensemble voting based on MI, RF, and LASSO
- Final selection visualized in `feature_scores.csv`, `selected_features.csv`
- Multicollinearity assessed via `vif_results.csv`

Biomechanical groupings:
- Full Model: All features
- Upper Body: Shoulder, elbow, wrist markers
- Lower Body: Pelvis, stride, lead knee
- Force Model: Ground reaction forces, CoP

---

## Models Trained

Each group is fit using four ML methods:

- `train_rf.py`: Random Forest
- `train_elasticnet.py`: ElasticNet Regression
- `train_mlp.py`: Multilayer Perceptron
- `train_gam.py`: Generalized Additive Models

All models are trained on standardized features with nested evaluation.

Trained outputs:
- `*_model_coefficients.csv`
- `*_model_importance.csv`

---

## Evaluation and Metrics

Model results are summarized in:
- `model_metrics.csv`: Global and per-model R²
- `normality_summary.csv`: Shapiro-Wilk and skew diagnostics
- `outlier_counts.csv`: Count of outliers by variable

Visual diagnostics include:
- `correlation_heatmap.png`: Inter-feature correlation
- `mi_importance.png`: MI ranking
- `rf_importance.png`: RF Gini importance

---

## Predictions

The `Predict` tab allows you to:
- Upload a new biomechanical assessment
- Select which model (full, upper, lower, force) to apply
- Receive predicted `pitch_speed_mph` and a breakdown of group-specific predictions
- Display associated coefficients or importances

---

## Dependencies

Key packages used (see `requirements.txt`):

- pandas, numpy, scikit-learn, xgboost
- matplotlib, seaborn, plotly
- statsmodels, pyGAM
- streamlit, openpyxl

---

## Use Cases

- Identify biomechanical contributors to fastball velocity
- Build interpretable models for pitch development and training
- Monitor athlete changes over time using prediction breakdowns
- Deploy via Streamlit to field or remote environments

---

## Acknowledgments

- Motion capture system and force plates used by ATH
- pyGAM, scikit-learn, and pandas for model development
- Streamlit for rapid UI deployment