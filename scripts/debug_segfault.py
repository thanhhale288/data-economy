"""
Debug script: test từng thư viện để tìm nguyên nhân segfault.
Chạy: python3 scripts/debug_segfault.py
"""
import sys
import os

print(f"Python: {sys.version}")
print(f"OS: {sys.platform}")
print()

steps = []

def check(label, fn):
    try:
        result = fn()
        print(f"✓ {label}: {result}")
        steps.append((label, "OK", result))
    except Exception as e:
        print(f"✗ {label}: {e}")
        steps.append((label, "ERROR", str(e)))

# 1. PyArrow
print("=== PyArrow ===")
check("import pyarrow", lambda: __import__("pyarrow").__version__)
check("pyarrow basic op", lambda: str(__import__("pyarrow").array([1,2,3])))

# 2. LightGBM
print("\n=== LightGBM ===")
check("import lightgbm", lambda: __import__("lightgbm").__version__)

# 3. XGBoost
print("\n=== XGBoost ===")
check("import xgboost", lambda: __import__("xgboost").__version__)

# 4. PyTorch
print("\n=== PyTorch ===")
check("import torch", lambda: __import__("torch").__version__)

# 5. Joblib load ML artifacts
print("\n=== ML Artifacts ===")
import joblib
from pathlib import Path

models_dir = Path(__file__).resolve().parents[1] / "data" / "models"
for artifact in ["xgboost_model.joblib", "lightgbm_model.joblib", "arima_model.joblib"]:
    path = models_dir / artifact
    check(f"load {artifact}", lambda p=path: f"OK size={p.stat().st_size}" if p.exists() else "missing")

# 6. DB connection
print("\n=== Database ===")
check("db connect", lambda: (
    __import__("backend.app.database", fromlist=["SessionLocal"]).SessionLocal().execute(
        __import__("sqlalchemy", fromlist=["text"]).text("SELECT 1")
    ).fetchone()[0]
))

# 7. build_features
print("\n=== build_features ===")
def _test_features():
    from backend.app.database import SessionLocal
    from pipeline.features.engineering import build_features
    db = SessionLocal()
    try:
        df = build_features(db)
        return f"shape={df.shape}" if df is not None else "None"
    finally:
        db.close()
check("build_features", _test_features)

# 8. generate_forecast xgboost
print("\n=== generate_forecast (xgboost) ===")
def _test_forecast():
    from backend.app.database import SessionLocal
    from ml.models.trainer import generate_forecast
    db = SessionLocal()
    try:
        result = generate_forecast(db, "xgboost", 3)
        return f"OK periods={[f['period'] for f in result['forecasts']]}"
    finally:
        db.close()
check("forecast xgboost", _test_forecast)

# 9. anomaly endpoint
print("\n=== anomaly service ===")
def _test_anomaly():
    from backend.app.database import SessionLocal
    from backend.app.services import ml_lab_service
    db = SessionLocal()
    try:
        result = ml_lab_service.get_anomaly_scores(db, vsic_code="C", include_va=True)
        return f"OK n={len(result.get('scores', []))}"
    finally:
        db.close()
check("anomaly scores", _test_anomaly)

print("\n=== SUMMARY ===")
for label, status, detail in steps:
    icon = "✓" if status == "OK" else "✗"
    print(f"{icon} {label}: {detail[:80] if isinstance(detail, str) else detail}")
