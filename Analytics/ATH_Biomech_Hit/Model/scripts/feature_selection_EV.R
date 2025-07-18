# -----------------------------
# 🚀 EXIT VELOCITY FEATURE SELECTION & AUTO-TUNED XGBOOST MODEL
# -----------------------------

# ✅ Load Constants & Helper Functions
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/constants.R")
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/helpers.R")

# ✅ Load Required Libraries
library(dplyr)
library(xgboost)
library(caret)  # Train-Test Split
library(minerva)  # MIC Scores
library(car)  # VIF Analysis
library(openxlsx)  # Save to Excel
library(ParBayesianOptimization)  # Bayesian Hyperparameter Optimization
library(iml)  # SHAP for Interpretability

# ✅ Ensure Necessary Directories Exist
dirs_to_create <- c(OUTPUTS_EV)
lapply(dirs_to_create, dir.create, recursive = TRUE, showWarnings = FALSE)

# ✅ Initialize Log File
log_message("🚀 Exit Velocity Feature Selection Started...", LOG_FILE_EV)

# ✅ Load Cleaned Data
df <- read.csv(file.path(DATA_PATH, "hitter_combined_cleaned.csv"))

# ✅ Remove Unwanted Features
excluded_vars <- c("la", "dist")
df_cleaned <- df %>%
  select(where(is.numeric)) %>%
  select(-all_of(excluded_vars)) %>%
  mutate(across(where(is.logical), as.numeric))  # Convert logicals to numeric

# ✅ Define Target Variable & Predictors
target_var <- TARGET_EV
predictors <- setdiff(names(df_cleaned), target_var)

# 🔄 Train-Test Split
split_data <- generate_train_test_split(df_cleaned, target_var)
train_df <- split_data$train
test_df <- split_data$test

log_message(paste("✅ Train Size:", nrow(train_df), "Test Size:", nrow(test_df)), LOG_FILE_EV)

# 🔄 Convert Data to XGBoost Format
xgb_train <- xgb.DMatrix(data = as.matrix(train_df[, predictors]), label = train_df[[target_var]])

# -------------------------------
# 🔍 BAYESIAN OPTIMIZATION FUNCTION
# -------------------------------
# ✅ Load Best Params if Already Found
if (file.exists(BEST_PARAMS_EV)) {
  best_params <- readRDS(BEST_PARAMS_EV)
  log_message("🔥 Using Previously Found Best EV Hyperparameters:", LOG_FILE_EV)
} else {
  # 🚀 Run Bayesian Optimization if best params are NOT found
  best_params <- run_bayesian_optimization(xgb_train, target_var)
  
  # 💾 Save Best Params for Future Runs
  saveRDS(best_params, BEST_PARAMS_EV)
  log_message("✅ Best EV Hyperparameters Saved!", LOG_FILE_EV)
}

# ✅ Log Best Params
log_message("🔥 Best Hyperparameters Found:", LOG_FILE_EV)
log_message(capture.output(print(best_params)), LOG_FILE_EV)

# -------------------------------
# 🏆 FINAL MODEL TRAINING (EV)
# -------------------------------
xgb_train <- xgb.DMatrix(data = as.matrix(train_df[, predictors]), label = train_df[[target_var]])
xgb_test <- xgb.DMatrix(data = as.matrix(test_df[, predictors]), label = test_df[[target_var]])

xgb_model_final <- train_xgboost_model(xgb_train, target_var, best_params)

# -------------------------------
# 🔍 SHAP FEATURE IMPORTANCE USING `iml`
# -------------------------------
# ✅ Convert Matrices to DataFrames for SHAP
x_train_df <- as.data.frame(as.matrix(train_df[, predictors]))
x_test_df <- as.data.frame(as.matrix(test_df[, predictors]))

# ✅ Compute SHAP Importance
shap_importance <- compute_shap_importance(xgb_model_final, x_train_df)

# ✅ Select Top 50 Features
top_features <- names(sort(shap_importance, decreasing = TRUE))[1:50]
log_message(paste("🔹 Using", length(top_features), "features from XGBoost/SHAP."), LOG_FILE_EV)

# -------------------------------
# 🔄 FEATURE SELECTION METRICS (MIC, VIF, CORR)
# -------------------------------
# ✅ Compute MIC Scores
mic_matrix <- mine(as.matrix(train_df[, c(top_features, target_var)]))$MIC
mic_df <- as.data.frame(as.table(mic_matrix))
colnames(mic_df) <- c("Var1", "Var2", "MIC")

# ✅ Compute Pearson Correlation
corr_matrix <- cor(train_df[, c(top_features, target_var)], use = "pairwise.complete.obs")
corr_df <- as.data.frame(as.table(corr_matrix))

# 🔍 Detect & Remove Aliased Variables (Perfect Collinearity)
alias_info <- alias(lm(as.formula(paste(target_var, "~ .")), data = train_df))

if (!is.null(alias_info$Complete)) {
  aliased_vars <- colnames(alias_info$Complete)
  
  if (length(aliased_vars) > 0) {
    log_message("🚨 Identified Aliased Variables (Perfectly Collinear):", LOG_FILE_EV)
    log_message(capture.output(print(aliased_vars)), LOG_FILE_EV)
    
    # ✅ Drop Aliased Variables
    train_df <- train_df %>% select(-all_of(aliased_vars))
    log_message(paste("✅ Removed", length(aliased_vars), "aliased variables. Proceeding with VIF Calculation."), LOG_FILE_EV)
  } else {
    log_message("✅ No Aliased Variables Found. Proceeding with VIF Calculation.", LOG_FILE_EV)
  }
} else {
  log_message("✅ No Aliased Variables Found. Proceeding with VIF Calculation.", LOG_FILE_EV)
}

# ✅ Run VIF Calculation Safely
tryCatch({
  vif_results <- vif(lm(as.formula(paste(target_var, "~ .")), data = train_df))
  log_message("✅ VIF Calculation Completed Successfully!", LOG_FILE_EV)
  
  # ✅ Remove High-VIF Features
  train_df_filtered <- remove_high_vif_features(train_df, target_var)
  log_message(paste("✅ Features kept after VIF filtering:", ncol(train_df_filtered) - 1), LOG_FILE_EV)
  
}, error = function(e) {
  log_message("🚨 VIF Calculation Failed. There may still be aliased variables.", LOG_FILE_EV)
  log_message(capture.output(print(e)), LOG_FILE_EV)
})

# -------------------------------
# 🔄 MODEL EVALUATION
# -------------------------------
eval_metrics <- evaluate_model_performance(xgb_model_final, xgb_train, xgb_test, 
                                           train_df[[target_var]], test_df[[target_var]])

# ✅ Print Model Evaluation
log_message("📊 Model Evaluation Results:", LOG_FILE_EV)
log_message(capture.output(print(eval_metrics)), LOG_FILE_EV)

# ✅ Save Predictions to CSV
predictions_df <- data.frame(
  actual = test_df[[target_var]],
  predicted = predict(xgb_model_final, xgb_test)
)
write.csv(predictions_df, file.path(OUTPUTS_EV, "test_predictions.csv"), row.names = FALSE)
log_message("✅ Test Predictions Saved!", LOG_FILE_EV)

# ✅ Save Results to Excel
wb <- createWorkbook()
addWorksheet(wb, "Feature Importance")
writeData(wb, "Feature Importance", data.frame(Feature = top_features, SHAP = shap_importance[top_features]))

addWorksheet(wb, "MIC Scores")
writeData(wb, "MIC Scores", mic_df)

addWorksheet(wb, "Correlation")
writeData(wb, "Correlation", corr_df)

addWorksheet(wb, "VIF Scores")
writeData(wb, "VIF Scores", train_df_filtered)

addWorksheet(wb, "Model Evaluation")
writeData(wb, "Model Evaluation", eval_metrics)

saveWorkbook(wb, file.path(OUTPUTS_EV, "feature_selection_exit_velocity.xlsx"), overwrite = TRUE)

log_message("✅ Feature Selection & Model Evaluation Completed!", LOG_FILE_EV)
print("✅ Feature Selection & Model Evaluation Completed!")

