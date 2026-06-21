import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

cols = joblib.load(BASE_DIR / "models" / "feature_columns.pkl")

print("Model Features:")
for col in cols:
    print(col)