# =========================================
# 📌 PREDICT LAUNCH ANGLE MODELS (TEST SET ONLY) - ✅ FINAL FIXED
# =========================================

# 🔹 Load Required Libraries, Constants, Helpers
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/constants.R")
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/helpers.R")
library(rstanarm)
library(readr)
library(dplyr)

log_message("🔄 Loading TEST dataset for LA predictions...", LOG_FILE_LA)

# 🔹 Load Scaled Test Set (already scaled features, but LA target in scaled units)
test_la <- read.csv(file.path(OUTPUTS_LA, "test_la_scaled.csv"))

# 🚨 Check for Missing Values
if (any(colSums(is.na(test_la)) > 0)) {
  log_message("❌ Missing values detected in the TEST dataset!", LOG_FILE_LA)
  stop("❌ Error: Test dataset contains missing values!")
}
log_message("✅ No missing values detected. Proceeding with predictions...", LOG_FILE_LA)

# 🔹 Load Trained Models
model_files <- list(
  "Base_LA"      = file.path(OUTPUTS_LA, "base_la_model.rds"),
  "Advanced_LA"  = file.path(OUTPUTS_LA, "advanced_la_model.rds")
)

models <- list()
for (model_name in names(model_files)) {
  model_path <- model_files[[model_name]]
  if (file.exists(model_path)) {
    models[[model_name]] <- readRDS(model_path)
    log_message(paste("✅", model_name, "Model loaded successfully."), LOG_FILE_LA)
  } else {
    log_message(paste("❌ Model file not found:", model_path), LOG_FILE_LA)
    stop(paste("❌ Error: Trained model for", model_name, "is missing!"))
  }
}

# 🔹 Load scaling params for unscaling predictions
scaling_params <- readRDS(file.path(OUTPUTS_LA, "scaling_params_la.rds"))
la_mean <- scaling_params$la_mean[1]
la_sd <- scaling_params$la_sd[1]
cat("✅ LA mean:", la_mean, " | LA SD:", la_sd, "\n")

# 🔹 Prepare Prediction DataFrame - preserve all test_la columns + add actual LA
la_predictions <- test_la %>%
  mutate(actual_la = la)  # Target column standardized

# 🔹 Generate Predictions Loop
for (model_name in names(models)) {
  model <- models[[model_name]]
  log_message(paste("🚀 Predicting with", model_name, "Model..."), LOG_FILE_LA)
  
  # ✅ Defensive: Check model type
  if (!inherits(model, "stanreg")) {
    log_message(paste("❌ Invalid model object for", model_name), LOG_FILE_LA)
    stop(paste("❌ Model", model_name, "is not a valid stanreg object"))
  }
  
  # 🔥 Posterior Predict (returns scaled predictions)
  posterior_samples <- posterior_predict(model, newdata = test_la)
  cat("✅ Posterior Samples Dim (", model_name, "): ", dim(posterior_samples), "\n")
  
  # ✅ Calculate mean predictions (scaled)
  preds_scaled <- colMeans(posterior_samples)
  cat("Range of preds_scaled (", model_name, "): ", range(preds_scaled), "\n")
  
  # ✅ Safety check - predictions should vary
  if (sd(preds_scaled) < 1e-5) {
    log_message(paste("❌ Warning: Predictions from", model_name, "are nearly constant."), LOG_FILE_LA)
  }
  
  # 🔹 ✅ Unscale predictions to actual LA units
  preds_unscaled <- (preds_scaled * la_sd) + la_mean
  cat("Range of preds_unscaled (", model_name, "): ", range(preds_unscaled), "\n")
  
  # ✅ Append unscaled predictions
  pred_col <- paste0(model_name, "_pred_LA")
  la_predictions[[pred_col]] <- preds_unscaled
  log_message(paste("✅", model_name, "predictions added and scaled back."), LOG_FILE_LA)
}

# 🔹 SAVE Final Predictions for Evaluation (✅ Unscaled Actuals & Predictions)
final_path <- file.path(OUTPUTS_LA, "la_predictions_test.csv")

# ✅ Save full predictions dataset for evaluation & PPC
write.csv(la_predictions, final_path, row.names = FALSE)

log_message(paste("✅ Test set predictions saved to:", final_path), LOG_FILE_LA)
print("🎯 Launch Angle Prediction (Test Set) completed successfully!")




