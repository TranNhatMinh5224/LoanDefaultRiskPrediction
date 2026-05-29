from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.prediction_model import PredictionLog
from datetime import datetime, timedelta

class PredictionRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_prediction(self, sk_id_curr: str, risk_score: float, decision: str, duration_ms: float = None, model_version: str = "v1") -> PredictionLog:
        log_entry = PredictionLog(
            sk_id_curr=sk_id_curr,
            risk_score=risk_score,
            decision=decision,
            duration_ms=duration_ms,
            model_version=model_version
        )
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        return log_entry

    def get_history(self, skip: int = 0, limit: int = 10) -> list[PredictionLog]:
        return self.db.query(PredictionLog).order_by(PredictionLog.created_at.desc()).offset(skip).limit(limit).all()

    def count_total(self) -> int:
        return self.db.query(PredictionLog).count()

    def get_monitoring_stats(self) -> dict:
        """Lấy các chỉ số thống kê cơ bản cho Dashboard Monitoring"""
        total = self.count_total()
        approve = self.db.query(PredictionLog).filter(PredictionLog.decision == "APPROVE").count()
        reject = total - approve

        # Tỷ lệ reject 7 ngày qua (đơn giản hóa)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_total = self.db.query(PredictionLog).filter(PredictionLog.created_at >= seven_days_ago).count()
        recent_reject = self.db.query(PredictionLog).filter(PredictionLog.created_at >= seven_days_ago, PredictionLog.decision == "REJECT").count()
        
        last_7_days_reject_rate = round(recent_reject / recent_total, 4) if recent_total > 0 else 0.0
        
        # Baseline rate giả định lúc deploy
        baseline_rate = 0.28
        
        avg_duration = self.db.query(func.avg(PredictionLog.duration_ms)).scalar()
        
        return {
            "total_predictions": total,
            "approve_count": approve,
            "reject_count": reject,
            "last_7_days_reject_rate": last_7_days_reject_rate,
            "baseline_reject_rate": baseline_rate,
            "drift_detected": (last_7_days_reject_rate - baseline_rate) > 0.1,  # Báo động nếu tăng đột biến > 10%
            "avg_latency_ms": round(avg_duration, 2) if avg_duration else 0.0
        }
