from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional, Any, List
from datetime import datetime

class PredictionRequest(BaseModel):
    sk_id_curr: str = Field(
        default="UNKNOWN", 
        title="Mã Khách Hàng", 
        description="Mã định danh duy nhất của khách hàng (Tùy chọn).",
        examples=["100002"]
    )
    features: Dict[str, float] = Field(
        ..., 
        title="Đặc trưng tài chính",
        description="Từ điển chứa các biến số (features) đầu vào cho mô hình AI.",
        examples=[{"EXT_SOURCE_1": 0.5, "EXT_SOURCE_2": 0.6, "EXT_SOURCE_3": 0.4, "AGE": 35, "BUREAU_TOTAL_DEBT": 50000}]
    )

    @field_validator('features')
    @classmethod
    def check_features_not_empty(cls, v):
        if not v:
            raise ValueError("Danh sách đặc trưng (features) không được để trống.")
        # Ví dụ validate một số field bắt buộc nếu cần:
        # if 'AGE' not in v:
        #     raise ValueError("Thiếu trường bắt buộc: AGE")
        return v

class PredictionResponse(BaseModel):
    sk_id_curr: str = Field(..., title="Mã Khách Hàng")
    risk_score: float = Field(..., title="Điểm Rủi Ro", ge=0.0, le=1.0, description="Xác suất vỡ nợ (từ 0.0 đến 1.0)")
    decision: str = Field(..., title="Quyết Định", examples=["APPROVE", "REJECT"])

class ModelInfoResponse(BaseModel):
    version: str = Field(..., title="Phiên bản mô hình")
    algorithm: str = Field(..., title="Thuật toán")
    status: str = Field(..., title="Trạng thái")
    total_features_expected: int = Field(..., title="Số lượng biến đầu vào")

class PredictionHistoryItem(BaseModel):
    id: int
    sk_id_curr: str = Field(title="Mã Khách Hàng")
    risk_score: float = Field(title="Điểm Rủi Ro")
    decision: str = Field(title="Quyết Định")
    created_at: datetime = Field(title="Thời gian dự đoán")

    class Config:
        from_attributes = True

class PaginatedPredictionHistory(BaseModel):
    total: int = Field(title="Tổng số bản ghi")
    page: int = Field(title="Trang hiện tại")
    size: int = Field(title="Kích thước trang")
    data: List[PredictionHistoryItem] = Field(title="Danh sách lịch sử")
