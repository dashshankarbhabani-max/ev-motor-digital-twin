from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd


MODEL_DIR = Path(__file__).resolve().parent.parent / "models"


@lru_cache(maxsize=1)
def load_model_artifacts():
    required = {
        "model": MODEL_DIR / "best_model.pkl",
        "scaler": MODEL_DIR / "scaler.pkl",
        "label_encoder": MODEL_DIR / "label_encoder.pkl",
        "feature_columns": MODEL_DIR / "feature_columns.pkl",
        "uses_scaler": MODEL_DIR / "model_uses_scaler.pkl",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing model artifact(s): {', '.join(missing)}")

    return {name: joblib.load(path) for name, path in required.items()}


def _model_row(features, feature_columns):
    defaults = {
        "record_id": 0.0,
        "load_fraction": min(abs(float(features.get("torque_nm", 0.0))) / 200.0, 1.0),
        "ambient_c": 25.0,
        "coolant_pressure": 2.5,
    }
    row = {
        column: float(features.get(column, defaults.get(column, 0.0)))
        for column in feature_columns
    }
    return pd.DataFrame([row], columns=feature_columns)


def _anomalies(features, fault_code):
    anomalies = []
    if fault_code != "NONE":
        anomalies.append(fault_code)
    if float(features.get("stator_temp_c", 0)) > 90:
        anomalies.append("High stator temperature")
    if float(features.get("bearing_temp_c", 0)) > 80:
        anomalies.append("High bearing temperature")
    if float(features.get("vibration_vel", 0)) > 4.5:
        anomalies.append("Excessive vibration")
    return anomalies


def predict_motor_health(features):
    """Predict the motor fault locally using the saved trained model."""
    artifacts = load_model_artifacts()
    model_input = _model_row(features, artifacts["feature_columns"])
    if artifacts["uses_scaler"]:
        model_input = artifacts["scaler"].transform(model_input)

    encoded_prediction = artifacts["model"].predict(model_input)
    model_fault_code = str(
        artifacts["label_encoder"].inverse_transform(encoded_prediction)[0]
    )

    confidence = None
    probabilities = {}
    if hasattr(artifacts["model"], "predict_proba"):
        scores = artifacts["model"].predict_proba(model_input)[0]
        labels = artifacts["label_encoder"].inverse_transform(
            artifacts["model"].classes_
        )
        probabilities = {
            str(label): round(float(score), 6)
            for label, score in zip(labels, scores)
        }
        confidence = round(max(probabilities.values()), 6)

    safety_fault_code = str(features.get("detected_fault_code", "NONE"))
    safety_override = safety_fault_code != "NONE"
    fault_code = safety_fault_code if safety_override else model_fault_code

    return {
        "fault_code": fault_code,
        "diagnosis_source": "safety_rules" if safety_override else "random_forest",
        "confidence": None if safety_override else confidence,
        "model_fault_code": model_fault_code,
        "model_confidence": confidence,
        "safety_fault_code": safety_fault_code,
        "class_probabilities": probabilities,
        "failure_probability": float(features.get("failure_probability", 0.0)),
        "rul_hours": float(features.get("rul_hours", 0.0)),
        "health_score": float(features.get("overall_health", 0.0)),
        "anomalies": _anomalies(features, fault_code),
    }
