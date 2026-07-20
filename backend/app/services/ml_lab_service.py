"""Module 4 ML Lab helpers — read Phase 3 artifacts without inventing metrics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODELS_DIR = Path(__file__).resolve().parents[3] / "data" / "models"
XGB_IMPORTANCE_NAME = "xgboost_importance.json"
XGB_MODEL_NAME = "xgboost_model.joblib"

# Models that never produce tree/gain importance artifacts.
_NO_IMPORTANCE_MODELS = frozenset({"arima", "lstm"})


def _resolve_dir(artifact_dir: Path | str | None) -> Path:
    return Path(artifact_dir) if artifact_dir is not None else MODELS_DIR


def _importance_from_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    gain = raw.get("gain")
    weight = raw.get("weight")
    if not isinstance(gain, dict) or not gain:
        return None
    feature_cols = raw.get("feature_cols")
    if not isinstance(feature_cols, list):
        feature_cols = list(gain.keys())
    return {
        "gain": {str(k): float(v) for k, v in gain.items()},
        "weight": (
            {str(k): float(v) for k, v in weight.items()}
            if isinstance(weight, dict)
            else {}
        ),
        "feature_cols": [str(c) for c in feature_cols],
        "source": str(path),
    }


def _importance_from_joblib(path: Path) -> dict[str, Any] | None:
    """Fallback when JSON is missing but wrapped Phase 3 joblib has ``importance``."""
    if not path.is_file():
        return None
    try:
        import joblib

        artifact = joblib.load(path)
    except Exception:
        return None
    if not isinstance(artifact, dict):
        return None
    importance = artifact.get("importance")
    if not isinstance(importance, dict):
        return None
    gain = importance.get("gain")
    if not isinstance(gain, dict) or not gain:
        return None
    weight = importance.get("weight") if isinstance(importance.get("weight"), dict) else {}
    feature_cols = artifact.get("feature_cols") or importance.get("feature_cols") or list(gain.keys())
    return {
        "gain": {str(k): float(v) for k, v in gain.items()},
        "weight": {str(k): float(v) for k, v in weight.items()},
        "feature_cols": [str(c) for c in feature_cols],
        "source": str(path),
    }


def get_feature_importance(
    model_name: str = "xgboost",
    *,
    artifact_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Load feature importance from #12 artifacts. Never invent scores.

    Returns a payload with ``available: bool``. Missing / unsupported models
    get an explicit Vietnamese message for Lab banners.
    """
    name = (model_name or "xgboost").strip().lower()
    out_dir = _resolve_dir(artifact_dir)

    base: dict[str, Any] = {
        "model_name": name,
        "available": False,
        "importance_type": "gain",
        "features": [],
        "gain": {},
        "weight": {},
        "feature_cols": [],
        "source": None,
        "message": None,
    }

    if name in _NO_IMPORTANCE_MODELS:
        base["message"] = (
            f"Model «{name}» không có artifact feature importance "
            "(chỉ XGBoost ghi gain/weight từ train #12 — không bịa số)."
        )
        return base

    if name != "xgboost":
        base["message"] = (
            f"Không hỗ trợ feature importance cho «{name}» "
            "(chỉ xgboost — không bịa số)."
        )
        return base

    json_path = out_dir / XGB_IMPORTANCE_NAME
    loaded = _importance_from_json(json_path)
    if loaded is None:
        loaded = _importance_from_joblib(out_dir / XGB_MODEL_NAME)

    if loaded is None:
        base["message"] = (
            "Chưa có xgboost_importance.json (và joblib không chứa importance) — "
            "chạy train ML (#12) trước; không bịa số."
        )
        return base

    gain = loaded["gain"]
    # Rank by gain descending for Lab chart (real scores only).
    ranked = sorted(gain.items(), key=lambda kv: kv[1], reverse=True)
    features = [{"feature": feat, "gain": score, "weight": loaded["weight"].get(feat)} for feat, score in ranked]

    return {
        **base,
        "available": True,
        "features": features,
        "gain": gain,
        "weight": loaded["weight"],
        "feature_cols": loaded["feature_cols"],
        "source": loaded["source"],
        "message": None,
    }
