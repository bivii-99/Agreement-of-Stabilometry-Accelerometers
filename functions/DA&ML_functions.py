###############################################################################
# classification_functions.py
#
# Shared functions for the stabilometric classification pipeline.
#
# Sections
#   1. Trajectory preprocessing
#   2. Data augmentation
#   3. Machine learning
###############################################################################

# =============================================================================
# Imports
# =============================================================================

import math
import random

import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from scipy.linalg import eigh
from scipy.signal import resample, find_peaks
from scipy.stats import skew

import torch
import torch.nn as nn
import torch.optim as optim

from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.manifold import TSNE
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    f1_score,
    precision_score,
    recall_score
)
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

from config import *

sns.set()

# =============================================================================
# TRAJECTORY PREPROCESSING
# =============================================================================

def safe_read_excel(file, col_indices):

    df = pd.read_excel(file)

    valid_cols = [i for i in col_indices if i < df.shape[1]]

    if not valid_cols:
        return pd.DataFrame(index=df.index)

    return df.iloc[:, valid_cols]


def drop_empty_tests(matrices, n_tests):

    cleaned = []

    for matrix in matrices:
        cleaned.append(matrix.iloc[:, :n_tests])

    return cleaned


def resample_matrix(matrix):

    if matrix.shape[0] <= 10000:
        return matrix

    n_samples = int(matrix.shape[0] * 100 / 1000)

    return resample(matrix, n_samples, axis=0)


def traj_centering(matrix):
    return matrix - matrix.mean()


def preparing_input_traj(matrix):

    matrix = resample_matrix(matrix)
    matrix = traj_centering(matrix)

    return matrix


# =============================================================================
# GENERAL SIGNAL UTILITIES
# =============================================================================

def get_rms(df):
    return np.sqrt(np.mean(df ** 2))

def get_acc(signal):
    return pd.DataFrame.diff(pd.DataFrame.diff(signal / 0.04))

def get_rms_global(x, y):
    return (
        np.sqrt(np.mean(x ** 2)),
        np.sqrt(np.mean(y ** 2))
    )


def get_acc_global(x, y):

    acc_x = pd.DataFrame.diff(
        pd.DataFrame.diff(x / 0.04)
    )

    acc_y = pd.DataFrame.diff(
        pd.DataFrame.diff(y / 0.04)
    )

    return acc_x[2:], acc_y[2:]


def get_path(x, y):
    return np.sum(np.sqrt(x ** 2 + y ** 2))


def get_fft(signal, n_points):

    signal = signal.dropna()
    f = np.linspace(0,1 / (2 * (1 / 25)),n_points // 2)
    power = np.abs( np.fft.fft(signal))[: n_points // 2]
    idx = f <= 4

    return f[idx], power[idx]


def get_f80(f, power, low, high):

    return np.sum(
        power[(f >= low) & (f < high)]
    ) * 4 / 5


def get_mean_freq(f, power, low, high):

    return np.mean(
        power[(f >= low) & (f < high)]
    )


def get_sampen(signal, m, r):

    N = len(signal)

    xmi = np.array([signal[i:i+m] for i in range(N-m)])
    xmj = np.array([signal[i:i+m] for i in range(N-m+1)])

    B = np.sum([np.sum(np.abs(xmii - xmj).max(axis=1) <= r) - 1for xmii in xmi])

    m += 1

    xm = np.array([signal[i:i+m] for i in range(N-m+1)])

    A = np.sum([np.sum(np.abs(xmi - xm).max(axis=1) <= r) - 1for xmi in xm])

    return -np.log(A / B)

# =============================================================================
# DATA AUGMENTATION
# =============================================================================

GROUP_COLORS = {"healthy": "tab:green", "dependent": "tab:red", "static": "tab:orange", "independent": "tab:blue"}

GROUP_LABELS = {"healthy": "Healthy", "dependent": "Dependent (LSS < 6)", "static": "Static (LSS = 6)", "independent": "Independent (LSS > 6)"}

# =============================================================================
# AUGMENTATION UTILITIES
# =============================================================================

def get_randomsamples(low_index, high_index, n_values, df):

    samples = random.sample(range(low_index, high_index), n_values)

    output = pd.DataFrame()

    for sample in samples:

        try:
            output = pd.concat([output, df.loc[:, str(sample)]], axis=1)
        except KeyError:
            continue

    return output


def establish_method_class(all_matrices, lss_array, method="COP"):

    healthy_xtrunk, healthy_ytrunk, healthy_xcop, healthy_ycop, patients_xtrunk, patients_ytrunk, patients_xcop, patients_ycop = all_matrices

    if method == "COP":
        hx, hy = healthy_xcop, healthy_ycop
        px, py = patients_xcop, patients_ycop
    elif method == "Trunk":
        hx, hy = healthy_xtrunk, healthy_ytrunk
        px, py = patients_xtrunk, patients_ytrunk
    else:
        raise ValueError("method must be 'COP' or 'Trunk'")

    dependent = lss_array < 6
    static = lss_array == 6
    independent = lss_array > 6

    val_x0, val_y0 = hx, hy
    val_x1, val_y1 = px.iloc[:, dependent], py.iloc[:, dependent]
    val_x2, val_y2 = px.iloc[:, static], py.iloc[:, static]
    val_x3, val_y3 = px.iloc[:, independent], py.iloc[:, independent]

    class_attribute = pd.concat([
        pd.DataFrame({"Path": val_x0.columns, "Class": "Healthy"}),
        pd.DataFrame({"Path": val_x1.columns, "Class": "Dependent"}),
        pd.DataFrame({"Path": val_x2.columns, "Class": "Static"}),
        pd.DataFrame({"Path": val_x3.columns, "Class": "Independent"})
    ], ignore_index=True)

    return val_x0, val_x1, val_x2, val_x3, val_y0, val_y1, val_y2, val_y3, class_attribute


# =============================================================================
# GENETIC OPERATORS
# =============================================================================

def selection(df_attr, median_value, n_subjects):

    rand_1 = random.sample(range(n_subjects), 10)
    rand_2 = random.sample(range(n_subjects), 10)

    while rand_1 == rand_2:
        rand_2 = random.sample(range(n_subjects), 10)

    return random.choice(rand_1), random.choice(rand_2)


def crossover(divisions, keep_segments, parent_1, parent_2, n_points):

    selected = np.sort(random.sample(range(divisions), keep_segments))
    child = pd.DataFrame()
    step = int(n_points / divisions)

    for i, start in enumerate(range(0, n_points, step)):
        end = start + step
        child = pd.concat([child, parent_1[start:end] if i in selected else parent_2[start:end]], ignore_index=True)

    return child


def mutation(divisions, keep_segments, crossed, parent, n_points):

    selected = np.sort(random.sample(range(divisions), keep_segments))
    average = pd.concat([crossed, parent], axis=1).mean(axis=1)
    child = pd.DataFrame()
    step = int(n_points / divisions)

    for i, start in enumerate(range(0, n_points, step)):
        end = start + step
        child = pd.concat([child, crossed[start:end] if i in selected else average[start:end]], ignore_index=True)

    return child


# =============================================================================
# AUGMENTED TRAJECTORY GENERATION
# =============================================================================

def get_augmented_data(df_attr, par_x, par_y, df_x, df_y, n_synthetic, median_x, median_y, class_attribute, n_points):

    indices_x, indices_y = [], []
    RX, RY = pd.DataFrame(), pd.DataFrame()
    names = pd.DataFrame(columns=["Axis", "Path", "Class"])

    i = 0

    while n_synthetic > 0:

        idx_x1, idx_x2 = selection(df_attr[par_x], median_x, df_x.shape[1] - 1)
        idx_y1, idx_y2 = selection(df_attr[par_y], median_y, df_y.shape[1] - 1)

        indices_x.append(idx_x2)
        indices_y.append(idx_y2)

        names.loc[len(names)] = ["x", class_attribute.iloc[idx_x1, 0], class_attribute.iloc[idx_x1, 1]]
        names.loc[len(names)] = ["y", class_attribute.iloc[idx_y1, 0], class_attribute.iloc[idx_y1, 1]]

        X1, X2 = df_x.iloc[:, idx_x1], df_x.iloc[:, idx_x2]
        Y1, Y2 = df_y.iloc[:, idx_y1], df_y.iloc[:, idx_y2]

        cross_x = crossover(20, 10, X1, X2, n_points)
        cross_y = crossover(20, 10, Y1, Y2, n_points)

        mut_x = mutation(20, 10, cross_x, X2, n_points)
        mut_y = mutation(20, 10, cross_y, Y2, n_points)

        RX.insert(i, i, mut_x.iloc[:, 0])
        RY.insert(i, i, mut_y.iloc[:, 0])

        i += 1
        n_synthetic -= 1

        if n_synthetic % 100 == 0:
            print(f"Remaining iterations: {n_synthetic}")

    return indices_x, indices_y, RX, RY, names



# =============================================================================
# DATASET PREPARATION
# =============================================================================

def preprocess_data(X_train, X_test):

    imputer = SimpleImputer(strategy="median")

    X_train = imputer.fit_transform(X_train)
    X_test = imputer.transform(X_test)

    scaler = StandardScaler()

    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    return X_train, X_test, scaler


def build_dataset(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE):

    indices = np.arange(len(X))

    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X,
        y,
        indices,
        test_size=test_size,
        random_state=random_state,
        shuffle=True,
        stratify=y
    )

    X_train, X_test, scaler = preprocess_data(X_train, X_test)

    return {
        "X_train": X_train,
        "X_test": X_test,
        "y_train": np.asarray(y_train).ravel(),
        "y_test": np.asarray(y_test).ravel(),
        "idx_train": idx_train,
        "idx_test": idx_test,
        "scaler": scaler
    }


# =============================================================================
# SUPERVISED MODELS
# =============================================================================

def RF_model():

    return RandomForestClassifier(**RF_PARAMETERS)


def KNN_model():

    return KNeighborsClassifier(**KNN_PARAMETERS)


def NB_model():

    return GaussianNB()


def FFN_model(X_train, y_train):

    hidden = FFN_PARAMETERS["hidden_units"]
    epochs = FFN_PARAMETERS["epochs"]
    lr = FFN_PARAMETERS["learning_rate"]

    class FFNWrapper:

        def __init__(self):

            self.model = nn.Sequential(
                nn.Linear(X_train.shape[1], hidden),
                nn.ReLU(),
                nn.Linear(hidden, hidden),
                nn.ReLU(),
                nn.Linear(hidden, 4)
            )

        def fit(self, X, y):

            X = torch.tensor(X, dtype=torch.float32)
            y = torch.tensor(y, dtype=torch.long)

            criterion = nn.CrossEntropyLoss()
            optimizer = optim.SGD(self.model.parameters(), lr=lr)

            for _ in range(epochs):

                prediction = self.model(X)

                loss = criterion(prediction, y)

                optimizer.zero_grad()

                loss.backward()

                optimizer.step()

        def predict(self, X):

            X = torch.tensor(X, dtype=torch.float32)

            with torch.no_grad():

                return self.model(X).argmax(dim=1).numpy()

    model = FFNWrapper()

    model.fit(X_train, y_train)

    return model


def available_models(X_train=None, y_train=None):

    models = {
        "RandomForest": RF_model(),
        "KNN": KNN_model(),
        "NaiveBayes": NB_model()
    }

    if X_train is not None and y_train is not None:
        models["FFN"] = FFN_model(X_train, y_train)

    return models


# =============================================================================
# HIERARCHICAL CLASSIFIER
# =============================================================================

def train_classifier(model_name, model, X_train, y_train, X_test, y_test):

    y_train = np.asarray(y_train).ravel()
    y_test = np.asarray(y_test).ravel()

    # =========================================================================
    # NODE 1 : HEALTHY VS PATIENT
    # =========================================================================

    y_train_node1 = (y_train != 0).astype(int)

    if model_name == "FFN":
        model_node1 = FFN_model(X_train, y_train_node1)
    else:
        model_node1 = clone(model)
        model_node1.fit(X_train, y_train_node1)

    # =========================================================================
    # NODE 2 : PATIENT SEVERITY
    # =========================================================================

    patient_mask = y_train != 0

    X_train_patients = X_train[patient_mask]
    y_train_patients = y_train[patient_mask] - 1

    if model_name == "FFN":
        model_node2 = FFN_model(X_train_patients, y_train_patients)
    else:
        model_node2 = clone(model)
        model_node2.fit(X_train_patients, y_train_patients)

    # =========================================================================
    # TRAIN PREDICTIONS
    # =========================================================================

    y_pred_train = np.zeros(len(X_train), dtype=int)

    node1_train = np.asarray(model_node1.predict(X_train)).astype(int)

    patient_prediction = node1_train == 1

    if np.any(patient_prediction):

        node2_train = np.asarray(
            model_node2.predict(X_train[patient_prediction])
        ).astype(int) + 1

        y_pred_train[patient_prediction] = node2_train

    # =========================================================================
    # TEST PREDICTIONS
    # =========================================================================

    y_pred_test = np.zeros(len(X_test), dtype=int)

    node1_test = np.asarray(model_node1.predict(X_test)).astype(int)

    patient_prediction = node1_test == 1

    if np.any(patient_prediction):

        node2_test = np.asarray(
            model_node2.predict(X_test[patient_prediction])
        ).astype(int) + 1

        y_pred_test[patient_prediction] = node2_test

    # =========================================================================
    # PERFORMANCE
    # =========================================================================

    train_results = hierarchical_metrics(
        y_train,
        y_pred_train,
        model_name,
        "train"
    )

    test_results = hierarchical_metrics(
        y_test,
        y_pred_test,
        model_name,
        "test"
    )

    if model_name == "RandomForest":
        confusion_matrix_f(y_test, y_pred_test)

    # =========================================================================
    # RETURN
    # =========================================================================

    return {
        "node1": model_node1,
        "node2": model_node2,
        "train_results": train_results,
        "test_results": test_results,
        "y_pred_train": y_pred_train,
        "y_pred_test": y_pred_test
    }


# =============================================================================
# CONFUSION MATRICES
# =============================================================================

def confusion_matrix_f(y_true, y_pred):

    # -------------------------------------------------------------------------
    # NODE 1 : Healthy vs Patient
    # -------------------------------------------------------------------------

    y_true_node1 = (y_true != 0).astype(int)
    y_pred_node1 = (y_pred != 0).astype(int)

    cm1 = confusion_matrix(y_true_node1, y_pred_node1, labels=[0, 1])

    disp = ConfusionMatrixDisplay(confusion_matrix=cm1, display_labels=["Healthy", "Patient"])
    disp.plot(cmap="Blues")
    plt.title("Random Forest - Node 1")
    plt.show()

    # -------------------------------------------------------------------------
    # NODE 2 : Patient severity
    # -------------------------------------------------------------------------

    patient_mask = y_true != 0

    y_true_patients = y_true[patient_mask]
    y_pred_patients = y_pred[patient_mask]

    cm2 = confusion_matrix(y_true_patients, y_pred_patients, labels=[1, 2, 3])

    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm2,
        display_labels=["Dependent", "Static", "Independent"]
    )

    disp.plot(cmap="Greens")
    plt.title("Random Forest - Node 2")
    plt.show()


# =============================================================================
# PERFORMANCE METRICS
# =============================================================================

def hierarchical_metrics(y_true, y_pred, model_name, dataset):

    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    results = []

    # -------------------------------------------------------------------------
    # NODE 1
    # -------------------------------------------------------------------------

    y_true_node1 = (y_true != 0).astype(int)
    y_pred_node1 = (y_pred != 0).astype(int)

    results.append({
        "Model": model_name,
        "Dataset": dataset,
        "Node": "Healthy vs Patient",
        "Accuracy": accuracy_score(y_true_node1, y_pred_node1),
        "Precision": precision_score(y_true_node1, y_pred_node1, average="binary", zero_division=0),
        "Recall": recall_score(y_true_node1, y_pred_node1, average="binary", zero_division=0),
        "F1-score": f1_score(y_true_node1, y_pred_node1, average="binary", zero_division=0)
    })

    # -------------------------------------------------------------------------
    # NODE 2
    # -------------------------------------------------------------------------

    patient_mask = y_true != 0

    if np.any(patient_mask):

        y_true_patients = y_true[patient_mask]
        y_pred_patients = y_pred[patient_mask]

        results.append({
            "Model": model_name,
            "Dataset": dataset,
            "Node": "Dependent vs Static vs Independent",
            "Accuracy": accuracy_score(y_true_patients, y_pred_patients),
            "Precision": precision_score(y_true_patients, y_pred_patients, average="macro", zero_division=0),
            "Recall": recall_score(y_true_patients, y_pred_patients, average="macro", zero_division=0),
            "F1-score": f1_score(y_true_patients, y_pred_patients, average="macro", zero_division=0)
        })

    else:

        results.append({
            "Model": model_name,
            "Dataset": dataset,
            "Node": "Dependent vs Static vs Independent",
            "Accuracy": np.nan,
            "Precision": np.nan,
            "Recall": np.nan,
            "F1-score": np.nan
        })

    return pd.DataFrame(results)


# =============================================================================
# AVAILABLE CLASSIFIERS
# =============================================================================

def available_models(X_train=None, y_train=None):

    models = {
        "RandomForest": RF_model(),
        "KNN": KNN_model(),
        "NaiveBayes": NB_model()
    }

    if X_train is not None and y_train is not None:
        models["FFN"] = FFN_model(X_train, y_train)

    return models