from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.api.dependencies import get_db
from app.schemas.auth_schema import UserCreate, UserResponse, TokenResponse, RefreshTokenRequest
from app.schemas.base_response import BaseResponse
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService

router = APIRouter()

# DI: FastAPI sẽ bơm db vào -> sau đó ta bơm repo vào service
def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    repo = UserRepository(db)
    return AuthService(repo)

@router.post("/register", response_model=BaseResponse[UserResponse])
def register(user_data: UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    new_user = auth_service.register_user(user_data)
    return BaseResponse(
        success=True,
        message="Đăng ký tài khoản thành công",
        data=new_user
    )

@router.post("/login", response_model=BaseResponse[TokenResponse])
def login(form_data: OAuth2PasswordRequestForm = Depends(), auth_service: AuthService = Depends(get_auth_service)):
    # Lấy bộ đôi Token
    access_token, refresh_token = auth_service.login(email=form_data.username, password=form_data.password)
    return BaseResponse(
        success=True,
        message="Đăng nhập thành công",
        data=TokenResponse(access_token=access_token, refresh_token=refresh_token)
    )

@router.post("/refresh", response_model=BaseResponse[TokenResponse])
def refresh_token(request: RefreshTokenRequest, auth_service: AuthService = Depends(get_auth_service)):
    # Đổi Token mới
    access_token, refresh_token = auth_service.refresh_access_token(request.refresh_token)
    return BaseResponse(
        success=True,
        message="Cấp lại Token thành công",
        data=TokenResponse(access_token=access_token, refresh_token=refresh_token)
    )
