library(refineR)
library(dplyr)

# agreement_functions.R

vec_outlier_idx <- function (X){
  X_scaled <- scale(X)
  outliers <- apply(abs(X_scaled) > 3, 1, any)
  return(outliers)
}

clean_patient <- function(fp, l3, trunk, parameters, patient_rows){
 
 if (nrow(fp) <= 1) {
    return(list(
      fp = fp,
      l3 = l3,
      trunk = trunk,
      removed_rows = integer(0)
    ))
  }
  keep <- rep(TRUE, nrow(fp))
  
  for (par in parameters) {
    
    fp_vec <- fp[[par]]
    l3_vec <- l3[[par]]
    trunk_vec <- trunk[[par]]
    
    out_fp <- vec_outlier_idx(fp_vec)
    out_l3 <- vec_outlier_idx(l3_vec)
    out_trunk <- vec_outlier_idx(trunk_vec)
    
    out_any <- out_fp | out_l3 | out_trunk
    
    keep <- keep & !out_any
  }
  
  list(
    fp = fp[keep, , drop = FALSE],
    l3 = l3[keep, , drop = FALSE],
    trunk = trunk[keep, , drop = FALSE],
    removed_rows = patient_rows[which(!keep)]
  )
}

safe_mean <- function(x){
  x <- x[!is.na(x)]
  if (length(x) == 0) {
    return(0)
  }
  mean(x)
}

safe_median <- function(x){
  x <- x[!is.na(x)]
  if (length(x) == 0) {
    return(0)
  }
  median(x)
}




average_subjects <- function(
    fp,
    l3,
    trunk,
    parameters,
    summary_method = c("mean", "median"),
    remove_outliers = TRUE
){
  
  summary_method <- match.arg(summary_method)
  
  patients <- unique(fp$PatientNumber)
  
  clean_avg_fp <- data.frame()
  clean_avg_l3 <- data.frame()
  clean_avg_trunk <- data.frame()
  
  rows_removed <- integer()
  patients_removed <- integer()
  
  for(id in patients){
    
    patient_rows <- which(fp$PatientNumber == id)
    
    patient_fp <- fp[patient_rows,,drop=FALSE]
    patient_l3 <- l3[patient_rows,,drop=FALSE]
    patient_trunk <- trunk[patient_rows,,drop=FALSE]
    
    if(remove_outliers){
      
      res <- clean_patient(
        patient_fp,
        patient_l3,
        patient_trunk,
        parameters,
        patient_rows
      )
      
      patient_fp <- res$fp
      patient_l3 <- res$l3
      patient_trunk <- res$trunk
      
      rows_removed <- c(rows_removed, res$removed_rows)
      
      if(nrow(patient_fp)==0){
        
        patients_removed <- c(patients_removed,id)
        next
        
      }
    }
    
    row_fp <- data.frame(PatientNumber=id)
    row_l3 <- data.frame(PatientNumber=id)
    row_trunk <- data.frame(PatientNumber=id)
    
    for(par in parameters){
      
      row_fp[[par]] <-
        safe_summary(patient_fp[[par]], summary_method)
      
      row_l3[[par]] <-
        safe_summary(patient_l3[[par]], summary_method)
      
      row_trunk[[par]] <-
        safe_summary(patient_trunk[[par]], summary_method)
      
    }
    
    clean_avg_fp <- rbind(clean_avg_fp,row_fp)
    clean_avg_l3 <- rbind(clean_avg_l3,row_l3)
    clean_avg_trunk <- rbind(clean_avg_trunk,row_trunk)
    
  }
  
  list(
    clean_avg_fp = clean_avg_fp,
    clean_avg_l3 = clean_avg_l3,
    clean_avg_trunk = clean_avg_trunk,
    rows_removed = unique(rows_removed),
    patients_removed = patients_removed
  )
  
}

extract_par_accel_names <- function (name){
  
  parts <- strsplit(name, "_")[[1]]
  
  if (length(parts) < 3) next  # skip if name too short
  
  # Extract parts based on your scheme
  par <- paste(parts[1:(length(parts)-3)], collapse = "_")
  pair_label <- paste(parts[(length(parts)-2):length(parts)], collapse = "_")
  
  return (list(
    par= par,
    label = pair_label
  ))
  
}

save_in_tibble<- function (name, var1_i, var2_i, diff_i, mean_i, best_tr_i=char(), parametric_var=TRUE){

  var_tibble<- tibble(
    var1 = var1_i,
    var2 = var2_i,
    diff = diff_i,
    mean = mean_i,
    fixed_bias = if(parametric_var==TRUE){round(mean(diff),2)}else{ round(median(diff),2)},
    best_tr = best_tr_i
  )

  return(var_tibble)
}

non_param_stats <- function(name,diff){
  
  loa <- quantile(diff, probs = c(0.05, 0.95), type = 6)
  med_diff <- median(diff)
  
  Q5= round(loa[1],2)
  Q95 = round(loa[2],2)
  
  
  return (list(
    median = med_diff,
    Q5 = Q5,
    Q95 = Q95
  ))
}

plot_BA_param <- function(mean_val, diff, patient_vec, par, pair_label){
  
  #Set the limits of agreement and fixed bias
  
  bias <- mean(diff, na.rm = TRUE)
  sd_diff <- sd(diff, na.rm = TRUE)
  
  hl <- bias + 1.96 * sd_diff
  ll <- bias - 1.96 * sd_diff
  
  # Plot WITHOUT points
  plot(
    mean_val, diff,
    # type = "n",   # no points
    ylim = c(ll - 0.2 * abs(ll), hl + 0.2 * abs(hl)),
    main = paste0("Bland–Altman Plot\nParameter: ", par,
                  " | Comparison: ", pair_label),
    xlab = "Mean",
    ylab = "Difference"
  )
  
  # Add patient numbers instead of points
  # text(
  #   mean_val, diff,
  #   labels = patient_vec,
  #   cex = 0.8
  # )
  
  # Add bias and LOA
  xrange <- range(mean_val, na.rm = TRUE)
  x_text <- xrange[1] + 0.85 * diff(xrange)
  
  abline(h = bias, lwd = 2)
  text(
    x = x_text,
    y = bias,
    labels = paste0("Bias = ", round(bias, 2)),
    pos = 3  # places text above the line
  ) 
  abline(h = bias + 1.96 * sd_diff, lty = 2)
  abline(h = bias - 1.96 * sd_diff, lty = 2)

  return(list(
    sd = sd_diff,
    ll = ll,
    hl = hl
  ))
  
}

plot_BA_nonparam <- function(mean_val,diff, patient_vec, par, pair_label, res_nonparam){
  
  #Set the limits of agreement and fixed bias
  
  bias <- median(diff, na.rm = TRUE)
  sd_diff <- sd(diff, na.rm = TRUE)
  
  ll <- res_nonparam$Q5
  hl <- res_nonparam$Q95
  
  # Plot WITHOUT points
  
  
  plot(
    mean_val, diff,
    # type = "n",   # no points
    ylim = c(ll - 0.2 * abs(ll), hl + 0.2 * abs(hl)),
    main = paste0("Non-param Bland–Altman Plot\nParameter: ", par,
                  " | Comparison: ", pair_label),
    xlab = "Mean",
    ylab = "Difference"
  )
  
  # Add patient numbers instead of points
  # text(
  #   mean_val, diff,
  #   labels = patient_vec,
  #   cex = 0.8
  # )
  
  # Add bias and LOA
  xrange <- range(mean_val, na.rm = TRUE)
  x_text <- xrange[1] + 0.85 * diff(xrange)
  
  abline(h = ll, lty = 2)
  abline(h = hl, lty = 2)
  abline(h = bias, lwd = 2)
  text(
    x = x_text,
    y = bias,
    labels = paste0("Bias = ", round(bias, 2)),
    pos = 3  # places text above the line
  ) 
  return(list(
    sd = sd_diff,
    ll = ll,
    hl = hl
  ))
  
}

WLS <- function(x, y, w = NULL) {
  if (is.null(w)) {
    model <- lm(y ~ x)
  } else {
    model <- lm(y ~ x, weights = w)
  }
  coef(model)[2]  # return slope
}

WLP <- function(x, y, w = NULL, alpha = 0.05) {
  
  n <- length(x)
  
  # Regression y on x
  b_yx <- WLS(x, y, w)
  
  # Regression x on y
  b_xy <- WLS(y, x, w)
  
  # Geometric mean slope
  b_WLP <- sqrt(b_yx * b_xy)
  
  # Intercept
  a_WLP <- mean(y) - b_WLP * mean(x)
  
  # Approximate 95% CI for slope
  if (is.null(w)) {
    model <- lm(y ~ x)
  } else {
    model <- lm(y ~ x, weights = w)
  }
  b_se <- summary(model)$coefficients[2,2]
  t_val <- qt(1 - alpha/2, df = n - 2)
  CI_lower <- b_WLP - t_val * b_se
  CI_upper <- b_WLP + t_val * b_se
  
  return(list(slope = b_WLP,
              intercept = a_WLP,
              CI_lower = CI_lower,
              CI_upper = CI_upper))
  
}

regression_stats <- function (DOA_to_regress){
  
  regression_list <- list()
  regression_table <- data.frame(
    par_comparison= character(),
    intercept= numeric(),
    slope = numeric(),
    stringsAsFactors = FALSE
  )
  

  for(name in names(DOA_to_regress)) {
    DOA <- DOA_to_regress[[name]]
    
    y <- DOA$var1   # FP → Y
    x <- DOA$var2   # Accelerometer → X
    
    # --- WLP regression ---
    res <- WLP(x, y)
    
    regression_list[[name]] <- paste("intercept:", round(res$intercept, 3),
                                     "slope:", round(res$slope, 3))
    
    regression_table <- rbind(
      regression_table,
      data.frame(
        par_comparison = name,
        intercept = round(res$intercept, 2),
        slope = round(res$slope, 2),
        stringsAsFactors = FALSE
      )
    )
    
  }
  
  return(regression_table)
}

logtransf_param <- function(var1_i,var2_i){
  
  var1_t <- log10(var1_i)
  var2_t <- log10(var2_i)
 
  diff_t <- var1_t - var2_t
  mean_t <- (var1_t + var2_t)/2
  fixed_bias_t <- mean(diff_t)
  
  return(list(
    var1_log= var1_t,
    var2_log = var2_t,
    diff_log = diff_t,
    mean_log = mean_t,
    fixed_bias_log = fixed_bias_t
  ))
}

boxtransf_param <- function (var1_i,var2_i){
  
  bn1 <- boxcox(var1_i)
  bn2 <- boxcox(var2_i)
  
  var1_t <- predict(bn1,var1_i)
  var2_t <- predict(bn2,var2_i)
  
  
  diff_t <- var1_t - var2_t
  mean_t <- (var1_t + var2_t)/2
  best_tr <- "Box-Cox"
  
  return(list(
    
    bn1 = bn1,
    bn2 = bn2,
    var1_box = var1_t,
    var2_box = var2_t,
    diff_box = diff_t,
    mean_box = mean_t,
    best_tr = best_tr
  ))

}

calibration_fixedbias <- function(
    list_tables,

proportional_calibration <- function(regression_table, param_tables, BA_tables) {

  proportional_param_tables <- list()
  DOA_new_fixed <- list()
  fixed_bias_prop <- list()
  
  for (name in names(param_tables)) {
    
    if (!(name %in% regression_table$par_comparison)) next

    # Extract labels
    par_label <- extract_par_accel_names(name)
    pair_label <- par_label$label
    
    
    row_indx <- which(regression_table$par_comparison == name)
    
    if (length(row_indx) == 0) next
    if (length(row_indx) > 1) {
      warning(paste("Multiple matches for", name))
      row_indx <- row_indx[1]
    }
    
    # Parameter selection
    par_type <- ifelse(row_indx <= 2, "MF", "centroidFreq")
    
    # Safer column access
    intercept <- regression_table$intercept[row_indx]
    slope <- regression_table$slope[row_indx]
    
    if (slope == 0) {
      warning(paste("Slope is zero for", name))
      next
    }
    
    df <- param_tables[[name]]

    # Calibration
    var2_corrected <- (df$var2 - intercept) / slope
    
    # Bland–Altman
    d <- df$var1 - var2_corrected
    mean_vals <- (var2_corrected + df$var1) / 2
    fixed_bias_OLS <- round(mean(d,na.rm=TRUE),2)
    
    # Establish fixed bias and substitute the value for the one obtained after
    # regression correction WITH NEW FIXED BIAS
    
    # # Ensure BA table exists
    # if (is.null(BA_tables[[pair_label]])) {
    #   BA_tables[[pair_label]] <- tibble(
    #     Parameter = par,
    #     sd = NA_real_,
    #     Var1_mean_SD = NA_character_,
    #     Var2_mean_SD = NA_character_,
    #     r = NA_real_,
    #     p_value = NA_real_,
    #     Fixed_bias = NA_real_,
    #     LoA = NA_character_,
    #     RPC = NA_real_
    #   )
    # }
    # 
    # 
    # BA_tables[[pair_label]] <- BA_tables[[pair_label]] %>%
    #   dplyr::mutate(
    #     Fixed_bias = ifelse(Parameter==par,round(mean(d),2),Fixed_bias),
    #     RPC = ifelse(Parameter == par, 1.96 * sd(d, na.rm = TRUE),RPC),
    #     sd = ifelse(Parameter == par, sd(d), sd),
    #     Var1_mean_SD = ifelse(Parameter == par,
    #                           sprintf("%.2f ± %.2f", mean(var1, na.rm = TRUE), sd(var1, na.rm = TRUE)),
    #                           Var1_mean_SD),
    #     Var2_mean_SD = ifelse(Parameter == par,
    #                           sprintf("%.2f ± %.2f", mean(var2, na.rm = TRUE), sd(var2, na.rm = TRUE)),
    #                           Var2_mean_SD),
    #     r = ifelse(Parameter == par, round(ct$estimate, 2), r),
    #     p_value = ifelse(Parameter == par, ct$p.value, p_value)
    #   )

    
    # Save in a same-structure list like param tables for the particular case of proportional bias 
    proportional_param_tables[[name]]<- tibble( var1 = df$var1, var2= var2_corrected, diff= d, mean = mean_vals, fixed_bias = fixed_bias_OLS ) 
    DOA_new_fixed[[length(DOA_new_fixed)+1]] <- name

  }
  
  return(list(
    proportional_param_tables= proportional_param_tables,
    DOA_new_fixed = DOA_new_fixed,
    BA_tables = BA_tables
  ))
}

calibrated_vars_extraction <- function(parameters, calibrated_accel) {
  
  fp_wo_outliers <- list()
  calibrated_l3 <- list()
  calibrated_trunk <- list()
  
  for (name in names(calibrated_accel)) {
    
    split_name <- strsplit(name, "_Platform_vs_")[[1]]
    if (length(split_name) != 2) next
    
    parameter <- trimws(split_name[1])
    accel_type <- trimws(split_name[2])
    platform_method <- "Platform"
    
    print(parameter)
    print(accel_type)
    
    if (!(parameter %in% parameters)) next
    
    df <- calibrated_accel[[name]]
    print(df)
    
    if (platform_method == "Platform") {
      fp_wo_outliers[[parameter]] <- df$var1
    }
    
    if (accel_type == "L3") {
      calibrated_l3[[parameter]] <- df$var2
    } else if (accel_type == "Trunk") {
      calibrated_trunk[[parameter]] <- df$var2
    }
  }
  
  return(list(
    fp_wo_outliers = as.data.frame(fp_wo_outliers),
    calibrated_l3 = as.data.frame(calibrated_l3),
    calibrated_trunk = as.data.frame(calibrated_trunk)
  ))
}

merge_unique <- function(...) {
  mats <- list(...)
  mats <- mats[sapply(mats, function(x) !is.null(x) && ncol(x) > 0)]
  
  if (length(mats) == 0) return(data.frame())
  
  result <- mats[[1]]
  
  for (i in 2:length(mats)) {
    new_cols <- setdiff(colnames(mats[[i]]), colnames(result))
    if (length(new_cols) > 0) {
      result <- cbind(result, mats[[i]][, new_cols, drop = FALSE])
    }
  }
  
  return(result)
}

create_BA_table <- function ( var1_orig, var2, diff, mean, par, p_value, fixed_bias, slope, p_slope, res_BA ){

  ct <- cor.test(var1, var2)
  # ---- BA TABLE ----

  BA_table <- tibble(
      Parameter = par,
      r = round(ct$estimate, 2),
      p_value = ct$p.value,
      Fixed_bias = fixed_bias,
      p_fixed = t.test(diff)$p.value,
      Proportional_bias = slope_value,
      p_proportional = slope_p,
      LoA = sprintf("[%.2f, %.2f]", res_BA$ll, res_BA$hl),
      sd = res_BA$sd,
      RPC = 1.96*res_BA$sd,
      Var1_mean_SD = sprintf("%.2f ± %.2f", mean(var1_orig), sd(var1)),
      Var2_mean_SD = sprintf("%.2f ± %.2f", mean(var2), sd(var2)),
    )
  
  return (BA_table)
  
}
