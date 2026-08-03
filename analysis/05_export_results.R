#==============================================================================
# Load parametric and non-parametric results
#==============================================================================

param <- readRDS(file.path(intermediate_dir, "03_parametric.rds"))
nonparam <- readRDS(file.path(intermediate_dir, "03_nonparametric.rds"))

#==============================================================================
# Merge BA tables
#==============================================================================

BA_l3 <- bind_rows(
  param$BA_tables$Platform_vs_L3,
  nonparam$BA_tables$Platform_vs_L3
)

BA_trunk <- bind_rows(
  param$BA_tables$Platform_vs_Trunk,
  nonparam$BA_tables$Platform_vs_Trunk
)

BA_l3 <- BA_l3 %>%
  mutate(Parameter = factor(Parameter, levels = all_parameters)) %>%
  arrange(Parameter)

BA_trunk <- BA_trunk %>%
  mutate(Parameter = factor(Parameter, levels = all_parameters)) %>%
  arrange(Parameter)

#==============================================================================
# Merge calibrated matrices
#==============================================================================

fp <- bind_cols(
  param$calibrated$fp,
  nonparam$calibrated$fp
)

l3 <- bind_cols(
  param$calibrated$l3,
  nonparam$calibrated$l3
)

trunk <- bind_cols(
  param$calibrated$trunk,
  nonparam$calibrated$trunk
)

#==============================================================================
# Keep desired parameter order
#==============================================================================

all_parameters <- c(
  param_parameters,
  nonparam_parameters
)

fp <- fp[, all_parameters, drop = FALSE]
l3 <- l3[, all_parameters, drop = FALSE]
trunk <- trunk[, all_parameters, drop = FALSE]

#==============================================================================
# Add metadata
#==============================================================================

fp$Class <- class_vector
l3$Class <- class_vector
trunk$Class <- class_vector

fp$PatientNumber <- patient_vector
l3$PatientNumber <- patient_vector
trunk$PatientNumber <- patient_vector

#==============================================================================
# Export
#==============================================================================

write_xlsx(fp, file.path(calibrated_tables, "calibrated_fp.xlsx"))
write_xlsx(l3, file.path(calibrated_tables, "calibrated_l3.xlsx"))
write_xlsx(trunk, file.path(calibrated_tables, "calibrated_trunk.xlsx"))

write_xlsx(
  BA_l3,
  file.path(summary_dir, "FP_L3_results.xlsx")
)

write_xlsx(
  BA_trunk,
  file.path(summary_dir, "FP_Trunk_results.xlsx")
)