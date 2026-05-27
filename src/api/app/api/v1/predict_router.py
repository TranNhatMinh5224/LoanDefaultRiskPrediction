from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.predict_schema import PredictionRequest, PredictionResponse
from app.api.dependencies import get_db
from app.services.ml_service import ml_service_instance
from app.repositories.predict_repo import PredictionRepository

router = APIRouter()

@router.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest, db: Session = Depends(get_db)):
    try:
        # Bước 1: Đưa dữ liệu sang tầng Dịch vụ để tính toán rủi ro (Business Logic)
        risk_score, decision = ml_service_instance.predict_default_risk(request.features)
        
        # Bước 2: Khởi tạo Repository và ra lệnh lưu vào DB (Repository Pattern)
        repo = PredictionRepository(db)
        repo.save_prediction(
            sk_id_curr=request.sk_id_curr, 
            risk_score=risk_score, 
            decision=decision
        )
        
        # Bước 3: Trả về kết quả
        return PredictionResponse(
            sk_id_curr=request.sk_id_curr,
            risk_score=risk_score,
            decision=decision
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
