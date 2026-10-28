import csv
import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from agarwood_minims.core import ALGORITHMS, read_spectra, train, predict, plot_spectra
from agarwood_minims.cli import main


@pytest.fixture
def table(tmp_path):
    rng = np.random.default_rng(9)
    frame = pd.DataFrame(rng.uniform(0, 1, (42, 8)), columns=[str(i) for i in range(50, 58)])
    frame.insert(0, "Sample", [f"S{i}" for i in range(42)])
    frame["Label"] = ["ZP"] * 28 + ["KY"] * 7 + ["WP"] * 7
    path = tmp_path / "data.csv"
    frame.to_csv(path, index=False)
    return path


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_roundtrip_and_feature_alignment(table, tmp_path, algorithm):
    out = tmp_path / algorithm
    metadata, report = train(table, out, algorithm=algorithm)
    assert len(metadata["train_samples"]) == (33 if algorithm == "gbdt" else 29)
    assert len(metadata["test_samples"]) == (9 if algorithm == "gbdt" else 13)
    assert not set(metadata["train_samples"]) & set(metadata["test_samples"])
    result, _ = predict(table, out / "model.joblib", trusted=True)
    frame = pd.read_csv(table)
    reordered = tmp_path / "reordered.csv"
    frame[frame.columns[::-1]].to_csv(reordered, index=False)
    other, _ = predict(reordered, out / "model.joblib", trusted=True)
    assert result.Predicted.tolist() == other.Predicted.tolist()
    assert set(result.Predicted) <= {"ZP", "KY", "WP"}


def test_rf_matches_original_recipe(table, tmp_path):
    data, features = read_spectra(table, training=True)
    xtrain, xtest, ytrain, ytest = train_test_split(features, data.Label, test_size=.3, random_state=42)
    old = RandomForestClassifier(n_estimators=100, random_state=42).fit(xtrain, ytrain)
    train(table, tmp_path / "model", profile="legacy")
    actual = pd.read_csv(tmp_path / "model/holdout_predictions.csv")
    assert actual.Predicted.tolist() == old.predict(xtest).tolist()


@pytest.mark.parametrize("n", [1, 2, 4, 5, 7])
def test_plot_partial_grid(table, tmp_path, n):
    train(table, tmp_path / "model")
    result, features = predict(table, tmp_path / "model/model.joblib", trusted=True)
    png = tmp_path / "spectra.png"
    plot_spectra(result.iloc[:n], features.iloc[:n], png)
    assert png.read_bytes().startswith(b"\x89PNG")


def test_missing_feature_and_untrusted_model(table, tmp_path):
    train(table, tmp_path / "model")
    with pytest.raises(ValueError, match="Explicitly trust"):
        predict(table, tmp_path / "model/model.joblib")
    data = pd.read_csv(table).drop(columns=["50"])
    data.to_csv(tmp_path / "bad.csv", index=False)
    with pytest.raises(ValueError, match="Feature mismatch"):
        predict(tmp_path / "bad.csv", tmp_path / "model/model.joblib", trusted=True)


@pytest.mark.parametrize("problem", ["nan", "negative", "duplicate", "label", "infinity"])
def test_invalid_input(table, problem):
    data = pd.read_csv(table)
    if problem == "nan":
        data.loc[0, "50"] = np.nan
    elif problem == "negative":
        data.loc[0, "50"] = -1
    elif problem == "duplicate":
        data.loc[1, "Sample"] = data.loc[0, "Sample"]
    elif problem == "label":
        data.loc[0, "Label"] = ""
    else:
        data.loc[0, "50"] = np.inf
    data.to_csv(table, index=False)
    with pytest.raises(ValueError):
        read_spectra(table, training=True)


def test_duplicate_headers(tmp_path):
    path = tmp_path / "duplicate.csv"
    path.write_text("Sample,50,50,Label\ns1,1,2,ZP\n")
    with pytest.raises(ValueError, match="duplicate"):
        read_spectra(path)


def test_output_preservation(table, tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("preserve")
    with pytest.raises(ValueError, match="preserved"):
        train(table, output)
    assert sentinel.read_text() == "preserve"


def test_cli(table, tmp_path):
    assert main(["train", "--input", str(table), "--output", str(tmp_path / "run")]) == 0
    assert main(["predict", "--input", str(table), "--model", str(tmp_path / "run/model.joblib"),
                 "--output", str(tmp_path / "pred.csv"), "--trust-model"]) == 0
    assert main(["predict", "--input", str(table), "--model", str(tmp_path / "run/model.joblib"),
                 "--output", str(tmp_path / "pred.csv"), "--trust-model"]) == 2

def test_unknown_profile_rejected(table, tmp_path):
    with pytest.raises(ValueError, match="Unknown split profile"):
        train(table, tmp_path / "invalid", profile="unsupported")


def test_custom_and_profile_guards(table, tmp_path):
    meta, _ = train(table, tmp_path / "custom", profile="custom", test_size=.3)
    assert len(meta["test_samples"]) == 13
    with pytest.raises(ValueError, match="overrides"):
        train(table, tmp_path / "bad", test_size=.3)
    with pytest.raises(ValueError, match="fraction"):
        train(table, tmp_path / "bad2", profile="custom", test_size=1)


def test_cross_version_bundle_is_rejected(table, tmp_path):
    import joblib
    train(table, tmp_path / "model")
    path = tmp_path / "model/model.joblib"
    bundle = joblib.load(path)
    bundle["metadata"]["versions"]["scikit-learn"] = "0.0.0"
    joblib.dump(bundle, path)
    with pytest.raises(ValueError, match="version differs"):
        predict(table, path, trusted=True)


def test_gbdt_matches_original_encoded_recipe(table, tmp_path):
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.preprocessing import LabelEncoder
    data, features = read_spectra(table, training=True)
    encoder = LabelEncoder().fit(data.Label)
    encoded = encoder.transform(data.Label)
    xtrain, xtest, ytrain, ytest = train_test_split(features, encoded, test_size=.2, random_state=42)
    reference = GradientBoostingClassifier(random_state=42).fit(xtrain, ytrain)
    meta, _ = train(table, tmp_path / "gbdt", algorithm="gbdt")
    actual = pd.read_csv(tmp_path / "gbdt/holdout_predictions.csv")
    assert len(meta["train_samples"]) == 33
    assert len(meta["test_samples"]) == 9
    assert actual.Predicted.tolist() == encoder.inverse_transform(reference.predict(xtest)).tolist()
    predicted, _ = predict(table, tmp_path / "gbdt/model.joblib", trusted=True)
    assert predicted.Predicted.tolist() == encoder.inverse_transform(reference.predict(features)).tolist()


def test_user_data_with_new_classes_and_features(tmp_path):
    data = pd.DataFrame({
        "Sample": [f"{i:03d}" for i in range(60)],
        "101.1": [float(i // 20) * 10 + 1 for i in range(60)],
        "205.2": [float(i % 20) / 20 for i in range(60)],
        "Label": ["Class A"] * 20 + ["Class B"] * 20 + ["Class C"] * 20,
    })
    training = tmp_path / "own_train.csv"
    data.to_csv(training, index=False)
    train(training, tmp_path / "own_model")
    selected = data.iloc[[0, 20, 40]].drop(columns="Label")
    prediction = tmp_path / "own_predict.csv"
    selected.to_csv(prediction, index=False)
    actual, _ = predict(prediction, tmp_path / "own_model/model.joblib", trusted=True)
    assert actual.Sample.tolist() == ["000", "020", "040"]
    assert actual.Predicted.tolist() == ["Class A", "Class B", "Class C"]
    assert actual.Category.tolist() == actual.Predicted.tolist()
    selected.rename(columns={"205.2": "206.2"}).to_csv(prediction, index=False)
    with pytest.raises(ValueError, match="Feature mismatch"):
        predict(prediction, tmp_path / "own_model/model.joblib", trusted=True)
