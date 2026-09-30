import pytest

from bot.database import crud

@pytest.mark.asyncio
async def test_create_and_get_change(db_session):
    change = await crud.create_change(
        db_session,
        data={
            "title": "Изменить фасад",
            "description": "Заменить материал",
            "reason": "Требование заказчика",
            "affected_area": "architecture",
            "priority": "high",
            "schedule_impact": "minor",
            "cost_impact": "increase",
            "responsible_person": "Иванов И.И.",
            "comment": "Тест",
        },
        user_id=100,
        username="ivan",
        full_name="Иванов Иван",
    )
    loaded = await crud.get_change(db_session, change.id)
    assert loaded is not None
    assert loaded.title == "Изменить фасад"
    assert loaded.status == "new"
    assert len(loaded.history) == 1

@pytest.mark.asyncio
async def test_status_and_history(db_session):
    change = await crud.create_change(
        db_session,
        data={
            "title": "Тест",
            "description": "Описание",
            "reason": "Причина",
            "affected_area": "other",
            "priority": "medium",
            "schedule_impact": "none",
            "cost_impact": "none",
            "responsible_person": "123456789",
            "comment": "",
        },
        user_id=1,
        username="u",
        full_name="User",
    )
    history = await crud.change_status(
        db_session,
        change,
        new_status="review",
        user_id=2,
        user_name="Reviewer",
        comment="Передано на проверку",
    )
    assert history.old_status == "new"
    assert history.new_status == "review"

    rows = await crud.get_history(db_session, change.id)
    assert len(rows) == 2
    assert rows[-1].comment == "Передано на проверку"

@pytest.mark.asyncio
async def test_filter_and_statistics(db_session):
    base = {
        "description": "D",
        "reason": "R",
        "affected_area": "architecture",
        "priority": "high",
        "schedule_impact": "none",
        "cost_impact": "increase",
        "responsible_person": "A",
        "comment": "",
    }
    await crud.create_change(
        db_session,
        data={**base, "title": "Фасад"},
        user_id=1, username="a", full_name="A",
    )
    await crud.create_change(
        db_session,
        data={**base, "title": "Кровля", "priority": "low", "affected_area": "construction"},
        user_id=1, username="a", full_name="A",
    )

    filtered = await crud.list_changes(db_session, priority="high")
    assert len(filtered) == 1
    assert filtered[0].title == "Фасад"

    stats = await crud.statistics(db_session)
    assert stats["total"] == 2
    assert stats["priorities"]["high"] == 1
    assert stats["priorities"]["low"] == 1
