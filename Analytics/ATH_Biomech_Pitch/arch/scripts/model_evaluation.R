# ==============================
# 🔹 Load Required Libraries
# ==============================
library(ggplot2)
library(readr)
library(dplyr)
library(Metrics)   # For RMSE, MAE
library(caret)     # For R² calculation
library(futile.logger)

# ==============================
# 🔹 Define File Paths
# ==============================
predictions_file <- "outputs/pitch_model_predictions.csv"
plots_dir <- "outputs/plots"
metrics_file <- "outputs/model_evaluation_metrics.txt"

# Ensure output directory exists
if (!dir.exists(plots_dir)) {
  dir.create(plots_dir, recursive = TRUE)
}

# ==============================
# 🔹 Load Predictions
# ==============================
flog.info("📂 Loading predictions dataset...")
predictions <- read_csv(predictions_file, show_col_types = FALSE)

# Define expected columns
required_columns <- c("session_pitch", "pitch_speed_mph", 
                      "Force_pred_pitch_speed", "Upper_Body_pred_pitch_speed",
                      "Lower_Body_pred_pitch_speed", "Full_pred_pitch_speed")

# Check for missing columns
missing_columns <- setdiff(required_columns, colnames(predictions))

if (length(missing_columns) > 0) {
  print("❌ Missing columns in predictions dataset:")
  print(missing_columns)
  stop("❌ Error: Some expected columns are missing.")
} else {
  print("✅ All required columns are present.")
}

# ==============================
# 🔹 Define Metrics Calculation Function
# ==============================
calculate_metrics <- function(actual, predicted) {
  rmse_val <- rmse(actual, predicted)
  mae_val <- mae(actual, predicted)
  r2_val <- R2(predicted, actual)
  
  return(data.frame(RMSE = rmse_val, MAE = mae_val, R2 = r2_val))
}

# ==============================
# 🔹 Compute Model Evaluation Metrics
# ==============================
flog.info("📊 Calculating evaluation metrics for each model...")

metrics <- list(
  Force_Model = calculate_metrics(predictions$pitch_speed_mph, predictions$Force_pred_pitch_speed),
  Upper_Body_Model = calculate_metrics(predictions$pitch_speed_mph, predictions$Upper_Body_pred_pitch_speed),
  Lower_Body_Model = calculate_metrics(predictions$pitch_speed_mph, predictions$Lower_Body_pred_pitch_speed),
  Full_Model = calculate_metrics(predictions$pitch_speed_mph, predictions$Full_pred_pitch_speed)
)

# Combine into a single DataFrame
metrics_df <- do.call(rbind, metrics)
metrics_df$model <- rownames(metrics_df)
rownames(metrics_df) <- NULL

# Save Metrics
write.table(metrics_df, metrics_file, row.names = FALSE, sep = "\t", quote = FALSE)
flog.info(paste("✅ Model evaluation metrics saved to:", metrics_file))

# Print Metrics
print("✅ Model Evaluation Metrics:")
print(metrics_df)

# ==============================
# 🔹 Function to Generate & Save Plots
# ==============================
plot_predictions <- function(predictions, model_name, model_column) {
  # Scatter Plot: Actual vs. Predicted
  p1 <- ggplot(predictions, aes(x = pitch_speed_mph, y = .data[[model_column]])) +
    geom_point(alpha = 0.7, color = "blue") +
    geom_abline(slope = 1, intercept = 0, linetype = "dashed", color = "red") +
    labs(title = paste(model_name, "- Actual vs Predicted Pitch Speed"),
         x = "Actual Pitch Speed (mph)", y = "Predicted Pitch Speed (mph)")
  
  # Residual Plot
  p2 <- ggplot(predictions, aes(x = .data[[model_column]], y = pitch_speed_mph - .data[[model_column]])) +
    geom_point(alpha = 0.7, color = "blue") +
    geom_hline(yintercept = 0, linetype = "dashed", color = "red") +
    labs(title = paste(model_name, "- Residuals vs Predicted Pitch Speed"),
         x = "Predicted Pitch Speed (mph)", y = "Residual (Actual - Predicted)")
  
  # Ensure output directory exists
  if (!dir.exists(plots_dir)) {
    dir.create(plots_dir, recursive = TRUE)
  }
  
  # Save the plots
  ggsave(filename = file.path(plots_dir, paste0(model_name, "_actual_vs_predicted.png")), plot = p1, width = 6, height = 5, dpi = 300)
  ggsave(filename = file.path(plots_dir, paste0(model_name, "_residuals.png")), plot = p2, width = 6, height = 5, dpi = 300)
  
  flog.info("✅ %s plots saved successfully in outputs/plots/", model_name)
  
  return(list(p1 = p1, p2 = p2))  # Return plots for debugging if needed
}

# ==============================
# 🔹 Generate and Save Plots for Each Model
# ==============================
flog.info("📊 Generating evaluation plots...")

plot_predictions(predictions, "Force_Model", "Force_pred_pitch_speed")
plot_predictions(predictions, "Upper_Body_Model", "Upper_Body_pred_pitch_speed")
plot_predictions(predictions, "Lower_Body_Model", "Lower_Body_pred_pitch_speed")
plot_predictions(predictions, "Full_Model", "Full_pred_pitch_speed")

flog.info("🎉 Model evaluation completed successfully!")
print("✅ Model evaluation and plots generation completed!")


