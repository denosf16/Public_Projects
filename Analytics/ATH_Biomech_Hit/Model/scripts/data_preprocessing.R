# -----------------------------------
# 🏗️ DATA PREPROCESSING SCRIPT (Final Fix)
# -----------------------------------

# ✅ Load Constants & Helper Functions
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/constants.R")
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/helpers.R")

# ✅ Load Required Libraries
library(dplyr)
library(stringr)
library(naniar)       # Missing data visualization
library(missRanger)   # Random Forest Imputation
library(VIM)          # KNN Imputation
library(ggplot2)      # For saving plots

# ✅ Ensure Necessary Directories Exist
dirs_to_create <- c(DATA_PATH, LOGS_EV, LOGS_LA, OUTPUTS_EV, OUTPUTS_LA)
lapply(dirs_to_create, dir.create, recursive = TRUE, showWarnings = FALSE)

# ✅ Initialize Log Files
log_ev <- file.path(LOGS_EV, "ev_pipeline_log.txt")
log_la <- file.path(LOGS_LA, "la_pipeline_log.txt")

log_message("🚀 Data preprocessing pipeline started...", log_ev)
log_message("🚀 Data preprocessing pipeline started...", log_la)

# 📥 Load Data (Ensure files exist, else download)
download_if_missing(RAW_METADATA_CSV, METADATA_CSV, log_ev)
download_if_missing(RAW_POI_CSV, POI_CSV, log_ev)
download_if_missing(RAW_HITTRAX_CSV, HITTRAX_CSV, log_ev)

log_message("📥 Loading datasets from DATA_PATH...", log_ev)

# ✅ Read CSV Files
hitter_metadata <- read.csv(METADATA_CSV, na.strings = c("", "NA"))
hitter_poi <- read.csv(POI_CSV, na.strings = c("", "NA"))
hitter_hittrax <- read.csv(HITTRAX_CSV, na.strings = c("", "NA"))

# 🔍 Log Dataset Row Counts
log_message(paste("📊 Metadata rows:", nrow(hitter_metadata)), log_ev)
log_message(paste("📊 POI rows:", nrow(hitter_poi)), log_ev)
log_message(paste("📊 HitTrax rows:", nrow(hitter_hittrax)), log_ev)

# 🔄 Convert `session_swing` to Character (Ensure Consistency)
hitter_metadata[[SESSION_KEY]] <- as.character(hitter_metadata[[SESSION_KEY]])
hitter_poi[[SESSION_KEY]] <- as.character(hitter_poi[[SESSION_KEY]])
hitter_hittrax[[SESSION_KEY]] <- as.character(hitter_hittrax[[SESSION_KEY]])

# 🔗 Merge Datasets on `session_swing`
log_message("🔗 Merging datasets...", log_ev)
hitter_combined <- hitter_metadata %>%
  full_join(hitter_poi, by = SESSION_KEY) %>%
  full_join(hitter_hittrax, by = SESSION_KEY) %>%
  arrange(!!sym(SESSION_KEY))

# 🛠️ **Fix Duplicate Column Names**
log_message("🧼 Cleaning up column names...", log_ev)
hitter_combined <- restore_column_names(hitter_combined)


# 🔥 Remove Duplicate Columns & Rows
log_message("🧹 Removing duplicate columns & rows...", log_ev)
hitter_combined <- hitter_combined[, !duplicated(as.list(hitter_combined))]
hitter_combined <- hitter_combined[!duplicated(hitter_combined), ]  # Remove duplicate rows

# 🛠️ Log Data Types
log_message("🛠️ Checking data types...", log_ev)
data_types <- data.frame(
  Variable = names(hitter_combined),
  Data_Type = sapply(hitter_combined, class)
)
write.csv(data_types, file.path(DATA_PATH, "data_types.csv"), row.names = FALSE)

# 📉 Count Missing Values
log_message("📉 Counting missing values...", log_ev)
missing_values <- colSums(is.na(hitter_combined))
missing_values <- missing_values[missing_values > 0]  # Only keep missing ones

if (length(missing_values) == 0) {
  log_message("✅ No missing values detected! Skipping imputation.", log_ev)
} else {
  log_message(paste0("🚨 Missing Values Detected in ", length(missing_values), " Columns!"), log_ev)
  print(missing_values)  # 🛠️ Debugging
  
  write.csv(data.frame(Feature = names(missing_values), Missing_Count = missing_values),
            file.path(DATA_PATH, "missing_values.csv"), row.names = FALSE)
  
  # 🎯 Identify Numeric Features for Imputation
  numeric_vars <- names(hitter_combined)[sapply(hitter_combined, is.numeric)]
  numeric_vars <- setdiff(numeric_vars, c(TARGET_EV, TARGET_LA))  # Exclude target variables
  
  # 🔍 Debugging: Print numeric columns with missing values
  missing_numeric <- colSums(is.na(hitter_combined[numeric_vars]))
  missing_numeric <- missing_numeric[missing_numeric > 0]
  print(missing_numeric)  # 🛠️ This should print columns with NAs
  
  # 🔄 **Perform Random Forest Imputation (NO FORMULA)**
  log_message("🌲 Performing Random Forest Imputation...", log_ev)
  
  hitter_combined_imputed <- missRanger(
    data = hitter_combined,
    num.trees = 200,  # ✅ Increased for better results
    seed = 42,
    verbose = 1
  )
  
  # ✅ Validate Imputation
  log_message("✅ Checking missing values post-imputation...", log_ev)
  post_impute_missing <- colSums(is.na(hitter_combined_imputed))
  remaining_missing <- post_impute_missing[post_impute_missing > 0]
  
  if (length(remaining_missing) > 0) {
    log_message("🚨 Some missing values remain after imputation! Manually imputing...", log_ev)
    print("🚨 Some missing values remain post-imputation!")
    print(remaining_missing)
    
    # 🔄 Manually Impute Any Remaining Missing Values
    for (col in names(remaining_missing)) {
      if (is.numeric(hitter_combined_imputed[[col]])) {
        hitter_combined_imputed[[col]][is.na(hitter_combined_imputed[[col]])] <- median(hitter_combined_imputed[[col]], na.rm = TRUE)
        log_message(paste0("🔄 Manually imputed ", col, " with median value."), log_ev)
      }
    }
  } else {
    log_message("✅ All missing values successfully imputed!", log_ev)
  }
  
  write.csv(data.frame(Feature = names(post_impute_missing), Missing_Count = post_impute_missing),
            file.path(DATA_PATH, "post_imputation_missing_values.csv"), row.names = FALSE)
  
  # 📊 Save Summary Statistics Pre & Post Imputation
  log_message("📈 Saving summary statistics...", log_ev)
  pre_impute_summary <- summary(hitter_combined[numeric_vars])
  post_impute_summary <- summary(hitter_combined_imputed[numeric_vars])
  
  write.csv(pre_impute_summary, file.path(DATA_PATH, "pre_imputation_summary.csv"), row.names = TRUE)
  write.csv(post_impute_summary, file.path(DATA_PATH, "post_imputation_summary.csv"), row.names = TRUE)
  
  # 🎨 Save Missing Data Plot
  log_message("📊 Generating missing data plot...", log_ev)
  missing_plot <- vis_miss(hitter_combined_imputed) +
    ggtitle("Missing Data Visualization") +
    theme_minimal()
  
  ggsave(filename = file.path(OUTPUTS_EV, "missing_data_plot.png"), plot = missing_plot, width = 10, height = 6)
  log_message("📊 Missing data plot saved.", log_ev)
}

# 💾 Save Processed Data
CLEANED_DATA_PATH <- file.path(DATA_PATH, "hitter_combined_cleaned.csv")
log_message("💾 Saving processed data...", log_ev)
write.csv(hitter_combined_imputed, CLEANED_DATA_PATH, row.names = FALSE)

log_message(paste0("✅ Data Preprocessing Completed! File saved at: ", CLEANED_DATA_PATH), log_ev)
print(paste0("✅ Data Preprocessing Completed! File saved at: ", CLEANED_DATA_PATH))





