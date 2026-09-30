import csv

import pytest
from sqlalchemy import select

from bot.database.models import ProjectChange
from bot.services.export_service import export_changes, export_history

@pytest.mark.asyncio
async def test_csv_exports(tmp_path, monkeypatch, db_session):
    # This test validates the generated CSV shape using the same database session API.
    # Replace service session factory with a local factory.
    from sqlalchemy.ext.asyncio import async_sessionmaker
    factory = async_sessionmaker(db_session.bind, expire_on_commit=False)

    import bot.services.export_service as exporter
    monkeypatch.setattr(exporter, "session_factory", lambda: factory)
    monkeypatch.setattr(exporter, "EXPORT_DIR", tmp_path)

    from bot.database import crud
    change = await crud.create_change(
        db_session,
        data={
            "title": "CSV Test",
            "description": "D",
            "reason": "R",
            "affected_area": "other",
            "priority": "low",
            "schedule_impact": "none",
            "cost_impact": "none",
            "responsible_person": "A",
            "comment": "",
        },
        user_id=1,
        username="u",
        full_name="User",
    )
    await crud.change_status(
        db_session,
        change,
        new_status="completed",
        user_id=2,
        user_name="Admin",
        comment="Done",
    )

    changes_path = await export_changes()
    history_path = await export_history()

    assert changes_path.exists()
    assert history_path.exists()

    with changes_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))
    assert rows[0][0] == "ID"
    assert rows[1][1] == "CSV Test"

    with history_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))
    assert rows[0][1] == "Change ID"
    assert len(rows) == 3
