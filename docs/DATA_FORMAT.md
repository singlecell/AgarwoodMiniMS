# CSV format

Use UTF-8 CSV with one sample per row:

```csv
Sample,50,51,52,Label
S001,0.0,1.2,0.3,ZP
S002,0.8,0.0,1.5,WP
```

- `Sample`: unique, nonempty sample identifier.
- `Label`: required for training; optional for prediction.
- Feature headers: unique positive numeric m/z values.
- Intensities: finite, nonnegative numbers, with no empty cells.

Prediction must contain the same features as training; column order may differ. Keep notes and other metadata outside the CSV.

Categories: ZP (authentic agarwood), KY (Kynam), WP (counterfeit). Other nonempty labels are also accepted.

The `demo` folder contains training and prediction CSV files from the paper. Replace them with your own tables and train a new model for your data.
