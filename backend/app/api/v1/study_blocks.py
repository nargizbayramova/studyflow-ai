from fastapi import APIRouter, HTTPException, Query, status
from pydantic import AwareDatetime
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.api.deps import (
    CurrentUser,
    DbSession,
    Paging,
    apply_update,
    delete_owned,
    get_owned,
    is_admin,
)
from app.models import BlockStatus, Course, StudyBlock, Task, User
from app.schemas.errors import ERROR_RESPONSES, ApiResponse, PaginatedResponse, ok, ok_list
from app.schemas.planner import StudyBlockCreate, StudyBlockRead, StudyBlockUpdate

router = APIRouter(prefix="/study-blocks", tags=["Study Blocks"], responses=ERROR_RESPONSES)


async def _get_block_with_details(db: DbSession, block_id: int, actor: User) -> StudyBlock:
    stmt = (
        select(StudyBlock)
        .options(joinedload(StudyBlock.task).joinedload(Task.course))
        .where(StudyBlock.id == block_id)
    )
    block = (await db.scalars(stmt)).unique().first()
    if block is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "StudyBlock not found")
    if not is_admin(actor) and block.user_id != actor.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "You do not have permission to access this StudyBlock",
        )
    return block


@router.get(
    "",
    response_model=PaginatedResponse[StudyBlockRead],
    summary="List / filter study blocks (FR-09, FR-10)",
)
async def list_study_blocks(
    user: CurrentUser,
    db: DbSession,
    page: Paging,
    task_id: int | None = None,
    user_id: int | None = Query(None, description="Admin only: filter by owner user_id"),
    semester: str | None = None,
    status_: BlockStatus | None = Query(None, alias="status"),
    start_from: AwareDatetime | None = None,
    start_to: AwareDatetime | None = None,
) -> dict:
    base = select(StudyBlock)
    if not is_admin(user):
        base = base.where(StudyBlock.user_id == user.id)
    elif user_id is not None:
        base = base.where(StudyBlock.user_id == user_id)

    if semester:
        base = base.join(StudyBlock.task).join(Task.course).where(Course.semester == semester)
    if task_id is not None:
        base = base.where(StudyBlock.task_id == task_id)
    if status_ is not None:
        base = base.where(StudyBlock.status == status_)
    if start_from is not None:
        base = base.where(StudyBlock.start_at >= start_from)
    if start_to is not None:
        base = base.where(StudyBlock.start_at <= start_to)

    total = await db.scalar(select(func.count()).select_from(base.subquery())) or 0
    stmt = (
        base.options(joinedload(StudyBlock.task).joinedload(Task.course))
        .order_by(StudyBlock.start_at, StudyBlock.id)
        .limit(page.limit)
        .offset(page.offset)
    )
    items = list((await db.scalars(stmt)).unique())
    return ok_list(items, total, page.page, page.per_page, "Study blocks retrieved successfully.")


@router.post(
    "",
    response_model=ApiResponse[StudyBlockRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create a study block",
)
async def create_study_block(
    body: StudyBlockCreate, user: CurrentUser, db: DbSession
) -> dict:
    task = await get_owned(db, Task, body.task_id, user)
    block = StudyBlock(**body.model_dump(), user_id=task.user_id)
    db.add(block)
    await db.commit()
    detailed = await _get_block_with_details(db, block.id, user)
    return ok(detailed, "Study block created successfully.")


@router.get(
    "/{block_id}",
    response_model=ApiResponse[StudyBlockRead],
    summary="Get a study block by ID",
)
async def get_study_block(block_id: int, user: CurrentUser, db: DbSession) -> dict:
    block = await _get_block_with_details(db, block_id, user)
    return ok(block, "Study block retrieved successfully.")


@router.put(
    "/{block_id}",
    response_model=ApiResponse[StudyBlockRead],
    summary="Replace a study block",
)
async def replace_study_block(
    block_id: int, body: StudyBlockCreate, user: CurrentUser, db: DbSession
) -> dict:
    block = await get_owned(db, StudyBlock, block_id, user)
    if body.task_id != block.task_id:
        task = await get_owned(db, Task, body.task_id, user)
        block.user_id = task.user_id
    for field, value in body.model_dump().items():
        setattr(block, field, value)
    await db.commit()
    detailed = await _get_block_with_details(db, block.id, user)
    return ok(detailed, "Study block updated successfully.")


@router.patch(
    "/{block_id}",
    response_model=ApiResponse[StudyBlockRead],
    summary="Partially update a study block",
)
async def update_study_block(
    block_id: int, body: StudyBlockUpdate, user: CurrentUser, db: DbSession
) -> dict:
    block = await get_owned(db, StudyBlock, block_id, user)
    if body.task_id is not None and body.task_id != block.task_id:
        task = await get_owned(db, Task, body.task_id, user)
        block.user_id = task.user_id
    new_start = body.start_at if body.start_at is not None else block.start_at
    new_end = body.end_at if body.end_at is not None else block.end_at
    if new_end <= new_start:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "end_at must be after start_at")
    apply_update(block, body)
    await db.commit()
    detailed = await _get_block_with_details(db, block.id, user)
    return ok(detailed, "Study block updated successfully.")


@router.delete(
    "/{block_id}",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a study block",
)
async def delete_study_block(block_id: int, user: CurrentUser, db: DbSession) -> dict:
    await delete_owned(db, StudyBlock, block_id, user)
    return ok(None, "Study block deleted successfully.")
