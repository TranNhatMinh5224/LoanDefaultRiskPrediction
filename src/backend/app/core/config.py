from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Cấu hình hệ thống — tự động đọc từ file .env hoặc biến môi trường.
    Pydantic-settings tự validate kiểu dữ liệu và báo lỗi rõ ràng
    nếu thiếu biến môi trường bắt buộc.
    """

    model_config = SettingsConfigDict(
        env_file=".env",        # Tự động đọc file .env
        env_file_encoding="utf-8",
        case_sensitive=False,   # POSTGRES_USER và postgres_user đều được
        extra="ignore",         # Bỏ qua các biến .env không dùng
    )

    # ---- App ----
    PROJECT_NAME: str = "Home Credit Default Risk API"
    DEBUG: bool = False

    # ---- Database (bắt buộc phải có trong .env) ----
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "loan_default_db"
    POSTGRES_PORT: int = 5432

    # ---- JWT Auth ----
    SECRET_KEY: str = "change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Tự động tạo connection string từ các biến trên"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
