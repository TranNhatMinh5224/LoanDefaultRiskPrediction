from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime
from app.db.database import Base

class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    sk_id_curr = Column(String, index=True, nullable=True)
    risk_score = Column(Float)
    decision = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
