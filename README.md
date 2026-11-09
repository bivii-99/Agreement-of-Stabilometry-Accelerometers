# Agreement-of-Stabilometry-Accelerometers
Folder that contains all steps of the project
## 1. Background
This repository contains the statistical analysis used in the manuscript.
An R analysis is used to study the agreement between force-plate stabilometric measures and wearable IMU accelerometers placed at L3 and trunk using Bland–Altman analysis. A Python analysis is used in data augmentation and heriarchical classification. The latter evaluates the performance of Random Forest (RF), Feedforward Neural Network (FNN), Naive Bayes (NB), K-and Nearest Neighbour (KNN) on two nodes: healthy vs patients — node 1 —, and Level Sitting Scale degree (LSS) for patients (DG: LSS<6, SG:LSS=6, IG:LSS>6) — node 2 —. 

## 2. Workflow
<img width="1171" height="1343" alt="image" src="https://github.com/user-attachments/assets/3eaf034d-d79e-4298-89e3-32bfd79c0d9c" />


## 3. File format
### Bland-Altman analysis
The present repository requires an input data frame must have NxM dimensions, where N is the number of total tests acquired and M corresponds to "Class", "Subject Number", and the extracted parameters. 
### Data augmentation
Data augmentation is done independently for each group. The input trajectory data frame must have NxM dimensions, where N are the test datapoints and M the test number. Output synthetic data frame is an NxM matrix, where N is the total number of agumented tests, and M corresponds to features extracted.

## 4. Software Ecosystem

A broader software ecosystem was developed for IMU-based postural assessment, which also includes tools for data acquisition and signal processing.

### IMU-Friendly Toolbox

The **IMU-Friendly Toolbox** is a Python-based graphical application designed for IMU data preprocessing, feature extraction, and classification.

The toolbox can import CSV recordings generated during acquisition and provides an intuitive workflow for signal visualization, preprocessing, feature computation, and machine learning-based classification. In addition to importing existing recordings, it supports **real-time data acquisition** from a **YOST Wireless Sensor v2.0** connected through a **YOST USB Wireless Dongle v1.0**.

Repository: https://github.com/bivii-99/IMU-Friendly-Toolbox

---

### YostCPP-MacOS

**YostCPP-MacOS** is a native C/C++ application for acquiring data from YOST wireless IMU sensors under macOS.

As an alternative to the acquisition module integrated into the IMU-Friendly Toolbox, this application records raw sensor data and exports it as CSV files, which can subsequently be imported into the Python toolbox for preprocessing and analysis.

Repository: https://github.com/bivii-99/YostCPP-MacOS
