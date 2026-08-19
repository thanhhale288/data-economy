"""Tiny digital-text PDF writer for synthetic BCTC fixtures (no reportlab).

Helvetica Type1 has no Vietnamese glyphs, so labels are ASCII-folded.
The extract mapper folds diacritics the same way. Fixtures are not filings.
"""

from __future__ import annotations

from pathlib import Path


def _escape_pdf_literal(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _content_stream(lines: list[str], *, font_size: int = 11, x: int = 50, y0: int = 750, leading: int = 16) -> bytes:
    parts = ["BT", f"/F1 {font_size} Tf", f"{x} {y0} Td"]
    for i, line in enumerate(lines):
        lit = _escape_pdf_literal(line)
        if i == 0:
            parts.append(f"({lit}) Tj")
        else:
            parts.append(f"0 {-leading} Td ({lit}) Tj")
    parts.append("ET")
    return ("\n".join(parts) + "\n").encode("latin-1")


def write_simple_text_pdf(path: str | Path, pages: list[list[str]]) -> None:
    """Write a multi-page ASCII text PDF that pdfplumber can extract."""
    if not pages:
        raise ValueError("pages must be non-empty")
    n = len(pages)
    font_id = 3
    page_ids = [4 + 2 * i for i in range(n)]
    content_ids = [5 + 2 * i for i in range(n)]
    streams = [_content_stream(lines) for lines in pages]

    objs: dict[int, bytes] = {}
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objs[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objs[2] = f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode("ascii")
    objs[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    for pid, cid, stream in zip(page_ids, content_ids, streams):
        objs[pid] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {cid} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>"
        ).encode("ascii")
        objs[cid] = f"<< /Length {len(stream)} >>stream\n".encode("ascii") + stream + b"endstream\n"

    max_id = max(objs)
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i in range(1, max_id + 1):
        offsets.append(len(out))
        out += f"{i} 0 obj".encode("ascii") + objs[i] + b"endobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {max_id + 1}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for i in range(1, max_id + 1):
        out += f"{offsets[i]:010d} 00000 n \n".encode("ascii")
    out += (
        f"trailer<< /Size {max_id + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"
    ).encode("ascii")
    Path(path).write_bytes(bytes(out))


def write_task70_fixtures(fixtures_dir: str | Path) -> list[Path]:
    """Generate de-identified HOSE-like synthetic PDFs for Task #70. Round numbers only."""
    root = Path(fixtures_dir)
    root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    cases: list[tuple[str, list[list[str]]]] = [
        (
            "hose_like_trieu.pdf",
            [
                [
                    "CONG TY CO PHAN MAU SANG CHE",
                    "Bao cao tai chinh hop nhat nam 2025 (synthetic, not a filing)",
                    "Ma CK: MSC (fake ticker, not a listed issuer)",
                    "Don vi: Trieu dong",
                    "Chi tieu Ma so Nam nay",
                    "Doanh thu thuan 10 12.500",
                    "Loi nhuan truoc thue 50 1.800",
                    "Tong tai san 270 45.000",
                    "Von chu so huu 400 22.000",
                    "So lao dong 1.250",
                ]
            ],
        ),
        (
            "en_sales_layout.pdf",
            [
                [
                    "Mau Den Che Limited (synthetic HOSE-like layout, not a filing)",
                    "Unit: VND",
                    "Revenue from sales 8,800,000,000",
                    "Profit before tax 440,000,000",
                    "Total assets 15,000,000,000",
                    "Total equity 7,200,000,000",
                    "Number of employees 880",
                ]
            ],
        ),
        (
            "partial_revenue_assets.pdf",
            [
                [
                    "Cong ty Co phan Mau Xanh Che (synthetic, not a filing)",
                    "Don vi: VND",
                    "Doanh thu thuan 2.000.000.000",
                    "Tong tai san 9.000.000.000",
                    "Ghi chu: thieu cac chi tieu khac (khong co LNTT / CSH / headcount)",
                ]
            ],
        ),
        (
            "hose_notes_noise.pdf",
            [
                [
                    "Cong ty Co phan Mau Vang Che",
                    "Bao cao tai chinh (synthetic, not a filing) - Don vi: VND",
                    "Doanh thu thuan 3.000.000.000",
                    "Loi nhuan truoc thue 300.000.000",
                    "Tong tai san 8.000.000.000",
                    "Von chu so huu 4.000.000.000",
                    "So lao dong 400",
                ],
                [
                    "Thuyet minh BCTC (synthetic notes page - not statement lines)",
                    "Gia von hang ban 1.111.000.000",
                    "Chi phi ban hang 222.000.000",
                    "Doanh thu tai chinh 55.000.000",
                    "Tai san co dinh 777.000.000",
                    "Phai thu khach hang 333.000.000",
                    "Tai san ngan han 1.500.000.000",
                    "Do not invent fields from this notes page.",
                ],
            ],
        ),
        (
            "hose_nghin_dong.pdf",
            [
                [
                    "Cong ty Co phan Mau Tim Che",
                    "Bao cao tai chinh (synthetic, not a filing)",
                    "Don vi: Nghin dong",
                    "Doanh thu thuan 4.200.000",
                    "Loi nhuan truoc thue 210.000",
                    "Tong tai san 9.900.000",
                    "Von chu so huu 5.100.000",
                    "So lao dong 210",
                ]
            ],
        ),
    ]

    for name, pages in cases:
        dest = root / name
        write_simple_text_pdf(dest, pages)
        written.append(dest)
    return written


if __name__ == "__main__":
    here = Path(__file__).resolve().parent / "fixtures"
    for path in write_task70_fixtures(here):
        print(path)
