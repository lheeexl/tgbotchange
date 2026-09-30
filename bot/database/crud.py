from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import ChangeHistory, ProjectChange, utcnow

async def create_change(
    session: AsyncSession,
    *,
    data: dict,
    user_id: int,
    username: str,
    full_name: str,
) -> ProjectChange:
    change = ProjectChange(
        **data,
        created_by=user_id,
        creator_username=username,
        creator_full_name=full_name,
        status="new",
    )
    session.add(change)
    await session.flush()

    session.add(
        ChangeHistory(
            change_id=change.id,
            old_status=None,
            new_status="new",
            changed_by=user_id,
            changed_by_name=full_name or username,
            comment="Изменение зарегистрировано.",
        )
    )
    await session.commit()
    await session.refresh(change)
    return change

async def get_change(
    session: AsyncSession,
    change_id: int,
) -> ProjectChange | None:
    result = await session.execute(
        select(ProjectChange)
        .options(selectinload(ProjectChange.history))
        .where(ProjectChange.id == change_id)
    )
    return result.scalar_one_or_none()

async def list_changes(
    session: AsyncSession,
    *,
    created_by: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    affected_area: str | None = None,
    title_query: str | None = None,
) -> list[ProjectChange]:
    query = select(ProjectChange).order_by(ProjectChange.created_at.desc())
    if created_by is not None:
        query = query.where(ProjectChange.created_by == created_by)
    if status is not None:
        query = query.where(ProjectChange.status == status)
    if priority is not None:
        query = query.where(ProjectChange.priority == priority)
    if affected_area is not None:
        query = query.where(ProjectChange.affected_area == affected_area)
    if title_query:
        query = query.where(ProjectChange.title.ilike(f"%{title_query}%"))

    result = await session.execute(query)
    return list(result.scalars().all())

async def update_change_fields(
    session: AsyncSession,
    change: ProjectChange,
    fields: dict,
) -> ProjectChange:
    for key, value in fields.items():
        setattr(change, key, value)
    change.updated_at = utcnow()
    await session.commit()
    await session.refresh(change)
    return change

async def change_status(
    session: AsyncSession,
    change: ProjectChange,
    *,
    new_status: str,
    user_id: int,
    user_name: str,
    comment: str,
) -> ChangeHistory:
    old_status = change.status
    change.status = new_status
    change.updated_at = utcnow()

    history = ChangeHistory(
        change_id=change.id,
        old_status=old_status,
        new_status=new_status,
        changed_by=user_id,
        changed_by_name=user_name,
        comment=comment,
    )
    session.add(history)
    await session.commit()
    await session.refresh(history)
    return history

async def get_history(
    session: AsyncSession,
    change_id: int,
) -> list[ChangeHistory]:
    result = await session.execute(
        select(ChangeHistory)
        .where(ChangeHistory.change_id == change_id)
        .order_by(ChangeHistory.changed_at.asc(), ChangeHistory.id.asc())
    )
    return list(result.scalars().all())

async def statistics(session: AsyncSession) -> dict:
    total = await session.scalar(select(func.count(ProjectChange.id))) or 0

    statuses = {}
    for status in (
        "new", "review", "approved", "rejected",
        "in_progress", "completed", "cancelled",
    ):
        statuses[status] = (
            await session.scalar(
                select(func.count(ProjectChange.id))
                .where(ProjectChange.status == status)
            )
            or 0
        )

    priorities = {}
    for priority in ("high", "medium", "low"):
        priorities[priority] = (
            await session.scalar(
                select(func.count(ProjectChange.id))
                .where(ProjectChange.priority == priority)
            )
            or 0
        )

    return {
        "total": total,
        "statuses": statuses,
        "priorities": priorities,
    }
