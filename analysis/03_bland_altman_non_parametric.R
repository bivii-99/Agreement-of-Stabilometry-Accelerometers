###############################################################################
# 03_bland_altman_nonparametric.R
#
# Perform non-parametric Bland–Altman analysis.
#
# Processing steps:
#   1. Load median-aggregated datasets
#   2. Compute median bias and non-parametric limits of agreement
#   3. Assess proportional bias
#   4. Apply fixed-bias calibration
#   5. Generate Bland–Altman plots
#   6. Create summary tables
#
# Input:
#   - 02_preprocessing.rds
#
# Output:
#   - 03_nonparametric.rds
###############################################################################

#==============================================================================
# Load preprocessing results
#==============================================================================

pre <- readRDS(file.path(intermediate_dir, "02_preprocessing.rds"))
fp    <- pre$nonparametric$fp
l3    <- pre$nonparametric$l3
trunk <- pre$nonparametric$trunk
patient_vector <- pre$patient_vector

#==============================================================================
# Initialize containers
#==============================================================================

med_list <- list()
Q5 <- list()
Q95 <- list()
calibrated_accel <- list()
BA_tables <- list()


#==============================================================================
# Main Bland–Altman loop
#==============================================================================

for(par in nonparam_nonparam_parameters){
  matrices <- list(
    fp = fp[[par]],
    l3 = l3[[par]],
    trunk = trunk[[par]]
  )
  
  for(pair in pair_definitions){
    name <- paste(par, pair$label, sep = "_")
    var1 <- matrices[[pair$v1]]
    var2 <- matrices[[pair$v2]]
    diff_vals <- var1 - var2
    mean_vals <- (var1 + var2)/2
    
    #----------------------------------------------------------
    # Non-parametric statistics
    #----------------------------------------------------------
    res_nonparam <- non_param_stats(name, diff_vals)

    med_diff <- res_nonparam$median
    
    Q5[[name]] <- res_nonparam$Q5
    Q95[[name]] <- res_nonparam$Q95
    med_list[[name]] <- med_diff
    
    #----------------------------------------------------------
    # Proportional bias
    #----------------------------------------------------------
    
    fit <- lm(diff_vals ~ mean_vals)
    slope_value <- coef(fit)["mean_vals"]
    slope_p <- summary(fit)$coefficients["mean_vals", "Pr(>|t|)"]
    
    #----------------------------------------------------------
    # Fixed bias
    #----------------------------------------------------------
    p_fixed <- t.test(diff_vals)$p.value
    
    #----------------------------------------------------------
    # Bland–Altman plot BEFORE calibration
    #----------------------------------------------------------
    png(file.path(graph_nonparam_dir,paste0("BA_", name, ".png")), width = 1600, height = 1200,res = 200)
    
    res_BA <- plot_BA_nonparam(mean_vals,diff_vals,patient_vector, par,pair$label,res_nonparam)
    dev.off()
    
    #----------------------------------------------------------
    # Fixed-bias calibration
    #----------------------------------------------------------
    
    if(p_fixed < 0.05){
      var2 <- var2 + med_diff
    }
    
    new_diff <- var1 - var2
    new_mean <- (var1 + var2)/2
    
    calibrated_accel[[name]] <- tibble(
      var1 = var1,
      var2 = var2,
      diff = new_diff,
      mean = new_mean
    )
    
    #----------------------------------------------------------
    # BA summary table
    #----------------------------------------------------------
    
    BA_row <- create_BA_table(var1,var2, new_diff, new_mean, par, p_fixed, med_diff, slope_value, slope_p, 
                              tibble(
                                ll = res_nonparam$Q5,
                                hl = res_nonparam$Q95,
                                sd = sd(diff_vals)
                              ))

    if(is.null(BA_tables[[pair$label]])){
      BA_tables[[pair$label]] <- BA_row
      
    }else{
      BA_tables[[pair$label]] <-bind_rows(BA_tables[[pair$label]],BA_row )
    }
  }
}

#==============================================================================
# Build calibrated matrices
#==============================================================================

calibrated <- calibrated_vars_extraction(nonparam_parameters,calibrated_accel)


#==============================================================================
# Save results
#==============================================================================

results_nonparam <- list(
  data = list(
    fp = calibrated$fp_wo_outliers,
    l3 = calibrated$calibrated_l3,
    trunk = calibrated$calibrated_trunk
  ),
  statistics = list(
    BA_tables = BA_tables,
    median_bias = med_list,
    Q5 = Q5,
    Q95 = Q95
  )
)

saveRDS(
  results_nonparam,
  file.path(intermediate_dir, "03_nonparametric.rds")
)