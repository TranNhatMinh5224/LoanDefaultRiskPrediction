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
    features: Dict[str, Any] = Field(
        ..., 
        title="Đặc trưng tài chính (Financial Features)",
        description="""
Bắt buộc phải truyền các trường (fields) sau để mô hình có thể dự đoán.
Giải thích các trường quan trọng (đã ánh xạ sang chuẩn Việt Nam):
- CODE_GENDER (Giới tính): 'F' (Nữ), 'M' (Nam).
- NAME_EDUCATION_TYPE (Trình độ học vấn): 'Higher education', 'Secondary / secondary special'...
- FLAG_OWN_CAR (Sở hữu ô tô): 'Y' (Có), 'N' (Không).
- EXT_SOURCE_1 (Điểm uy tín Dân cư): Điểm từ cơ sở dữ liệu quốc gia (Bảo hiểm, hộ khẩu...). (0.0 -> 1.0).
- EXT_SOURCE_2 (Điểm tín dụng Ngân hàng): Tương đương điểm CIC, đánh giá uy tín tín dụng hiện tại. (0.0 -> 1.0).
- EXT_SOURCE_3 (Điểm uy tín Viễn thông): Alternative data (Dữ liệu thanh toán cước, sinh hoạt...). (0.0 -> 1.0).
- DAYS_BIRTH: Tuổi của khách hàng tính bằng số ngày âm.
- DAYS_EMPLOYED: Số ngày đã làm việc tại công ty hiện tại (số âm).
- AMT_INCOME_TOTAL: Tổng thu nhập hàng năm (VND/USD).
- AMT_CREDIT: Tổng số tiền muốn vay.
- AMT_ANNUITY: Số tiền phải trả góp hàng tháng.
- BUREAU_AMT_CREDIT_SUM_mean: Trung bình dư nợ tại tổ chức tín dụng CIC.
- INSTAL_DPD_max: Số ngày trễ hạn thanh toán tối đa trong quá khứ.
        """,
        json_schema_extra={
            "examples": [
                {
                    "CODE_GENDER": "F",
                    "NAME_EDUCATION_TYPE": "Higher education",
                    "FLAG_OWN_CAR": "Y",
                    "EXT_SOURCE_1": 0.501,
                    "EXT_SOURCE_2": 0.222,
                    "EXT_SOURCE_3": 0.155,
                    "DAYS_BIRTH": -15000,
                    "DAYS_EMPLOYED": -2500,
                    "AMT_INCOME_TOTAL": 200000,
                    "AMT_CREDIT": 500000,
                    "AMT_ANNUITY": 25000,
                    "BUREAU_AMT_CREDIT_SUM_mean": 150000,
                    "INSTAL_DPD_max": 5
                }
            ]
        }
    )

    @field_validator('features')
    @classmethod
    def check_features_not_empty(cls, v):
        if not v:
            raise ValueError("Danh sách đặc trưng (features) không được để trống.")
        
        # Validate EXT_SOURCE (Điểm tín dụng thường từ 0 đến 1)
        for ext in ['EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3']:
            if ext in v:
                val = v[ext]
                if val < 0 or val > 1:
                    raise ValueError(f'{ext} phải nằm trong khoảng từ 0.0 đến 1.0.')
        
        # Validate DAYS_BIRTH (Vì lúc train là số âm, khách tuổi từ 18->100 tương đương số ngày âm từ -6570 đến -36500)
        if 'DAYS_BIRTH' in v:
            if v['DAYS_BIRTH'] > 0:
                raise ValueError('DAYS_BIRTH phải là số ngày âm (Tính từ quá khứ đến hiện tại).')
            if v['DAYS_BIRTH'] < -40000:
                raise ValueError('DAYS_BIRTH có vẻ không hợp lệ (Lớn hơn 100 tuổi).')

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
