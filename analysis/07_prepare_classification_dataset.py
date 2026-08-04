

###############################################################################
# 07_prepare_classification_dataset.py
#
# Prepare the classification dataset.
#
# Pipeline
#   1. Load augmented feature matrices
#   2. Divide subjects into four groups
#   3. Filter augmented features (k = 1.1)
#   4. Merge real + augmented features
#   5. Build training dataset
#
# Input
#   - 06_augmented_features.pkl
#
# Output
#   - 07_dataset.pkl
###############################################################################

# =============================================================================
# Imports
# =============================================================================

from pathlib import Path
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from config import *
import DAML_functions as f

# =============================================================================
# Paths
# =============================================================================

base = Path("Insert main path") if sys.platform == "darwin" else Path(r"Insert main path")

intermediate_dir = base / "Intermediate"

# =============================================================================
# Configuration
# =============================================================================

PARAMETERS = ["Max_dev_AP", "PATH", "DIST", "freqDispersion"]
PARAMS_REF = ["PATH", "DIST", "freqDispersion"]

METHODS = ["COP", "Trunk"] # Use only Trunk accelerometer


# =============================================================================
# Load datasets
# =============================================================================

real_data = joblib.load(CALIBRATED_DATA)
augmented_data = joblib.load(AUGMENTED_FEATURES)

# =============================================================================
# Output container
# =============================================================================

datasets = {}

# =============================================================================
# Main loop
# =============================================================================

for method in METHODS:

    print(f"\n{'=' * 70}")
    print(f"METHOD: {method}")
    print(f"{'=' * 70}")

    if method == "COP":

        df_real = real_data["fp"].copy()

    elif method == "L3":

        df_real = real_data["l3"].copy()

    else:

        df_real = real_data["trunk"].copy()
    # -------------------------------------------------------------------------
    # Divide REAL data into groups
    # -------------------------------------------------------------------------

    g0_real, g1_real, g2_real, g3_real = mf.divide_by_group(df_real, PARAMETERS)

    for g in (g0_real, g1_real, g2_real, g3_real):

        g["source"] = "real"

    # -------------------------------------------------------------------------
    # Divide AUGMENTED data into groups
    # -------------------------------------------------------------------------

    g0_aug, g1_aug, g2_aug, g3_aug = mf.divide_by_group(df_aug, PARAMETERS)

    # -------------------------------------------------------------------------
    # Filter augmented features (k = 1.1)
    # -------------------------------------------------------------------------

    idx0 = mf.select_median_band_indices(g0_aug, PARAMS_REF, k=K_MAD)
    idx1 = mf.select_median_band_indices(g1_aug, PARAMS_REF, k=K_MAD)
    idx2 = mf.select_median_band_indices(g2_aug, PARAMS_REF, k=K_MAD)
    idx3 = mf.select_median_band_indices(g3_aug, PARAMS_REF, k=K_MAD)

    g0_aug = g0_aug.loc[idx0].copy()
    g1_aug = g1_aug.loc[idx1].copy()
    g2_aug = g2_aug.loc[idx2].copy()
    g3_aug = g3_aug.loc[idx3].copy()

    for g in (g0_aug, g1_aug, g2_aug, g3_aug):

        g["source"] = "augmented"

    # =============================================================================
    # Merge real + augmented features
    # =============================================================================

    G0 = pd.concat([g0_real, g0_aug], ignore_index=True)
    G1 = pd.concat([g1_real, g1_aug], ignore_index=True)
    G2 = pd.concat([g2_real, g2_aug], ignore_index=True)
    G3 = pd.concat([g3_real, g3_aug], ignore_index=True)

    G0["group"] = 0
    G1["group"] = 1
    G2["group"] = 2
    G3["group"] = 3

    # =============================================================================
    # Build classification dataset
    # =============================================================================

    X_df = pd.concat([G0, G1, G2, G3], ignore_index=True)

    metadata = X_df[["group", "source"]].copy()

    X = X_df.drop(columns=["group", "source"])
    y = X_df["group"]

    indices = np.arange(len(X))

    # =============================================================================
    # Train / Test split
    # =============================================================================

    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X,
        y,
        indices,
        TEST_SIZE,
        RANDOM_STATE,
        shuffle=True,
        stratify=y
    )

    # =============================================================================
    # Feature preprocessing
    # =============================================================================

    X_train, X_test, scaler = f.preprocess_data(
        X_train,
        X_test
    )

    # =============================================================================
    # Store dataset
    # =============================================================================

    datasets[method] = {

        "X_train": X_train,
        "X_test": X_test,

        "y_train": y_train.values,
        "y_test": y_test.values,

        "idx_train": idx_train,
        "idx_test": idx_test,

        "metadata": metadata,

        "scaler": scaler

    }

# =============================================================================
# Save dataset
# =============================================================================

joblib.dump(
    datasets,
    intermediate_dir / "07_dataset.pkl"
)

print("\n" + "=" * 70)
print("07_prepare_dataset.py completed successfully.")
print(f"Dataset saved to: {intermediate_dir / '07_dataset.pkl'}")
print("=" * 70)