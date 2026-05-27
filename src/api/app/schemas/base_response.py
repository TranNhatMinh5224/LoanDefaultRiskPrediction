from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Thành công"
    data: Optional[T] = None
