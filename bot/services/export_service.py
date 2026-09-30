import csv
from pathlib import Path

from bot.database.database import get_session
from bot.database.models import ChangeHistory, ProjectChange
from sqlalchemy import select

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)

def _dt(value):
    return value.astimezone().strftime("%Y-%m-%d %H:%M:%S") if value else ""

async def export_changes() -> Path:
    async with get_session() as session:
        result = await session.execute(
            select(ProjectChange).order_by(ProjectChange.id.asc())
        )
        changes = result.scalars().all()

    path = EXPORT_DIR / "changes.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "ID", "Название", "Описание", "Причина", "Область",
            "Приоритет", "Влияние на сроки", "Влияние на стоимость",
            "Ответственный", "Статус", "Автор", "Дата создания", "Дата изменения",
        ])
        for c in changes:
            writer.writerow([
                c.id, c.title, c.description, c.reason, c.affected_area,
                c.priority, c.schedule_impact, c.cost_impact,
                c.responsible_person, c.status,
                c.creator_full_name or c.creator_username or c.created_by,
                _dt(c.created_at), _dt(c.updated_at),
            ])
    return path

async def export_history() -> Path:
    async with get_session() as session:
        result = await session.execute(
            select(ChangeHistory).order_by(
                ChangeHistory.change_id.asc(),
                ChangeHistory.changed_at.asc(),
                ChangeHistory.id.asc(),
            )
        )
        history = result.scalars().all()

    path = EXPORT_DIR / "change_history.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "ID", "Change ID", "Старый статус", "Новый статус",
            "Изменил", "Telegram ID", "Дата", "Комментарий",
        ])
        for h in history:
            writer.writerow([
                h.id, h.change_id, h.old_status or "", h.new_status,
                h.changed_by_name, h.changed_by, _dt(h.changed_at), h.comment,
            ])
    return path
