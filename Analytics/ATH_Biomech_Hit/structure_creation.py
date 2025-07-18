import os

def create_project_structure(base_path):
    directories = [
        "data",
        "EDA",
        "Model/scripts",
        "outputs/models",
        "outputs/plots",
        "outputs/logs",
        "outputs/predictions",
        "reports",
        "DataViz"
    ]
    
    for directory in directories:
        os.makedirs(os.path.join(base_path, directory), exist_ok=True)
    
    print("✅ Directories created successfully!")

def create_r_scripts(base_path):
    scripts = {
        "Model/scripts/constants.R": "# Constants and global variables\n",
        "Model/scripts/helpers.R": "# Helper functions\n",
        "Model/scripts/data_preprocessing.R": "# Data cleaning and preprocessing\n",
        "Model/scripts/feature_selection.R": "# Feature selection and engineering\n",
        "Model/scripts/train_LA_EV_models.R": "# Train Launch Angle & Exit Velocity models\n",
        "Model/scripts/train_wOBA_model.R": "# Train final wOBA model\n",
        "Model/scripts/model_evaluation_LA_EV.R": "# Evaluate LA & EV models\n",
        "Model/scripts/model_evaluation_wOBA.R": "# Evaluate wOBA model\n",
        "Model/scripts/predict_LA_EV.R": "# Predict using LA & EV models\n",
        "Model/scripts/predict_wOBA.R": "# Predict using wOBA model\n",
        "Model/scripts/run_pipeline.R": "# Master script to run everything in order\n"
    }
    
    for script, content in scripts.items():
        script_path = os.path.join(base_path, script)
        with open(script_path, "w") as file:
            file.write(content)
    
    print("✅ R scripts created successfully!")

if __name__ == "__main__":
    base_path = "C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit"
    create_project_structure(base_path)
    create_r_scripts(base_path)
    print("🎯 Project setup complete!")
