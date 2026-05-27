from sqlalchemy.orm import Session
from app.db.models import PredictionLog

class PredictionRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_prediction(self, sk_id_curr: str, risk_score: float, decision: str) -> PredictionLog:
        log_entry = PredictionLog(
            sk_id_curr=sk_id_curr,
            risk_score=risk_score,
            decision=decision
        )
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        return log_entry
