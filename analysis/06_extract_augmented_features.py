###############################################################################
# 06_extract_augmented_features.py
#
# Extract time- and frequency-domain features from augmented trajectories.
#
# Input
#   - 05_augmented_trajectories.pkl
#
# Output
#   - 06_augmented_features.pkl
###############################################################################

# =============================================================================
# Imports
# =============================================================================

from config import *
import functions_to_extract_features as ff

import joblib
import pandas as pd

# =============================================================================
# Load augmented trajectories
# =============================================================================

augmented_data = joblib.load(AUGMENTED_TRAJECTORIES)

# =============================================================================
# Extract features
# =============================================================================

augmented_features = {"COP": {}, "Trunk": {}}

for method in METHODS:

    fs = fs_fp if method == "COP" else fs_accel

    for group in GROUPS:

        print(f"Extracting features: {method} - {group}")

        ap = augmented_data[method][group]["AP"]
        ml = augmented_data[method][group]["ML"]

        features = []

        for i in range(ap.shape[1]):

            features.append(ff.extract_features(ap.iloc[:, i],ml.iloc[:, i],fs))

        augmented_features[method][group] = pd.DataFrame(features)

# =============================================================================
# Save augmented features
# =============================================================================

joblib.dump(
    augmented_features,
    AUGMENTED_FEATURES
)

print("=" * 70)
print("06_extract_augmented_features.py completed successfully.")
print("=" * 70)