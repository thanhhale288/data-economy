#!/usr/bin/env python3
"""Evol-1 T04: pin-check + classify 10 cached pages on lab Ollama; write throughput log.

Does not call OpenAI/Gemini. CI should use mocked unit tests, not this script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from crawlers.companies.listed_companies import load_seed_companies
from ml.local_llm.client import (
    DEFAULT_TIMEOUT,
    LocalLlmSettings,
    extract_page,
    list_running,
    load_pin,
    prompt_sha256,
    schema_sha256,
    verify_pin,
)
from ml.local_llm.text import html_to_text

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "local_llm"
PAGES_DIR = RAW_DIR / "pages"
MANIFEST_PAGES = RAW_DIR / "pages_manifest.json"
PROVENANCE = RAW_DIR / "PROVENANCE.md"
OUT_DIR = ROOT / "data" / "processed" / "local_llm"
SMOKE_RUN = OUT_DIR / "smoke_run.json"
RUN_MANIFEST = OUT_DIR / "run_manifest.json"

SMOKE_TICKERS = ("RAL", "HPG", "VNM", "FPT", "GVR", "DGC", "MSN", "PNJ", "REE", "BMP")
USER_AGENT = "Mozilla/5.0 (compatible; MfgDataEconomy/1.0; +research)"
FETCH_TIMEOUT = 20.0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--fetch-pages",
        action="store_true",
        help="Download listed-company homepages into data/raw/local_llm/pages/",
    )
    p.add_argument(
        "--skip-warmup",
        action="store_true",
        help="Skip the one-shot warmup request (load_duration isolation).",
    )
    p.add_argument(
        "--no-verify-pin",
        action="store_true",
        help="Skip digest check (debug only).",
    )
    return p.parse_args()


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_pages() -> dict:
    seed = {c["stock_code"]: c for c in load_seed_companies()}
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    with httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=FETCH_TIMEOUT,
        follow_redirects=True,
    ) as client:
        for ticker in SMOKE_TICKERS:
            company = seed.get(ticker)
            if not company:
                rows.append({"ticker": ticker, "ok": False, "error": "missing_seed"})
                continue
            url = (company.get("website_url") or "").strip()
            name = company.get("name") or ticker
            entry = {
                "ticker": ticker,
                "name": name,
                "url": url,
                "retrieved_at": _utcnow(),
                "ok": False,
            }
            try:
                resp = client.get(url)
                entry["http_status"] = resp.status_code
                html = resp.text or ""
                text = html_to_text(html)
                text_path = PAGES_DIR / f"{ticker}.txt"
                text_path.write_text(text, encoding="utf-8")
                entry.update(
                    {
                        "ok": resp.is_success and bool(text.strip()),
                        "char_count": len(text),
                        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                        "path": str(text_path.relative_to(ROOT)),
                    }
                )
                if not resp.is_success:
                    entry["error"] = f"http_{resp.status_code}"
            except httpx.HTTPError as exc:
                entry["error"] = type(exc).__name__
                entry["detail"] = str(exc)[:200]
            rows.append(entry)
            time.sleep(0.4)
    payload = {"retrieved_at": _utcnow(), "tickers": list(SMOKE_TICKERS), "pages": rows}
    MANIFEST_PAGES.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _write_provenance(payload)
    return payload


def _write_provenance(pages_manifest: dict) -> None:
    ok_n = sum(1 for p in pages_manifest["pages"] if p.get("ok"))
    lines = [
        "# PROVENANCE — Local LLM smoke pages (Evol-1 T04)",
        "",
        f"- Retrieved at (UTC): {pages_manifest['retrieved_at']}",
        "- Source: homepage URLs from `data/seeds/companies.json` (listed sample).",
        f"- Tickers: {', '.join(SMOKE_TICKERS)}",
        f"- Pages with usable text: {ok_n}/{len(SMOKE_TICKERS)}",
        "- Text truncated to ~8000 visible characters (scripts/styles removed).",
        "- Purpose: smoke-test pinned Ollama model JSON extraction — **not** a research estimate.",
        "",
        "## Limits",
        "",
        "- Listed firms only; easy websites. Do not generalize to Section C.",
        "- Fetch failures stay as missing pages — never invent page text.",
        "- HTML dumps are not required; truncated `.txt` is the model input.",
        "",
    ]
    PROVENANCE.write_text("\n".join(lines), encoding="utf-8")


def load_cached_pages() -> list[dict]:
    if not MANIFEST_PAGES.exists():
        raise SystemExit(
            f"Missing {MANIFEST_PAGES}. Re-run with --fetch-pages first."
        )
    manifest = json.loads(MANIFEST_PAGES.read_text(encoding="utf-8"))
    pages = []
    for row in manifest["pages"]:
        if not row.get("ok"):
            continue
        path = ROOT / row["path"]
        text = path.read_text(encoding="utf-8")
        pages.append({**row, "text": text})
    if len(pages) < 10:
        raise SystemExit(
            f"Need 10 cached pages for DoD; got {len(pages)}. Re-run --fetch-pages."
        )
    return pages[:10]


def main() -> None:
    args = parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.fetch_pages:
        fetch_pages()

    pages = load_cached_pages()
    settings = LocalLlmSettings.from_pin_and_env()
    pin = load_pin()

    with httpx.Client(base_url=settings.base_url, timeout=DEFAULT_TIMEOUT) as http:
        pin_info = None
        if not args.no_verify_pin:
            pin_info = verify_pin(http, settings)
        running_before = list_running(http)

        warmup = None
        if not args.skip_warmup:
            t0 = time.perf_counter()
            warm = extract_page(
                "Trang gioi thieu. San pham. Gio hang. VNPay.",
                url="https://example.invalid/warmup",
                http=http,
                settings=settings,
                verify=False,
            )
            warmup = {
                "wall_s": round(time.perf_counter() - t0, 3),
                "decision": warm.decision,
                "load_duration_ns": warm.load_duration_ns,
                "eval_duration_ns": warm.eval_duration_ns,
            }

        results = []
        wall_times: list[float] = []
        eval_ns: list[int] = []
        for page in pages:
            t0 = time.perf_counter()
            out = extract_page(
                page["text"],
                url=page.get("url"),
                http=http,
                settings=settings,
                verify=False,
            )
            wall = time.perf_counter() - t0
            wall_times.append(wall)
            if out.eval_duration_ns:
                eval_ns.append(out.eval_duration_ns)
            results.append(
                {
                    "ticker": page["ticker"],
                    "url": page.get("url"),
                    "wall_s": round(wall, 3),
                    **out.to_json_dict(),
                    # Drop raw model text from durable artifact (can be long).
                    "raw_content": None,
                }
            )

        running_after = list_running(http)

    mean_wall = sum(wall_times) / len(wall_times)
    pages_per_hour = round(3600.0 / mean_wall, 2) if mean_wall > 0 else None
    mean_eval_s = (sum(eval_ns) / len(eval_ns) / 1e9) if eval_ns else None
    pages_per_hour_eval = (
        round(3600.0 / mean_eval_s, 2) if mean_eval_s and mean_eval_s > 0 else None
    )

    smoke = {
        "task": "evol1-t04-local-llm-smoke",
        "created_at": _utcnow(),
        "model": settings.model,
        "digest": (pin_info or {}).get("digest") or settings.digest,
        "n_pages": len(results),
        "decisions": {
            "ok": sum(1 for r in results if r["decision"] == "ok"),
            "retry_ok": sum(1 for r in results if r["decision"] == "retry_ok"),
            "abstain": sum(1 for r in results if r["decision"] == "abstain"),
        },
        "pages": results,
    }
    SMOKE_RUN.write_text(json.dumps(smoke, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    manifest = {
        "task": "evol1-t04-local-llm-setup",
        "created_at": _utcnow(),
        "base_url": settings.base_url,
        "model": settings.model,
        "digest": (pin_info or {}).get("digest") or settings.digest,
        "digest_pinned": pin["digest"],
        "digest_match": True if pin_info else None,
        "ollama_version": (pin_info or {}).get("ollama_version"),
        "quantization": (pin_info or {}).get("quantization") or pin.get("quantization"),
        "parameter_size": (pin_info or {}).get("parameter_size") or pin.get("parameter_size"),
        "temperature": settings.temperature,
        "seed": settings.seed,
        "think": settings.think,
        "prompt_sha256": prompt_sha256(),
        "schema_sha256": schema_sha256(),
        "warmup": warmup,
        "n_pages": len(results),
        "mean_wall_s": round(mean_wall, 3),
        "pages_per_hour_wall": pages_per_hour,
        "mean_eval_s": round(mean_eval_s, 3) if mean_eval_s is not None else None,
        "pages_per_hour_eval": pages_per_hour_eval,
        "decisions": smoke["decisions"],
        "running_models_before": running_before,
        "running_models_after": running_after,
        "artifacts": {
            "smoke_run": str(SMOKE_RUN.relative_to(ROOT)),
            "pages_manifest": str(MANIFEST_PAGES.relative_to(ROOT)),
        },
        "notes": [
            "Throughput is a lab snapshot on a shared GPU — record timestamp.",
            "Cost ~0 (lab Ollama open-weights). Not a P/R measurement (see T06).",
        ],
    }
    RUN_MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
