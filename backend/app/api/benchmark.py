from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import BenchmarkInput, BenchmarkResult
from backend.app.services import benchmark_service

router = APIRouter()


@router.post("/compare", response_model=BenchmarkResult)
def compare_benchmark(data: BenchmarkInput, db: Session = Depends(get_db)):
    return benchmark_service.run_benchmark(db, data)
