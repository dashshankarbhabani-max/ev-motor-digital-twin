import warnings
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler

warnings.filterwarnings("ignore")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
MODEL_DIR = PROJECT_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)


def find_dataset():
    search_roots = [
        SCRIPT_DIR,
        PROJECT_DIR,
        PROJECT_DIR / "datasets",
        Path(r"C:\Users\dashs\OneDrive\Desktop\project ev motor"),
    ]

    seen = set()
    csv_files = []

    for root in search_roots:
        if not root.exists() or root in seen:
            continue
        seen.add(root)
        print(f"Searching in: {root}")
        csv_files.extend(list(root.rglob("*.csv")))

    if not csv_files:
        raise FileNotFoundError("No CSV files found in the project folders.")

    preferred = None
    for p in csv_files:
        if "motor" in p.name.lower():
            preferred = p
            break

    if preferred is None:
        print("\nCSV files found:")
        for p in csv_files:
            print(p)
        raise FileNotFoundError("CSV found, but none matched the expected motor dataset name.")

    print(f"Found dataset: {preferred}")
    return preferred


def load_data():
    path = find_dataset()
    return pd.read_csv(path, low_memory=False)


def prepare_data(df):
    df = df.copy()
    target_col = "fault_code"

    if target_col not in df.columns:
        raise ValueError("fault_code column not found in dataset.")

    if "timestamp" in df.columns:
        df = df.drop(columns=["timestamp"])

    y_raw = df[target_col].astype(str)
    X = df.drop(columns=[target_col])

    X = X.select_dtypes(include=["number"]).copy()
    X = X.apply(pd.to_numeric, errors="coerce")
    X = X.fillna(X.median(numeric_only=True))

    le = LabelEncoder()
    y = le.fit_transform(y_raw)

    return X, y, le


def evaluate_model(name, model, X_test, y_test, le, use_scaler=False, scaler=None):
    X_eval = scaler.transform(X_test) if use_scaler and scaler is not None else X_test
    preds = model.predict(X_eval)
    acc = accuracy_score(y_test, preds)

    print("\n" + "=" * 80)
    print(f"MODEL: {name}")
    print("=" * 80)
    print(f"Accuracy: {acc:.4f}")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, preds))
    print("\nClassification Report:")
    print(classification_report(y_test, preds, target_names=le.classes_, zero_division=0))

    return acc


def main():
    print("=" * 80)
    print("EV PROJECT - TRAIN, TEST, FINALIZE")
    print("=" * 80)

    print("\nLoading dataset...")
    df = load_data()
    print(f"Loaded: {df.shape[0]} rows, {df.shape[1]} columns")

    print("\nPreparing data...")
    X, y, le = prepare_data(df)
    print(f"Numeric features: {X.shape[1]}")
    print(f"Classes: {list(le.classes_)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    models = [
        (
            "Random Forest",
            RandomForestClassifier(
                n_estimators=250,
                random_state=42,
                n_jobs=-1,
                class_weight="balanced_subsample",
            ),
            False,
        ),
        (
            "Gradient Boosting",
            HistGradientBoostingClassifier(
                learning_rate=0.08,
                max_depth=8,
                max_iter=250,
                random_state=42,
            ),
            False,
        ),
        (
            "Neural Network",
            MLPClassifier(
                hidden_layer_sizes=(128, 64),
                activation="relu",
                solver="adam",
                alpha=0.0005,
                batch_size=512,
                learning_rate_init=0.001,
                max_iter=40,
                random_state=42,
                early_stopping=True,
                validation_fraction=0.1,
            ),
            True,
        ),
    ]

    results = []

    for name, model, use_scaled in models:
        print(f"\nTraining {name}...")
        if use_scaled:
            model.fit(X_train_scaled, y_train)
            acc = evaluate_model(name, model, X_test, y_test, le, use_scaler=True, scaler=scaler)
        else:
            model.fit(X_train, y_train)
            acc = evaluate_model(name, model, X_test, y_test, le)
        results.append((name, acc, model, use_scaled))

    results.sort(key=lambda x: x[1], reverse=True)

    print("\n" + "=" * 80)
    print("FINAL COMPARISON")
    print("=" * 80)
    for i, (name, acc, _, _) in enumerate(results, start=1):
        print(f"{i}. {name:<20} {acc:.4f} ({acc * 100:.2f}%)")

    best_name, best_acc, best_model, best_scaled = results[0]

    print(f"\nBest model: {best_name}")
    print(f"Best accuracy: {best_acc:.4f}")

    joblib.dump(best_model, MODEL_DIR / "best_model.pkl")
    joblib.dump(scaler, MODEL_DIR / "scaler.pkl")
    joblib.dump(le, MODEL_DIR / "label_encoder.pkl")
    joblib.dump(list(X.columns), MODEL_DIR / "feature_columns.pkl")
    joblib.dump(best_scaled, MODEL_DIR / "model_uses_scaler.pkl")

    print("\nSaved files:")
    print(f"- {MODEL_DIR / 'best_model.pkl'}")
    print(f"- {MODEL_DIR / 'scaler.pkl'}")
    print(f"- {MODEL_DIR / 'label_encoder.pkl'}")
    print(f"- {MODEL_DIR / 'feature_columns.pkl'}")
    print(f"- {MODEL_DIR / 'model_uses_scaler.pkl'}")


if __name__ == "__main__":
    main()