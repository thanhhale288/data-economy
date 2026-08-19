from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import ModelPrediction, ModelRegistry
from backend.app.schemas import (
    CategorizeRequest,
    CategorizeResponse,
    ForecastNarrativeRequest,
    ForecastNarrativeResponse,
    ForecastRequest,
    ModelPredictionOut,
)
from backend.app.services import forecast_narrative, ml_lab_service, product_categorizer_service

router = APIRouter()


@router.get("/models")
def list_models(db: Session = Depends(get_db)):
    """Return registered models (ORM includes metrics JSON: mae/rmse/mape/status)."""
    return db.query(ModelRegistry).order_by(ModelRegistry.trained_at.desc()).all()


@router.get("/predictions", response_model=list[ModelPredictionOut])
def list_predictions(
    model_name: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(ModelPrediction)
    if model_name:
        q = q.filter(ModelPrediction.model_name == model_name)
    return q.order_by(ModelPrediction.period).all()


@router.get("/feature-importance")
def feature_importance(
    model_name: str = Query(
        "xgboost",
        description="Model with importance artifact (xgboost|lightgbm)",
    ),
):
    """Read feature-importance artifact. Missing → available=false (no invented scores)."""
    return ml_lab_service.get_feature_importance(model_name)


@router.post("/narrative", response_model=ForecastNarrativeResponse)
def forecast_narrative_explain(data: ForecastNarrativeRequest):
    """Tóm tắt horizon / sai số / driver tiếng Việt — chỉ cite số từ payload + importance.

    Không train lại; thiếu importance → nói thiếu, không bịa nguyên nhân.
    """
    return forecast_narrative.generate_forecast_narrative(
        {
            "model": data.model,
            "horizon": data.horizon,
            "forecasts": [p.model_dump() for p in data.forecasts],
        },
        metrics=data.metrics,
        importance=data.importance,
        load_importance=data.load_importance,
    )


@router.post("/categorize", response_model=CategorizeResponse)
def categorize_product(data: CategorizeRequest) -> CategorizeResponse:
    """Classify a marketplace product name into VSIC Section C (4-digit).

    Loads the offline TF-IDF artifact once; never trains in-request.
    Uncertain / OOV / short input → vsic_code=null + reason (no invented code).
    """
    result = product_categorizer_service.categorize_product(data.product_name)
    return CategorizeResponse(
        product_name=result.product_name,
        vsic_code=result.vsic_code,
        confidence=result.confidence,
        reason=result.reason,
    )


@router.post("/forecast")
def run_forecast(request: ForecastRequest, db: Session = Depends(get_db)):
    from ml.models.trainer import generate_forecast

    try:
        return generate_forecast(db, request.model_name, request.horizon_months)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/train")
def train_models(db: Session = Depends(get_db)):
    from ml.models.trainer import train_all_models

    count = train_all_models(db)
    return {"status": "success", "records": count}
