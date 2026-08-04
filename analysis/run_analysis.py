
###############################################################################
# run_analysis.py
#
# Main execution script for the machine learning pipeline.
#
# Pipeline
#   05. Data augmentation
#   06. Extract augmented features
#   07. Prepare dataset
#   08. Train classifier
#
# Author:
###############################################################################
import subprocess
import sys
from config import *

ROOT = PROJECT_DIR

R_PIPELINE = [
    "00_config.R",
    "01_load_data.R",
    "02_preprocessing.R",
    "03_parametric.R",
    "03_nonparametric.R",
    "04_merge_calibration.R"
]

PYTHON_PIPELINE = [
    "00_config.py",
    "05_data_augmentation.py",
    "06_extract_augmented_features.py",
    "07_prepare_dataset.py",
    "08_train_classifier.py"
]


for script in R_PIPELINE:
    subprocess.run(["Rscript", ROOT / script], check=True)

for script in PYTHON_PIPELINE:
    subprocess.run([sys.executable, ROOT / script],check=True)