# ============================================
# 📉 FINAL LA MODEL EVALUATION (UPDATED & BULLETPROOFED)
# ============================================

# 🔹 Load Required Libraries & Helpers
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/constants.R")
source("C:/Repos/Athlyticz_Projects/ATH_Biomech_Hit/Model/scripts/helpers.R")
library(rstanarm)
library(bayesplot)
library(ggplot2)
library(dplyr)
library(caret)
library(Metrics)

log_message("🚀 Starting Final LA Model Evaluation (Unscaled)...", LOG_FILE_LA)

# 🔹 Paths
base_model_path <- file.path(OUTPUTS_LA, "base_la_model.rds")
adv_model_path <- file.path(OUTPUTS_LA, "advanced_la_model.rds")
preds_path <- file.path(OUTPUTS_LA, "la_predictions_test.csv")
test_la_path <- file.path(OUTPUTS_LA, "test_la_scaled.csv")  # ✅ Full test features for PPC
metrics_file <- file.path(OUTPUTS_LA, "la_model_test_metrics.txt")
plots_dir <- file.path(OUTPUTS_LA, "plots")
if (!dir.exists(plots_dir)) dir.create(plots_dir, recursive = TRUE)

# 🔹 Load Test Predictions
la_csv_preds <- read.csv(preds_path)
log_message("✅ Test Predictions Loaded Successfully.", LOG_FILE_LA)

# ✅ Align Column References
la_csv_preds <- la_csv_preds %>%
  mutate(
    actual_unscaled = la,
    base_pred_unscaled = Base_LA_pred_LA,
    adv_pred_unscaled = Advanced_LA_pred_LA
  )

# ============================================
# 📊 Evaluation Metrics
# ============================================
calculate_metrics <- function(actual, predicted) {
  if (sd(actual, na.rm = TRUE) < 1e-5) {
    warning("⚠Low variance in actuals. R² will be NA.")
    r2 <- NA
  } else {
    r2 <- caret::R2(predicted, actual, form = "traditional")
  }
  data.frame(RMSE = rmse(actual, predicted), MAE = mae(actual, predicted), R2 = r2)
}

metrics_df <- bind_rows(
  calculate_metrics(la_csv_preds$actual_unscaled, la_csv_preds$base_pred_unscaled) %>% mutate(model = "Base_Model_Test"),
  calculate_metrics(la_csv_preds$actual_unscaled, la_csv_preds$adv_pred_unscaled) %>% mutate(model = "Advanced_Model_Test")
)

plot(y= la_csv_preds$actual_unscaled, x=la_csv_preds$base_pred_unscaled)

write.table(metrics_df, metrics_file, row.names = FALSE, sep = "\t", quote = FALSE)
print("✅ FINAL TEST SET EVALUATION METRICS (UNSCALED):")
print(metrics_df)

# ============================================
# 📌 Bayesian Diagnostics - Trace Plots
# ============================================
base_la_model <- readRDS(base_model_path)
advanced_la_model <- readRDS(adv_model_path)

if (!inherits(base_la_model, "stanreg")) stop("❌ base_la_model is not a stanreg model!")
if (!inherits(advanced_la_model, "stanreg")) stop("❌ advanced_la_model is not a stanreg model!")

for (model in list(base_la_model, advanced_la_model)) {
  model_name <- ifelse(identical(model, base_la_model), "base", "advanced")
  valid_params <- dimnames(as.array(model))[[3]]
  non_user_params <- valid_params[!grepl("^s\\(user", valid_params)]
  
  for (param in non_user_params) {
    trace_plot_path <- file.path(plots_dir, paste0("trace_", model_name, "_", param, ".png"))
    trace_plot <- mcmc_trace(as.array(model), pars = param) + PLOT_THEME
    ggsave(trace_plot_path, plot = trace_plot, width = 6, height = 5, dpi = 300)
    
    if (file.exists(trace_plot_path) && file.info(trace_plot_path)$size < 50 * 1024) {
      log_message(paste("⚠️ Trace plot small or incomplete:", trace_plot_path), LOG_FILE_LA)
    }
  }
}

# ============================================
# 📌 Posterior Predictive Checks (SAFE & FIXED)
# ============================================
run_ppc_plot <- function(model, model_name, newdata) {
  if (!inherits(model, "stanreg")) stop(paste("❌", model_name, "is not a stanreg model"))
  log_message(paste("📌 Running PPC for", model_name), LOG_FILE_LA)
  
  yrep <- posterior_predict(model, newdata = newdata)
  if (ncol(yrep) != nrow(newdata)) stop("❌ ncol(yrep) does not match test set! Check newdata columns.")
  
  ppc_plot <- bayesplot::ppc_dens_overlay(y = la_csv_preds$actual_unscaled, yrep = yrep) + PLOT_THEME
  ggsave(file.path(plots_dir, paste0(model_name, "_la_pp_check.png")), plot = ppc_plot, width = 6, height = 5, dpi = 300)
}

test_la_full <- read.csv(test_la_path)
run_ppc_plot(base_la_model, "base", test_la_full)
run_ppc_plot(advanced_la_model, "advanced", test_la_full)

# ============================================
# 📌 Residuals & Scatterplots
# ============================================
la_csv_preds <- la_csv_preds %>%
  mutate(
    base_resid = actual_unscaled - base_pred_unscaled,
    adv_resid = actual_unscaled - adv_pred_unscaled
  )

for (model in c("base", "adv")) {
  # Scatter Plot
  scatter <- ggplot(la_csv_preds, aes_string(x = "actual_unscaled", y = paste0(model, "_pred_unscaled"))) +
    geom_point(alpha = PLOT_ALPHA, color = "#4682B4") +
    geom_abline(slope = 1, intercept = 0, color = "red", linetype = "dashed") +
    labs(title = paste("Actual vs Predicted (", toupper(model), " LA Model)"),
         x = "Actual LA", y = "Predicted LA") +
    PLOT_THEME
  
  ggsave(file.path(plots_dir, paste0("scatter_actual_vs_pred_", model, "_la.png")), plot = scatter, width = 7, height = 5, dpi = 300)
  
  # Residuals vs Fitted
  resid_plot <- ggplot(la_csv_preds, aes_string(x = paste0(model, "_pred_unscaled"), y = paste0(model, "_resid"))) +
    geom_point(alpha = PLOT_ALPHA, color = "#4682B4") +
    geom_hline(yintercept = 0, color = "red", linetype = "dashed") +
    labs(title = paste("Residuals vs Fitted (", toupper(model), " LA Model)"),
         x = "Fitted LA", y = "Residuals") +
    PLOT_THEME
  
  ggsave(file.path(plots_dir, paste0("residuals_vs_fitted_", model, "_la.png")), plot = resid_plot, width = 7, height = 5, dpi = 300)
}

log_message("🎯 FINAL LA Model Test Set Evaluation Completed Successfully!", LOG_FILE_LA)
print("🎯 FINAL LA Model Test Set Evaluation Completed Successfully!")



