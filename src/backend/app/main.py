from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.predict_router import router as predict_router
from app.api.v1.auth_router import router as auth_router
from app.db.database import Base, engine
import app.models  # Import toàn bộ models để SQLAlchemy nhận diện được

# Tự động chạy Migration tương đương với context.Database.Migrate() trong .NET
from alembic.config import Config
from alembic import command

alembic_cfg = Config("alembic.ini")
command.upgrade(alembic_cfg, "head")

app = FastAPI(
    title=settings.PROJECT_NAME, 
    version="2.0",
    description="Hệ thống chấm điểm tín dụng Home Credit chuẩn Clean Architecture"
)

# Đăng ký các Router
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(predict_router, prefix="/api/v1", tags=["Prediction (V1)"])

@app.get("/", tags=["Health Check"])
def health_check():
    return {"status": "OK", "message": "Clean Architecture FastAPI is running perfectly!"}
