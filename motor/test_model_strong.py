import warnings
from pathlib import Path

import joblib
import pandas as pd

warnings.filterwarnings("ignore")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
MODEL_DIR = PROJECT_DIR / "models"
OUTPUT_DIR = PROJECT_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


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


def prepare_data(df, feature_columns):
    df = df.copy()

    if "fault_code" not in df.columns:
        raise ValueError("fault_code column not found in dataset.")

    y = df["fault_code"].astype(str)
    X = df.drop(columns=["fault_code"])

    if "timestamp" in X.columns:
        X = X.drop(columns=["timestamp"])

    X = X.select_dtypes(include=["number"]).copy()
    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.fillna(X.median(numeric_only=True))

    for col in feature_columns:
        if col not in X.columns:
            X[col] = 0.0

    X = X[feature_columns]
    return X, y


def main():
    print("=" * 80)
    print("EV PROJECT - STRONG MODEL TEST")
    print("=" * 80)

    dataset_path = find_dataset()
    print(f"\nUsing dataset: {dataset_path}")

    model, scaler, le, feature_columns, use_scaler = load_artifacts()
    print("Loaded saved model artifacts.")

    df = pd.read_csv(dataset_path, low_memory=False)

    sample_size = min(100, len(df))
    sample_df = df.sample(n=sample_size, random_state=42).reset_index(drop=True)

    X_sample, y_true = prepare_data(sample_df, feature_columns)

    if use_scaler:
        X_input = scaler.transform(X_sample)
    else:
        X_input = X_sample

    preds = model.predict(X_input)
    pred_labels = le.inverse_transform(preds)

    results = sample_df.copy()
    results["actual_fault_code"] = y_true.values
    results["predicted_fault_code"] = pred_labels
    results["match"] = results["actual_fault_code"] == results["predicted_fault_code"]

    output_csv = OUTPUT_DIR / "model_test_results.csv"
    results.to_csv(output_csv, index=False)

    correct = results["match"].sum()
    total = len(results)
    acc = correct / total

    print("\nSample Results:")
    print(results[["actual_fault_code", "predicted_fault_code", "match"]].head(20).to_string(index=False))

    print("\nSummary:")
    print(f"Correct: {correct}/{total}")
    print(f"Accuracy on sample: {acc:.4f}")
    print(f"Saved results to: {output_csv}")


if __name__ == "__main__":
    main()