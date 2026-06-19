import warnings
from pathlib import Path

import joblib
import pandas as pd

warnings.filterwarnings("ignore")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
MODEL_DIR = PROJECT_DIR / "models"


def find_dataset():
    search_roots = [
        SCRIPT_DIR,
        PROJECT_DIR,
        PROJECT_DIR / "datasets",
        Path(r"C:\Users\dashs\OneDrive\Desktop\project ev motor"),
    ]

    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.csv"):
            if "motor" in path.name.lower():
                return path

    raise FileNotFoundError("No motor CSV dataset found.")


def load_artifacts():
    model = joblib.load(MODEL_DIR / "best_model.pkl")
    scaler = joblib.load(MODEL_DIR / "scaler.pkl")
    le = joblib.load(MODEL_DIR / "label_encoder.pkl")
    feature_columns = joblib.load(MODEL_DIR / "feature_columns.pkl")
    use_scaler = joblib.load(MODEL_DIR / "model_uses_scaler.pkl")
    return model, scaler, le, feature_columns, use_scaler


def prepare_sample(df, feature_columns):
    if "fault_code" in df.columns:
        y_true = df["fault_code"].astype(str).values
        X = df.drop(columns=["fault_code"])
    else:
        y_true = None
        X = df.copy()

    if "timestamp" in X.columns:
        X = X.drop(columns=["timestamp"])

    X = X.select_dtypes(include=["number"]).copy()
    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.fillna(X.median(numeric_only=True))

    for col in feature_columns:
        if col not in X.columns:
            X[col] = 0.0

    X = X[feature_columns]
    return X, y_true


def main():
    print("=" * 80)
    print("EV PROJECT - MODEL TEST")
    print("=" * 80)

    dataset_path = find_dataset()
    print(f"\nUsing dataset: {dataset_path}")

    model, scaler, le, feature_columns, use_scaler = load_artifacts()
    print("Loaded saved model artifacts.")

    df = pd.read_csv(dataset_path, low_memory=False)

    sample_df = df.head(10).copy()
    X_sample, y_true = prepare_sample(sample_df, feature_columns)

    if use_scaler:
        X_input = scaler.transform(X_sample)
    else:
        X_input = X_sample

    preds = model.predict(X_input)
    pred_labels = le.inverse_transform(preds)

    print("\nSample Predictions:")
    for i, pred in enumerate(pred_labels):
        actual = y_true[i] if y_true is not None else "N/A"
        print(f"Row {i+1}: actual={actual} | predicted={pred}")

    if y_true is not None:
        print("\nPrediction Summary:")
        correct = sum(actual == pred for actual, pred in zip(y_true, pred_labels))
        print(f"Correct: {correct}/{len(pred_labels)}")
        print(f"Accuracy on sample: {correct / len(pred_labels):.4f}")


if __name__ == "__main__":
    main()