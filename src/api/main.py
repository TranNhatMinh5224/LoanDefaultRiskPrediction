from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional
import pandas as pd
import joblib
import os
import time

from .database import SessionLocal, PredictionLog

app = FastAPI(title="Home Credit Default Risk API (Production)", version="1.0")

# Chú ý: Đặt thư mục "models" chứa 2 file .joblib nằm chung cấp với file main.py này
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models/lgbm_model_v3.joblib')
IMPUTER_PATH = os.path.join(os.path.dirname(__file__), 'models/imputer_v3.joblib')

try:
    model = joblib.load(MODEL_PATH)
    imputer = joblib.load(IMPUTER_PATH)
    print("✅ Đã load Model và Imputer thành công!")
except Exception as e:
    print(f"❌ Lỗi: Không tìm thấy file tại {MODEL_PATH}. Nhớ copy thư mục Model vào src/api/models nhé!")
    model = None
    imputer = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PredictionRequest(BaseModel):
    sk_id_curr: Optional[str] = "UNKNOWN_ID"
    features: Dict[str, float] 

@app.get("/")
def read_root():
    return {"message": "✅ API Production Home Credit (FastAPI + PostgreSQL) đang chạy!"}

@app.post("/predict")
def predict_risk(request: PredictionRequest, db: Session = Depends(get_db)):
    if model is None or imputer is None:
        raise HTTPException(status_code=500, detail="Mô hình chưa được nạp.")
    
    df = pd.DataFrame([request.features])
    
    try:
        df_imputed = pd.DataFrame(imputer.transform(df), columns=df.columns)
        risk_prob = model.predict_proba(df_imputed)[0][1]
        decision = "REJECT" if risk_prob > 0.3 else "APPROVE"
        
        # Lưu vào PostgreSQL
        log_entry = PredictionLog(
            sk_id_curr=request.sk_id_curr,
            risk_score=float(risk_prob),
            decision=decision
        )
        db.add(log_entry)
        db.commit()
        
        return {
            "sk_id_curr": request.sk_id_curr,
            "risk_score": float(risk_prob),
            "decision": decision
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
