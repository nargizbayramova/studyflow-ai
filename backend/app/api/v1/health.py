from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.deps import DbSession
from app.core.config import settings
from app.schemas.errors import ApiResponse, ErrorDetail, ErrorResponse, ok
from app.schemas.health import HealthResponse
from app.services import monitoring

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=ApiResponse[HealthResponse],
    summary="Liveness & database health check",
    responses={503: {"model": ErrorResponse, "description": "Database unreachable"}},
)
async def health(response: Response, db: DbSession) -> dict | JSONResponse:
    """Used by Docker/monitoring probes (checked every 60s per the monitoring matrix)."""
    try:
        await db.execute(text("SELECT 1"))
        return ok(
            HealthResponse(status="ok", database="up", version=settings.VERSION),
            "Service is healthy.",
        )
    except Exception:
        monitoring.record_db_error()
        err = ErrorResponse(
            error=ErrorDetail(
                code="SERVICE_UNAVAILABLE",
                message="Database is currently unreachable.",
            )
        )
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=err.model_dump(exclude_none=True))
