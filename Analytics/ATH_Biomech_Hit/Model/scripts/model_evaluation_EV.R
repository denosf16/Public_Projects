# ============================================
# 📉 FINAL EV MODEL EVALUATION (UPDATED & BULLETPROOFED)
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

log_message("🚀 Starting Final EV Model Evaluation (Unscaled)...", LOG_FILE_EV)

# 🔹 Paths
base_model_path <- file.path(OUTPUTS_EV, "base_ev_model.rds")
adv_model_path <- file.path(OUTPUTS_EV, "advanced_ev_model.rds")
preds_path <- file.path(OUTPUTS_EV, "ev_predictions_test.csv")      # ✅ Predictions with all features
test_ev_path <- file.path(OUTPUTS_EV, "test_ev_scaled.csv")         # ✅ Full test features for PPC
metrics_file <- file.path(OUTPUTS_EV, "ev_model_test_metrics.txt")
plots_dir <- file.path(OUTPUTS_EV, "plots")
if (!dir.exists(plots_dir)) dir.create(plots_dir, recursive = TRUE)

# 🔹 Load Test Predictions
ev_csv_preds <- read.csv(preds_path)
log_message("✅ Test Predictions Loaded Successfully.", LOG_FILE_EV)

# ✅ Align Column References
ev_csv_preds <- ev_csv_preds %>%
  mutate(
    actual_unscaled = actual_exit_velo,
    base_pred_unscaled = Base_EV_pred_exit_velo,
    adv_pred_unscaled = Advanced_EV_pred_exit_velo
  )

# ============================================
# 📊 Evaluation Metrics
# ============================================
calculate_metrics <- function(actual, predicted) {
  if (sd(actual, na.rm = TRUE) < 1e-5) {
    warning("⚠️ Low variance in actuals. R² will be NA.")
    r2 <- NA
  } else {
    r2 <- caret::R2(predicted, actual, form = "traditional")
  }
  data.frame(RMSE = rmse(actual, predicted), MAE = mae(actual, predicted), R2 = r2)
}

metrics_df <- bind_rows(
  calculate_metrics(ev_csv_preds$actual_unscaled, ev_csv_preds$base_pred_unscaled) %>% mutate(model = "Base_Model_Test"),
  calculate_metrics(ev_csv_preds$actual_unscaled, ev_csv_preds$adv_pred_unscaled) %>% mutate(model = "Advanced_Model_Test")
)

plot(ev_csv_preds$actual_unscaled, ev_csv_preds$base_pred_unscaled)

ev_csv_preds %>% 
  ggplot(aes(x=actual_unscaled,y=base_pred_unscaled))+
  geom_point()+
  geom_smooth(method="lm")



lm_test <- lm(actual_unscaled~adv_pred_unscaled,data=ev_csv_preds)
summary(lm_test)$r.squared

ypred = ev_csv_preds$base_pred_unscaled
actual <- ev_csv_preds$actual_unscaled
ss_res <- sum((actual-ypred)^2)
ss_total <- sum((actual-mean(actual))^2)
r2 <- 1-(ss_res/ss_total)
print(r2)

plot(actual-ypred)

sum(actual)
sum(ypred)

write.table(metrics_df, metrics_file, row.names = FALSE, sep = "\t", quote = FALSE)
print("✅ FINAL TEST SET EVALUATION METRICS (UNSCALED):")
print(metrics_df)

# ============================================
# 📌 Bayesian Diagnostics - Trace Plots
# ============================================
base_ev_model <- readRDS(base_model_path)
advanced_ev_model <- readRDS(adv_model_path)

# ✅ Model Class Check for Safety
if (!inherits(base_ev_model, "stanreg")) stop("❌ base_ev_model is not a stanreg model!")
if (!inherits(advanced_ev_model, "stanreg")) stop("❌ advanced_ev_model is not a stanreg model!")

print(class(base_ev_model))
print(class(advanced_ev_model))

for (model in list(base_ev_model, advanced_ev_model)) {
  model_name <- ifelse(identical(model, base_ev_model), "base", "advanced")
  valid_params <- dimnames(as.array(model))[[3]]
  non_user_params <- valid_params[!grepl("^s\\(user", valid_params)]  # Skip random effects
  
  for (param in non_user_params) {
    trace_plot_path <- file.path(plots_dir, paste0("trace_", model_name, "_", param, ".png"))
    trace_plot <- mcmc_trace(as.array(model), pars = param) + PLOT_THEME
    ggsave(trace_plot_path, plot = trace_plot, width = 6, height = 5, dpi = 300)
    
    if (file.exists(trace_plot_path) && file.info(trace_plot_path)$size < 50 * 1024) {
      log_message(paste("⚠️ Trace plot small or incomplete:", trace_plot_path), LOG_FILE_EV)
    }
  }
}

# ============================================
# 📌 Posterior Predictive Checks (SAFE & FIXED)
# ============================================
run_ppc_plot <- function(model, model_name, newdata) {
  if (!inherits(model, "stanreg")) stop(paste("❌", model_name, "is not a stanreg model"))
  log_message(paste("📌 Running PPC for", model_name), LOG_FILE_EV)
  
  yrep <- posterior_predict(model, newdata = newdata)
  if (ncol(yrep) != nrow(newdata)) stop("❌ ncol(yrep) does not match test set! Check newdata columns.")
  
  # ✅ PPC uses ev_csv_preds$actual_unscaled for y
  ppc_plot <- bayesplot::ppc_dens_overlay(y = ev_csv_preds$actual_unscaled, yrep = yrep) + PLOT_THEME
  ggsave(file.path(plots_dir, paste0(model_name, "_ev_pp_check.png")), plot = ppc_plot, width = 6, height = 5, dpi = 300)
}

# ✅ Load Full Test Data for PPC
test_ev_full <- read.csv(test_ev_path)
run_ppc_plot(base_ev_model, "base", test_ev_full)
run_ppc_plot(advanced_ev_model, "advanced", test_ev_full)

# ============================================
# 📌 Residuals & Scatterplots
# ============================================
ev_csv_preds <- ev_csv_preds %>%
  mutate(
    base_resid = actual_unscaled - base_pred_unscaled,
    adv_resid = actual_unscaled - adv_pred_unscaled
  )

for (model in c("base", "adv")) {
  # Scatter Plot
  scatter <- ggplot(ev_csv_preds, aes_string(x = "actual_unscaled", y = paste0(model, "_pred_unscaled"))) +
    geom_point(alpha = PLOT_ALPHA, color = "#4682B4") +
    geom_abline(slope = 1, intercept = 0, color = "red", linetype = "dashed") +
    labs(title = paste("Actual vs Predicted (", toupper(model), " Model)"),
         x = "Actual EV (mph)", y = "Predicted EV (mph)") +
    PLOT_THEME
  
  ggsave(file.path(plots_dir, paste0("scatter_actual_vs_pred_", model, ".png")), plot = scatter, width = 7, height = 5, dpi = 300)
  
  # Residuals vs Fitted
  resid_plot <- ggplot(ev_csv_preds, aes_string(x = paste0(model, "_pred_unscaled"), y = paste0(model, "_resid"))) +
    geom_point(alpha = PLOT_ALPHA, color = "#4682B4") +
    geom_hline(yintercept = 0, color = "red", linetype = "dashed") +
    labs(title = paste("Residuals vs Fitted (", toupper(model), " Model)"),
         x = "Fitted EV (mph)", y = "Residuals (mph)") +
    PLOT_THEME
  
  ggsave(file.path(plots_dir, paste0("residuals_vs_fitted_", model, ".png")), plot = resid_plot, width = 7, height = 5, dpi = 300)
}

log_message("🎯 FINAL EV Model Test Set Evaluation Completed Successfully!", LOG_FILE_EV)
print("🎯 FINAL EV Model Test Set Evaluation Completed Successfully!")




