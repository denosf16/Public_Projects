# =================================
# 📌 TRAIN LAUNCH ANGLE MODEL (UPDATED STRUCTURE)
# =================================

# 🔹 Load Libraries & Constants
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/constants.R")
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/helpers.R")
library(rstanarm)
library(mgcv)
library(dplyr)

log_message("🚀 Starting Launch Angle Model Training...", LOG_FILE_LA)

# 🔹 Load Cleaned Data
log_message("🔄 Loading cleaned dataset for Launch Angle...", LOG_FILE_LA)
cleaned_data <- read.csv(file.path(OUTPUTS_PATH, "processed_data", "hitter_combined_cleaned.csv"))

if (any(colSums(is.na(cleaned_data)) > 0)) {
  log_message("❌ Missing values detected in Launch Angle dataset.", LOG_FILE_LA)
  stop("❌ Training halted due to missing values.")
}
log_message("✅ No missing values detected. Proceeding...", LOG_FILE_LA)

# 🔹 Ensure `user` is a Factor BEFORE Scaling
cleaned_data$user <- as.factor(cleaned_data$user)

# 🔹 Train/Test Split
set.seed(123)
train_indices <- sample(seq_len(nrow(cleaned_data)), size = floor(TRAIN_SPLIT * nrow(cleaned_data)))
train_data <- cleaned_data[train_indices, ]
test_data <- cleaned_data[-train_indices, ]

# 🔹 Standardize Numeric Predictors (EXCLUDE `user`, ONLY using train_data for mean/sd)
numeric_cols <- names(train_data)[sapply(train_data, is.numeric)]
numeric_cols <- setdiff(numeric_cols, TARGET_LA)

scaling_params <- train_data %>%
  summarise(across(all_of(numeric_cols), list(mean = mean, sd = sd)))

scale_columns <- function(df, scaling) {
  df %>%
    mutate(across(all_of(numeric_cols), 
                  ~ (. - scaling[[paste0(cur_column(), "_mean")]]) / scaling[[paste0(cur_column(), "_sd")]]))
}

# 🔹 Apply scaling
scaled_train <- scale_columns(train_data, scaling_params)
scaled_train$user <- train_data$user  # Re-attach as factor

scaled_test <- scale_columns(test_data, scaling_params)
scaled_test$user <- test_data$user

# 🔹 Save Scaling Parameters
target_scaling <- data.frame(
  la_mean = mean(train_data$la, na.rm = TRUE),
  la_sd = sd(train_data$la, na.rm = TRUE)
)
scaling_params_full <- cbind(scaling_params, target_scaling)

saveRDS(scaling_params_full, file.path(OUTPUTS_LA, "scaling_params_la.rds"))
log_message("✅ Numeric predictors and target scaling standardized and saved.", LOG_FILE_LA)

# 🔍 Data Structure Check Before Training
log_message("🔍 Checking data structure before training...", LOG_FILE_LA)
print(str(scaled_train))
print(summary(scaled_train))

# ===========================================
# 📌 BASE LAUNCH ANGLE MODEL (if not already saved)
# ===========================================
base_model_path <- file.path(OUTPUTS_LA, "base_la_model.rds")
if (!file.exists(base_model_path)) {
  log_message("🚀 Training Base Launch Angle Model...", LOG_FILE_LA)
  base_la_model <- stan_gamm4(
    la ~ attack_angle_contact_x + s(user, bs = "re"),  
    family = gaussian(),
    data = scaled_train,
    prior_intercept = normal(0, 0.5),
    prior = normal(0, 0.5),
    prior_aux = exponential(1),
    chains = STAN_CHAINS, iter = STAN_ITER, warmup = 2000, adapt_delta = STAN_DELTA, 
    control = list(max_treedepth = STAN_TREED), cores = STAN_CORES
  )
  saveRDS(base_la_model, base_model_path)
  log_message("✅ Base Launch Angle Model saved.", LOG_FILE_LA)
} else {
  log_message("✅ Base Launch Angle Model already exists. Skipping training.", LOG_FILE_LA)
}

# ===========================================
# 📌 ADVANCED LAUNCH ANGLE MODEL (if not already saved)
# ===========================================
adv_model_path <- file.path(OUTPUTS_LA, "advanced_la_model.rds")
if (!file.exists(adv_model_path)) {
  log_message("🚀 Training Advanced Launch Angle Model...", LOG_FILE_LA)
  advanced_la_model <- stan_gamm4(
    la ~ 
      pelvis_swing_max_z + 
      torso_angular_velocity_fp_x + 
      pelvis_loadedpos_x + 
      rear_elbow_fm_x + 
      torso_stride_max_z + 
      lead_wrist_swing_max_x + 
      pelvis_angular_velocity_fp_x + 
      x_factor_fp_y + 
      torso_pelvis_stride_max_y +
      rear_shoulder_stride_max_y + 
      attack_angle_contact_x * pitch_angle +
      s(user, bs = "re"),  
    family = gaussian(),
    data = scaled_train,
    prior_intercept = normal(0, 0.5),
    prior = normal(0, 0.5),
    prior_aux = exponential(1),
    chains = STAN_CHAINS, iter = STAN_ITER, warmup = 2000, adapt_delta = STAN_DELTA, 
    control = list(max_treedepth = STAN_TREED), cores = STAN_CORES
  )
  saveRDS(advanced_la_model, adv_model_path)
  log_message("✅ Advanced Launch Angle Model saved.", LOG_FILE_LA)
} else {
  log_message("✅ Advanced Launch Angle Model already exists. Skipping training.", LOG_FILE_LA)
}

# 🔹 Save Test Set for Prediction Script
write.csv(scaled_test, file.path(OUTPUTS_LA, "test_la_scaled.csv"), row.names = FALSE)
log_message("✅ Test set saved for prediction.", LOG_FILE_LA)

log_message("🎉 Launch Angle model training completed successfully!", LOG_FILE_LA)
print("🎉 Launch Angle model training completed successfully!")



