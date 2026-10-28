"""Create deterministic synthetic fixtures; no experimental measurements."""
from pathlib import Path
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parent / "fixtures"
root.mkdir(exist_ok=True)
rng = np.random.default_rng(42)
labels = np.array(["ZP"] * 28 + ["KY"] * 7 + ["WP"] * 7)
values = rng.uniform(0, 2, (42, 24))
for i in range(42):
    block = {"ZP": 0, "KY": 1, "WP": 2}[labels[i]]
    values[i, block * 8:(block + 1) * 8] += rng.uniform(4, 8, 8)
data = pd.DataFrame(values.round(5), columns=[str(50 + i * 40) for i in range(24)])
data.insert(0, "Sample", [f"SYN-{i+1:03}" for i in range(42)])
data["Label"] = labels
data.to_csv(root / "synthetic_train.csv", index=False)
new_values = rng.uniform(0, 2, (5, 24))
for i in range(5):
    block = i % 3
    new_values[i, block * 8:(block + 1) * 8] += rng.uniform(4, 8, 8)
new = pd.DataFrame(new_values.round(5), columns=data.columns[1:-1])
new.insert(0, "Sample", [f"SYN-NEW-{i+1}" for i in range(5)])
new.to_csv(root / "synthetic_predict.csv", index=False)
