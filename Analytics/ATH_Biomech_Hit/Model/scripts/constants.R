# -----------------------------
# 🔧 CONSTANTS & CONFIGURATIONS
# -----------------------------

# 🏠 Base Project Path
BASE_PATH <- "C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit"

# 📂 Data & Output Paths
DATA_PATH <- file.path(BASE_PATH, "data")
OUTPUTS_PATH <- file.path(BASE_PATH, "outputs")

# 📂 EV & LA Subdirectories
OUTPUTS_EV <- file.path(OUTPUTS_PATH, "exit_velocity")
OUTPUTS_LA <- file.path(OUTPUTS_PATH, "launch_angle")

# 📂 Plot, Logs, and Processed Data Directories
PLOTS_EV <- file.path(OUTPUTS_EV, "plots")
PLOTS_LA <- file.path(OUTPUTS_LA, "plots")
LOGS_EV <- file.path(OUTPUTS_EV, "logs")
LOGS_LA <- file.path(OUTPUTS_LA, "logs")
DATA_OUTPUTS_PATH <- file.path(OUTPUTS_PATH, "processed_data")

# ✅ Ensure All Required Directories Exist
dirs_to_create <- c(DATA_PATH, OUTPUTS_EV, OUTPUTS_LA, PLOTS_EV, PLOTS_LA, LOGS_EV, LOGS_LA, DATA_OUTPUTS_PATH)
lapply(dirs_to_create, dir.create, recursive = TRUE, showWarnings = FALSE)

# 🌍 Raw Data URLs
RAW_METADATA_CSV <- "https://raw.githubusercontent.com/drivelineresearch/openbiomechanics/main/baseball_hitting/data/metadata.csv"
RAW_POI_CSV <- "https://raw.githubusercontent.com/drivelineresearch/openbiomechanics/main/baseball_hitting/data/poi/poi_metrics.csv"
RAW_HITTRAX_CSV <- "https://raw.githubusercontent.com/drivelineresearch/openbiomechanics/main/baseball_hitting/data/poi/hittrax.csv"

# 📥 Local File Paths
METADATA_CSV <- file.path(DATA_PATH, "metadata.csv")
POI_CSV <- file.path(DATA_PATH, "poi_metrics.csv")
HITTRAX_CSV <- file.path(DATA_PATH, "hittrax.csv")

# 🔑 Key Identifiers & Targets
SESSION_KEY <- "session_swing"
TARGET_LA <- "la"
TARGET_EV <- "exit_velo_mph_x"

# 📏 Training Split Ratio
TRAIN_SPLIT <- 0.7  # 70% Train, 30% Test

# 📜 Logging Configurations
TIMESTAMP <- format(Sys.time(), "%Y%m%d_%H%M%S")
LOG_FILE_EV <- file.path(LOGS_EV, paste0("ev_log_", TIMESTAMP, ".log"))
LOG_FILE_LA <- file.path(LOGS_LA, paste0("la_log_", TIMESTAMP, ".log"))

# 💾 Versioned Outputs (Prevents Overwrites)
FEATURE_IMPORTANCE_EV <- file.path(OUTPUTS_EV, paste0("feature_importance_", TIMESTAMP, ".csv"))
FEATURE_IMPORTANCE_LA <- file.path(OUTPUTS_LA, paste0("feature_importance_", TIMESTAMP, ".csv"))
MODEL_EVAL_EV <- file.path(OUTPUTS_EV, paste0("model_evaluation_", TIMESTAMP, ".csv"))
MODEL_EVAL_LA <- file.path(OUTPUTS_LA, paste0("model_evaluation_", TIMESTAMP, ".csv"))
PREDICTIONS_EV <- file.path(OUTPUTS_EV, paste0("test_predictions_", TIMESTAMP, ".csv"))
PREDICTIONS_LA <- file.path(OUTPUTS_LA, paste0("test_predictions_", TIMESTAMP, ".csv"))

# 🔥 Hyperparameter Tuning (Bayesian Optimization)
XGB_TUNING_PARAMS <- list(
  eta = c(0.01, 0.2),
  max_depth = c(3, 6),
  gamma = c(0, 3),
  colsample_bytree = c(0.6, 0.9),
  min_child_weight = c(1, 10),
  subsample = c(0.6, 0.9)
)
BEST_PARAMS_EV <- file.path(OUTPUTS_EV, "best_params_ev.rds")
BEST_PARAMS_LA <- file.path(OUTPUTS_LA, "best_params_la.rds")

# 🧠 Stan Model Configs
STAN_ITER <- 4000
STAN_CHAINS <- 4
STAN_CORES <- 4
STAN_TREED <- 12
STAN_DELTA <- 0.99

# 📂 Trained Model File Paths
BASE_EV_MODEL_FILE <- file.path(OUTPUTS_EV, "base_ev_model.rds")
ADVANCED_EV_MODEL_FILE <- file.path(OUTPUTS_EV, "advanced_ev_model.rds")
BASE_LA_MODEL_FILE <- file.path(OUTPUTS_LA, "base_la_model.rds")
ADVANCED_LA_MODEL_FILE <- file.path(OUTPUTS_LA, "advanced_la_model.rds")

# 🎨 Plot Theme (Dark Mode)
DEFAULT_THEME <- theme_minimal(base_size = 14) +
  theme(
    plot.background = element_rect(fill = "black"),
    panel.background = element_rect(fill = "black"),
    text = element_text(color = "white"),
    axis.text = element_text(color = "white"),
    axis.title = element_text(color = "white"),
    plot.title = element_text(color = "white", face = "bold"),
    panel.grid.major = element_line(color = "gray30"),
    panel.grid.minor = element_line(color = "gray30")
  )
PLOT_ALPHA <- 0.6  # Transparency for points

# 📢 Confirmation
print("✅ Constants Loaded Successfully!")





