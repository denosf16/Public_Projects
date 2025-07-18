# ==============================
# 🔹 Load Required Libraries
# ==============================
library(dplyr)
library(randomForest)
library(corrplot)
library(minerva)  # MIC analysis
library(ggplot2)
library(car)  # VIF analysis

# ==============================
# 🔹 Define File Paths
# ==============================
input_file <- "outputs/pitch_data_cleaned.csv"
feature_importance_plot <- "outputs/feature_importance.png"
mic_plot <- "outputs/mic_analysis.png"
vif_output_file <- "outputs/vif_results.csv"

# ==============================
# 🔹 Load Cleaned Data
# ==============================
pitch_data <- read.csv(input_file)

# ==============================
# 🔹 Remove Unwanted Variables
# ==============================
exclude_vars <- c("session_pitch", "user", "session_mass_kg", "session_height_m", "age_yrs", "playing_level")

pitch_data <- pitch_data %>%
  select(-all_of(exclude_vars))

# ==============================
# 🔹 Compute Correlation Matrix
# ==============================
flog.info("📊 Computing correlation matrix...")
numeric_data <- pitch_data %>% select(where(is.numeric))
cor_matrix <- cor(numeric_data, use = "complete.obs")

# Set correlation threshold
cor_threshold <- 0.2

# Identify variables highly correlated with pitch_speed_mph
high_corr_vars <- rownames(cor_matrix)[cor_matrix["pitch_speed_mph", ] > cor_threshold | 
                                         cor_matrix["pitch_speed_mph", ] < -cor_threshold]

# Generate heatmap if correlated variables exist
if (length(high_corr_vars) > 1) {
  png("outputs/correlation_heatmap.png", width = 800, height = 600)
  corrplot(cor_matrix[high_corr_vars, high_corr_vars], method = "color", tl.cex = 0.8, title = "Correlation Heatmap - Pitch Speed")
  dev.off()
  flog.info("✅ Correlation heatmap saved to outputs/correlation_heatmap.png")
}

# ==============================
# 🔹 Train Random Forest Model for Feature Importance
# ==============================
if (length(high_corr_vars) > 1) {
  flog.info("🌲 Training Random Forest Model for Feature Importance...")
  
  rf_model <- randomForest(
    pitch_speed_mph ~ ., 
    data = na.omit(pitch_data %>% select(pitch_speed_mph, all_of(high_corr_vars))), 
    importance = TRUE, ntree = 2500
  )
  
  # Extract Feature Importance
  feature_importance <- importance(rf_model)
  feature_importance_df <- data.frame(
    Variable = rownames(feature_importance),
    Importance = feature_importance[, "IncNodePurity"]
  )
  
  # Save Feature Importance Plot
  if (nrow(feature_importance_df) > 0) {
    p <- ggplot(feature_importance_df, aes(x = reorder(Variable, Importance), y = Importance)) +
      geom_bar(stat = "identity", fill = "blue") +
      coord_flip() +
      labs(title = "Feature Importance - Pitch Speed",
           x = "Variable",
           y = "Importance (IncNodePurity)") +
      theme_minimal()
    
    ggsave(feature_importance_plot, p, width = 8, height = 6)
    flog.info("✅ Feature importance plot saved to: %s", feature_importance_plot)
  }
}

# ==============================
# 🔹 MIC (Maximal Information Coefficient) Analysis
# ==============================
flog.info("📊 Running MIC Analysis for nonlinear relationships...")

high_corr_vars <- setdiff(high_corr_vars, "pitch_speed_mph")

mic_results <- apply(pitch_data %>% select(all_of(high_corr_vars)), 2, function(x) {
  mine(x, pitch_data$pitch_speed_mph)$MIC
})

mic_df <- data.frame(Variable = names(mic_results), MIC = mic_results)

# Save MIC Plot
p_mic <- ggplot(mic_df, aes(x = reorder(Variable, MIC), y = MIC)) +
  geom_bar(stat = "identity", fill = "blue") +
  coord_flip() +
  labs(title = "MIC Score - Pitch Speed (Excluding Itself)",
       x = "Variable",
       y = "MIC Score") +
  theme_minimal()

ggsave(mic_plot, p_mic, width = 8, height = 6)
flog.info("✅ MIC analysis plot saved to: %s", mic_plot)

# ==============================
# 🔹 Variance Inflation Factor (VIF) Test
# ==============================
flog.info("📊 Running VIF Test to detect multicollinearity...")

final_vars <- mic_df$Variable[mic_df$MIC >= 0.2]  # Keep only meaningful predictors

if (length(final_vars) > 1) {
  vif_model <- lm(pitch_speed_mph ~ ., data = pitch_data %>% select(pitch_speed_mph, all_of(final_vars)))
  vif_results <- vif(vif_model)
  
  vif_df <- data.frame(Variable = names(vif_results), VIF = vif_results) %>%
    arrange(desc(VIF))
  
  write.csv(vif_df, vif_output_file, row.names = FALSE)
  flog.info("✅ VIF results saved to: %s", vif_output_file)
  
  # Identify Multicollinear Variables (VIF > 5)
  high_vif_vars <- vif_df$Variable[vif_df$VIF > 5]
  flog.warn("⚠️ High multicollinearity detected in variables: %s", paste(high_vif_vars, collapse = ", "))
  
  # Remove high VIF variables
  final_vars <- setdiff(final_vars, high_vif_vars)
} else {
  flog.warn("⚠️ No variables meet the MIC threshold.")
}

# ==============================
# 🔹 Final Feature Selection
# ==============================
flog.info("✅ Selected Predictors for Modeling: %s", paste(final_vars, collapse = ", "))

final_feature_set <- pitch_data %>% select(pitch_speed_mph, all_of(final_vars))
write.csv(final_feature_set, "outputs/selected_features.csv", row.names = FALSE)
flog.info("✅ Final selected feature dataset saved to: outputs/selected_features.csv")

print("✅ Feature Selection Completed!")
