from datetime import datetime

from bot.keyboards.changes import STATUS_LABELS

def format_dt(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.astimezone().strftime("%d.%m.%Y %H:%M")

def format_history(history: list) -> str:
    if not history:
        return "📜 История отсутствует."
    lines = []
    for item in history:
        old = STATUS_LABELS.get(item.old_status, "—") if item.old_status else "—"
        new = STATUS_LABELS.get(item.new_status, item.new_status)
        lines.append(
            f"<b>{format_dt(item.changed_at)}</b>\n"
            f"{old} → {new}\n"
            f"Автор: {item.changed_by_name or item.changed_by}\n"
            f"Комментарий: {item.comment or '—'}"
        )
    return "\n\n".join(lines)
