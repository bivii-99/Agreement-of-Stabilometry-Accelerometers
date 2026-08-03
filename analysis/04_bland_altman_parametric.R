###############################################################################
# 03_parametric.R
#
# Parametric Bland–Altman analysis
#
# Workflow
#   1. Load preprocessed mean datasets
#   2. Assess normality
#   3. Apply Box-Cox / Log transformations
#   4. Detect fixed and proportional bias
#   5. Calibrate measurements
#   6. Generate Bland–Altman plots
#   7. Save calibrated datasets
#
# Input
#   - 02_preprocessing.rds
#
# Output
#   - 03_parametric.rds
###############################################################################

#==============================================================================
# Load preprocessing results
#==============================================================================

pre <- readRDS(file.path(intermediate_dir, "02_preprocessing.rds"))

fp <- pre$parametric$fp
l3 <- pre$parametric$l3
trunk <- pre$parametric$trunk

patient_vector <- pre$patient_vector
class_vector <- pre$class_vector
lss_vector <- pre$lss_vector

patient <- seq_along(patient_vector)

#==============================================================================
# Initialize containers
#==============================================================================

original_vals <- list()

DOA_to_regress <- list()
DOA_inversed_pb <- list()

ols_stats <- list()

param_tables <- list()
non_param_tables_log <- list()
non_param_tables_orig <- list()

BA_tables <- list()

transformed_comparisons <- list()

results <- list()

#------------------------------------------------------------------------------
# Parameter names
#------------------------------------------------------------------------------

param_names <- character()
non_param_names <- character()

normal_0 <- character()
non_normal_0 <- character()

fixed_names <- character()
inverse_names_0 <- character()
proportional_names_0 <- character()

log_comparisons <- character()
box_comparisons <- character()

#==============================================================================
# Main loop
#==============================================================================

for (par in param_parameters) {
  
  matrices <- list(
    Platform = fp[[par]],
    L3 = l3[[par]],
    Trunk = trunk[[par]]
  )
  
  for (pair in pair_definitions) {
    
    label <- pair$label
    name <- paste(par, label, sep = "_")
    
    var1_orig <- matrices[[pair$v1]]
    var2_orig <- matrices[[pair$v2]]
    
    diff_orig <- var1_orig - var2_orig
    mean_orig <- (var1_orig + var2_orig) / 2
    
    original_vals[[name]] <- save_in_tibble(name,var1_orig,var2_orig,diff_orig,mean_orig,best_tr = "None",parametric_var = TRUE)
    
    #--------------------------------------------------------------------------
    # NORMALITY
    #--------------------------------------------------------------------------
    p <- shapiro.test(diff_orig)$p.value
    
    if (p > 0.05) {
      
      normal_0 <- c(normal_0, name)
      param_names <- c(param_names, name)
      
      param_tables[[name]] <- save_in_tibble(name,var1_orig,var2_orig,diff_orig,mean_orig,best_tr = "None",parametric_var = TRUE)
      
      var1 <- var1_orig
      var2 <- var2_orig
      diff_vals <- diff_orig
      mean_vals <- mean_orig
      
      best_tr <- "None"
      
    } else {
      
      non_normal_0 <- c(non_normal_0, name)
      #==============================================================
      # Box-Cox transformation
      #==============================================================
      
      box_res <- boxtransf_param(var1_orig, var2_orig)
      
      original_vals[[name]] <- tibble(
        bn1 = box_res$bn1,
        bn2 = box_res$bn2
      )
      
      p <- shapiro.test(box_res$diff_box)$p.value
      
      if (p > 0.05) {
        
        best_tr <- "Box-Cox"
        
        box_comparisons <- c(box_comparisons, name)
        param_names <- c(param_names, name)
        
        param_tables[[name]] <- save_in_tibble(name,box_res$var1_box,box_res$var2_box,box_res$diff_box,box_res$mean_box,best_tr = best_tr,parametric_var = TRUE)
        
        transformed_comparisons[[name]] <- param_tables[[name]]
        
        var1 <- box_res$var1_box
        var2 <- box_res$var2_box
        diff_vals <- box_res$diff_box
        mean_vals <- box_res$mean_box
        
      } else {
        
        #============================================================
        # Log transformation
        #============================================================
        
        log_res <- logtransf_param(var1_orig, var2_orig)
        p <- shapiro.test(log_res$diff_log)$p.value
        
        if (p > 0.05) {
          best_tr <- "Log"
          log_comparisons <- c(log_comparisons, name)
          param_names <- c(param_names, name)
          
          param_tables[[name]] <- save_in_tibble(name,log_res$var1_log,log_res$var2_log,log_res$diff_log,log_res$mean_log,best_tr = best_tr,parametric_var = TRUE)
          transformed_comparisons[[name]] <- param_tables[[name]]
          
          var1 <- log_res$var1_log
          var2 <- log_res$var2_log
          diff_vals <- log_res$diff_log
          mean_vals <- log_res$mean_log
          
        } else {
          best_tr <- "Log"
          log_comparisons <- c(log_comparisons, name)
          non_param_names <- c(non_param_names, name)
          
          non_param_tables_log[[name]] <- save_in_tibble(name,log_res$var1_log,log_res$var2_log,log_res$diff_log,log_res$mean_log,best_tr = best_tr,parametric_var = FALSE)
          non_param_tables_orig[[name]] <- save_in_tibble(name,var1_orig,var2_orig,diff_orig,mean_orig,best_tr = "None")
          
          var1 <- log_res$var1_log
          var2 <- log_res$var2_log
          diff_vals <- log_res$diff_log
          mean_vals <- log_res$mean_log
          
        }
      }
    }
    
    #==========================================================================
    # Bland–Altman statistics
    #==========================================================================
    
    fixed_bias <- mean(diff_vals, na.rm = TRUE)
    
    fit <- lm(diff_vals ~ mean_vals)
    
    slope_value <- coef(fit)[["mean_vals"]]
    slope_p <- summary(fit)$coefficients["mean_vals", "Pr(>|t|)"]
    
    ols_stats[[name]] <- tibble(
      slope_value = slope_value,
      slope_p = slope_p
    )
    
    #==========================================================================
    # BA plot
    #==========================================================================
    
    if (!name %in% non_param_names) {
      
      filename <- switch(
        TRUE,
        name %in% log_comparisons ~
          paste0("BlandAltman_log_", par, "_", label, ".png"),
        
        name %in% box_comparisons ~
          paste0("BlandAltman_Box_", par, "_", label, ".png"),
        
        TRUE ~
          paste0("BlandAltman_", par, "_", label, ".png")
      )
      
      png(filename = file.path(graph_param, filename),width = 1600,height = 1200,res = 200)
      
      res_BA_param <- plot_BA_param(mean_vals,diff_vals,patient,par,label)
      
      BA_table <- create_BA_table(var1_orig,var2,diff_vals,mean_vals,par,p,fixed_bias,slope_value,slope_p,res_BA_param)
      
      if (is.null(BA_tables[[label]])) {
        BA_tables[[label]] <- BA_table
      } else {
        
        BA_tables[[label]] <-
          dplyr::bind_rows(
            BA_tables[[label]],
            BA_table
          )
        
      }
      
      #-----------------------------------------------------------------------
      # Bias classification
      #-----------------------------------------------------------------------
      if (is.na(slope_p) || slope_p > 0.05) {
        fixed_names <- c(fixed_names,name)
        
      } else {
        abline(fit,col = "black",lwd = 2)
        
        if (slope_value > 0) {
          proportional_names_0 <-c(proportional_names_0,name)
          DOA_to_regress[[name]] <-save_in_tibble(name,var1,var2,diff_vals,mean_vals,best_tr = "_",parametric_var = TRUE)
          
        } else {
          
          inverse_names_0 <-c(inverse_names_0,name)
          log_res <- logtransf_param(var1_orig,var2_orig)
          
          DOA_inversed_pb[[name]] <-save_in_tibble(name,log_res$var1_log,log_res$var2_log,log_res$diff_log,log_res$mean_log,best_tr = "Log",parametric_var = TRUE)
        }
      }
      dev.off()
    }
    
    #==========================================================================
    # Summary
    #==========================================================================
    
    results[[length(results) + 1]] <-tibble(
        parameter = par,
        comparison = label,
        transformation = best_tr,
        shapiro_p = p,
        fixed_bias = fixed_bias,
        slope = slope_value,
        proportional_bias = !is.na(slope_p) && slope_p <= 0.05
      )
  }
}


#==============================================================================
# Transformation summary
#==============================================================================

final_results <- bind_rows(results)

write_xlsx(
  final_results,
  file.path(summary_dir, "Best_transformation_averages_summary.xlsx")
)

#==============================================================================
# Inverse proportional bias
#==============================================================================

for (name in names(DOA_inversed_pb)) {
  df <- DOA_inversed_pb[[name]]
  p <- shapiro.test(df$diff)$p.value
  if (p > 0.05) {
    param_tables[[name]] <- save_in_tibble(name,df$var1,df$var2,df$diff,df$mean,best_tr = "Log",parametric_var = TRUE)
    param_names <- c(param_names, name)
    
  } else {
    non_param_tables_log[[name]] <-save_in_tibble(name,df$var1,df$var2,df$diff,df$mean,best_tr = "Log",parametric_var = TRUE)
    non_param_names <- c(non_param_names, name)
  }
}

#==============================================================================
# Non-parametric variables
#==============================================================================

nonparametric_table <- purrr::map_dfr(
  names(non_param_tables_log),
  function(name) {
    
    df <- non_param_tables_log[[name]]
    stats <- non_param_stats(name, df$diff)
    par_label <- extract_par_accel_names(name)
    png(file.path(graph_nonparam,paste0("BlandAltman_", name, ".png")),width = 1600,height = 1200,res = 200)
    
    plot_BA_nonparam(df$mean,df$diff,patient,par_label$par,par_label$label,stats)
    dev.off()
    tibble(name = name,fixed_bias = round(stats$median,2),Q5 = stats$Q5,Q95 = stats$Q95)
  }
)

write_xlsx(
  nonparametric_table,
  file.path(summary_dir, "limits_nonparam.xlsx")
)

#==============================================================================
# Regression statistics
#==============================================================================

regression_table <- regression_stats(DOA_to_regress)

#==============================================================================
# Fixed bias calibration
#==============================================================================

cal_fixed <- calibration_fixedbias(
  param_tables,
  DOA_fixed = param_names,
  DOA_inversed_pb = DOA_inversed_pb,
  transformed_comparisons = transformed_comparisons,
  log_comparisons = log_comparisons,
  original_vals = original_vals,
  BA_tables = BA_tables,
  non_param_names = non_param_names
)

BA_tables <- cal_fixed$BA_tables

mat_fixed <- calibrated_vars_extraction(param_parameters,cal_fixed$calibrated_accel)

#==============================================================================
# Non-parametric calibration
#==============================================================================

cal_nonparam <- calibration_fixedbias(
  non_param_tables_log,
  DOA_fixed = non_param_names,
  DOA_inversed_pb = DOA_inversed_pb,
  transformed_comparisons = transformed_comparisons,
  log_comparisons = log_comparisons,
  original_vals = original_vals,
  BA_tables = BA_tables,
  non_param_names = non_param_names
)

BA_tables <- cal_nonparam$BA_tables
mat_nonparam <- calibrated_vars_extraction(param_parameters,cal_nonparam$calibrated_accel)

#==============================================================================
# Proportional calibration
#==============================================================================

prop_res <- proportional_calibration(regression_table,param_tables,BA_tables)

BA_tables <- prop_res$BA_tables

cal_prop <- calibration_fixedbias(
  prop_res$proportional_param_tables,
  DOA_fixed = prop_res$DOA_new_fixed,
  DOA_inversed_pb = DOA_inversed_pb,
  transformed_comparisons = transformed_comparisons,
  log_comparisons = log_comparisons,
  original_vals = original_vals,
  BA_tables = BA_tables,
  non_param_names = non_param_names,
  proportional_names_0 = proportional_names_0
)

BA_tables <- cal_prop$BA_tables

mat_prop <- calibrated_vars_extraction(
  param_parameters,
  cal_prop$calibrated_accel
)

#==============================================================================
# Merge calibrated matrices
#==============================================================================
fp_wo_outliers <- merge_unique ( 
  mat_fixed$calibrated_fp,
  mat_nonparam$calibrated_fp,
  mat_prop$calibrated_fp
  
)
calibrated_l3 <- merge_unique(
  mat_fixed$calibrated_l3,
  mat_nonparam$calibrated_l3,
  mat_prop$calibrated_l3
)

calibrated_trunk <- merge_unique(
  mat_fixed$calibrated_trunk,
  mat_nonparam$calibrated_trunk,
  mat_prop$calibrated_trunk
)

#==============================================================================
# BA tables
#==============================================================================

BA_trunk <- BA_tables[["Platform_vs_Trunk"]] |>
  mutate(Parameter = factor(Parameter, levels = param_parameters)) |>
  tidyr::complete(Parameter) |>
  arrange(Parameter)

BA_l3 <- BA_tables[["Platform_vs_L3"]] |>
  mutate(Parameter = factor(Parameter, levels = param_parameters)) |>
  tidyr::complete(Parameter) |>
  arrange(Parameter)

#==============================================================================
# Save results
#==============================================================================

results_parametric <- list(
  
  calibrated = list(
    fp = fp_wo_outliers,
    l3 = calibrated_l3,
    trunk = calibrated_trunk
  ),
  
  BA_tables = list(
    Platform_vs_L3 = BA_l3,
    Platform_vs_Trunk = BA_trunk
  ),
  
  transformations = final_results,
  regression = regression_table,
  nonparametric = nonparametric_table
)

saveRDS(
  results_parametric,
  file.path(intermediate_dir, "03_parametric.rds"))





