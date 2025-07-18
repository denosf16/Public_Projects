library(futile.logger)
library(missRanger)
library(readr)
library(dplyr)

# 🔹 Safe CSV Reader (Avoids Errors)
safe_read_csv <- function(filepath) {
  if (file.exists(filepath)) {
    flog.info(paste("📂 Reading file:", filepath))
    read_csv(filepath, show_col_types = FALSE)
  } else {
    flog.error(paste("❌ File not found:", filepath))
    return(NULL)
  }
}

impute_missing_values <- function(df) {
  flog.info("🔄 Running Random Forest Imputation...")
  
  df$imputed_flag <- ifelse(rowSums(is.na(df)) > 0, 1, 0)
  
  missing_before <- colSums(is.na(df))
  missing_before <- missing_before[missing_before > 0]
  
  if (length(missing_before) > 0) {
    flog.warn("⚠️ Columns with missing values before imputation:")
    print(missing_before)
  }
  
  # Run missRanger for imputation (ignoring non-numeric columns)
  df_imputed <- missRanger(
    df,
    formula = . ~ .,  # Use all available features
    pmm.k = 3,  # Predictive mean matching
    num.trees = 100,  # Number of trees for RF
    seed = 123,
    verbose = 2
  )
  
  missing_after <- colSums(is.na(df_imputed))
  missing_after <- missing_after[missing_after > 0]
  
  if (length(missing_after) > 0) {
    flog.error("❌ Imputation failed! Columns still have missing values:")
    print(missing_after)
  } else {
    flog.info("✅ Imputation complete. No missing values remain.")
  }
  
  return(df_imputed)
}

flog.appender(appender.file(file.path(LOG_PATH, "pipeline.log")))

test_helpers <- function() {
  flog.info("✅ Testing safe_read_csv()")
  df <- safe_read_csv(file.path(OUTPUT_PATH, "pitch_data_cleaned.csv"))
  print(head(df, 5))
  
  flog.info("✅ Testing impute_missing_values()")
  df_imputed <- impute_missing_values(df)
  print(head(df_imputed, 5))
}

