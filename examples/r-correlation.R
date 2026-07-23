# AI Career Threat Index — R analysis example
#
# Loads the live dataset and runs basic statistical analysis on the
# relationship between displacement risk score, salary, and tenure trends.
#
# Dependencies: jsonlite, dplyr (or use base R as shown)
# Run: Rscript r-correlation.R

# Load
library(jsonlite)
data <- fromJSON("https://raw.githubusercontent.com/Jott2121/ai-career-threat-index/main/data/ai-career-threat-index.json", flatten = TRUE)
roles <- data$roles
cat(sprintf("Loaded %d roles from version %s (updated %s)\n",
            nrow(roles), data$metadata$version, data$metadata$lastUpdated))

# Compute salary midpoints from low/high parsed values
roles$salary_mid <- (roles$salary.low + roles$salary.high) / 2

# Score x salary correlation
cor_test <- cor.test(roles$score, roles$salary_mid, use = "complete.obs")
cat(sprintf("\nCorrelation: AI displacement score vs. salary midpoint\n"))
cat(sprintf("  r = %.3f, p = %.4f, n = %d\n",
            cor_test$estimate, cor_test$p.value, sum(complete.cases(roles$score, roles$salary_mid))))

# Mean salary by risk band
cat("\nMean salary midpoint by risk band:\n")
bands <- c("Low", "Moderate", "High", "Very High")
for (b in bands) {
  band_roles <- roles[roles$riskLevel == b & !is.na(roles$salary_mid), ]
  if (nrow(band_roles) > 0) {
    cat(sprintf("  %-10s $%s  (n=%d)\n",
                b, format(round(mean(band_roles$salary_mid)), big.mark = ","),
                nrow(band_roles)))
  }
}

# Roles with biggest score increase since Q1 2025
roles$delta <- roles$historicalScores..Q2.2026 - roles$historicalScores..Q1.2025
cat("\nTop 10 risers (Q1 2025 -> Q2 2026):\n")
top_movers <- roles[order(-roles$delta), c("title", "category", "historicalScores..Q1.2025", "historicalScores..Q2.2026", "delta")]
top_movers <- head(top_movers, 10)
print(top_movers, row.names = FALSE)

# Risk band distribution
cat("\nRisk band distribution:\n")
print(table(factor(roles$riskLevel, levels = bands)))

# Most resilient roles (lowest scores)
cat("\nTop 10 most resilient roles:\n")
resilient <- head(roles[order(roles$score), c("title", "category", "score", "riskLevel")], 10)
print(resilient, row.names = FALSE)
