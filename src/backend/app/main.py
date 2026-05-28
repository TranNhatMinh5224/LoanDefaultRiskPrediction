from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.predict_router import router as predict_router
from app.api.v1.auth_router import router as auth_router
from app.db.database import Base, engine
import app.models  # Import toàn bộ models để SQLAlchemy nhận diện được

try:
    # Thử chạy tạo bảng tự động (An toàn hơn Alembic nếu DB chưa kịp khởi động)
    Base.metadata.create_all(bind=engine)
    print("✅ Đã khởi tạo các bảng trong Database thành công!")
except Exception as e:
    print("❌ Lỗi khi khởi tạo Database:", e)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME, 
    version="2.0",
    description="Hệ thống chấm điểm tín dụng Home Credit chuẩn Clean Architecture"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các Router
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(predict_router, prefix="/api/v1", tags=["Prediction (V1)"])

@app.get("/", tags=["Health Check"])
def health_check():
    return {"status": "OK", "message": "Clean Architecture FastAPI is running perfectly!"}
