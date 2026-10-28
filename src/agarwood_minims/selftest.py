"""Exercise real Tk button callbacks with scripted file-dialog responses.

The diagnostic uses only bundled DEMO data and a new output directory.
It also runs inside the frozen executable to check packaged dependencies.
"""
import json
import sys
import traceback
from pathlib import Path


def run(output_dir):
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=False)
    try:
        result = _exercise(output)
    except Exception:
        (output / "self-test.json").write_text(json.dumps({"passed": False, "error": traceback.format_exc()}, indent=2), encoding="utf-8")
        raise
    (output / "self-test.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def _exercise(output):
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    import pandas as pd
    from . import __version__
    from .core import ALGORITHMS
    from .gui import create_window

    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]
    if not (base / "demo").is_dir() and (Path.cwd() / "demo").is_dir():
        base = Path.cwd()
    training = base / "demo/demo_train.csv"
    prediction = base / "demo/demo_predict.csv"
    originals = [(filedialog, name, getattr(filedialog, name)) for name in ("askopenfilename", "askdirectory", "asksaveasfilename")]
    originals += [(messagebox, name, getattr(messagebox, name)) for name in ("askyesno", "showerror")]
    root = create_window()
    root.withdraw()
    errors = []
    callback_errors = []
    root.report_callback_exception = lambda *exc: callback_errors.append(str(exc[1]))
    messagebox.showerror = lambda title, message: errors.append((title, message))
    messagebox.askyesno = lambda *args, **kwargs: True
    def descendants(widget):
        for child in widget.winfo_children():
            yield child
            yield from descendants(child)
    widgets = list(descendants(root))
    buttons = {w.cget("text"): w for w in widgets if isinstance(w, ttk.Button)}
    combos = [w for w in widgets if isinstance(w, ttk.Combobox)]
    runs = {}
    try:
        for algorithm in ALGORITHMS:
            combos[0].set(algorithm)
            parent = output / algorithm
            parent.mkdir()
            filedialog.askopenfilename = lambda **kwargs: str(training)
            filedialog.askdirectory = lambda **kwargs: str(parent)
            buttons["Train and evaluate"].invoke()
            root.update()
            assert not errors and not callback_errors, (errors, callback_errors)
            run_dir, = parent.glob("training-*")
            meta = json.loads((run_dir / "metadata.json").read_text())
            assert (len(meta["train_samples"]), len(meta["test_samples"])) == ((33, 9) if algorithm == "gbdt" else (29, 13))
            for name in ("model.joblib", "metrics.json", "classification_report.txt", "confusion_matrix.csv", "holdout_predictions.csv"):
                assert (run_dir / name).stat().st_size > 0, name
            paths = iter((run_dir / "model.joblib", prediction))
            filedialog.askopenfilename = lambda **kwargs: str(next(paths))
            target = parent / "predictions.csv"
            filedialog.asksaveasfilename = lambda **kwargs: str(target)
            buttons["Predict and save spectra"].invoke()
            root.update()
            assert not errors and not callback_errors, (errors, callback_errors)
            result = pd.read_csv(target)
            assert len(result) == 6
            assert target.with_name("predictions-spectra.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
            runs[algorithm] = {"predictions": result.Predicted.tolist(), "train_samples": meta["train_samples"], "test_samples": meta["test_samples"], "metrics": json.loads((run_dir / "metrics.json").read_text())}
        # Cancellation must not create a run or report an error.
        filedialog.askopenfilename = lambda **kwargs: ""
        buttons["Train and evaluate"].invoke()
        buttons["Predict and save spectra"].invoke()
        assert not errors and not callback_errors
        # Existing output must survive a second prediction attempt.
        saved = target.read_bytes()
        paths = iter((run_dir / "model.joblib", prediction))
        filedialog.askopenfilename = lambda **kwargs: str(next(paths))
        buttons["Predict and save spectra"].invoke()
        assert len(errors) == 1 and "preserved" in errors[0][1]
        assert target.read_bytes() == saved
        errors.clear()
        # Custom controls must actually reach the training workflow.
        combos[1].set("custom")
        entry, = [w for w in widgets if isinstance(w, ttk.Entry) and not isinstance(w, ttk.Combobox)]
        assert str(entry.cget("state")) == "normal"
        entry.delete(0, tk.END)
        entry.insert(0, "0.25")
        parent = output / "custom"
        parent.mkdir()
        filedialog.askopenfilename = lambda **kwargs: str(training)
        filedialog.askdirectory = lambda **kwargs: str(parent)
        buttons["Train and evaluate"].invoke()
        custom_dir, = parent.glob("training-*")
        meta = json.loads((custom_dir / "metadata.json").read_text())
        assert meta["test_size"] == .25 and meta["stratify"] is True
        assert len(meta["test_samples"]) == 11
        assert not errors and not callback_errors, (errors, callback_errors)
        return {"passed": True, "version": __version__, "frozen": bool(getattr(sys, "frozen", False)), "models": runs, "checks": ["Tk button callbacks", "five models", "serialization", "CSV and PNG export", "cancellation", "output preservation", "custom controls"]}
    finally:
        root.destroy()
        for module, name, original in originals:
            setattr(module, name, original)
