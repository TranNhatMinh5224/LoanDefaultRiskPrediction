from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from fastapi.responses import StreamingResponse
import io
import pandas as pd
from sqlalchemy.orm import Session
from app.schemas.predict_schema import (
    PredictionRequest, 
    PredictionResponse, 
    ModelInfoResponse,
    PaginatedPredictionHistory,
    MonitoringStatsResponse
)
from app.schemas.base_response import BaseResponse
from app.api.dependencies import get_db
from app.services.ml_service import ml_service_instance
from app.repositories.predict_repo import PredictionRepository

router = APIRouter()

@router.post("/predict", response_model=BaseResponse[PredictionResponse])
def predict(request: PredictionRequest, db: Session = Depends(get_db)):
    try:
        # Bước 1: Đưa dữ liệu sang tầng Dịch vụ để tính toán rủi ro (Business Logic)
        risk_score, decision, duration_ms = ml_service_instance.predict_default_risk(request.features)
        model_version = ml_service_instance.active_version
        
        # Bước 2: Khởi tạo Repository và ra lệnh lưu vào DB (Repository Pattern)
        repo = PredictionRepository(db)
        repo.save_prediction(
            sk_id_curr=request.sk_id_curr, 
            risk_score=risk_score, 
            decision=decision,
            duration_ms=duration_ms,
            model_version=model_version
        )
        
        # Bước 3: Trả về kết quả
        return BaseResponse(
            success=True,
            message="Dự đoán thành công",
            data=PredictionResponse(
                sk_id_curr=request.sk_id_curr,
                risk_score=risk_score,
                decision=decision,
                duration_ms=duration_ms,
                model_version=model_version
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/predict/batch", tags=["Prediction (V1)"])
async def predict_batch(file: UploadFile = File(...)):
    """
    API Xử lý hàng loạt. Nhận vào file CSV/Excel, trả về file CSV chứa cột kết quả.
    """
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ upload file .csv hoặc .xlsx")
        
    contents = await file.read()
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Không thể đọc file: {str(e)}")
        
    # Gọi Service xử lý nguyên cái DataFrame
    try:
        df_result = ml_service_instance.predict_batch_risk(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi chạy model: {str(e)}")
    
    # Xuất ra bộ đệm String để trả về dưới dạng File Tải xuống
    stream = io.StringIO()
    df_result.to_csv(stream, index=False)
    
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=predicted_{file.filename}.csv"
    return response

@router.get("/model/info", response_model=BaseResponse[ModelInfoResponse], tags=["MLOps"])
def get_model_info():
    """
    Lấy thông tin siêu dữ liệu (Metadata) của mô hình AI đang chạy.
    Rất quan trọng cho MLOps để biết API đang chạy version model nào.
    """
    if ml_service_instance.model is None:
        raise HTTPException(status_code=503, detail="Mô hình AI chưa sẵn sàng.")
    
    # LightGBM sklearn wrapper lưu số feature trong thuộc tính n_features_in_ hoặc n_features_
    n_features = getattr(ml_service_instance.model, 'n_features_in_', 
                 getattr(ml_service_instance.model, 'n_features_', 245))
    
    return BaseResponse(
        success=True,
        message="Lấy thông tin mô hình thành công",
        data=ModelInfoResponse(
            version="v1.0.0",
            algorithm="LightGBM Classifier",
            status="Healthy",
            total_features_expected=n_features
        )
    )

@router.get("/history", response_model=BaseResponse[PaginatedPredictionHistory], tags=["History"])
def get_prediction_history(
    page: int = Query(1, ge=1, description="Số trang hiện tại"),
    size: int = Query(10, ge=1, le=100, description="Số bản ghi trên mỗi trang (tối đa 100)"),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách lịch sử dự đoán có phân trang (Pagination).
    Trả về dữ liệu mới nhất trước.
    """
    repo = PredictionRepository(db)
    
    # Tính toán offset
    skip = (page - 1) * size
    
    # Lấy dữ liệu từ Repo
    total_records = repo.count_total()
    records = repo.get_history(skip=skip, limit=size)
    
    return BaseResponse(
        success=True,
        message="Lấy lịch sử dự đoán thành công",
        data=PaginatedPredictionHistory(
            total=total_records,
            page=page,
            size=size,
            data=records
        )
    )

@router.get("/monitoring/stats", response_model=BaseResponse[MonitoringStatsResponse], tags=["MLOps"])
def get_monitoring_stats(db: Session = Depends(get_db)):
    """
    Lấy thống kê model monitoring (Data drift, Performance latency, Tỷ lệ Reject).
    Dành cho Dashboard Monitoring.
    """
    repo = PredictionRepository(db)
    stats = repo.get_monitoring_stats()
    
    return BaseResponse(
        success=True,
        message="Lấy thống kê thành công",
        data=MonitoringStatsResponse(**stats)
    )
