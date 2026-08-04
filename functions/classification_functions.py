
import pandas as pd
import numpy as np

from scipy.signal import resample
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.stats import skew
from sklearn import preprocessing
import pandas as pd
import networkx as nx
import seaborn as sns
from scipy.linalg import eigh
from scipy.signal import resample
import math
import random

import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.cluster import KMeans
from sklearn.naive_bayes import GaussianNB
from sklearn.mixture import GaussianMixture

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)
from sklearn.base import clone
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

import matplotlib.pyplot as plt
"""
# =============================================================================
# MATRICES EXCTRACTION - TRAJECTORIES AND PARAMETERS
# =============================================================================
"""


def safe_read_excel(file, col_indices):
    df = pd.read_excel(file)
    
    # keep only indices that exist
    valid_cols = [i for i in col_indices if i < df.shape[1]]
    
    if not valid_cols:
        # return empty DataFrame with same number of rows
        return pd.DataFrame(index=df.index)
    
    return df.iloc[:, valid_cols]


def drop_empty_tests(matrices, n_tests):
    cleaned = []

    for matrix in matrices:
        cleaned_matrix = matrix.iloc[:, :n_tests]
        cleaned.append(cleaned_matrix)

    return cleaned

def resample_matrix(matrix):
    
    if matrix.shape[0]>10000:
        
        original_fs = 1000
        target_fs = 100
    
        n_samples_new = int(
            matrix.shape[0] * target_fs / original_fs
        )
    
        resampled = resample(
            matrix,
            n_samples_new,
            axis=0
        )
        
    else:
        resampled=matrix
        
    return resampled

def traj_centering(matrix):
    return matrix - matrix.mean()

def preparing_input_traj (matrix):
    
    # Resampling
    resampled_matrix = resample_matrix(matrix)
    # Centering
    centered_matrix = traj_centering (resampled_matrix)
    
    return centered_matrix



"""
# =============================================================================
# DATA AUGMENTATION
# =============================================================================
"""

sns.set()

def get_rms(df):
  return  np.sqrt(np.mean(df **2))  #np.mean(df)


def get_acc(x):
  a = pd.DataFrame.diff(pd.DataFrame.diff(x / 0.04))
  return a


def get_rms_global(x, y):
  rms_x = np.sqrt(np.mean(x **2))
  rms_y = np.sqrt(np.mean(y **2))
  return  rms_x, rms_y


def get_acc_global(x, y):
  acc_x = pd.DataFrame()
  acc_y = pd.DataFrame()
  acc_x = pd.DataFrame.diff(pd.DataFrame.diff(x / 0.04))
  acc_y = pd.DataFrame.diff(pd.DataFrame.diff(y / 0.04))
  return acc_x[2:], acc_y[2:]


def get_sampen(L, m, r):
    N = len(L)
    B = 0.0
    A = 0.0
    # Split time series and save all templates of length m
    xmi = np.array([L[i : i + m] for i in range(N - m)])
    xmj = np.array([L[i : i + m] for i in range(N - m + 1)])
    # Save all matches minus the self-match, compute B
    B = np.sum([np.sum(np.abs(xmii - xmj).max(axis=1) <= r) - 1 for xmii in xmi])
    # Similar for computing A
    m += 1
    xm = np.array([L[i : i + m] for i in range(N - m + 1)])
    A = np.sum([np.sum(np.abs(xmi - xm).max(axis=1) <= r) - 1 for xmi in xm])
    # Return SampEn
    return -np.log(A / B)


def get_path(x, y):
  return sum(np.sqrt(x**2 + y**2))


def plot_multiple_vline(plots, div, k, n_points):
  for item in plots:
    i = int(n_points/div)
    item.axhline(y = 0.0, color = 'r', linestyle = '-')
    for val in range(1, div):
      item.axvline(i, linestyle= '--', color='silver')
      i += int(n_points/div)


def get_fft(serie, n_points):
  serie = serie.dropna()
  f = np.linspace(0.0, 1.0/(2.0*(1/25)), n_points//2)
  power = np.abs(np.fft.fft(serie))[0:n_points//2]
  return f[f<=4], power[f <= 4]


def get_f80(f, power, min, max):
  return np.sum(power[(f >= min) & (f < max)]) * 4/5


def get_mean_freq(f, power, min, max):
  mean = np.mean(power[(f >= min) & (f < max)])
  return mean


def plot_frequent_series(indices_1, indices_2):
  to_plot = pd.DataFrame(data=indices_1)
  to_plot = pd.DataFrame(to_plot.value_counts())
  to_plot = to_plot.sort_index()

  fig = plt.figure(figsize=(20, 10))
  ax1 = fig.add_subplot(211)
  plt.title('Most frequent COP X instances')
  plt.ylabel('Quantity')
  to_plot.plot.bar( ax=ax1, xlabel='Instances')
  plt.legend(['Instances'])
  plt.axhline(y=to_plot.max()[0]//2, xmin=0, xmax=to_plot.max()[0], linewidth=4, color='r', linestyle='--')

  ax2 = fig.add_subplot(212)
  plt.title('Most frequent COP Y instances')
  plt.ylabel('Quantity')
  plt.xlabel('Instances')
  to_plot = pd.DataFrame(data=indices_2)
  to_plot = pd.DataFrame(to_plot.value_counts())
  to_plot = to_plot.sort_index()
  to_plot.plot.bar( color='red', ax=ax2, xlabel='Instances')
  plt.legend(['Instances'])
  plt.axhline(y=to_plot.max()[0]//2, xmin=0, xmax=to_plot.max()[0], linewidth=4, color='r', linestyle='--')

  plt.subplots_adjust(hspace=0.4)
  plt.show()


def get_randomsamples(low_index, high_index, n_values, da_df):
  da_df_val = pd.DataFrame()
  rand_values = random.sample(range(low_index, high_index), n_values)
  print('Samples:', rand_values)
  for val in rand_values:
      try:
          da_df_val = pd.concat([da_df_val, da_df.loc[:, str(val)]], axis=1)
      except KeyError:
          print('Columna', val, 'eliminada, se escoge otra.')
  print('Val:', da_df_val.shape)
  return da_df_val


# READ METHOD MATRICES

def establish_method_class(all_matrices, lss_array, method="COP"):

    # ------------------------------------------------------------------
    # Choose the method to use
    # ------------------------------------------------------------------

    (
        healthy_xtrunk, healthy_ytrunk,
        healthy_xcop, healthy_ycop,
        all_patients_xtrunk, all_patients_ytrunk,
        all_patients_xcop, all_patients_ycop
    ) = all_matrices

    if method == "COP":
        hx, hy = healthy_xcop, healthy_ycop
        px, py = all_patients_xcop, all_patients_ycop

    elif method == "Trunk":
        hx, hy = healthy_xtrunk, healthy_ytrunk
        px, py = all_patients_xtrunk, all_patients_ytrunk

    else:
        raise ValueError("method must be 'COP' or 'Trunk'")

    # ------------------------------------------------------------------
    # Separate into 4 groups
    # ------------------------------------------------------------------

    mask_dependent = lss_array < 6
    mask_static = lss_array == 6
    mask_independent = lss_array > 6

    # Healthy
    val_x0, val_y0 = hx, hy

    # Dependent
    val_x1 = px.iloc[:, mask_dependent]
    val_y1 = py.iloc[:, mask_dependent]

    # Static
    val_x2 = px.iloc[:, mask_static]
    val_y2 = py.iloc[:, mask_static]

    # Independent
    val_x3 = px.iloc[:, mask_independent]
    val_y3 = py.iloc[:, mask_independent]

    # ------------------------------------------------------------------
    # Create class_attribute dataframe
    # ------------------------------------------------------------------

    class_attribute = pd.DataFrame(columns=["Path", "Class"])

    # Healthy
    for col in val_x0.columns:
        class_attribute.loc[len(class_attribute)] = [col, "Healthy"]

    # Dependent
    for col in val_x1.columns:
        class_attribute.loc[len(class_attribute)] = [col, "Dependent"]

    # Static
    for col in val_x2.columns:
        class_attribute.loc[len(class_attribute)] = [col, "Static"]

    # Independent
    for col in val_x3.columns:
        class_attribute.loc[len(class_attribute)] = [col, "Independent"]

    return (
        val_x0, val_x1, val_x2, val_x3,
        val_y0, val_y1, val_y2, val_y3,
        class_attribute
    )


    
# SELECTION, CROSSOVER AND MUTATION FUNCTIONS

def selection(df_attr, median_val, indexes):
  #Calculate four random values from the range of indices of each class
  index_1, index_2, rand_values, rand_1, rand_2 = 0, 0, 10, 0, 0
  while rand_1 == rand_2:
    rand_1 = random.sample(range(0, indexes), rand_values)
    rand_2 = random.sample(range(0, indexes), rand_values)
  attr_1, attr_2 = [], []
  #Obtain the median (F80 or Path) from the previously obtained random indices
  for val in range(0, rand_values):
    attr_1.append(df_attr[rand_1[val]])
    attr_2.append(df_attr[rand_2[val]])
  #Select the index that has the value (F80 or Path) closest to the median
  ## If you want to ignore Median value, comment line 16 and 17 and uncomment 18 and 19.
  #index_1 = rand_1[attr_1.index(max(attr_1, key=lambda x:abs(x-median_val))) ]
  #index_2 = rand_2[attr_2.index(max(attr_2, key=lambda y:abs(y-median_val))) ]
  index_1 = random.sample(rand_1, 1)[0]
  index_2 = random.sample(rand_2, 1)[0]
  return index_1, index_2


def crossover(div, k, X, Y, n_points):
  #Get k values between 0 and div
  
  part = np.sort(random.sample(range(0, div), k))
  R1 = pd.DataFrame()
  i = 0
  for val in range(0, div):
    if val in part:
      #Keep
      R1 = pd.concat([R1, X[i:i+int(n_points/div)]], axis=0, ignore_index=True)
    else:
      #Crossover
      R1 = pd.concat([R1, Y[i:i+int(n_points/div)]], axis=0, ignore_index=True)
    i += int(n_points/div)
  return R1

def mutation(div, k, X, Y, n_points):
  #Get k values between 0 and div
  part = np.sort(random.sample(range(0, div), k))
  
#   Y_mean = pd.concat(
#     [X.reset_index(drop=True),
#       Y.reset_index(drop=True)],
#     axis=1
# ).mean(axis=1)
  
  Y = pd.concat([X, Y], axis=1)
  Y = Y.mean(axis=1)
  R2 = pd.DataFrame()
  i = 0
  for val in range(0, div):
    if val in part:
      #Keep
      R2 = pd.concat([R2, X[i:i+int(n_points/div)]], axis=0, ignore_index=True)
    else:
      #Mutate
      R2 = pd.concat([R2, Y[i:i+int(n_points/div)]], axis=0, ignore_index=True)
    i += int(n_points/div)
  return R2





def get_augmented_data(df_attr, par_x,par_y, df_x, df_y, iter, median_x, median_y, class_attribute, n_points):
  #Array to save indices for plot.
  indices_1, indices_2 = [], []
  #Variables to save selected indices.
  X_1, X_2, Y_1, Y_2 = 0, 0, 0, 0
  #Indexes to control the insertion of data in dataframe.
  i, j = 0, 0
  #Dataframes to save augmented time series.
  RX_true, RY_true = pd.DataFrame(), pd.DataFrame()
  names = pd.DataFrame(columns=['Axis','Path','Class'])

  while iter > 0:
    # SELECTION
    # idx1, idx2 = selection(df_attr[par_x], median_x, len(df_x.iloc[0,:]-1))

    # X_1, X_2 = df_x.iloc[:, idx1], df_x.iloc[:, idx2]
    # Y_1, Y_2 = df_y.iloc[:, idx1], df_y.iloc[:, idx2]


    X_1, X_2 = selection(df_attr[par_x], median_x, len(df_x.iloc[0,:]-1))
    Y_1, Y_2 = selection(df_attr[par_y], median_y, len(df_y.iloc[0,:]-1))

    indices_1.append(X_2)
    indices_2.append(Y_2)
    names.loc[len(names)] = ['x', class_attribute.iloc[X_1, 0], class_attribute.iloc[X_1, 1]]
    names.loc[len(names)] = ['y', class_attribute.iloc[Y_1, 0], class_attribute.iloc[Y_1, 1]]
    X_1, Y_1 = df_x.iloc[:,X_1], df_y.iloc[:,Y_1]
    X_2, Y_2 = df_x.iloc[:,X_2], df_y.iloc[:,Y_2]
    # CROSSOVER
    R1_X = crossover(20, 10, X_1,X_2, n_points)
    R1_Y = crossover(20, 10, Y_1,Y_2, n_points)
    # MUTACION
    R2_X = mutation(20, 10, R1_X, X_2, n_points)
    R2_Y = mutation(20, 10, R1_Y, Y_2, n_points)
    
    # Insertion to a new dataset
    # RX_true[i] = R2_X.values
    # RY_true[j] = R2_Y.values
    
    RX_true.insert(i, i, R2_X[0])
    RY_true.insert(j, j, R2_Y[0])
    i += 1
    j += 1
    iter -= 1
    if iter % 100 == 0:
      print('Remaining iterations:'+ str(iter) )
  print()
  return indices_1, indices_2, RX_true, RY_true, names


def _prepare(n_points_plot, *arrays):
    n = min(n_points_plot, *[len(a) for a in arrays])
    sliced = [np.asarray(a[:n]) for a in arrays]
    x = np.arange(n)
    return x, n, sliced
  
# ============================================================
# GROUP DEFINITIONS
# healthy      -> Healthy controls
# dependent    -> LSS < 6
# static       -> LSS = 6
# independent  -> LSS > 6
# ============================================================

GROUP_COLORS = {
    "healthy": "tab:green",
    "dependent": "tab:red",
    "static": "tab:orange",
    "independent": "tab:blue",
}

GROUP_LABELS = {
    "healthy": "Healthy",
    "dependent": "Dependent (LSS < 6)",
    "static": "Static (LSS = 6)",
    "independent": "Independent (LSS > 6)",
}


# ------------------------- PLOT -------------------------
def plot_crossover(X_1,X_2,Y_1,Y_2,R1_X,R1_Y, group_1="healthy",group_2="independent", n_points_plot=500):

    x, n, (X_1, X_2, Y_1, Y_2, R1_X, R1_Y) = _prepare(
        n_points_plot, X_1, X_2, Y_1, Y_2, R1_X, R1_Y
    )

    c1 = GROUP_COLORS[group_1]
    c2 = GROUP_COLORS[group_2]

    l1 = GROUP_LABELS[group_1]
    l2 = GROUP_LABELS[group_2]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4))

    # ---------------- X ----------------
    ax1.set_title("Parents vs Crossed COP X")
    ax1.plot(x, X_1, color=c1)
    ax1.plot(x, X_2, color=c2)
    ax1.plot(x, R1_X, "o", ms=3, color="darkgoldenrod")

    ax1.legend([l1, l2, "Crossed X"])
    ax1.set_xlim(0, n - 1)

    # ---------------- Y ----------------
    ax2.set_title("Parents vs Crossed COP Y")
    ax2.plot(x, Y_1, color=c1)
    ax2.plot(x, Y_2, color=c2)
    ax2.plot(x, R1_Y, "o", ms=3, color="darkgoldenrod")

    ax2.legend([l1, l2, "Crossed Y"])
    ax2.set_xlim(0, n - 1)

    fig.suptitle("New COP Time Series Crossed", fontsize=14)
    plt.tight_layout()
    plt.show()


# ------------------------- MUTATION -------------------------
def plot_mutation( X_2,Y_2,R1_X,R1_Y,R2_X,R2_Y,group="independent",n_points_plot=500):

    x, n, (X_2, Y_2, R1_X, R1_Y, R2_X, R2_Y) = _prepare(
        n_points_plot, X_2, Y_2, R1_X, R1_Y, R2_X, R2_Y
    )

    group_color = GROUP_COLORS[group]
    group_label = GROUP_LABELS[group]

    fig = plt.figure(figsize=(14, 5))

    ax1 = fig.add_subplot(121)
    ax1.set_title("Crossed X vs Mutated COP X")

    ax1.plot(x, R1_X, "o", color="darkgoldenrod", ms=3)
    ax1.plot(x, X_2, color=group_color)
    ax1.plot(x, R2_X, "ro", ms=3)

    ax1.legend(["Crossed X", group_label, "Mutated X"])
    ax1.set_xlim(0, n - 1)

    ax2 = fig.add_subplot(122)
    ax2.set_title("Crossed Y vs Mutated COP Y")

    ax2.plot(x, R1_Y, "o", color="darkgoldenrod", ms=3)
    ax2.plot(x, Y_2, color=group_color)
    ax2.plot(x, R2_Y, "ro", ms=3)

    ax2.legend(["Crossed Y", group_label, "Mutated Y"])
    ax2.set_xlim(0, n - 1)

    fig.suptitle("New COP Time Series Mutated", fontsize=14)
    plt.tight_layout()
    plt.show()


# ------------------ PARENTS VS MUTATED ---------------------
def plot_parents_vs_mutated(X_2,Y_2,R1_X,R1_Y,R2_X, R2_Y, group="independent",n_points_plot=500):

    x, n, (X_2, Y_2, R1_X, R1_Y, R2_X, R2_Y) = _prepare(n_points_plot, X_2, Y_2, R1_X, R1_Y, R2_X, R2_Y)
    x = np.arange(n)

    group_color = GROUP_COLORS[group]
    group_label = GROUP_LABELS[group]

    fig = plt.figure(figsize=(14, 4))

    ax1 = fig.add_subplot(121)
    ax1.set_title("Parents vs Mutated COP X")

    ax1.plot(x, R1_X, "o", color="darkgoldenrod", ms=3)
    ax1.plot(x, X_2, color=group_color)
    ax1.plot(x, R2_X, "ro", ms=3)

    ax1.legend(["Parent X", group_label, "Mutated X"])
    ax1.set_xlim(0, n - 1)

    ax2 = fig.add_subplot(122)
    ax2.set_title("Parents vs Mutated COP Y")

    ax2.plot(x, R1_Y, "o", color="darkgoldenrod", ms=3)
    ax2.plot(x, Y_2, color=group_color)
    ax2.plot(x, R2_Y, "ro", ms=3)

    ax2.legend(["Parent Y", group_label, "Mutated Y"])
    ax2.set_xlim(0, n - 1)

    plot_multiple_vline([ax1, ax2], 20, 10, n)

    fig.suptitle("New COP Time Series Mutated", fontsize=14)
    plt.tight_layout()
    plt.show()


"""
# =============================================================================
# MACHINE LEARNING
# =============================================================================
"""
def divide_by_group (matrix, parameters):
    # Input matrix struct:
#       .columns: parameters + "CLass"
#       .rows trials

    g_0 = matrix[matrix["Class"]=="Healthy"]
    g_1 = matrix[matrix["Class"]=="Dependent"]
    g_2 = matrix[matrix["Class"]=="Static"]
    g_3 = matrix[matrix["Class"]=="Independent"]
    
    # Select only parameters needed
    g_0 = g_0[parameters]
    g_1 = g_1[parameters]
    g_2 = g_2[parameters]
    g_3 = g_3[parameters]
    
    return g_0, g_1, g_2, g_3

def calibrate_trunk(matrix, BA_table, parameters):
    
    # Ensure correct order
    # if list(BA_table["Parameter"]) != list(parameters):
    #     raise ValueError("Parameter order in BA_table does not match parameters list")
    
    fixed_bias_vector = BA_table["Fixed_bias"].values
    new_matrix = pd.DataFrame(index=matrix.index)
    for par in parameters:
        par_indx = parameters.index(par)
        new_matrix[par] = matrix[par] - fixed_bias_vector[par_indx]
    # Add Class column
    new_matrix["Class"] = matrix["Class"]
    
    return new_matrix

def select_median_band_indices(df, params_ref, k=1.05):

    """
    Select rows whose parameter values are within
    k * MAD from the group median for ALL parameters.
    """
    selected_indices = None
    for par in params_ref:
        col = df[par]
        median = np.median(col)
        mad = np.median(np.abs(col - median))
        # avoid zero MAD
        if mad == 0:
            threshold = 0
        else:
            threshold = k * mad
        idx = set(
            df.index[np.abs(col - median) <= threshold])
        # first parameter
        if selected_indices is None:
            selected_indices = idx
        # intersection with previous parameters
        else:
            selected_indices = selected_indices.intersection(idx)
    return sorted(selected_indices)

# =============================================================================
# Supervised model constructors
# =============================================================================

def FFN_model(X_train, y_train):

    class FFNWrapper:

        def __init__(self):

            self.model = nn.Sequential(
                nn.Linear(X_train.shape[1], 50),
                nn.ReLU(),
                nn.Linear(50, 50),
                nn.ReLU(),
                nn.Linear(50, 4)  # 4 CLASSES
            )

        def fit(self, X, y):

            X = torch.tensor(X, dtype=torch.float32)
            y = torch.tensor(y, dtype=torch.long)
            criterion = nn.CrossEntropyLoss()
            optimizer = optim.SGD(self.model.parameters(),lr=0.01)

            for _ in range(30):
                out = self.model(X)
                loss = criterion(out, y)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        def predict(self, X):
            X = torch.tensor(X, dtype=torch.float32)
            with torch.no_grad():
                preds = self.model(X).argmax(dim=1).numpy()
            return preds
    model = FFNWrapper()
    model.fit(X_train, y_train)
    return model

def RF_model():

    return RandomForestClassifier(
        n_estimators=10,
        criterion="entropy",
        max_depth=6,
        ccp_alpha=0.01,
        random_state=42)


def KNN_model():

    return KNeighborsClassifier(
        n_neighbors=3)


def NB_model():
    return GaussianNB()


# Implementing classifiers

def try_model_supervised(model_name,model,X_train,y_train,X_test,y_test):

    # CONVERT TO NUMPY
    y_train = np.array(y_train).ravel()
    y_test = np.array(y_test).ravel()
    
    # =========================================================================
    # NODE 1 : HEALTHY VS PATIENT
    # =========================================================================

    y_train_bin = (y_train != 0).astype(int)
    if model_name == "FFN":

        model_stage1 = FFN_model(X_train,y_train_bin)
    else:
        model_stage1 = clone(model)
        model_stage1.fit(X_train,y_train_bin)

    # =========================================================================
    # NODE 2 : PATIENT SUBGROUPS
    # =========================================================================

    patient_mask_train = y_train != 0
    X_train_pat = X_train[patient_mask_train]
    y_train_pat = y_train[patient_mask_train]

    # optional remapping:
    # 1->0, 2->1, 3->2
    y_train_pat_remap = y_train_pat - 1
    if model_name == "FFN":
        model_stage2 = FFN_model( X_train_pat,y_train_pat_remap)
    else:
        model_stage2 = clone(model)
        model_stage2.fit(X_train_pat, y_train_pat_remap)

    # =========================================================================
    # PREDICT TRAIN
    # =========================================================================
    y_pred_train = np.zeros(len(X_train), dtype=int)
    pred_stage1_train = model_stage1.predict(X_train)
    pred_stage1_train = np.array(pred_stage1_train).astype(int)
    patient_pred_mask_train = pred_stage1_train == 1

    if np.sum(patient_pred_mask_train) > 0:
        pred_stage2_train = model_stage2.predict(X_train[patient_pred_mask_train])
        pred_stage2_train = np.array(pred_stage2_train).astype(int)

        # remap back:
        # 0->1, 1->2, 2->3
        pred_stage2_train = pred_stage2_train + 1
        y_pred_train[patient_pred_mask_train] = pred_stage2_train

    # =========================================================================
    # PREDICT TEST
    # =========================================================================
    y_pred_test = np.zeros(len(X_test), dtype=int)
    pred_stage1_test = model_stage1.predict(X_test)
    pred_stage1_test = np.array(pred_stage1_test).astype(int)
    patient_pred_mask_test = pred_stage1_test == 1

    if np.sum(patient_pred_mask_test) > 0:
        pred_stage2_test = model_stage2.predict( X_test[patient_pred_mask_test])
        pred_stage2_test = np.array(pred_stage2_test).astype(int)
        pred_stage2_test = pred_stage2_test + 1
        y_pred_test[patient_pred_mask_test] = pred_stage2_test
    
    # =========================================================================
    # CONFUSION MATRICES (Random Forest only)
    # =========================================================================
    if model_name == "RandomForest": confusion_matrix_f (y_test, y_pred_test)

    # =========================================================================
    # METRICS
    # =========================================================================
    train_df = hierarchical_metrics(y_train,y_pred_train,model_name,"train")
    test_df = hierarchical_metrics( y_test,y_pred_test,model_name,"test")

    return train_df, test_df

def confusion_matrix_f (y_test, y_pred_test):

       # Healthy vs Patient
       y_test_bin = (y_test != 0).astype(int)
       y_pred_bin = (y_pred_test != 0).astype(int)
    
       cm1 = confusion_matrix(y_test_bin,y_pred_bin,labels=[0, 1])
    
       disp = ConfusionMatrixDisplay(
           confusion_matrix=cm1,
           display_labels=["Healthy", "Patient"]
       )
    
       disp.plot(cmap="Blues")
       plt.title("Random Forest - Node 1")
       plt.show()
        
       # Distinction between patient LSS levels
       patient_mask = y_test != 0

       y_true_pat = y_test[patient_mask]
       y_pred_pat = y_pred_test[patient_mask]
    
       cm2 = confusion_matrix(y_true_pat,y_pred_pat,labels=[1, 2, 3])
    
       disp = ConfusionMatrixDisplay(
           confusion_matrix=cm2,
           display_labels=[
               "Independent",
               "Static",
               "Dependent"
        ]
       )
    
       disp.plot(cmap="Greens")
       plt.title("Random Forest - Node 2")
       plt.show()
       
def hierarchical_metrics(y_true, y_pred, model_name, dataset):

    y_true = np.array(y_true).ravel()
    y_pred = np.array(y_pred).ravel()

    results = []
    # =========================================================================
    # NODE 1 : HEALTHY VS PATIENT
    # =========================================================================

    y_true_bin = (y_true != 0).astype(int)
    y_pred_bin = (y_pred != 0).astype(int)

    results.append({
        "model": model_name,
        "dataset": dataset,
        "node": "Healthy vs Patient",
        "accuracy": accuracy_score(y_true_bin,y_pred_bin),
        "precision": precision_score(y_true_bin,y_pred_bin,average='binary',zero_division=0),
        "recall": recall_score(y_true_bin,y_pred_bin,average='binary',zero_division=0),
        "f1": f1_score( y_true_bin,y_pred_bin,average='binary',zero_division=0)})

    # =========================================================================
    # NODE 2 : DEPENDENT / STATIC / INDEPENDENT
    # =========================================================================

    patient_mask = y_true != 0

    if np.sum(patient_mask) > 0:

        y_true_pat = y_true[patient_mask]
        y_pred_pat = y_pred[patient_mask]

        print("NODE 2 - PATIENT SEVERITY")
        print("\nUnique TRUE labels:")
        print(np.unique(y_true_pat))

        print("\nUnique PRED labels:")
        print(np.unique(y_pred_pat))

        print("\nCONFUSION MATRIX")
        print(confusion_matrix(y_true_pat, y_pred_pat))

        print("\nCLASSIFICATION REPORT")
        print(classification_report(y_true_pat,y_pred_pat,zero_division=0))

        results.append({
            "model": model_name,
            "dataset": dataset,
            "node": "Dependent vs Static vs Independent",
            "accuracy": accuracy_score(y_true_pat,y_pred_pat),
            "precision": precision_score( y_true_pat,y_pred_pat,average='macro',zero_division=0),
            "recall": recall_score( y_true_pat,y_pred_pat,average='macro',zero_division=0),
            "f1": f1_score(y_true_pat,y_pred_pat,average='macro',zero_division=0)})
    else:

        results.append({

            "model": model_name,
            "dataset": dataset,
            "node": "Dependent vs Static vs Independent",
            "accuracy": np.nan,
            "precision": np.nan,
            "recall": np.nan,
            "f1": np.nan
        })

    return pd.DataFrame(results)

