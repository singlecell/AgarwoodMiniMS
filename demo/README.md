# DEMO data

- `demo_train.csv`: 42 labeled samples for training.
- `demo_predict.csv`: six samples for prediction.

Both tables contain prepared spectral data used in the paper, with 951 m/z features per sample.

Train a model with the training table, then try the prediction table. To use your own data, prepare tables in the same CSV format and train a new model before predicting.

Each row represents one sample: `Sample` is a unique identifier, numeric m/z columns contain intensities, and training tables also require a `Label` column. Prediction and training tables must use the same spectral features.
