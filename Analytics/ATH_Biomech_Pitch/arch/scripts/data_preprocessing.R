# ==============================
# 🔹 Load Required Libraries
# ==============================
library(dplyr)
library(readr)
library(missRanger)
library(futile.logger)
library(tidyr)
library(ggplot2)
library(corrplot)

# ==============================
# 🔹 Define File Paths
# ==============================
meta_file <- "data/pitch_meta.csv"
poi_file <- "data/pitch_poi.csv"
output_file <- "outputs/pitch_data_cleaned.csv"
scaling_params_file <- "outputs/scaling_params.rds"

# ==============================
# 🔹 Ensure Files Exist Before Proceeding
# ==============================
if (!file.exists(meta_file) || !file.exists(poi_file)) {
  stop("❌ Error: Missing required data files ('pitch_meta.csv' or 'pitch_poi.csv')!")
}

# ==============================
# 🔹 Read and Merge Data
# ==============================
flog.info("📂 Reading input data...")
pitch_meta <- read_csv(meta_file, show_col_types = FALSE)
pitch_poi <- read_csv(poi_file, show_col_types = FALSE)

# Select relevant metadata columns
pitch_meta_selected <- pitch_meta %>%
  select(session_pitch, user, session_mass_kg, session_height_m, age_yrs, playing_level)

# Merge Metadata with POI Metrics
pitch_data <- pitch_poi %>%
  left_join(pitch_meta_selected, by = "session_pitch")

flog.info("✅ Data merged successfully.")

# ==============================
# 🔹 Check for Missing Values Before Imputation
# ==============================
missing_before <- colSums(is.na(pitch_data))
missing_cols <- names(missing_before[missing_before > 0])

if (length(missing_cols) > 0) {
  flog.warn("⚠️ Columns with missing values before imputation: %s", paste(missing_cols, collapse = ", "))
} else {
  flog.info("✅ No missing values detected before imputation.")
}

# ==============================
# 🔹 Perform Missing Data Imputation
# ==============================
flog.info("🔄 Running Random Forest imputation...")

pitch_data_imputed <- missRanger(
  pitch_data,
  formula = . ~ .,   # Use all variables for imputation
  num.trees = 100,   # Random Forest-based imputation
  pmm.k = 3,
  seed = 123,
  verbose = 2
)

# ==============================
# 🔹 Check for Missing Values After Imputation
# ==============================
missing_after <- colSums(is.na(pitch_data_imputed))
remaining_missing <- names(missing_after[missing_after > 0])

if (length(remaining_missing) > 0) {
  flog.error("❌ Imputation failed! Still missing values in columns: %s", paste(remaining_missing, collapse = ", "))
  stop("❌ Data contains missing values even after imputation!")
} else {
  flog.info("✅ Imputation successful. No missing values remain.")
}

# ==============================
# 🔹 Normality Testing (Shapiro-Wilk)
# ==============================
flog.info("📊 Conducting normality tests...")

normality_results <- sapply(pitch_data_imputed %>% select(where(is.numeric)), function(x) {
  if (length(na.omit(x)) > 3) {  # Ensure enough data for test
    return(shapiro.test(na.omit(x))$p.value)
  } else {
    return(NA)
  }
})

normality_df <- data.frame(Variable = names(normality_results), 
                           P_Value = normality_results) %>%
  mutate(Normal_Distribution = ifelse(P_Value > 0.05, TRUE, FALSE))

flog.info("✅ Normality tests completed.")

# ==============================
# 🔹 Outlier Detection
# ==============================

flog.info("🚨 Detecting outliers...")

# Define Outlier Detection Functions
detect_z_outliers <- function(x) {
  z_scores <- (x - mean(x, na.rm = TRUE)) / sd(x, na.rm = TRUE)
  return(abs(z_scores) > 3)
}

detect_iqr_outliers <- function(x) {
  q1 <- quantile(x, 0.25, na.rm = TRUE)
  q3 <- quantile(x, 0.75, na.rm = TRUE)
  iqr_value <- q3 - q1
  return(x < (q1 - 1.5 * iqr_value) | x > (q3 + 1.5 * iqr_value))
}

# Apply appropriate outlier detection method based on normality
pitch_data_imputed <- pitch_data_imputed %>%
  mutate(across(where(is.numeric), ~ ifelse(
    coalesce(normality_df$Normal_Distribution[match(cur_column(), normality_df$Variable)], FALSE), 
    detect_z_outliers(.), 
    detect_iqr_outliers(.)
  ), .names = "{.col}_outlier"))

# Count Outliers Per Variable
outlier_counts <- colSums(select(pitch_data_imputed, ends_with("_outlier")), na.rm = TRUE)
flog.info("🚨 Outliers detected per variable:")
print(outlier_counts)

# Optional: Filter Rows with Any Outliers
outlier_rows <- pitch_data_imputed %>%
  filter(if_any(ends_with("_outlier"), ~ . == TRUE))

flog.info("🚨 Total rows with outliers: %d", nrow(outlier_rows))

# ==============================
# 🔹 Correlation Analysis & Heatmap
# ==============================
flog.info("📊 Computing correlation matrix...")

numeric_data <- pitch_data_imputed %>% select(where(is.numeric))
cor_matrix <- cor(numeric_data, use = "complete.obs")

# Save Correlation Heatmap
cor_threshold <- 0.2  # Adjust as needed

# Get variables highly correlated with pitch speed
high_corr_vars <- rownames(cor_matrix)[cor_matrix["pitch_speed_mph", ] > cor_threshold | 
                                         cor_matrix["pitch_speed_mph", ] < -cor_threshold]

if (length(high_corr_vars) > 1) {
  png("outputs/correlation_heatmap.png", width = 800, height = 600)
  corrplot(cor_matrix[high_corr_vars, high_corr_vars], method = "color", tl.cex = 0.8, title = "Correlation Heatmap - Pitch Speed")
  dev.off()
  flog.info("✅ Correlation heatmap saved to outputs/correlation_heatmap.png")
}

# ==============================
# 🔹 Save Cleaned Dataset
# ==============================
write.csv(pitch_data_imputed, output_file, row.names = FALSE, quote = FALSE)
flog.info("✅ Cleaned dataset saved successfully to: %s", output_file)

print("✅ Data Preprocessing Completed!")









