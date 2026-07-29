# Agreement-of-Stabilometry-Accelerometers
Folder that contains all steps of the project
## 1. Background

This repository contains the R analysis used in the manuscript:
Agreement between force-plate stabilometric measures and wearable IMU accelerometers placed at L3 and trunk using Bland–Altman analysis.
## 2. Workflow

      
 IMU L3       Force plate       IMU Trunk
      │            | |              │
      └────────────┘ └──────────────┘
             │                │
             ▼                ▼
            Bland–Altman analysis
                     │
                     ▼
             Bias estimation
                     │
                     ▼
        Calibrated accelerometer variables
        
## 3. Software Ecosystem

This repository contains the statistical analysis used in the manuscript. It is part of a broader software ecosystem developed for IMU-based postural assessment, which also includes tools for data acquisition and signal processing.

### IMU-Friendly Toolbox

The **IMU-Friendly Toolbox** is a Python-based graphical application designed for IMU data preprocessing, feature extraction, and classification.

The toolbox can import CSV recordings generated during acquisition and provides an intuitive workflow for signal visualization, preprocessing, feature computation, and machine learning-based classification. In addition to importing existing recordings, it supports **real-time data acquisition** from a **YOST Wireless Sensor v2.0** connected through a **YOST USB Wireless Dongle v1.0**.

Repository: https://github.com/bivii-99/IMU-Friendly-Toolbox

---

### YostCPP-MacOS

**YostCPP-MacOS** is a native C/C++ application for acquiring data from YOST wireless IMU sensors under macOS.

As an alternative to the acquisition module integrated into the IMU-Friendly Toolbox, this application records raw sensor data and exports it as CSV files, which can subsequently be imported into the Python toolbox for preprocessing and analysis.

Repository: https://github.com/bivii-99/YostCPP-MacOS
