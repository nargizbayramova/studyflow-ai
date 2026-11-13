from typing import Annotated, TypeVar

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import Base, User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(db: DbSession, token: str = Depends(oauth2_scheme)) -> User:
    user_id = decode_access_token(token)
    user = await db.get(User, user_id) if user_id is not None else None
    if user is None or not user.is_active:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN


class Page:
    """Bounded pagination for every list endpoint (supports page/perPage and limit/offset)."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="1-based page number"),
        per_page: int = Query(50, ge=1, le=100, alias="perPage", description="Items per page"),
        limit: int | None = Query(None, ge=1, le=100, include_in_schema=False),
        offset: int | None = Query(None, ge=0, include_in_schema=False),
    ) -> None:
        self.limit = limit if limit is not None else per_page
        self.offset = offset if offset is not None else (page - 1) * self.limit
        self.page = (self.offset // self.limit) + 1 if offset is not None else page
        self.per_page = self.limit


Paging = Annotated[Page, Depends()]

M = TypeVar("M", bound=Base)


async def get_owned(db: AsyncSession, model: type[M], obj_id: int, actor: User | int) -> M:
    """Fetch a row by ID; 404 if missing, 403 if owned by another user (unless admin)."""
    obj = await db.scalar(select(model).where(model.id == obj_id))
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{model.__name__} not found")
    actor_id = actor.id if isinstance(actor, User) else actor
    actor_admin = isinstance(actor, User) and is_admin(actor)
    if not actor_admin and obj.user_id != actor_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"You do not have permission to access this {model.__name__}",
        )
    return obj


async def delete_owned(db: AsyncSession, model: type[Base], obj_id: int, actor: User | int) -> None:
    """Verify ownership/admin role, then delete in one statement with ON DELETE CASCADE."""
    await get_owned(db, model, obj_id, actor)
    await db.execute(delete(model).where(model.id == obj_id))
    await db.commit()


def apply_update(obj: Base, body: BaseModel, nullable: frozenset[str] = frozenset()) -> None:
    """Apply only the fields the client sent (PATCH semantics)."""
    for field, value in body.model_dump(exclude_unset=True).items():
        if value is None and field not in nullable:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{field} cannot be null")
        setattr(obj, field, value)
