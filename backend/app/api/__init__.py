from fastapi import APIRouter

from backend.app.api import benchmark, companies, dashboard, macro, ml, pipeline

router = APIRouter()
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(companies.router, prefix="/companies", tags=["companies"])
router.include_router(macro.router, prefix="/macro", tags=["macro"])
router.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
router.include_router(ml.router, prefix="/ml", tags=["ml"])
router.include_router(benchmark.router, prefix="/benchmark", tags=["benchmark"])
