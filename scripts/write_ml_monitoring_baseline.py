#!/usr/bin/env python3
"""Write data/models/ml_monitoring_baseline.json from ModelRegistry MAPE.

Honesty: only canonical models with a real numeric ``mape`` on the latest
registry row are included. Empty registry / no mape → warning, non-zero
exit, and no file written (never invent zeros).

Usage:
  PYTHONPATH=. python scripts/write_ml_monitoring_baseline.py
  PYTHONPATH=. python scripts/write_ml_monitoring_baseline.py --dry-run
  PYTHONPATH=. python scripts/write_ml_monitoring_baseline.py \
      --database-url sqlite:////path/to/mfg_economy.db
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.schemas.ml_monitoring import MlMonitoringBaselineIn
from backend.app.services.ml_monitoring import (
    CANONICAL_MODELS,
    DEFAULT_BASELINE_PATH,
    DEFAULT_MAPE_DRIFT_THRESHOLD,
    _coerce_metric,
    _latest_registry_row,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _metrics_dict(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def collect_latest_mape(db: Session) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Latest numeric MAPE per canonical model. Omits rows without mape."""
    models: dict[str, dict[str, Any]] = {}
    omitted: list[str] = []
    for name in CANONICAL_MODELS:
        row = _latest_registry_row(db, name)
        if row is None:
            omitted.append(f"{name}:registry_missing")
            continue
        mape = _coerce_metric(_metrics_dict(row.metrics).get("mape"))
        if mape is None:
            omitted.append(f"{name}:mape_missing")
            continue
        entry: dict[str, Any] = {"mape": float(mape)}
        trained = _iso(row.trained_at)
        if trained:
            entry["trained_at"] = trained
        if row.version:
            entry["version"] = row.version
        models[name] = entry
    return models, omitted


def build_payload(
    models: dict[str, dict[str, Any]],
    *,
    threshold: float = DEFAULT_MAPE_DRIFT_THRESHOLD,
) -> dict[str, Any]:
    payload = MlMonitoringBaselineIn(
        models=models,
        mape_drift_threshold=float(threshold),
    ).model_dump()
    payload["source"] = "ModelRegistry"
    return payload


def write_baseline_file(
    payload: dict[str, Any],
    path: Path,
    *,
    dry_run: bool = False,
) -> None:
    models = payload.get("models") or {}
    if not models:
        raise ValueError("refusing to write empty baseline (no numeric mape)")
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _open_session(database_url: str | None) -> Session:
    if database_url:
        url = database_url
    else:
        from backend.app.config import settings

        url = settings.database_url
    connect_args: dict[str, Any] = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
    return sessionmaker(bind=engine)()


def _print_report(
    models: dict[str, dict[str, Any]],
    omitted: list[str],
    *,
    path: Path,
    dry_run: bool,
    database_label: str,
) -> None:
    action = "would write" if dry_run else "wrote"
    print(f"source=ModelRegistry database={database_label}")
    if models:
        print(f"{action} {path}")
        for name, row in models.items():
            trained = row.get("trained_at") or "unknown"
            print(f"  {name}: mape={row['mape']} trained_at={trained}")
    if omitted:
        print("omitted (no real numeric mape):")
        for item in omitted:
            print(f"  {item}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write ml_monitoring_baseline.json from ModelRegistry MAPE."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written; do not create or overwrite the file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_BASELINE_PATH,
        help=f"Output JSON path (default: {DEFAULT_BASELINE_PATH})",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="SQLAlchemy URL. Defaults to DATABASE_URL / Settings (do not invent MAPE).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_MAPE_DRIFT_THRESHOLD,
        help=f"mape_drift_threshold (default: {DEFAULT_MAPE_DRIFT_THRESHOLD})",
    )
    args = parser.parse_args(argv)

    try:
        db = _open_session(args.database_url)
    except Exception as exc:  # noqa: BLE001
        print(
            f"warning: ModelRegistry unreachable ({type(exc).__name__}: {exc}). "
            "Not writing baseline (honesty — no invented MAPE).",
            file=sys.stderr,
        )
        return 2

    try:
        models, omitted = collect_latest_mape(db)
    except Exception as exc:  # noqa: BLE001
        print(
            f"warning: failed to read ModelRegistry ({type(exc).__name__}: {exc}). "
            "Not writing baseline (honesty — no invented MAPE).",
            file=sys.stderr,
        )
        return 2
    finally:
        db.close()

    db_label = "cli --database-url" if args.database_url else "Settings.database_url"
    if not models:
        _print_report(models, omitted, path=args.output, dry_run=True, database_label=db_label)
        print(
            "warning: no numeric mape in ModelRegistry for canonical models. "
            "Not writing a file (honesty — will not invent MAPE or zeros).",
            file=sys.stderr,
        )
        return 1

    payload = build_payload(models, threshold=args.threshold)
    if not args.dry_run:
        write_baseline_file(payload, args.output, dry_run=False)
    _print_report(
        models,
        omitted,
        path=args.output,
        dry_run=args.dry_run,
        database_label=db_label,
    )
    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
