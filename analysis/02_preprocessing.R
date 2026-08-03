###############################################################################
# 02_preprocessing.R
#
# Preprocess the input feature matrices.
#
# Processing steps:
#   1. Detect intra-subject outliers
#   2. Remove outlier acquisitions (|z| > 3)
#   3. Aggregate repeated acquisitions using:
#        - mean (parametric analysis)
#        - median (non-parametric analysis)
#   4. Remove non-feature columns
#   5. Generate patient and class vectors
#
# Input:
#   - 01_load_data.rds
#
# Output:
#   - fp_mean, l3_mean, trunk_mean
#   - fp_median, l3_median, trunk_median
#   - patient_vector
#   - class_vector
#   - rows_removed
###############################################################################

#==============================================================================
# Load data
#==============================================================================

data <- readRDS(file.path(intermediate_dir, "01_load_data.rds"))

fp    <- data$fp
l3    <- data$l3
trunk <- data$trunk
lss <- data$lss


#==============================================================================
# Preprocessing pipeline
#==============================================================================

analysis_configs <- list(
    parametric = list(
    parameters = param_parameters,
    summary_method = "mean"
  ),
    nonparametric = list(
    parameters = nonparam_parameters,
    summary_method = "median"
  )
)

preprocessing <- list()

for (analysis in names(analysis_configs)) {
  
  cfg <- analysis_configs[[analysis]]
  
  # Run preprocessing
  res <- average_subjects(fp, l3, trunk, cfg$parameters, summary_method= cfg$summary_method,remove_outliers = TRUE)

  # Keep only feature columns
  feature_columns <- intersect(cfg$parameters, colnames(res$clean_avg_fp))
  
  preprocessing[[analysis]] <- list(
    fp = res$clean_avg_fp[, feature_columns, drop = FALSE],
    l3 = res$clean_avg_l3[, feature_columns, drop = FALSE],
    trunk = res$clean_avg_trunk[, feature_columns, drop = FALSE],
    rows_removed = res$rows_removed
  )
}

#==============================================================================
# Patient metadata
#==============================================================================

unique_patients <- fp[!duplicated(fp$PatientNumber), ]

patient_vector <- unique_patients$PatientNumber
class_vector   <- unique_patients$Class

rows_removed <- preprocessing$parametric$rows_removed

if (length(rows_removed) > 0) {
  patient_vector <- patient_vector[-rows_removed]
  class_vector   <- class_vector[-rows_removed]
}

#==============================================================================
# Save
#==============================================================================

saveRDS(
  list(
    parametric = preprocessing$parametric,
    nonparametric = preprocessing$nonparametric,
    patient_vector = patient_vector,
    class_vector = class_vector
  ),
  file.path(intermediate_dir, "02_preprocessing.rds")
)