# =========================================
# 📌 PREDICT EXIT VELOCITY MODELS (TEST SET ONLY) - ✅ FINAL FIXED
# =========================================

# 🔹 Load Required Libraries, Constants, Helpers
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/constants.R")
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/helpers.R")
library(rstanarm)
library(readr)
library(dplyr)

log_message("🔄 Loading TEST dataset for EV predictions...", LOG_FILE_EV)

# 🔹 Load Test Set (ALREADY in MPH, no scaling needed for actual_exit_velo)
test_ev <- read.csv(file.path(OUTPUTS_EV, "test_ev_scaled.csv"))

# 🚨 Check for Missing Values
if (any(colSums(is.na(test_ev)) > 0)) {
  log_message("❌ Missing values detected in the TEST dataset!", LOG_FILE_EV)
  stop("❌ Error: Test dataset contains missing values!")
}
log_message("✅ No missing values detected. Proceeding with predictions...", LOG_FILE_EV)

# 🔹 Load Trained Models
model_files <- list(
  "Base_EV" = file.path(OUTPUTS_EV, "base_ev_model.rds"),
  "Advanced_EV" = file.path(OUTPUTS_EV, "advanced_ev_model.rds")
)

models <- list()
for (model_name in names(model_files)) {
  model_path <- model_files[[model_name]]
  if (file.exists(model_path)) {
    models[[model_name]] <- readRDS(model_path)
    log_message(paste("✅", model_name, "Model loaded successfully."), LOG_FILE_EV)
  } else {
    log_message(paste("❌ Model file not found:", model_path), LOG_FILE_EV)
    stop(paste("❌ Error: Trained model for", model_name, "is missing!"))
  }
}

# 🔹 Load scaling params for prediction unscaling
scaling_params <- readRDS(file.path(OUTPUTS_EV, "scaling_params_ev.rds"))
ev_mean <- scaling_params$exit_velo_mph_x_mean[1]
ev_sd <- scaling_params$exit_velo_mph_x_sd[1]
cat("✅ EV mean:", ev_mean, " | EV SD:", ev_sd, "\n")

# 🔹 Prepare Prediction DataFrame - preserve all test_ev columns + add actual EV
ev_predictions <- test_ev %>%
  mutate(actual_exit_velo = exit_velo_mph_x)  # Target column standardized

# 🔹 Generate Predictions Loop
for (model_name in names(models)) {
  model <- models[[model_name]]
  log_message(paste("🚀 Predicting with", model_name, "Model..."), LOG_FILE_EV)
  
  # ✅ Defensive: Check model type
  if (!inherits(model, "stanreg")) {
    log_message(paste("❌ Invalid model object for", model_name), LOG_FILE_EV)
    stop(paste("❌ Model", model_name, "is not a valid stanreg object"))
  }
  
  # 🔥 Posterior Predict (returns scaled predictions)
  posterior_samples <- posterior_predict(model, newdata = test_ev)
  cat("✅ Posterior Samples Dim (", model_name, "): ", dim(posterior_samples), "\n")
  
  # ✅ Calculate mean predictions (scaled)
  preds_scaled <- colMeans(posterior_samples)
  cat("Range of preds_scaled (", model_name, "): ", range(preds_scaled), "\n")
  
  # ✅ Safety check - predictions should vary
  if (sd(preds_scaled) < 1e-5) {
    log_message(paste("❌ Warning: Predictions from", model_name, "are nearly constant."), LOG_FILE_EV)
  }
  
  # 🔹 ✅ Unscale predictions to MPH
  preds_unscaled <- (preds_scaled * ev_sd) + ev_mean
  cat("Range of preds_unscaled (", model_name, "): ", range(preds_unscaled), "\n")
  
  # ✅ Append unscaled predictions
  pred_col <- paste0(model_name, "_pred_exit_velo")
  ev_predictions[[pred_col]] <- preds_unscaled
  log_message(paste("✅", model_name, "predictions added and scaled back."), LOG_FILE_EV)
}

# 🔹 SAVE Final Predictions for Evaluation (✅ Unscaled Actuals & Predictions)
final_path <- file.path(OUTPUTS_EV, "ev_predictions_test.csv")

# ✅ Save full predictions dataset for evaluation & PPC
write.csv(ev_predictions, final_path, row.names = FALSE)

log_message(paste("✅ Test set predictions saved to:", final_path), LOG_FILE_EV)
print("🎯 Exit Velocity Prediction (Test Set) completed successfully!")





