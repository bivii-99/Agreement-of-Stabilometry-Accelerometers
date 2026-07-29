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
        
## 3. Software ecosystem

### IMU-Friendly Toolbox
The processed CSV files can be imported into the IMU-Friendly Toolbox for preprocessing, feature extraction and classification. ù
The software allows new recordings using Wireless YOST sensor v2.0, connected to a USB-connected dongle v1.0. 
See https://github.com/bivii-99/IMU-Friendly-Toolbox

### YostCPP-MacOS
Alternatively, IMU recordings can be acquired directly through the C/C++ acquisition software.
See https://github.com/bivii-99/YostCPP-MacOS
