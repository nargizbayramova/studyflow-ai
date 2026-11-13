from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import (
    CurrentUser,
    DbSession,
    Paging,
    apply_update,
    delete_owned,
    get_owned,
    is_admin,
)
from app.models import Course
from app.schemas.errors import ERROR_RESPONSES, ApiResponse, PaginatedResponse, ok, ok_list
from app.schemas.planner import CourseCreate, CourseRead, CourseUpdate

router = APIRouter(prefix="/courses", tags=["Courses"], responses=ERROR_RESPONSES)

DUPLICATE = "A course with this code already exists for this semester"


async def _commit(db: DbSession) -> None:
    try:
        await db.commit()
    except IntegrityError:  # uq_courses_user_code_semester
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, DUPLICATE)


@router.get("", response_model=PaginatedResponse[CourseRead], summary="List courses")
async def list_courses(
    user: CurrentUser,
    db: DbSession,
    page: Paging,
    semester: str | None = None,
    include_archived: bool = False,
    user_id: int | None = Query(None, description="Admin only: filter by owner user_id"),
) -> dict:
    q = select(Course)
    if not is_admin(user):
        q = q.where(Course.user_id == user.id)
    elif user_id is not None:
        q = q.where(Course.user_id == user_id)

    if semester:
        q = q.where(Course.semester == semester)
    if not include_archived:
        q = q.where(Course.is_archived.is_(False))

    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = list(
        await db.scalars(
            q.order_by(Course.semester.desc(), Course.code).limit(page.limit).offset(page.offset)
        )
    )
    return ok_list(items, total, page.page, page.per_page, "Courses retrieved successfully.")


@router.post(
    "",
    response_model=ApiResponse[CourseRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create a course",
)
async def create_course(body: CourseCreate, user: CurrentUser, db: DbSession) -> dict:
    course = Course(**body.model_dump(), user_id=user.id)
    db.add(course)
    await _commit(db)
    return ok(course, "Course created successfully.")


@router.get(
    "/semesters",
    response_model=ApiResponse[list[str]],
    summary="List distinct semesters / workspaces",
)
async def list_semesters(user: CurrentUser, db: DbSession) -> dict:
    q = select(Course.semester).distinct().order_by(Course.semester.desc())
    if not is_admin(user):
        q = q.where(Course.user_id == user.id)
    semesters = list(await db.scalars(q))
    return ok(semesters, "Semesters retrieved successfully.")


@router.get("/{course_id}", response_model=ApiResponse[CourseRead], summary="Get a course by ID")
async def get_course(course_id: int, user: CurrentUser, db: DbSession) -> dict:
    course = await get_owned(db, Course, course_id, user)
    return ok(course, "Course retrieved successfully.")


@router.put("/{course_id}", response_model=ApiResponse[CourseRead], summary="Replace a course")
async def replace_course(
    course_id: int, body: CourseCreate, user: CurrentUser, db: DbSession
) -> dict:
    course = await get_owned(db, Course, course_id, user)
    for field, value in body.model_dump().items():
        setattr(course, field, value)
    await _commit(db)
    return ok(course, "Course updated successfully.")


@router.patch(
    "/{course_id}",
    response_model=ApiResponse[CourseRead],
    summary="Edit or archive a course",
)
async def update_course(
    course_id: int, body: CourseUpdate, user: CurrentUser, db: DbSession
) -> dict:
    course = await get_owned(db, Course, course_id, user)
    apply_update(course, body, nullable=frozenset({"instructor"}))
    await _commit(db)
    return ok(course, "Course updated successfully.")


@router.delete(
    "/{course_id}",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete a course",
)
async def delete_course(course_id: int, user: CurrentUser, db: DbSession) -> dict:
    await delete_owned(db, Course, course_id, user)
    return ok(None, "Course deleted successfully.")
