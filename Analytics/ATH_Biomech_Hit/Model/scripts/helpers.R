# -----------------------------
# 🔧 HELPER FUNCTIONS (FULL VERSION)
# -----------------------------

# ✅ Load Required Libraries
library(dplyr)
library(ggplot2)
library(reshape2)
library(corrplot)
library(minerva)  # MIC computation
library(Hmisc)  # Pearson correlation matrix
library(randomForest)  # Feature importance
library(xgboost)  # Model training
library(ParBayesianOptimization)  # Bayesian Optimization
library(openxlsx)  # Excel file handling
library(caret)  # Train-test split
library(car)  # VIF calculations (used in feature selection)
library(shapr)  # SHAP feature importance
library(iml)  # SHAP Feature Importance

# ✅ Load Constants (Ensures Directory Paths & Parameters are Available)
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/constants.R")

# 🎨 Define Plot Theme
PLOT_THEME <- theme_minimal()

# -----------------------------
# 📥 File Handling & Logging
# -----------------------------

# 📩 Function: Log Messages with Separate Logs for EV & LA
log_message <- function(message, log_file) {
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  log_entry <- paste0("[", timestamp, "] ", message, "\n")
  
  con <- file(log_file, open = "a")
  writeLines(log_entry, con)
  close(con)
}

# 📥 Function: Download File if Missing
download_if_missing <- function(url, destfile, log_file) {
  if (!file.exists(destfile)) {
    log_message(paste("⬇️ Downloading:", url, "to", destfile), log_file)
    tryCatch(
      {
        download.file(url, destfile, mode = "wb")
        log_message(paste("✔ Successfully downloaded:", destfile), log_file)
      },
      error = function(e) {
        log_message(paste("❌ Error downloading:", url, "-", e$message), log_file)
      }
    )
  } else {
    log_message(paste("✔ File already exists:", destfile), log_file)
  }
}

# -----------------------------
# 🔄 Data Cleaning & Preprocessing
# -----------------------------

# 🔎 Function: Identify Missing Values
count_missing_values <- function(df) {
  missing_vals <- colSums(is.na(df))
  return(missing_vals[missing_vals > 0])  # Return only columns with missing values
}

# 🔄 Function: Restore Clean Column Names
restore_column_names <- function(df) {
  colnames(df) <- gsub("\\.x$", "", colnames(df))  # Remove `.x` suffix from duplicate columns
  colnames(df) <- gsub("\\.y$", "", colnames(df))  # Remove `.y` suffix from duplicate columns
  return(df)
}

# 🔄 Function: Impute Missing Values (Numerical: Median, Categorical: Mode)
impute_missing_values <- function(df) {
  for (col in colnames(df)) {
    if (is.numeric(df[[col]])) {
      df[[col]][is.na(df[[col]])] <- median(df[[col]], na.rm = TRUE)
    } else if (is.factor(df[[col]]) || is.character(df[[col]])) {
      df[[col]][is.na(df[[col]])] <- as.character(stats::names(sort(table(df[[col]]), decreasing = TRUE)[1]))
    }
  }
  return(df)
}

# 🔄 Function: Normalize Numeric Data
normalize_features <- function(df, feature_list) {
  for (feature in feature_list) {
    if (feature %in% colnames(df)) {
      df[[paste0(feature, "_scaled")]] <- scale(df[[feature]])
    }
  }
  return(df)
}

# 📥 Function: Standard Train-Test Split Using `TRAIN_SPLIT`
generate_train_test_split <- function(df, target_var) {
  set.seed(42)
  train_index <- caret::createDataPartition(df[[target_var]], p = TRAIN_SPLIT, list = FALSE)
  train_df <- df[train_index, ]
  test_df <- df[-train_index, ]
  return(list(train = train_df, test = test_df))
}

# -----------------------------
# 🔍 Feature Selection & Model Training
# -----------------------------

compute_shap_importance <- function(model, x_train_df) {
  # ✅ Ensure Data is in Correct Format
  x_train_df <- as.data.frame(as.matrix(x_train_df))  # Ensure DataFrame format
  
  # ✅ Define Prediction Function
  predict_function <- function(model, newdata) {
    predict(model, as.matrix(newdata))
  }
  
  # ✅ Create `iml` Predictor Object
  predictor <- Predictor$new(
    model = model,
    data = x_train_df,  # Ensure DataFrame format
    predict.function = predict_function
  )
  
  # ✅ Compute SHAP Values (Subset for Performance)
  shapley <- Shapley$new(predictor, x_train_df[1:50, ])  
  
  # ✅ Extract Mean Absolute SHAP Importance
  shap_df <- as.data.frame(shapley$results)  
  shap_importance <- aggregate(abs(phi) ~ feature, data = shap_df, mean)  
  colnames(shap_importance) <- c("feature", "mean_shap")
  
  # ✅ Convert SHAP Data Frame to Named Numeric Vector (Prevents `xtfrm` Sorting Error)
  shap_vector <- setNames(shap_importance$mean_shap, shap_importance$feature)
  
  return(shap_vector)  # ✅ Return as a Named Numeric Vector
}



# 🔍 Function: Remove High VIF Features (Fixes Aliased Variables & `(Intercept)`)
remove_high_vif_features <- function(df, target_var, threshold = 10) {
  print("🔍 Checking for Aliased Variables Before Running VIF...")
  
  # ✅ Detect Aliased Variables (Perfect Multicollinearity)
  alias_info <- alias(lm(as.formula(paste(target_var, "~ .")), data = df))
  
  if (!is.null(alias_info$Complete)) {
    aliased_vars <- colnames(alias_info$Complete)
    
    # 🚨 Remove `(Intercept)` if it exists
    aliased_vars <- setdiff(aliased_vars, "(Intercept)")
    
    if (length(aliased_vars) > 0) {
      print("🚨 Identified Aliased Variables (Perfectly Collinear):")
      print(aliased_vars)
      
      # ✅ Drop Aliased Variables (Ensuring they exist before selecting)
      aliased_vars <- aliased_vars[aliased_vars %in% colnames(df)]
      
      if (length(aliased_vars) > 0) {
        df <- df %>% select(-all_of(aliased_vars))
        print(paste("✅ Removed", length(aliased_vars), "aliased variables before VIF calculation."))
      } else {
        print("✅ No valid aliased variables to remove. Proceeding with VIF Calculation.")
      }
    } else {
      print("✅ No Aliased Variables Found. Proceeding with VIF Calculation.")
    }
  } else {
    print("✅ No Aliased Variables Found. Proceeding with VIF Calculation.")
  }
  
  # ✅ Compute Initial VIF
  vif_results <- tryCatch({
    car::vif(lm(as.formula(paste(target_var, "~ .")), data = df))
  }, error = function(e) {
    print("🚨 VIF Calculation Failed. There may still be aliased variables.")
    print(e)
    return(NULL)
  })
  
  if (is.null(vif_results)) {
    print("🚨 Skipping VIF Feature Selection Due to Errors.")
    return(df)  # Return original data if VIF fails
  }
  
  print("📊 Initial VIF Values:")
  print(vif_results)
  
  # 🔄 Iteratively Remove High-VIF Features
  while (max(vif_results) > threshold) {
    worst_feature <- names(which.max(vif_results))
    print(paste("🚨 Removing High-VIF Feature:", worst_feature, "VIF =", round(max(vif_results), 2)))
    
    df <- df %>% select(-all_of(worst_feature))  # Remove the worst feature
    vif_results <- tryCatch({
      car::vif(lm(as.formula(paste(target_var, "~ .")), data = df))
    }, error = function(e) {
      print("🚨 VIF Calculation Failed During Iteration.")
      print(e)
      return(NULL)
    })
    
    if (is.null(vif_results)) {
      break  # Stop iteration if VIF fails
    }
  }
  
  print("✅ VIF Calculation Completed Successfully!")
  return(df)
}



# 🔍 Function: Run Bayesian Hyperparameter Optimization Using `XGB_TUNING_PARAMS`
run_bayesian_optimization <- function(x_train, target_var, iterations = 20, init_points = 10) {
  scoring_function <- function(eta, max_depth, gamma, colsample_bytree, min_child_weight, subsample) {
    params <- list(
      booster = "gbtree",
      eta = eta,
      max_depth = round(max_depth),  # ✅ FIX: Round before passing to XGBoost
      gamma = gamma,
      colsample_bytree = colsample_bytree,
      min_child_weight = round(min_child_weight),  # ✅ FIX: Round before passing to XGBoost
      subsample = subsample,
      objective = "reg:squarederror",
      eval_metric = "rmse"
    )
    
    xgb_cv <- xgboost::xgb.cv(
      params = params,
      data = x_train,
      nrounds = 250,
      nfold = 5,
      early_stopping_rounds = 20,
      verbose = 0
    )
    
    list(Score = -min(xgb_cv$evaluation_log$test_rmse_mean))
  }
  
  bayes_opt_results <- ParBayesianOptimization::bayesOpt(
    FUN = scoring_function,
    bounds = XGB_TUNING_PARAMS,  # **Uses Constants Instead of Hardcoding**
    initPoints = init_points,
    iters.n = iterations
  )
  
  # ✅ Ensure `max_depth` and `min_child_weight` are integers before returning
  best_params <- ParBayesianOptimization::getBestPars(bayes_opt_results)
  best_params$max_depth <- as.integer(best_params$max_depth)  # ✅ Enforce integer type
  best_params$min_child_weight <- as.integer(best_params$min_child_weight)  # ✅ Enforce integer type
  return(best_params)
}


# 🔥 Function: Train XGBoost Model
train_xgboost_model <- function(x_train, target_var, best_params, num_rounds = 250) {
  xgb_model <- xgboost::xgboost(
    data = x_train,
    objective = "reg:squarederror",
    nrounds = num_rounds,
    max_depth = round(best_params$max_depth),  # ✅ Ensure integer type
    eta = best_params$eta,
    gamma = best_params$gamma,
    colsample_bytree = best_params$colsample_bytree,
    min_child_weight = round(best_params$min_child_weight),  # ✅ Ensure integer type
    subsample = best_params$subsample,
    early_stopping_rounds = 20,
    eval_metric = "rmse"
  )
  
  return(xgb_model)
}


# -----------------------------
# 📈 Model Evaluation
# -----------------------------

# 📉 Function: Evaluate Model Performance
evaluate_model_performance <- function(model, x_train, x_test, y_train, y_test) {
  train_preds <- predict(model, x_train)
  test_preds <- predict(model, x_test)
  
  train_rmse <- sqrt(mean((train_preds - y_train)^2))
  test_rmse <- sqrt(mean((test_preds - y_test)^2))
  train_r2 <- cor(train_preds, y_train)^2
  test_r2 <- cor(test_preds, y_test)^2
  train_mae <- mean(abs(train_preds - y_train))
  test_mae <- mean(abs(test_preds - y_test))
  
  return(data.frame(
    Metric = c("RMSE", "R²", "MAE"),
    Train = c(train_rmse, train_r2, train_mae),
    Test = c(test_rmse, test_r2, test_mae)
  ))
}

# 🎨 Consistent Plot Wrapper for All ggplots
create_consistent_plot <- function(plot_obj, title = NULL, x_label = NULL, y_label = NULL) {
  plot_obj +
    PLOT_THEME +
    theme(
      plot.background = element_rect(fill = "white", color = NA),
      panel.grid.major = element_line(color = "grey80"),
      panel.grid.minor = element_line(color = "grey90"),
      axis.title = element_text(size = 12, face = "bold"),
      axis.text = element_text(size = 10),
      plot.title = element_text(size = 14, face = "bold", hjust = 0.5)
    ) +
    labs(title = title, x = x_label, y = y_label)
}


# ✅ Final Confirmation
print("✅ Helper Functions Updated & Loaded Successfully!")




