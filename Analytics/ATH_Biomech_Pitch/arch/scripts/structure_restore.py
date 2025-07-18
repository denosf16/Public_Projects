import os

# Define the base directory
base_dir = r"C:\Repos\Athlyticz_Projects\ATH_Biomech_Pitch"

# Define the directory structure
directories = [
    "data",
    "Data Viz",
    "EDA",
    "MISC",
    "Model",
    "Model/archive",
    "outputs",
    "outputs/logs",
    "outputs/models",
    "outputs/plots",
    "outputs/predictions",
    "reports",
    "scripts"
]

# Define the files to recreate
files = [
    "data/pitch_meta.csv",
    "data/pitch_poi.csv",
    "outputs/model_evaluation_metrics.txt",
    "outputs/pitch_data_cleaned.csv",
    "outputs/pitch_model_predictions.csv",
    "outputs/scaling_params.rds",
    "outputs/logs/pipeline.log",
    "outputs/models/force_model.rds",
    "outputs/models/full_model.rds",
    "outputs/models/lower_body_model.rds",
    "outputs/models/upper_body_model.rds",
    "outputs/plots/actual_vs_predicted.png",
    "outputs/plots/residuals.png",
    "outputs/predictions/pitch_model_predictions.csv",
    "outputs/predictions/pitch_model_predictions_unscaled.csv",
    "reports/Initial_Pitch_Models.Rmd",
    "scripts/calibrate_model.R",
    "scripts/constants.R",
    "scripts/data_preprocessing.R",
    "scripts/feature_selection.R",
    "scripts/helpers.R",
    "scripts/model_evaluation.R",
    "scripts/predict.R",
    "scripts/run_pipeline.R",
    "scripts/train_model.R"
]

# Recreate the directories
for directory in directories:
    os.makedirs(os.path.join(base_dir, directory), exist_ok=True)

# Recreate the files
for file in files:
    file_path = os.path.join(base_dir, file)
    with open(file_path, 'w') as f:
        pass  # Create an empty file

print("✅ All missing directories and files have been recreated.")
