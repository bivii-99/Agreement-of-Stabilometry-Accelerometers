###############################################################################
# 00_config.R
#
# Configuration file for the Bland–Altman agreement analysis between
# force plate and IMU-derived stabilometric parameters.
#
# This script defines:
#   - required packages
#   - project directories
#   - input/output files
#   - analysis parameters
#   - comparison pairs
#   - helper functions
###############################################################################


#==============================================================================
# Required packages
#==============================================================================

library(BlandAltmanLeh)
library(bestNormalize)
library(dplyr)
library(ggplot2)
library(ggrepel)
library(plotly)
library(purrr)
library(readxl)
library(refineR)
library(scatterplot3d)
library(writexl)

#==============================================================================
# Directory creation
#==============================================================================
#------------------------------------------------------------------------------
# Project directories
#------------------------------------------------------------------------------

# Root directory of the repository
project_dir <- "."

# Input data
input_dir <- file.path(project_dir, "data")

# Output directories
results_dir      <- file.path(project_dir, "results")
graphs_dir       <- file.path(results_dir, "figures")
tables_dir       <- file.path(results_dir, "tables")
intermediate_dir <- file.path(project_dir, "intermediate")

# Helper functions
functions_dir <- file.path(project_dir, "functions")


#------------------------------------------------------------------------------
# Input files
#------------------------------------------------------------------------------

platform_file <- file.path(input_dir, "df_platform.xlsx")
l3_file       <- file.path(input_dir, "df_l3.xlsx")
trunk_file    <- file.path(input_dir, "df_trunk.xlsx")
lss_file      <- file.path(input_dir, "subjects_lss.xlsx")


#------------------------------------------------------------------------------
# Output folders
#------------------------------------------------------------------------------

graph_param_dir      <- file.path(graphs_dir, "parametric")
graph_nonparam_dir   <- file.path(graphs_dir, "nonparametric")
graph_regression_dir <- file.path(graphs_dir, "regression")
graph_calibration_dir<- file.path(graphs_dir, "calibration")

summary_dir          <- file.path(tables_dir, "summary")
calibrated_dir       <- file.path(tables_dir, "calibrated")



#------------------------------------------------------------------------------
# Create the dirs if empty
#------------------------------------------------------------------------------

dirs <- c(results_dir,graphs_dir,tables_dir,summary_dir,calibrated_dir,graph_param_dir,graph_nonparam_dir,graph_regression_dir,graph_calibration_dir,intermediate_dir)

invisible(
  lapply(dirs, dir.create,
         recursive = TRUE,
         showWarnings = FALSE)
)


#==============================================================================
# Analysis parameters
#==============================================================================

param_parameters <- c(
  "area_cop", "Max_dev_AP", "Max_dev_ML", "PATH", "MF",
  "DIST", "RMS", "avg_vel", "totalPower", "centroidFreq", "freqDispersion"
)
nonparam_parameters <- c("F50", "F95")


#==============================================================================
# Bland–Altman comparisons
#==============================================================================

pair_definitions <- list(
  
  list(
    label = "Platform_vs_L3",
    v1 = "fp",
    v2 = "l3"
  ),
  
  list(
    label = "Platform_vs_Trunk",
    v1 = "fp",
    v2 = "trunk"
  )
  
)


#==============================================================================
# Load custom functions
#==============================================================================

source(file.path(functions_dir, "agreement_functions.R"))



