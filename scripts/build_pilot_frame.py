#!/usr/bin/env python3
"""Build Evol-1 T02 pilot frame from masothue industry listings."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from crawlers.companies.masothue_frame import (
    DEFAULT_DIVISIONS,
    INDUSTRY_INDEX,
    MasothueClient,
    dedupe_by_tax,
    write_frame_csv,
    write_summary_csv,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target", type=int, default=800, help="Target unique firms")
    p.add_argument("--delay", type=float, default=1.2, help="Seconds between requests")
    p.add_argument("--max-index-pages", type=int, default=40)
    p.add_argument("--max-pages-per-industry", type=int, default=80)
    p.add_argument(
        "--output-dir",
        default="data/raw/frame_pilot",
        help="Output folder for frame, summary, and provenance",
    )
    return p.parse_args()


def write_provenance(
    path: Path,
    *,
    retrieved_at: str,
    target: int,
    divisions: list[str],
    industries: list[tuple[str, str]],
    n_unique: int,
    division_counts: Counter[str],
) -> None:
    lines: list[str] = [
        "# PROVENANCE — Frame Pilot (Evol-1 T02)",
        "",
        f"- Retrieved at (UTC): {retrieved_at}",
        "- Source: https://www.masothue.com public listing pages",
        f"- Industry index: {INDUSTRY_INDEX}",
        f"- Requested divisions: {', '.join(divisions)}",
        f"- Target unique firms: {target}",
        f"- Final unique firms: {n_unique}",
        "",
        "## Coverage",
        "",
        "- VSIC 4-digit industries discovered and harvested:",
    ]
    for code, url in industries:
        lines.append(f"  - {code}: {url}")
    lines.extend(
        [
            "",
            "## Counts by division",
            "",
        ]
    )
    for div in sorted(division_counts):
        lines.append(f"- {div}: {division_counts[div]}")
    lines.extend(
        [
            "",
            "## Limits",
            "",
            "- Data comes from public directory pages; unavailable or blocked pages reduce coverage.",
            "- Firms are deduplicated by tax_code; no synthetic records are created.",
            "- founded_year is left empty when not present on listing pages.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    frame_csv = out_dir / "frame_pilot.csv"
    summary_csv = out_dir / "frame_pilot_summary.csv"
    provenance_md = out_dir / "PROVENANCE.md"

    divisions = sorted(DEFAULT_DIVISIONS)
    all_rows = []
    seen_taxes: set[str] = set()

    with MasothueClient(delay_seconds=args.delay) as client:
        industries = client.discover_industries(
            divisions=divisions,
            max_index_pages=args.max_index_pages,
        )

        by_div: dict[str, list] = defaultdict(list)
        for industry in industries:
            by_div[industry.vsic_code[:2]].append(industry)

        ordered: list = []
        max_len = max((len(v) for v in by_div.values()), default=0)
        for i in range(max_len):
            for div in sorted(divisions):
                items = by_div.get(div, [])
                if i < len(items):
                    ordered.append(items[i])

        harvested: list[tuple[str, str]] = []
        for industry in ordered:
            harvested.append((industry.vsic_code, industry.url))
            batch = client.harvest_industry(
                industry,
                max_pages=args.max_pages_per_industry,
                stop_at=args.target,
                seen_taxes=seen_taxes,
            )
            all_rows.extend(batch)
            if len(seen_taxes) >= args.target:
                break

    unique_rows = dedupe_by_tax(all_rows)
    n_rows = write_frame_csv(frame_csv, unique_rows)
    _ = write_summary_csv(summary_csv, unique_rows)

    division_counts = Counter(r.vsic_division for r in unique_rows)
    retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    write_provenance(
        provenance_md,
        retrieved_at=retrieved_at,
        target=args.target,
        divisions=divisions,
        industries=harvested,
        n_unique=n_rows,
        division_counts=division_counts,
    )

    print(f"unique_firms={n_rows}")
    print("counts_by_division=")
    for div in sorted(division_counts):
        print(f"  {div}: {division_counts[div]}")
    print(f"wrote={frame_csv}")
    print(f"wrote={summary_csv}")
    print(f"wrote={provenance_md}")

    # Quick CSV health check
    with frame_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in ["company_name", "tax_code", "vsic_4digit", "vsic_division"] if c not in reader.fieldnames]
        if missing:
            raise RuntimeError(f"Missing columns in frame CSV: {missing}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
