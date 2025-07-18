# ==============================
# 🔹 Load Constants and Libraries
# ==============================
source("scripts/constants.R")
library(rstanarm)
library(mgcv)
library(futile.logger)
library(readr)
library(dplyr)

# ==============================
# 🔹 Load Cleaned Data
# ==============================
flog.info("🔄 Loading cleaned dataset...")
cleaned_data <- read.csv(file.path(OUTPUT_PATH, "pitch_data_cleaned.csv"))

# 🚨 Check for Missing Values Before Training
if (any(colSums(is.na(cleaned_data)) > 0)) {
  flog.error("❌ Missing values detected! Ensure preprocessing completed successfully.")
  stop("❌ Training halted due to missing values in dataset.")
}
flog.info("✅ No missing values detected. Proceeding with training...")

# ==============================
# 🔹 Standardize Numeric Predictors
# ==============================
flog.info("🔄 Standardizing numeric predictor variables...")

numeric_cols <- names(cleaned_data)[sapply(cleaned_data, is.numeric)]
numeric_cols <- setdiff(numeric_cols, "pitch_speed_mph")  # Exclude response variable

# Compute mean and standard deviation for each numeric column
scaling_params <- cleaned_data %>%
  summarise(across(all_of(numeric_cols), list(
    mean = \(x) mean(x, na.rm = TRUE),
    sd = \(x) sd(x, na.rm = TRUE)
  )))

# Apply z-score standardization
scaled_pitch_data <- cleaned_data %>%
  mutate(across(all_of(numeric_cols), 
                ~ (. - scaling_params[[paste0(cur_column(), "_mean")]]) / scaling_params[[paste0(cur_column(), "_sd")]]))

# Save scaling parameters for use in predictions
saveRDS(scaling_params, file.path(OUTPUT_PATH, "scaling_params.rds"))

flog.info("✅ Numeric predictors successfully scaled and scaling parameters saved.")

# ==============================
# ✅ Train Force Model
# ==============================
flog.info("🚀 Training Force Model...")
force_model <- stan_gamm4(
  pitch_speed_mph ~ s(rear_grf_z_max) + lead_grf_z_max + p_throws + s(user, bs = "re"),
  family = gaussian(),
  data = scaled_pitch_data,
  chains = 2, iter = 4000, warmup = 1500, adapt_delta = 0.95, 
  control = list(max_treedepth = 12), cores = 2
)
saveRDS(force_model, FORCE_MODEL_FILE)
flog.info("✅ Force Model saved.")

# ==============================
# ✅ Train Upper Body Model
# ==============================
flog.info("🚀 Training Upper Body Model...")
upper_body_model <- stan_gamm4(
  pitch_speed_mph ~ s(max_shoulder_internal_rotational_velo) + 
    max_shoulder_external_rotation + 
    max_shoulder_horizontal_abduction + 
    elbow_varus_moment + 
    elbow_transfer_fp_br,
  family = gaussian(),
  data = scaled_pitch_data,
  chains = 2, iter = 4000, warmup = 1500, adapt_delta = 0.95, 
  control = list(max_treedepth = 12), cores = 2
)
saveRDS(upper_body_model, UPPER_BODY_MODEL_FILE)
flog.info("✅ Upper Body Model saved.")

# ==============================
# ✅ Train Lower Body Model
# ==============================
flog.info("🚀 Training Lower Body Model...")
lower_body_model <- stan_gamm4(
  pitch_speed_mph ~ s(max_torso_rotational_velo) + 
    max_rotation_hip_shoulder_separation + 
    pelvis_anterior_tilt_fp + 
    max_cog_velo_x + 
    lead_knee_extension_from_fp_to_br + 
    lead_knee_transfer_fp_br + 
    rear_hip_generation_pkh_fp,
  family = gaussian(),
  data = scaled_pitch_data,
  chains = 2, iter = 4000, warmup = 1500, adapt_delta = 0.95, 
  control = list(max_treedepth = 12), cores = 2
)
saveRDS(lower_body_model, LOWER_BODY_MODEL_FILE)
flog.info("✅ Lower Body Model saved.")

# ==============================
# ✅ Train Full Model (All Key Features & Interactions)
# ==============================
flog.info("🚀 Training Full Model...")
full_model <- stan_gamm4(
  pitch_speed_mph ~ s(max_shoulder_internal_rotational_velo) + 
    max_shoulder_external_rotation + 
    max_shoulder_horizontal_abduction + 
    elbow_varus_moment + 
    elbow_transfer_fp_br + 
    s(max_torso_rotational_velo) + 
    max_rotation_hip_shoulder_separation + 
    pelvis_anterior_tilt_fp + 
    s(max_cog_velo_x) + 
    lead_knee_extension_from_fp_to_br + 
    lead_knee_transfer_fp_br + 
    rear_hip_generation_pkh_fp + 
    s(rear_grf_z_max) + 
    lead_grf_z_max + 
    # 🔹 Key Interactions
    max_rotation_hip_shoulder_separation:lead_knee_extension_from_fp_to_br + 
    elbow_varus_moment:elbow_transfer_fp_br + 
    rear_grf_z_max:lead_grf_z_max,
  family = gaussian(),
  data = scaled_pitch_data,
  chains = 2, iter = 4000, warmup = 1500, adapt_delta = 0.95, 
  control = list(max_treedepth = 12), cores = 2
)
saveRDS(full_model, FULL_MODEL_FILE)
flog.info("✅ Full Model saved.")

# ==============================
# ✅ Training Process Complete
# ==============================
flog.info("🎉 All models trained and saved successfully!")
print("✅ Training process completed successfully!")





