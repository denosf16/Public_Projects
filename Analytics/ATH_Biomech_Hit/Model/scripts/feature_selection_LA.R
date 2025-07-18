# -----------------------------
# 🚀 FINALIZED FEATURE SELECTION & AUTO-TUNED XGBOOST MODEL (Launch Angle)
# -----------------------------

# ✅ Load Constants & Helpers
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/constants.R")
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/helpers.R")

# ✅ Required Libraries
library(dplyr)
library(xgboost)
library(caret)  
library(minerva)  
library(car)  
library(openxlsx)  
library(iml)  

# ✅ Define Paths
OUTPUT_PATH <- OUTPUTS_LA  
dir.create(OUTPUT_PATH, showWarnings = FALSE)

# ✅ Load Data
df <- read.csv(file.path(DATA_PATH, "hitter_combined_cleaned.csv"))

# ✅ Remove Unwanted Features (Exclude Exit Velocity, Keep Biomech Variables)
excluded_vars <- c("exit_velo_mph_x", "dist")
df_cleaned <- df %>%
  select(where(is.numeric)) %>%
  select(-all_of(excluded_vars)) %>%
  mutate(across(where(is.logical), as.numeric))  

# ✅ Define Target & Predictors
target_var <- "la"
predictors <- setdiff(names(df_cleaned), target_var)

# ✅ Train-Test Split (80-20)
train_test <- generate_train_test_split(df_cleaned, target_var)  
train_df <- train_test$train
test_df <- train_test$test

print(paste("✅ Train size:", nrow(train_df), "Test size:", nrow(test_df)))

# ✅ Convert Data to XGBoost Format
xgb_train <- xgb.DMatrix(data = as.matrix(train_df[, predictors]), label = train_df[[target_var]])
xgb_test <- xgb.DMatrix(data = as.matrix(test_df[, predictors]), label = test_df[[target_var]])

# -------------------------------
# 🔍 BAYESIAN OPTIMIZATION FUNCTION
# -------------------------------
# ✅ Load Best Params if Already Found
if (file.exists(BEST_PARAMS_LA)) {
  best_params <- readRDS(BEST_PARAMS_LA)
  print("🔥 Using Previously Found Best LA Hyperparameters:")
  print(best_params)
} else {
  # 🚀 Run Bayesian Optimization if best params are NOT found
  best_params <- run_bayesian_optimization(xgb_train, target_var)
  
  # 💾 Save Best Params for Future Runs
  saveRDS(best_params, BEST_PARAMS_LA)
  print("✅ Best LA Hyperparameters Saved!")
}

# ✅ Log Best Params
log_message("🔥 Best Hyperparameters Found:", LOG_FILE_LA)
log_message(capture.output(print(best_params)), LOG_FILE_LA)

# ✅ Convert Data to XGBoost Format
xgb_train <- xgb.DMatrix(data = as.matrix(train_df[, predictors]), label = train_df[[target_var]])
xgb_test <- xgb.DMatrix(data = as.matrix(test_df[, predictors]), label = test_df[[target_var]])

# -------------------------------
# 🏆 FINAL MODEL TRAINING (LA)
# -------------------------------
xgb_model_final <- train_xgboost_model(xgb_train, target_var, best_params)


# -------------------------------
# 🔍 SHAP FEATURE IMPORTANCE USING `iml`
# -------------------------------
# ✅ Prepare Data for SHAP
x_train_df <- as.data.frame(as.matrix(train_df[, predictors]))  
x_test_df <- as.data.frame(as.matrix(test_df[, predictors]))

# ✅ Compute SHAP Importance
# ✅ Ensure X_train is a Data Frame
shap_importance <- compute_shap_importance(xgb_model_final, as.data.frame(as.matrix(train_df[, predictors])))


# ✅ Select Top 20 Features (More Aggressive Feature Reduction)
top_features <- names(sort(shap_importance, decreasing = TRUE))[1:20]
log_message(paste("🔹 Using", length(top_features), "features from XGBoost/SHAP."), LOG_FILE_LA)

# -------------------------------
# 🔄 FEATURE SELECTION METRICS (MIC, VIF, CORR)
# -------------------------------
mic_df <- compute_mic_scores(train_df, top_features, target_var)
corr_df <- compute_correlation(train_df, top_features, target_var)
vif_df <- remove_high_vif_features(train_df[, c(top_features, target_var)], target_var)
log_message(paste("✅ Features kept after VIF filtering:", nrow(vif_df)), LOG_FILE_LA)

# -------------------------------
# 🔄 MODEL EVALUATION
# -------------------------------
eval_metrics <- evaluate_model_performance(xgb_model_final, xgb_train, xgb_test, 
                                           train_df[[target_var]], test_df[[target_var]])

# ✅ Print Model Evaluation
log_message("📊 Model Evaluation Results:", LOG_FILE_LA)
log_message(capture.output(print(eval_metrics)), LOG_FILE_LA)

# ✅ Save Predictions to CSV
predictions_df <- data.frame(
  actual = test_df[[target_var]],
  predicted = predict(xgb_model_final, xgb_test)
)
write.csv(predictions_df, file.path(OUTPUT_PATH, "test_predictions.csv"), row.names = FALSE)
log_message("✅ Test Predictions Saved!", LOG_FILE_LA)

# ✅ Save Results to Excel
wb <- createWorkbook()
addWorksheet(wb, "Feature Importance")
writeData(wb, "Feature Importance", shap_importance)

addWorksheet(wb, "MIC Scores")
writeData(wb, "MIC Scores", mic_df)

addWorksheet(wb, "Correlation")
writeData(wb, "Correlation", corr_df)

addWorksheet(wb, "VIF Scores")
writeData(wb, "VIF Scores", vif_df)

addWorksheet(wb, "Model Evaluation")
writeData(wb, "Model Evaluation", eval_metrics)

saveWorkbook(wb, file.path(OUTPUT_PATH, "feature_selection_launch_angle.xlsx"), overwrite = TRUE)

log_message("✅ Feature Selection & Model Evaluation Completed!", LOG_FILE_LA)
print("✅ Feature Selection & Model Evaluation Completed!")







