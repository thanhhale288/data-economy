from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import BenchmarkInput, BenchmarkResult
from backend.app.services import benchmark_service

router = APIRouter()


@router.post("/compare", response_model=BenchmarkResult)
def compare_benchmark(data: BenchmarkInput, db: Session = Depends(get_db)):
    """Compare firm ratios to VSIC-division peers from seeded BCTC.

    Missing peer samples return null percentiles and ``insufficient_peers``
    warnings — never a fabricated 50th percentile.
    """
    return benchmark_service.run_benchmark(db, data)


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
