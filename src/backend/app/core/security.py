import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import os
import secrets

# Config JWT (Thực tế nên lấy từ file .env)
SECRET_KEY = os.getenv("JWT_SECRET", "super_secret_key_for_loan_prediction_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15 # Giảm xuống 15 phút để bảo mật

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token() -> str:
    # Sinh một chuỗi ngẫu nhiên 128 ký tự an toàn tuyệt đối
    return secrets.token_hex(64)
