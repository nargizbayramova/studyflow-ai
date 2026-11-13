from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class FieldError(BaseModel):
    field: str
    message: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[FieldError] | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class PaginationMeta(BaseModel):
    total: int
    page: int
    perPage: int


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: list[T]
    meta: PaginationMeta


def ok(data: T, message: str) -> dict:
    return {"success": True, "message": message, "data": data}


def ok_list(data: list[T], total: int, page: int, per_page: int, message: str) -> dict:
    return {
        "success": True,
        "message": message,
        "data": data,
        "meta": {"total": total, "page": page, "perPage": per_page},
    }


ERROR_RESPONSES: dict[int | str, dict] = {
    400: {"model": ErrorResponse, "description": "Invalid input or validation error"},
    401: {"model": ErrorResponse, "description": "Missing or invalid bearer token"},
    403: {"model": ErrorResponse, "description": "Insufficient permissions for resource"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    409: {"model": ErrorResponse, "description": "Conflict with existing data"},
}
