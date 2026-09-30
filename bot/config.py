import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_id: int
    database_url: str

def get_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    admin_raw = os.getenv("ADMIN_ID", "").strip()
    database_url = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./project_changes.db",
    )
    if not token:
        raise RuntimeError("BOT_TOKEN is not set in .env")
    if not admin_raw.isdigit():
        raise RuntimeError("ADMIN_ID must be a numeric Telegram ID")
    return Settings(
        bot_token=token,
        admin_id=int(admin_raw),
        database_url=database_url,
    )
