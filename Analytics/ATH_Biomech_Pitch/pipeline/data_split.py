import os
import pandas as pd
from sklearn.model_selection import train_test_split
from utils import config

# ------------------------------
# 🔹 Load Final Dataset
# ------------------------------
input_path = os.path.join(config.OUTPUT_PATH, "eda_data", "selected_features.csv")
df = pd.read_csv(input_path)

# ------------------------------
# 🔹 Train/Val/Test Split
# ------------------------------
train_df, temp_df = train_test_split(df, test_size=0.30, random_state=42)
val_df, test_df = train_test_split(temp_df, test_size=0.50, random_state=42)

# ------------------------------
# 🔹 Save Splits to config.DATA_PATH
# ------------------------------
os.makedirs(config.DATA_PATH, exist_ok=True)

train_df.to_csv(os.path.join(config.DATA_PATH, "train.csv"), index=False)
val_df.to_csv(os.path.join(config.DATA_PATH, "val.csv"), index=False)
test_df.to_csv(os.path.join(config.DATA_PATH, "test.csv"), index=False)

print("✅ Data split complete — saved to /data/")




