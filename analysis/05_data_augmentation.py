

###############################################################################
# 05_data_augmentation.py
#
# Generate augmented trajectories for COP and Trunk measurements.
#
# Pipeline
#   1. Load trajectory matrices
#   2. Divide trajectories into four clinical groups
#   3. Generate synthetic trajectories
#   4. Save augmented trajectories
#
# Input
#   - Trajectory matrices
#   - lss_array.csv
#   - df_pedana.xlsx
#   - df_trunk.xlsx
#
# Output
#   - 05_augmented_trajectories.pkl
###############################################################################

# =============================================================================
# Imports
# =============================================================================
from config import *
import DAML_functions as f

from pathlib import Path
import sys
import joblib
import numpy as np
import pandas as pd


# =============================================================================
# Load metadata
# =============================================================================

lss_array = pd.read_csv(TRAJECTORY_DIR / "lss_array.csv").to_numpy().flatten()

parameter_tables = {
    "COP": pd.read_excel(PARAMETER_DIR / "df_pedana.xlsx"),
    "Trunk": pd.read_excel(PARAMETER_DIR / "df_trunk.xlsx")
}

# =============================================================================
# Load trajectory matrices
# =============================================================================

trajectory_data = {
    "COP": {
        "healthy_x": pd.read_excel(HEALTHY_DIR / "Pedana" / "COP_X_traj.xlsx"),
        "healthy_y": pd.read_excel(HEALTHY_DIR / "Pedana" / "COP_Y_traj.xlsx"),
        "patients_x": pd.read_excel(PATIENTS_DIR / "Pedana" / "COP_X_traj.xlsx"),
        "patients_y": pd.read_excel(PATIENTS_DIR / "Pedana" / "COP_Y_traj.xlsx")
    },
    "Trunk": {
        "healthy_x": pd.read_excel(HEALTHY_DIR / "Trunk_accel" / "Trunk_X_traj.xlsx"),
        "healthy_y": pd.read_excel(HEALTHY_DIR / "Trunk_accel" / "Trunk_Y_traj.xlsx"),
        "patients_x": pd.read_excel(PATIENTS_DIR / "Trunk_accel" / "Trunk_X_traj.xlsx"),
        "patients_y": pd.read_excel(PATIENTS_DIR / "Trunk_accel" / "Trunk_Y_traj.xlsx")
    }
}

# =============================================================================
# Output container
# =============================================================================

augmented_data = {"COP": {}, "Trunk": {}}

# =============================================================================
# Main loop
# =============================================================================

for method in METHODS:

    print(f"\n{'=' * 70}\nMETHOD: {method}\n{'=' * 70}")

    df_attr = parameter_tables[method]
    traj = trajectory_data[method]

    all_matrices = [
        trajectory_data["Trunk"]["healthy_x"], trajectory_data["Trunk"]["healthy_y"],
        trajectory_data["COP"]["healthy_x"], trajectory_data["COP"]["healthy_y"],
        trajectory_data["Trunk"]["patients_x"], trajectory_data["Trunk"]["patients_y"],
        trajectory_data["COP"]["patients_x"], trajectory_data["COP"]["patients_y"]
    ]

    lss_patients = lss_array[1:len(lss_array) - trajectory_data["COP"]["healthy_x"].shape[1] + 1]

    val_x0, val_x1, val_x2, val_x3, val_y0, val_y1, val_y2, val_y3, class_attribute = \
        f.establish_method_class(all_matrices, lss_patients, method=method)

    groups = {
        "Healthy": {"x": val_x0, "y": val_y0},
        "Dependent": {"x": val_x1, "y": val_y1},
        "Static": {"x": val_x2, "y": val_y2},
        "Independent": {"x": val_x3, "y": val_y3}
    }
    
    # =============================================================================
    # Compute group medians
    # =============================================================================

    median_x = {group: np.median(df_attr.loc[groups[group]["x"].columns, PAR_X]) for group in GROUPS}
    median_y = {group: np.median(df_attr.loc[groups[group]["y"].columns, PAR_Y]) for group in GROUPS}

    # =============================================================================
    # Generate augmented trajectories
    # =============================================================================

    augmented_data[method] = {}

    for group in GROUPS:

        print(f"Generating {method} - {group}")

        df_x = groups[group]["x"]
        df_y = groups[group]["y"]

        indices_x, indices_y, aug_x, aug_y, names = f.get_augmented_data(
            df_attr=df_attr,
            par_x=PAR_X,
            par_y=PAR_Y,
            df_x=df_x,
            df_y=df_y,
            iter=N_SYNTHETIC,
            median_x=median_x[group],
            median_y=median_y[group],
            class_attribute=class_attribute,
            n_points=df_x.shape[0]
        )

        augmented_data[method][group] = {
            "X": aug_x,
            "Y": aug_y,
            "Names": names,
            "Parent_X": indices_x,
            "Parent_Y": indices_y
        }

        print(
            f"   Original trajectories : {df_x.shape[1]}\n"
            f"   Augmented trajectories: {aug_x.shape[1]}"
        )

    print(f"{method} completed.\n")

# =============================================================================
# Save augmented trajectories
# =============================================================================

joblib.dump(
    augmented_data,
    INTERMEDIATE_DIR / "05_augmented_trajectories.pkl"
)

print("=" * 70)
print("05_data_augmentation.py completed successfully.")
print("=" * 70)




