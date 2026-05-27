from fastapi import HTTPException, status
from datetime import datetime, timedelta
from app.schemas.auth_schema import UserCreate
from app.models.user_model import User
from app.models.refresh_token_model import RefreshToken
from app.repositories.user_repo import UserRepository
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token

class AuthService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def register_user(self, user_data: UserCreate) -> User:
        # Business Logic 1: Check trùng Email
        if self.repo.get_user_by_email(user_data.email):
            raise HTTPException(status_code=400, detail="Email đã tồn tại trong hệ thống.")
            
        # Business Logic 2: Check trùng Username
        if self.repo.get_user_by_username(user_data.username):
            raise HTTPException(status_code=400, detail="Username đã tồn tại.")

        # Business Logic 3: Băm mật khẩu và lưu
        hashed_pw = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_pw
        )
        return self.repo.create_user(new_user)

    def login(self, email: str, password: str) -> tuple[str, str]:
        # Tìm user
        user = self.repo.get_user_by_email(email)
        
        # Validate logic
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoặc mật khẩu không chính xác."
            )
        
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Tài khoản đã bị khóa.")

        # Trả về bộ đôi JWT Token và Refresh Token
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token()
        
        # Lưu Refresh Token xuống DB (Thọ 7 ngày)
        rt_entry = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        self.repo.save_refresh_token(rt_entry)
        
        return access_token, refresh_token

    def refresh_access_token(self, refresh_token: str) -> tuple[str, str]:
        # 1. Tìm Token trong DB
        rt_entry = self.repo.get_refresh_token(refresh_token)
        if not rt_entry:
            raise HTTPException(status_code=401, detail="Refresh Token không hợp lệ.")
            
        # 2. Kiểm tra thu hồi & Hết hạn
        if rt_entry.is_revoked:
            raise HTTPException(status_code=401, detail="Refresh Token đã bị thu hồi.")
        if rt_entry.expires_at < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Refresh Token đã hết hạn.")
            
        # 3. Lấy thông tin user
        user = rt_entry.user
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Tài khoản đã bị khóa.")
            
        # 4. Sinh bộ đôi Token mới
        token_data = {"sub": str(user.id), "email": user.email}
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token()
        
        # Xoay vòng Token (Thu hồi token cũ)
        rt_entry.is_revoked = True
        
        # Lưu token mới
        new_rt_entry = RefreshToken(
            user_id=user.id,
            token=new_refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        self.repo.save_refresh_token(new_rt_entry)
        
        return new_access_token, new_refresh_token
