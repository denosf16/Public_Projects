import os

# ==============================
# 🔹 Base Path Configuration
# ==============================
ROOT_DIR = r"C:\Repos\ATH_PIT"

DATA_PATH = os.path.join(ROOT_DIR, "data")
OUTPUT_PATH = os.path.join(ROOT_DIR, "outputs")
MODEL_PATH = os.path.join(ROOT_DIR, "models")
PLOTS_PATH = os.path.join(OUTPUT_PATH, "plots")
LOG_PATH = os.path.join(OUTPUT_PATH, "logs")  # unused for now

# ==============================
# 🔹 Ensure Folders Exist
# ==============================
for path in [DATA_PATH, OUTPUT_PATH, MODEL_PATH, PLOTS_PATH]:
    os.makedirs(path, exist_ok=True)

# ==============================
# 🔹 Model Training Parameters
# ==============================
NUM_CHAINS = 2
NUM_ITER = 2000
NUM_WARMUP = 1000
HS_GLOBAL_SCALE = 0.1  # For reference, if we use PyMC or similar later

# ==============================
# 🔹 File Paths
# ==============================
FORCE_MODEL_FILE = os.path.join(MODEL_PATH, "force_model.pkl")
UPPER_BODY_MODEL_FILE = os.path.join(MODEL_PATH, "upper_body_model.pkl")
LOWER_BODY_MODEL_FILE = os.path.join(MODEL_PATH, "lower_body_model.pkl")
FULL_MODEL_FILE = os.path.join(MODEL_PATH, "full_model.pkl")

PREDICTIONS_FILE = os.path.join(OUTPUT_PATH, "pitch_model_predictions.csv")
EVALUATION_METRICS_FILE = os.path.join(OUTPUT_PATH, "model_evaluation_metrics.txt")

# ==============================
# 🔹 Config Load Check (Optional)
# ==============================
if __name__ == "__main__":
    print("✅ Configuration loaded.")

