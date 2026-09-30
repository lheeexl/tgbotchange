from bot.database import crud
from bot.database.database import get_session

async def create_change(data: dict, user_id: int, username: str, full_name: str):
    async with get_session() as session:
        return await crud.create_change(
            session,
            data=data,
            user_id=user_id,
            username=username,
            full_name=full_name,
        )

async def get_change(change_id: int):
    async with get_session() as session:
        return await crud.get_change(session, change_id)

async def list_changes(**filters):
    async with get_session() as session:
        return await crud.list_changes(session, **filters)

async def edit_change(change_id: int, fields: dict):
    async with get_session() as session:
        change = await crud.get_change(session, change_id)
        if change is None:
            return None
        return await crud.update_change_fields(session, change, fields)

async def set_status(
    change_id: int,
    new_status: str,
    user_id: int,
    user_name: str,
    comment: str,
):
    async with get_session() as session:
        change = await crud.get_change(session, change_id)
        if change is None:
            return None, None
        history = await crud.change_status(
            session,
            change,
            new_status=new_status,
            user_id=user_id,
            user_name=user_name,
            comment=comment,
        )
        return change, history

async def history(change_id: int):
    async with get_session() as session:
        return await crud.get_history(session, change_id)

async def stats():
    async with get_session() as session:
        return await crud.statistics(session)
