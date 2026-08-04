
###############################################################################
# 01_load_data.R
#
# Load all input datasets required for the Bland–Altman analysis.
#
# Input:
#   - Force plate feature matrix
#   - IMU L3 feature matrix
#   - IMU Trunk feature matrix
#   - LSS matrix
#
# Output:
#   - fp
#   - l3
#   - trunk
#   - lss
#   - subjects IDs
###############################################################################


#==============================================================================
# Load feature matrices
#==============================================================================

fp <- read_excel(platform_file)
l3 <- read_excel(l3_file)
trunk <- read_excel(trunk_file)
lss <- read_excel(lss_file)

#==============================================================================
# Basic validation
#==============================================================================

stopifnot(
  nrow(fp) == nrow(l3),
  nrow(fp) == nrow(trunk)
)

stopifnot(
  all(fp$PatientNumber == l3$PatientNumber),
  all(fp$PatientNumber == trunk$PatientNumber)
)


#==============================================================================
# Save patient IDs
#==============================================================================
patient_ids <- fp$PatientNumber

#==============================================================================
# Save loaded datasets
#==============================================================================

load_data <- list(
  fp = fp,
  l3 = l3,
  trunk = trunk,
  lss = lss,
  patient_ids = patient_ids
)

saveRDS(
  load_data,
  file.path(intermediate_dir, "01_load_data.rds")
)
