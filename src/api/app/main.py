from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.predict_router import router as predict_router
from app.db.database import Base, engine

# Tự động tạo bảng DB nếu chưa có
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME, 
    version="2.0",
    description="Hệ thống chấm điểm tín dụng Home Credit chuẩn Clean Architecture"
)

# Đăng ký các Router
app.include_router(predict_router, prefix="/api/v1", tags=["Prediction (V1)"])

@app.get("/", tags=["Health Check"])
def health_check():
    return {"status": "OK", "message": "Clean Architecture FastAPI is running perfectly!"}
