from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Standardized API response wrapper schema to unify API response formats.
    """

    success: bool
    message: str
    data: Optional[T] = None
