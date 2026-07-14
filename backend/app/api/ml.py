from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import ModelPrediction, ModelRegistry
from backend.app.schemas import ForecastRequest, ModelPredictionOut

router = APIRouter()


@router.get("/models")
def list_models(db: Session = Depends(get_db)):
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


@router.post("/forecast")
def run_forecast(request: ForecastRequest, db: Session = Depends(get_db)):
    from ml.models.trainer import generate_forecast

    return generate_forecast(db, request.model_name, request.horizon_months)


@router.post("/train")
def train_models(db: Session = Depends(get_db)):
    from ml.models.trainer import train_all_models

    count = train_all_models(db)
    return {"status": "success", "records": count}
