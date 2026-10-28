"""Command-line entry point."""
import argparse
import sys
from pathlib import Path
from .core import ALGORITHMS, plot_spectra, predict, train


def main(argv=None):
    parser = argparse.ArgumentParser(description="AgarwoodMiniMS: train and predict spectral tables")
    commands = parser.add_subparsers(dest="command", required=True)
    fit = commands.add_parser("train")
    fit.add_argument("--input", required=True)
    fit.add_argument("--output", required=True)
    fit.add_argument("--algorithm", choices=ALGORITHMS, default="rf")
    fit.add_argument("--profile", choices=("legacy", "custom"), default="legacy")
    fit.add_argument("--test-size", type=float)
    fit.add_argument("--seed", type=int, default=42)
    fit.add_argument("--stratify", action=argparse.BooleanOptionalAction, default=None)
    pred = commands.add_parser("predict")
    pred.add_argument("--input", required=True)
    pred.add_argument("--model", required=True)
    pred.add_argument("--output", required=True)
    pred.add_argument("--plot")
    pred.add_argument("--trust-model", action="store_true", help="Only for models from a trusted source")
    commands.add_parser("gui")
    args = parser.parse_args(argv)
    try:
        if args.command == "train":
            metadata, _ = train(args.input, args.output, args.algorithm, args.test_size, args.seed, args.stratify, args.profile)
            print(f"Saved model and evaluation: {args.output} ({len(metadata['train_samples'])} train / {len(metadata['test_samples'])} test)")
        elif args.command == "predict":
            targets = [Path(args.output)] + ([Path(args.plot)] if args.plot else [])
            if len(set(p.resolve() for p in targets)) != len(targets):
                raise ValueError("Prediction and plot output paths must differ.")
            if any(p.exists() for p in targets):
                raise ValueError("Output already exists; choose a new filename.")
            result, features = predict(args.input, args.model, args.trust_model)
            for p in targets:
                p.parent.mkdir(parents=True, exist_ok=True)
            if args.plot:
                plot_spectra(result, features, args.plot)
            result.to_csv(args.output, index=False)
            print(f"Saved {len(result)} predictions: {args.output}")
        else:
            from .gui import launch
            launch()
    except (ValueError, OSError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
