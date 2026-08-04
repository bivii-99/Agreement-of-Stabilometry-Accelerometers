
###############################################################################
# 00_config.py
#
# Global configuration for the Python machine learning pipeline.
#
# Shared by:
#   - 05_data_augmentation.py
#   - 06_extract_augmented_features.py
#   - 07_prepare_dataset.py
#   - 08_train_classifier.py
###############################################################################

from pathlib import Path
import sys

# =============================================================================
# PROJECT PATHS
# =============================================================================

PROJECT_DIR = Path("Insert main path") if sys.platform == "darwin" else Path(r"Insert main path")

INTERMEDIATE_DIR = PROJECT_DIR / "Intermediate"
TRAJECTORY_DIR = PROJECT_DIR / "Trajectory matrices"
PARAMETER_DIR = PROJECT_DIR / "Table results"
CLASSIFIER_DIR = PROJECT_DIR / "Classifier"
GRAPH_DIR = PROJECT_DIR / "Graphs"

CLASSIFIER_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# INTERMEDIATE FILES
# =============================================================================

CALIBRATED_DATA = INTERMEDIATE_DIR / "04_calibrated_data.rds"
AUGMENTED_TRAJECTORIES = INTERMEDIATE_DIR / "05_augmented_trajectories.pkl"
AUGMENTED_FEATURES = INTERMEDIATE_DIR / "06_augmented_features.pkl"
DATASET = INTERMEDIATE_DIR / "07_dataset.pkl"
CLASSIFIER = INTERMEDIATE_DIR / "08_classifier.pkl"

# =============================================================================
# FINAL OUTPUTS
# =============================================================================

RF_MODEL = CLASSIFIER_DIR / "RF.pkl"
SCALER_MODEL = CLASSIFIER_DIR / "scaler.pkl"

TRAIN_RESULTS = CLASSIFIER_DIR / "train_results.xlsx"
TEST_RESULTS = CLASSIFIER_DIR / "test_results.xlsx"
SUPERVISED_RESULTS = CLASSIFIER_DIR / "results_supervised.xlsx"

NODE1_CONFUSION = CLASSIFIER_DIR / "confusion_matrix_node1.png"
NODE2_CONFUSION = CLASSIFIER_DIR / "confusion_matrix_node2.png"


# =============================================================================
# ACQUISITION PARAMETERS
# =============================================================================
fs_fp= 200
fs_accel = 1000


# =============================================================================
# ACQUISITION METHODS
# =============================================================================

METHODS = ["COP", "L3", "Trunk"]
GROUPS = ["Healthy", "Dependent", "Static", "Independent"]

# =============================================================================
# FEATURE SET
# =============================================================================

FEATURES = ["Max_dev_AP", "Max_dev_ML", "PATH", "DIST", "freqDispersion"]

REFERENCE_PARAMETERS = ["PATH", "DIST", "freqDispersion"]

PAR_X = "PATH"
PAR_Y = "F95"

# =============================================================================
# DATA AUGMENTATION
# =============================================================================

N_SYNTHETIC = 3000
K_MAD = 1.1

# =============================================================================
# TRAIN / TEST
# =============================================================================

TEST_SIZE = 0.20
RANDOM_STATE = 42

# =============================================================================
# RANDOM FOREST
# =============================================================================

RF_PARAMETERS = {
    "n_estimators": 10,
    "criterion": "entropy",
    "max_depth": 6,
    "ccp_alpha": 0.01,
    "random_state": RANDOM_STATE
}

# =============================================================================
# KNN
# =============================================================================

KNN_PARAMETERS = {
    "n_neighbors": 3
}

# =============================================================================
# FEEDFORWARD NEURAL NETWORK
# =============================================================================

FFN_PARAMETERS = {
    "hidden_units": 50,
    "epochs": 30,
    "learning_rate": 0.01
}

# =============================================================================
# PLOTS
# =============================================================================

FIGURE_SIZE = (8, 6)
DPI = 300
FONT = "Times New Roman"

# =============================================================================
# COLORS
# =============================================================================

GROUP_COLORS = {
    "Healthy": "blue",
    "Dependent": "red",
    "Static": "orange",
    "Independent": "green"
}