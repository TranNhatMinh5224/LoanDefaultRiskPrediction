from pydantic import BaseModel
from typing import Dict, Optional

class PredictionRequest(BaseModel):
    sk_id_curr: Optional[str] = "UNKNOWN_ID"
    features: Dict[str, float]

class PredictionResponse(BaseModel):
    sk_id_curr: str
    risk_score: float
    decision: str
