import os

# Root project directory
PROJECT_ROOT = r"C:\\Repos\\NBA_Shot"

# Folder and file structure
structure = {
    "scripts": [
        "create_db.py",
        "create_tables.py",
        "db_connect.py",
        "etl_logger.py",
        "load_players.py",
        "load_teams.py",
        "load_stats.py",
        "load_shots.py",
        "verify_sql.py"
    ],
    "models": [
        "train_rf.py",
        "train_gam.py",
        "train_fnn.py",  # Optional
        "model_eval.py"
    ],
    "app": [
        "sql_observability.py",
        "data_preprocessing.py",
        "feature_engineering.py"
    ],
    "data": [],
    "logs": ["etl.log"],
}

# Create folders and files
for folder, files in structure.items():
    folder_path = os.path.join(PROJECT_ROOT, folder)
    os.makedirs(folder_path, exist_ok=True)
    for file in files:
        file_path = os.path.join(folder_path, file)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                if file.endswith(".py"):
                    f.write(f"# {file}\n")
                elif file.endswith(".log"):
                    f.write("")

# Create top-level files
for top_file in [".gitignore", "requirements.txt", "README.md"]:
    top_file_path = os.path.join(PROJECT_ROOT, top_file)
    if not os.path.exists(top_file_path):
        with open(top_file_path, 'w') as f:
            if top_file == "README.md":
                f.write("# NBA Shot Modeling Project\n")
            else:
                f.write("")

print("✅ NBA Shot project structure created.")
