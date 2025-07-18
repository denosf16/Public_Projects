# ==============================
# 🔹 File Paths
# ==============================
DATA_PATH <- "data/"
OUTPUT_PATH <- "outputs/"
MODEL_PATH <- file.path(OUTPUT_PATH, "models")  # Model output path
LOG_PATH <- file.path(OUTPUT_PATH, "logs")

# Ensure directories exist
dir.create(OUTPUT_PATH, showWarnings = FALSE, recursive = TRUE)
dir.create(MODEL_PATH, showWarnings = FALSE, recursive = TRUE)
dir.create(LOG_PATH, showWarnings = FALSE, recursive = TRUE)

# ==============================
# 🔹 Model Training Parameters
# ==============================
NUM_CHAINS <- 2      # Number of MCMC chains
NUM_ITER <- 2000     # Total iterations per chain
NUM_WARMUP <- 1000   # Warmup iterations
HS_GLOBAL_SCALE <- 0.1  # Horseshoe prior scale for regularization

# ==============================
# 🔹 Model File Paths
# ==============================
FORCE_MODEL_FILE <- file.path(MODEL_PATH, "force_model.rds")
UPPER_BODY_MODEL_FILE <- file.path(MODEL_PATH, "upper_body_model.rds")
LOWER_BODY_MODEL_FILE <- file.path(MODEL_PATH, "lower_body_model.rds")
FULL_MODEL_FILE <- file.path(MODEL_PATH, "full_model.rds")

# ==============================
# 🔹 Output File Paths
# ==============================
PREDICTIONS_FILE <- file.path(OUTPUT_PATH, "pitch_model_predictions.csv")
EVALUATION_METRICS_FILE <- file.path(OUTPUT_PATH, "model_evaluation_metrics.txt")

# ==============================
# 🔹 Logging Settings
# ==============================
LOG_FILE <- file.path(LOG_PATH, "model_training.log")

# ==============================
# ✅ Configurations Loaded Message
# ==============================
#message("✅ Constants Loaded Successfully.")


