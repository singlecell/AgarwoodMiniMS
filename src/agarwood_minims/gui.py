"""Small local GUI; no background artwork or fixed working directory required."""
def create_window():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from pathlib import Path
    from .core import ALGORITHMS, train, predict, plot_spectra

    import sys
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]
    if not (base / "demo").is_dir() and (Path.cwd() / "demo").is_dir():
        base = Path.cwd()
    demo = base / "demo"
    data_directory = str(demo) if demo.is_dir() else str(Path.home())
    last_model = None
    root = tk.Tk()
    root.title("AgarwoodMiniMS")
    root.geometry("760x550")
    root.minsize(760, 550)
    frame = ttk.Frame(root, padding=24)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="AgarwoodMiniMS", font=("", 22, "bold")).pack(anchor="w")
    ttk.Label(frame, text="Train from a labeled CSV, or predict with your own trusted model.").pack(anchor="w", pady=12)
    ttk.Label(frame, text="Algorithm: rf = Random forest, svm = SVM, knn = KNN, nb = Naive Bayes, gbdt = Gradient boosting", wraplength=690).pack(anchor="w")
    algo = tk.StringVar(value="rf")
    ttk.Combobox(frame, textvariable=algo, values=ALGORITHMS, state="readonly").pack(anchor="w")
    profile = tk.StringVar(value="legacy")
    ttk.Label(frame, text="Split: legacy = original script; custom = configurable experiment").pack(anchor="w", pady=6)
    ttk.Combobox(frame, textvariable=profile, values=("legacy", "custom"), state="readonly").pack(anchor="w")
    custom = ttk.Frame(frame)
    custom.pack(anchor="w", pady=6)
    fraction = tk.StringVar(value="0.3")
    stratified = tk.BooleanVar(value=True)
    ttk.Label(custom, text="Custom test fraction:").pack(side="left")
    fraction_entry = ttk.Entry(custom, textvariable=fraction, width=8)
    fraction_entry.pack(side="left", padx=8)
    stratify_check = ttk.Checkbutton(custom, text="Stratify", variable=stratified)
    stratify_check.pack(side="left")
    def update_custom(*_):
        state = "normal" if profile.get() == "custom" else "disabled"
        fraction_entry.configure(state=state)
        stratify_check.configure(state=state)
    profile.trace_add("write", update_custom)
    update_custom()
    status = tk.StringVar(value="Ready")
    def fit():
        nonlocal last_model
        src = filedialog.askopenfilename(title="Training CSV", initialdir=data_directory, filetypes=[("CSV", "*.csv")])
        if not src:
            return
        parent = filedialog.askdirectory(title="Choose parent folder for a NEW training run")
        if not parent:
            return
        from datetime import datetime
        out = Path(parent) / ("training-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
        try:
            status.set("Training...")
            root.update_idletasks()
            settings = {}
            if profile.get() == "custom":
                settings = {"test_size": float(fraction.get()), "stratify": stratified.get()}
            train(src, out, algorithm=algo.get(), profile=profile.get(), **settings)
            last_model = out / "model.joblib"
            status.set(f"Saved: {out}")
        except Exception as exc:
            messagebox.showerror("Training failed", str(exc))
            status.set("Training failed")
    def run():
        options = {"title": "Trusted model", "filetypes": [("Model", "*.joblib")]}
        if last_model is not None:
            options.update(initialdir=str(last_model.parent), initialfile=last_model.name)
        model = filedialog.askopenfilename(**options)
        if not model:
            return
        if not messagebox.askyesno("Trust model", "Model files can execute code. Did you create this model or trust its source?"):
            return
        src = filedialog.askopenfilename(title="Prediction CSV", initialdir=data_directory, filetypes=[("CSV", "*.csv")])
        if not src:
            return
        target = filedialog.asksaveasfilename(title="Save predictions", defaultextension=".csv")
        if not target:
            return
        try:
            out = Path(target)
            plot = out.with_name(out.stem + "-spectra.png")
            if out.exists() or plot.exists():
                raise ValueError("Choose a new filename; existing outputs are preserved.")
            result, features = predict(src, model, trusted=True)
            if len(result) <= 60:
                plot_spectra(result, features, plot)
            result.to_csv(out, index=False)
            note = " (spectra skipped: more than 60 samples)" if len(result) > 60 else ""
            status.set(f"Saved {len(result)} predictions: {out}{note}")
        except Exception as exc:
            messagebox.showerror("Prediction failed", str(exc))
            status.set("Prediction failed")
    ttk.Button(frame, text="Train and evaluate", command=fit).pack(anchor="w", pady=14)
    ttk.Button(frame, text="Predict and save spectra", command=run).pack(anchor="w")
    ttk.Label(frame, textvariable=status, wraplength=640).pack(anchor="w", pady=20)
    ttk.Label(frame, text="ZP: authentic agarwood    KY: Kynam    WP: counterfeit").pack(anchor="w")
    return root


def launch():
    create_window().mainloop()
