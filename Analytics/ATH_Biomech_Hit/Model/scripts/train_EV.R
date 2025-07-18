# =================================
# 📌 TRAIN EXIT VELOCITY MODEL
# =================================

# 🔹 Load Libraries & Constants
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/constants.R")
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/helpers.R")
library(rstanarm)
library(mgcv)
library(dplyr)

log_message("🚀 Starting Exit Velocity Model Training...", LOG_FILE_EV)

# 🔹 Load Cleaned Data
log_message("🔄 Loading cleaned dataset for Exit Velocity...", LOG_FILE_EV)
cleaned_data <- read.csv(file.path(OUTPUTS_PATH, "processed_data", "hitter_combined_cleaned.csv"))

if (any(colSums(is.na(cleaned_data)) > 0)) {
  log_message("❌ Missing values detected in Exit Velocity dataset.", LOG_FILE_EV)
  stop("❌ Training halted due to missing values.")
}
log_message("✅ No missing values detected. Proceeding...", LOG_FILE_EV)

# 🔹 Ensure `user` is a Factor BEFORE Scaling
cleaned_data$user <- as.factor(cleaned_data$user)

# 🔹 Train/Test Split (by session_swing or row count if needed)
set.seed(123)
train_indices <- sample(seq_len(nrow(cleaned_data)), size = floor(TRAIN_SPLIT * nrow(cleaned_data)))
train_data <- cleaned_data[train_indices, ]
test_data <- cleaned_data[-train_indices, ]

# 🔹 Standardize Numeric Predictors (EXCLUDE `user`, ONLY using train_data for mean/sd)
numeric_cols <- names(train_data)[sapply(train_data, is.numeric)]
numeric_cols <- setdiff(numeric_cols, TARGET_EV)

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
# 🔹 Append Target Scaling (EV mean/sd) for prediction scaling-back later
target_scaling <- data.frame(
  exit_velo_mph_x_mean = mean(train_data$exit_velo_mph_x, na.rm = TRUE),
  exit_velo_mph_x_sd = sd(train_data$exit_velo_mph_x, na.rm = TRUE)
)

# 🔹 Combine feature scaling and target scaling
scaling_params_full <- cbind(scaling_params, target_scaling)

# 🔹 Save combined scaling params
saveRDS(scaling_params_full, file.path(OUTPUTS_EV, "scaling_params_ev.rds"))
log_message("✅ Numeric predictors and target scaling standardized and saved.", LOG_FILE_EV)


# 🔍 Check Data Structure Before Training
log_message("🔍 Checking data structure before training...", LOG_FILE_EV)
print(str(scaled_train))
print(summary(scaled_train))

# 🔹 Train Base EV Model
base_model_path <- file.path(OUTPUTS_EV, "base_ev_model.rds")
if (!file.exists(base_model_path)) {
  log_message("🚀 Training Base Exit Velocity Model...", LOG_FILE_EV)
  base_ev_model <- stan_gamm4(
    exit_velo_mph_x ~ bat_speed_mph_contact_x + s(user, bs = "re"),  
    family = gaussian(),
    data = scaled_train,
    prior_intercept = normal(0, 0.5),
    prior = normal(0, 0.5),
    prior_aux = exponential(1),
    chains = STAN_CHAINS, iter = STAN_ITER, warmup = 2000, adapt_delta = STAN_DELTA, 
    control = list(max_treedepth = STAN_TREED), cores = STAN_CORES
  )
  saveRDS(base_ev_model, base_model_path)
  log_message("✅ Base Exit Velocity Model saved.", LOG_FILE_EV)
} else {
  log_message("✅ Base Exit Velocity Model already exists. Skipping training.", LOG_FILE_EV)
}

# 🔹 Train Advanced EV Model
adv_model_path <- file.path(OUTPUTS_EV, "advanced_ev_model.rds")
if (!file.exists(adv_model_path)) {
  log_message("🚀 Training Advanced Exit Velocity Model...", LOG_FILE_EV)
  advanced_ev_model <- stan_gamm4(
    exit_velo_mph_x ~ 
      rear_shoulder_stride_max_y + 
      torso_pelvis_stride_max_y + 
      bat_speed_mph_contact_x + 
      lead_knee_launchpos_x + 
      pelvis_angular_velocity_fp_x + 
      s(user, bs = "re") + 
      pelvis_angular_velocity_fp_x * x_factor_hs_z + 
      rear_shoulder_stride_max_y * torso_pelvis_stride_max_y,  
    family = gaussian(),
    data = scaled_train,
    prior_intercept = normal(0, 0.5),
    prior = normal(0, 0.5),
    prior_aux = exponential(1),
    chains = STAN_CHAINS, iter = STAN_ITER, warmup = 2000, adapt_delta = STAN_DELTA, 
    control = list(max_treedepth = STAN_TREED), cores = STAN_CORES
  )
  saveRDS(advanced_ev_model, adv_model_path)
  log_message("✅ Advanced Exit Velocity Model saved.", LOG_FILE_EV)
} else {
  log_message("✅ Advanced Exit Velocity Model already exists. Skipping training.", LOG_FILE_EV)
}

# 🔹 Save Test Set for Prediction Script
write.csv(scaled_test, file.path(OUTPUTS_EV, "test_ev_scaled.csv"), row.names = FALSE)
log_message("✅ Test set saved for prediction.", LOG_FILE_EV)

log_message("🎉 Exit Velocity model training completed successfully!", LOG_FILE_EV)
print("🎉 Exit Velocity model training completed successfully!")


