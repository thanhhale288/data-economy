from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import (
    BenchmarkExtractResponse,
    BenchmarkInput,
    BenchmarkNarrativeResponse,
    BenchmarkResult,
)
from backend.app.services import benchmark_narrative, benchmark_service
from backend.app.services.bctc_extract import extract_bctc_dict

router = APIRouter()


@router.post("/compare", response_model=BenchmarkResult)
def compare_benchmark(data: BenchmarkInput, db: Session = Depends(get_db)):
    """Compare firm ratios to VSIC-division peers from seeded BCTC.

    Missing peer samples return null percentiles and ``insufficient_peers``
    warnings — never a fabricated 50th percentile.
    """
    return benchmark_service.run_benchmark(db, data)


@router.post("/narrative", response_model=BenchmarkNarrativeResponse)
def benchmark_narrative_explain(data: BenchmarkResult):
    """Giải thích percentile/ROA/ROE tiếng Việt chỉ từ số trong BenchmarkResult.

    Không chạy lại compare math; không ghi DB; thiếu metric → omitted / nói thiếu.
    """
    return benchmark_narrative.generate_benchmark_narrative(data)


@router.post("/extract", response_model=BenchmarkExtractResponse)
async def extract_benchmark_file(file: UploadFile = File(...)):
    """Extract benchmark fields from uploaded BCTC file.

    Reuses Task #52/#53 parser + OCR router (no DB writes, no compare side effects).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must include a filename.")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    return extract_bctc_dict(content, filename=file.filename)


@router.get("/prefill/{stock_code}", response_model=BenchmarkInput)
def prefill_benchmark(stock_code: str, db: Session = Depends(get_db)):
    """Load form defaults from a listed company's latest annual report."""
    payload = benchmark_service.load_input_from_company(db, stock_code)
    if payload is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No complete BCTC prefill for {stock_code.upper()} "
                "(need revenue, profit_before_tax, and employees)."
            ),
        )
    return payload
