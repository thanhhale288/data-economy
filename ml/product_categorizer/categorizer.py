"""TF-IDF + sklearn classifier: marketplace product_name → VSIC 4-digit.

Uncertain predictions return ``vsic_code=None`` with an explicit reason —
never invent codes outside the Section C 4-digit whitelist.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ml.product_categorizer.vsic import is_allowed_vsic, section_c_vsic_4digit

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DEFAULT_LABELS_PATH = DATA_DIR / "seeds" / "product_categorizer_labels.json"
DEFAULT_ARTIFACT_PATH = DATA_DIR / "models" / "product_categorizer.joblib"

DEFAULT_CONFIDENCE_THRESHOLD = 0.22
DEFAULT_MARGIN_THRESHOLD = 0.04
MIN_NAME_LEN = 3
UNKNOWN_LABEL = "__UNKNOWN__"

ARTIFACT_VERSION = 1


@dataclass(frozen=True)
class CategorizeResult:
    """Single product classification outcome."""

    product_name: str
    vsic_code: str | None
    confidence: float
    reason: str | None = None
    runner_up: str | None = None
    runner_up_confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _strip_diacritics(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def normalize_product_name(text: str) -> str:
    """Lowercase ASCII-ish form for TF-IDF (keeps digits / spaces)."""
    ascii_text = _strip_diacritics(text or "").lower()
    ascii_text = re.sub(r"[_\-.+/]+", " ", ascii_text)
    ascii_text = re.sub(r"[^a-z0-9\s]", " ", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()


def load_labels(path: Path | None = None) -> list[dict[str, Any]]:
    """Load labeled sample JSON (product_name, vsic_code|null, split)."""
    labels_path = path or DEFAULT_LABELS_PATH
    if not labels_path.exists():
        return []
    with open(labels_path, encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list):
        raise ValueError(f"labels must be a JSON list: {labels_path}")
    return rows


def _split_rows(
    labels: Iterable[dict[str, Any]], split: str | None
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in labels:
        if split is not None and row.get("split", "train") != split:
            continue
        out.append(row)
    return out


class ProductCategorizer:
    """Offline product_name → VSIC 4-digit seed classifier (TF-IDF baseline)."""

    def __init__(
        self,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        margin_threshold: float = DEFAULT_MARGIN_THRESHOLD,
        model_path: Path | None = None,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.margin_threshold = margin_threshold
        self.model_path = Path(model_path) if model_path else DEFAULT_ARTIFACT_PATH
        self._pipeline: Pipeline | None = None
        self._classes: list[str] = []

    @property
    def is_fitted(self) -> bool:
        return self._pipeline is not None and bool(self._classes)

    def _build_pipeline(self) -> Pipeline:
        return Pipeline(
            steps=[
                (
                    "tfidf",
                    TfidfVectorizer(
                        analyzer="char_wb",
                        ngram_range=(3, 5),
                        min_df=1,
                        sublinear_tf=True,
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=2000,
                        solver="lbfgs",
                        C=4.0,
                    ),
                ),
            ]
        )

    def train(
        self,
        labels: list[dict[str, Any]] | None = None,
        *,
        labels_path: Path | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        """Fit on labeled rows (VSIC whitelist + optional null→UNKNOWN class)."""
        rows = labels if labels is not None else load_labels(labels_path)
        whitelist = section_c_vsic_4digit()
        X: list[str] = []
        y: list[str] = []
        for r in _split_rows(rows, "train"):
            name = normalize_product_name(str(r.get("product_name") or ""))
            if not name:
                continue
            code = r.get("vsic_code")
            if code is None:
                X.append(name)
                y.append(UNKNOWN_LABEL)
                continue
            code_s = str(code)
            if code_s not in whitelist:
                raise ValueError(f"Labels outside Section C whitelist: [{code_s}]")
            X.append(name)
            y.append(code_s)

        if not X:
            raise ValueError("No trainable labeled rows (need split=train)")
        if UNKNOWN_LABEL not in y:
            # Keep an abstain sink even if labels omit null rows
            X.extend(
                [
                    "dich vu tu van thue",
                    "khoa hoc online",
                    "ve may bay",
                    "thue can ho",
                ]
            )
            y.extend([UNKNOWN_LABEL] * 4)

        n_vsic = len({c for c in y if c != UNKNOWN_LABEL})
        if n_vsic < 2:
            raise ValueError("Need at least 2 VSIC classes to train")

        pipe = self._build_pipeline()
        pipe.fit(X, y)
        self._pipeline = pipe
        self._classes = [str(c) for c in pipe.named_steps["clf"].classes_]

        summary = {
            "n_train": len(X),
            "n_classes": len(self._classes),
            "classes": self._classes,
            "confidence_threshold": self.confidence_threshold,
            "margin_threshold": self.margin_threshold,
            "backend": "sklearn_tfidf_logreg",
            "embedding_path": False,
        }
        if persist:
            path = self.save()
            summary["artifact"] = str(path)
        return summary

    def save(self, path: Path | None = None) -> Path:
        if not self.is_fitted:
            raise RuntimeError("Cannot save: model not fitted")
        out = Path(path) if path else self.model_path
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": ARTIFACT_VERSION,
            "pipeline": self._pipeline,
            "classes": self._classes,
            "confidence_threshold": self.confidence_threshold,
            "margin_threshold": self.margin_threshold,
            "backend": "sklearn_tfidf_logreg",
            "embedding_path": False,
        }
        joblib.dump(payload, out)
        return out

    def load(self, path: Path | None = None) -> bool:
        artifact = Path(path) if path else self.model_path
        if not artifact.exists():
            return False
        try:
            payload = joblib.load(artifact)
            self._pipeline = payload["pipeline"]
            self._classes = list(payload.get("classes") or [])
            if "confidence_threshold" in payload:
                self.confidence_threshold = float(payload["confidence_threshold"])
            if "margin_threshold" in payload:
                self.margin_threshold = float(payload["margin_threshold"])
            return self.is_fitted
        except Exception as exc:  # noqa: BLE001 — optional artifact
            logger.warning("ProductCategorizer.load failed: %s", exc)
            return False

    def predict(self, product_name: str) -> CategorizeResult:
        """Classify one product name; uncertain → vsic_code=None + reason."""
        raw = product_name if product_name is not None else ""
        normalized = normalize_product_name(raw)
        if len(normalized) < MIN_NAME_LEN:
            return CategorizeResult(
                product_name=raw,
                vsic_code=None,
                confidence=0.0,
                reason="empty_or_short_input",
            )

        if not self.is_fitted and not self.load():
            return CategorizeResult(
                product_name=raw,
                vsic_code=None,
                confidence=0.0,
                reason="model_not_loaded",
            )

        assert self._pipeline is not None
        proba = self._pipeline.predict_proba([normalized])[0]
        classes = list(self._pipeline.named_steps["clf"].classes_)
        ranked = sorted(zip(classes, proba), key=lambda t: t[1], reverse=True)
        top_code, top_p = ranked[0]
        runner = ranked[1] if len(ranked) > 1 else (None, 0.0)
        margin = float(top_p - runner[1]) if runner[0] is not None else float(top_p)

        if str(top_code) == UNKNOWN_LABEL:
            return CategorizeResult(
                product_name=raw,
                vsic_code=None,
                confidence=float(top_p),
                reason="unknown_class",
                runner_up=str(runner[0]) if runner[0] is not None else None,
                runner_up_confidence=float(runner[1]) if runner[0] is not None else None,
            )

        if not is_allowed_vsic(str(top_code)):
            return CategorizeResult(
                product_name=raw,
                vsic_code=None,
                confidence=float(top_p),
                reason="predicted_code_not_in_whitelist",
                runner_up=str(runner[0]) if runner[0] is not None else None,
                runner_up_confidence=float(runner[1]) if runner[0] is not None else None,
            )

        if float(top_p) < self.confidence_threshold:
            return CategorizeResult(
                product_name=raw,
                vsic_code=None,
                confidence=float(top_p),
                reason="low_confidence",
                runner_up=str(runner[0]) if runner[0] is not None else None,
                runner_up_confidence=float(runner[1]) if runner[0] is not None else None,
            )

        if margin < self.margin_threshold:
            return CategorizeResult(
                product_name=raw,
                vsic_code=None,
                confidence=float(top_p),
                reason="ambiguous_margin",
                runner_up=str(runner[0]) if runner[0] is not None else None,
                runner_up_confidence=float(runner[1]) if runner[0] is not None else None,
            )

        return CategorizeResult(
            product_name=raw,
            vsic_code=str(top_code),
            confidence=float(top_p),
            reason=None,
            runner_up=str(runner[0]) if runner[0] is not None else None,
            runner_up_confidence=float(runner[1]) if runner[0] is not None else None,
        )


def evaluate_precision(
    categorizer: ProductCategorizer,
    labels: list[dict[str, Any]] | None = None,
    *,
    labels_path: Path | None = None,
    split: str = "test",
) -> dict[str, Any]:
    """Precision / honesty report on a labeled split (null = abstain)."""
    rows = labels if labels is not None else load_labels(labels_path)
    eval_rows = _split_rows(rows, split)
    if not eval_rows:
        return {
            "split": split,
            "n": 0,
            "precision": None,
            "recall_labeled": None,
            "abstain_rate": None,
            "accuracy_including_abstain": None,
            "tp": 0,
            "fp": 0,
            "fn": 0,
            "tn_abstain_correct": 0,
            "details": [],
        }

    tp = fp = fn = tn_ok = 0
    details: list[dict[str, Any]] = []
    for row in eval_rows:
        name = str(row.get("product_name") or "")
        truth = row.get("vsic_code")
        truth_s = str(truth) if truth is not None else None
        pred = categorizer.predict(name)
        pred_s = pred.vsic_code

        if truth_s is None:
            # Correct abstain / unknown
            if pred_s is None:
                tn_ok += 1
                status = "tn_abstain"
            else:
                fp += 1
                status = "fp_invented"
        else:
            if pred_s is None:
                fn += 1
                status = "fn_abstain"
            elif pred_s == truth_s:
                tp += 1
                status = "tp"
            else:
                fp += 1
                status = "fp_wrong"

        details.append(
            {
                "product_name": name,
                "truth": truth_s,
                "pred": pred_s,
                "confidence": pred.confidence,
                "reason": pred.reason,
                "status": status,
            }
        )

    predicted = tp + fp
    labeled = sum(1 for r in eval_rows if r.get("vsic_code") is not None)
    precision = (tp / predicted) if predicted else None
    recall = (tp / labeled) if labeled else None
    abstain_rate = sum(1 for d in details if d["pred"] is None) / len(eval_rows)
    # Exact match including correct nulls
    correct = tp + tn_ok
    accuracy = correct / len(eval_rows)

    return {
        "split": split,
        "n": len(eval_rows),
        "precision": precision,
        "recall_labeled": recall,
        "abstain_rate": abstain_rate,
        "accuracy_including_abstain": accuracy,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn_abstain_correct": tn_ok,
        "backend": "sklearn_tfidf_logreg",
        "embedding_path": False,
        "details": details,
    }
