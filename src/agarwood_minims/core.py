"""Validated input, explicit experiment settings, and portable model bundles."""
import csv
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC

ALGORITHMS = ("rf", "svm", "knn", "nb", "gbdt")
CATEGORIES = {"ZP": "Authentic agarwood", "KY": "Kynam agarwood", "WP": "Counterfeit"}
FORMAT_VERSION = 1


def read_spectra(path, training=False):
    """Read a sample-by-feature CSV. Numeric column names are m/z coordinates."""
    path = Path(path)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        header = next(csv.reader(stream), [])
    if not header or len(header) != len(set(header)):
        raise ValueError("CSV must have a nonempty header without duplicate columns.")
    data = pd.read_csv(path, encoding="utf-8-sig", dtype={"Sample": str, "Label": str})
    if data.empty or "Sample" not in data:
        raise ValueError("CSV must contain Sample and at least one sample row.")
    if data.Sample.isna().any() or data.Sample.str.strip().eq("").any():
        raise ValueError("Sample identifiers must not be empty.")
    if data.Sample.duplicated().any():
        raise ValueError("Sample identifiers must be unique; aggregate repeated measurements first.")
    if training and "Label" not in data:
        raise ValueError("Training requires a Label column.")
    if "Label" in data:
        if data.Label.isna().any() or data.Label.str.strip().eq("").any():
            raise ValueError("Labels must not be empty.")
        if training and data.Label.nunique() < 2:
            raise ValueError("Training requires at least two classes.")
    features = data.drop(columns=["Sample", "Label"], errors="ignore")
    if features.shape[1] == 0:
        raise ValueError("CSV has no spectral features.")
    try:
        mz = np.asarray(features.columns, dtype=float)
        features = features.apply(pd.to_numeric, errors="raise").astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Feature names must be numeric m/z values and intensities numeric.") from exc
    if not np.isfinite(mz).all() or (mz <= 0).any() or len(set(mz)) != len(mz):
        raise ValueError("m/z coordinates must be finite, positive and unique.")
    if not np.isfinite(features.to_numpy()).all() or (features.to_numpy() < 0).any():
        raise ValueError("Intensities must be finite, nonnegative, with no missing values.")
    return data, features


def estimator(algorithm, seed=42):
    models = {
        "rf": lambda: RandomForestClassifier(n_estimators=100, random_state=seed),
        "svm": lambda: SVC(kernel="linear", random_state=seed),
        "knn": lambda: KNeighborsClassifier(n_neighbors=5),
        "nb": GaussianNB,
        "gbdt": lambda: GradientBoostingClassifier(random_state=seed),
    }
    if algorithm not in models:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    return models[algorithm]()


def train(csv_path, output_dir, algorithm="rf", test_size=None, seed=42, stratify=None, profile="legacy"):
    """Fit on training rows only; record actual holdout membership and parameters."""
    data, features = read_spectra(csv_path, training=True)
    labels = data.Label
    if profile not in ("legacy", "custom"):
        raise ValueError("Unknown split profile.")
    if profile != "custom" and (test_size is not None or stratify is not None):
        raise ValueError("Use profile=custom for explicit split overrides.")
    if profile == "legacy":
        test_size, stratify = (0.2 if algorithm == "gbdt" else 0.3), False
    else:
        test_size = 0.3 if test_size is None else test_size
        stratify = True if stratify is None else stratify
        if not 0 < test_size < 1:
            raise ValueError("Custom test_size must be a fraction between 0 and 1.")
    indices = np.arange(len(data))
    train_idx, test_idx = train_test_split(
        indices, test_size=test_size, random_state=seed,
        stratify=labels if stratify else None,
    )
    if set(labels.iloc[train_idx]) != set(labels):
        raise ValueError("A class is missing from training; use stratification or more samples.")
    if algorithm == "knn" and len(train_idx) < 5:
        raise ValueError("KNN requires at least five training samples.")
    model = estimator(algorithm, seed)
    model.fit(features.iloc[train_idx], labels.iloc[train_idx])
    predictions = model.predict(features.iloc[test_idx])
    classes = sorted(labels.unique().tolist())
    metadata = {
        "format_version": FORMAT_VERSION,
        "algorithm": algorithm, "seed": seed, "test_size": test_size, "split_profile": profile,
        "stratify": stratify, "preprocessing": "none",
        "features": list(features.columns), "classes": classes,
        "estimator_parameters": model.get_params(),
        "input_sha256": hashlib.sha256(Path(csv_path).read_bytes()).hexdigest(),
        "train_class_counts": labels.iloc[train_idx].value_counts().to_dict(),
        "test_class_counts": labels.iloc[test_idx].value_counts().to_dict(),
        "train_samples": data.Sample.iloc[train_idx].tolist(),
        "test_samples": data.Sample.iloc[test_idx].tolist(),
        "versions": {p: version(p) for p in ("numpy", "pandas", "scikit-learn", "joblib")},
        "python": platform.python_version(),
    }
    report = classification_report(
        labels.iloc[test_idx], predictions, labels=classes, output_dict=True, zero_division=0
    )
    output = Path(output_dir)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory must be new or empty; previous results are preserved.")
    output.mkdir(parents=True, exist_ok=True)
    joblib.dump({"metadata": metadata, "model": model}, output / "model.joblib")
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (output / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "classification_report.txt").write_text(
        classification_report(labels.iloc[test_idx], predictions, labels=classes, zero_division=0),
        encoding="utf-8",
    )
    pd.DataFrame(confusion_matrix(labels.iloc[test_idx], predictions, labels=classes),
                 index=classes, columns=classes).to_csv(output / "confusion_matrix.csv", index_label="True")
    pd.DataFrame({"Sample": data.Sample.iloc[test_idx].to_numpy(),
                  "Actual": labels.iloc[test_idx].to_numpy(),
                  "Predicted": predictions}).to_csv(output / "holdout_predictions.csv", index=False)
    return metadata, report


def predict(csv_path, model_path, trusted=False):
    """Only load model files whose origin the caller trusts (joblib executes code)."""
    if not trusted:
        raise ValueError("Loading joblib can execute code. Explicitly trust your own model first.")
    bundle = joblib.load(model_path)
    if not isinstance(bundle, dict) or bundle.get("metadata", {}).get("format_version") != FORMAT_VERSION:
        raise ValueError("Unsupported model bundle; retrain using this package.")
    metadata = bundle["metadata"]
    if metadata["versions"]["scikit-learn"] != version("scikit-learn"):
        raise ValueError("scikit-learn version differs from training; recreate the recorded environment.")
    data, features = read_spectra(csv_path)
    expected = metadata["features"]
    missing = sorted(set(expected) - set(features.columns))
    extra = sorted(set(features.columns) - set(expected))
    if missing or extra:
        raise ValueError(f"Feature mismatch. Missing: {missing[:8]}; unexpected: {extra[:8]}")
    features = features.loc[:, expected]
    predictions = bundle["model"].predict(features)
    result = pd.DataFrame({"Sample": data.Sample, "Predicted": predictions})
    result["Category"] = result.Predicted.map(CATEGORIES).fillna(result.Predicted)
    return result, features


def plot_spectra(result, features, output_path):
    """Plot actual numeric m/z coordinates and handle partly filled subplot grids."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    n = len(result)
    if n == 0 or n > 60:
        raise ValueError("Plot 1 to 60 samples at a time.")
    cols = min(3, n)
    fig, axes = plt.subplots((n + cols - 1) // cols, cols, squeeze=False,
                             figsize=(5 * cols, 3.5 * ((n + cols - 1) // cols)))
    mz = np.asarray(features.columns, dtype=float)
    for i, ax in enumerate(axes.flat):
        if i >= n:
            ax.set_visible(False)
            continue
        ax.vlines(mz, 0, features.iloc[i].to_numpy(), color="#207c65", linewidth=0.8)
        ax.set(xlabel="m/z", ylabel="Intensity",
               title=f"{result.Sample.iloc[i]}: {result.Category.iloc[i]}")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
