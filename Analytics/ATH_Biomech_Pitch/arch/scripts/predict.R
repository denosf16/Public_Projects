# ==============================
# 🔹 Load Required Libraries
# ==============================
source("scripts/constants.R")
library(rstanarm)
library(futile.logger)
library(readr)
library(dplyr)

# ==============================
# 🔹 Load Cleaned Data
# ==============================
flog.info("🔄 Loading cleaned dataset...")
pitch_data <- read.csv(file.path(OUTPUT_PATH, "pitch_data_cleaned.csv"))

# 🚨 Check for Missing Values
if (any(colSums(is.na(pitch_data)) > 0)) {
  flog.error("❌ Missing values detected in cleaned dataset!")
  stop("❌ Error: Dataset contains missing values!")
}
flog.info("✅ No missing values detected. Proceeding with predictions...")

# ==============================
# 🔹 Standardize Numeric Features (Exclude Response)
# ==============================
flog.info("🔄 Standardizing numeric predictor variables...")
numeric_cols <- names(pitch_data)[sapply(pitch_data, is.numeric)]
numeric_cols <- setdiff(numeric_cols, "pitch_speed_mph")  # Exclude response variable

pitch_data_scaled <- pitch_data %>%
  mutate(across(all_of(numeric_cols), ~ scale(.)[,1]))

flog.info("✅ Numeric predictors successfully standardized.")

# 🚨 Debugging Check: Ensure Required Features Exist
flog.info("📌 Checking feature availability for models...")

model_features <- list(
  "Force"       = c("lead_grf_z_max", "rear_grf_z_max"),
  "Upper_Body"  = c("max_shoulder_internal_rotational_velo", 
                    "max_shoulder_external_rotation",
                    "max_shoulder_horizontal_abduction",
                    "elbow_varus_moment",
                    "elbow_transfer_fp_br"),
  "Lower_Body"  = c("max_torso_rotational_velo",
                    "max_rotation_hip_shoulder_separation",
                    "pelvis_anterior_tilt_fp",
                    "max_cog_velo_x",
                    "lead_knee_extension_from_fp_to_br",
                    "lead_knee_transfer_fp_br",
                    "rear_hip_generation_pkh_fp"),
  "Full"        = c("max_shoulder_internal_rotational_velo",
                    "max_shoulder_external_rotation",
                    "max_shoulder_horizontal_abduction",
                    "elbow_varus_moment",
                    "elbow_transfer_fp_br",
                    "max_torso_rotational_velo",
                    "max_rotation_hip_shoulder_separation",
                    "pelvis_anterior_tilt_fp",
                    "max_cog_velo_x",
                    "lead_knee_extension_from_fp_to_br",
                    "lead_knee_transfer_fp_br",
                    "rear_hip_generation_pkh_fp",
                    "rear_grf_z_max",
                    "lead_grf_z_max")
)

for (model_name in names(model_features)) {
  missing_features <- setdiff(model_features[[model_name]], colnames(pitch_data_scaled))
  
  if (length(missing_features) > 0) {
    flog.error("❌ Missing features for %s model: %s", model_name, paste(missing_features, collapse = ", "))
    stop(paste("❌ Error: Required features missing for", model_name, "model!"))
  }
}

flog.info("✅ All required features are present.")

# ==============================
# 🔹 Load Trained Models
# ==============================
model_files <- list(
  "Force"       = FORCE_MODEL_FILE,
  "Upper_Body"  = UPPER_BODY_MODEL_FILE,
  "Lower_Body"  = LOWER_BODY_MODEL_FILE,
  "Full"        = FULL_MODEL_FILE
)

models <- list()
for (model_name in names(model_files)) {
  if (!file.exists(model_files[[model_name]])) {
    flog.error("❌ Model file not found: %s", model_files[[model_name]])
    stop(paste("❌ Error: Trained model for", model_name, "is missing!"))
  }
  
  models[[model_name]] <- readRDS(model_files[[model_name]])
  flog.info("✅ %s Model loaded successfully.", model_name)
}

# ==============================
# 🔹 Generate Predictions
# ==============================
flog.info("🔄 Generating posterior predictions for all models...")

predictions <- pitch_data %>%
  select(session_pitch, pitch_speed_mph)  # Keep original pitch speed for reference

for (model_name in names(models)) {
  model <- models[[model_name]]
  required_features <- model_features[[model_name]]
  
  flog.info("🚀 Predicting with %s Model...", model_name)
  tryCatch({
    posterior_samples <- posterior_predict(model, newdata = pitch_data_scaled[ , required_features, drop = FALSE])
    predictions[[paste0(model_name, "_pred_pitch_speed")]] <- colMeans(posterior_samples)  # Mean posterior prediction
    flog.info("✅ %s Model predictions added.", model_name)
  }, error = function(e) {
    flog.error("❌ Prediction failed for %s Model: %s", model_name, e$message)
  })
}

# ==============================
# 🔹 Save Predictions
# ==============================
write_csv(predictions, PREDICTIONS_FILE)
flog.info("✅ Predictions saved to: %s", PREDICTIONS_FILE)

print("✅ Prediction process completed successfully!")








