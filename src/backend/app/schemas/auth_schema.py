from pydantic import BaseModel, Field
from typing import List

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["nguyenvana"])
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", examples=["nguyenvana@bank.com"])
    password: str = Field(..., min_length=6, examples=["Abc@123456"])

class RoleResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    roles: List[RoleResponse] = []

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str = Field(description="Token dùng để gia hạn đăng nhập")
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Mã Refresh Token để xin Access Token mới")
