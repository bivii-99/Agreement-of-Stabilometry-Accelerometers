
###############################################################################
# 08_train_classifier.py
#
# Train and evaluate supervised classifiers.
#
# Pipeline
#   1. Load prepared dataset
#   2. Create classifiers
#   3. Train classifiers
#   4. Evaluate classifiers
#   5. Save trained models
#
# Input
#   - 07_dataset.pkl
#
# Output
#   - 08_classifier.pkl
###############################################################################

# =============================================================================
# Imports
# =============================================================================

from pathlib import Path
import sys
import joblib
import traceback
import pandas as pd

from config import *
import DAML_functions as f

# =============================================================================
# Paths
# =============================================================================

base = Path("Insert main path") if sys.platform == "darwin" else Path(r"Insert main path")

intermediate_dir = base / "Intermediate"

# =============================================================================
# Load dataset
# =============================================================================

datasets = joblib.load(intermediate_dir / "07_dataset.pkl")

# =============================================================================
# Output container
# =============================================================================

classifier_results = {}

# =============================================================================
# Main loop
# =============================================================================

for method, dataset in datasets.items():

    print(f"\n{'=' * 70}")
    print(f"METHOD: {method}")
    print(f"{'=' * 70}")

    X_train = dataset["X_train"]
    X_test = dataset["X_test"]

    y_train = dataset["y_train"]
    y_test = dataset["y_test"]

    scaler = dataset["scaler"]

    # =========================================================================
    # Models
    # =========================================================================

    models = {
        "RandomForest": f.RF_model(),
        "KNN": f.KNN_model(),
        "NaiveBayes": f.NB_model(),
        "FFN": None
    }

    train_results = []
    test_results = []
    trained_models = {}

# =============================================================================
# Train classifiers
# =============================================================================

for name, model in models.items():

    print(f"\nRUNNING MODEL: {name}")

    try:

        train_df, test_df = f.try_model_supervised(name, model, X_train, y_train, X_test, y_test)

        train_results.append(train_df)
        test_results.append(test_df)

        if name != "FFN":
            model.fit(X_train, y_train)

        trained_models[name] = model

    except Exception:

        print(f"FAILED: {name}")
        traceback.print_exc()

# =============================================================================
# Merge results
# =============================================================================

train_results = pd.concat(train_results, ignore_index=True)
test_results = pd.concat(test_results, ignore_index=True)
final_results = pd.concat([train_results, test_results], ignore_index=True)

# =============================================================================
# Store results
# =============================================================================

classifier_results[method] = {
    "models": trained_models,
    "scaler": scaler,
    "train_results": train_results,
    "test_results": test_results,
    "results": final_results
}

# =============================================================================
# Save classifiers
# =============================================================================

joblib.dump(classifier_results, intermediate_dir / "classifier.pkl")
joblib.dump(classifier_results, intermediate_dir / "scaler.pkl")

print("\n" + "=" * 70)
print("08_train_classifier.py completed successfully.")
print(f"Classifier and scaler saved to: {intermediate_dir}")
print("=" * 70)