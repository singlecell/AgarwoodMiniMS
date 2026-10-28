# AgarwoodMiniMS

A desktop application for agarwood mass-spectrum classification using random forest, SVM, KNN, Gaussian naive Bayes, or gradient boosting.

[中文说明](WINDOWS.zh-CN.md)

## Installation

Extract the complete Windows ZIP and double-click `AgarwoodMiniMS.exe`. Python is not required. Keep the `_internal` folder beside the executable.

## Try the DEMO

1. Keep the default `rf` and `legacy`, then click **Train and evaluate**.
2. Select `demo/demo_train.csv` and choose a results folder.
3. Click **Predict and save spectra**, select the newly generated `model.joblib`, and confirm its trusted origin.
4. Select `demo/demo_predict.csv` and choose a new output filename.

The application exports predictions as CSV and spectra as PNG.

## Use your own data

Follow the DEMO CSV layout: unique `Sample` identifiers, numeric m/z intensity columns, and a `Label` column for training.

Train a new model with your own training table, then select your prediction table. Both tables must use the same spectral features. To try another algorithm, select it in the interface and retrain.
