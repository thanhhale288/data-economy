from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import (
    BctcConsistencyIn,
    BctcConsistencyOut,
    BenchmarkExtractResponse,
    BenchmarkInput,
    BenchmarkNarrativeResponse,
    BenchmarkResult,
)
from backend.app.schemas.feedback_signal import FeedbackSignalIn, FeedbackSignalOut
from backend.app.services import benchmark_narrative, benchmark_service, feedback_signal
from backend.app.services.bctc_consistency import check_consistency
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


@router.post("/feedback", response_model=FeedbackSignalOut)
def benchmark_feedback(data: FeedbackSignalIn):
    """Store DocAI/Benchmark edit→confirm as a safe training signal.

    Persists field diffs + ticker + source_type + timestamp only.
    Never stores raw PDF/bytes/API keys (Task #64).
    """
    try:
        return feedback_signal.append_signal(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/consistency", response_model=BctcConsistencyOut)
def check_bctc_consistency(data: BctcConsistencyIn, db: Session = Depends(get_db)):
    """So sánh các trường extract/nhập tay với BCTC lịch sử trong DB cho cùng ticker.

    Flags các trường lệch ≥ 10% so với kỳ annual gần nhất.
    Không overwrite DB — chỉ đọc và báo cáo.
    Trả có_db_record=false nếu ticker không tìm thấy — không invent.
    """
    report = check_consistency(db, data.ticker, data.fields)
    return BctcConsistencyOut(
        ticker=report.ticker,
        period=report.period,
        report_type=report.report_type,
        flags=[
            {
                "extract_field": f.extract_field,
                "db_column": f.db_column,
                "extract_value": f.extract_value,
                "db_value": f.db_value,
                "rel_deviation": f.rel_deviation,
                "severity": f.severity,
                "note": f.note,
            }
            for f in report.flags
        ],
        has_db_record=report.has_db_record,
        summary=report.summary,
    )


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
