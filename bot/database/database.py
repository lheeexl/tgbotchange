from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.database.models import Base

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None

async def init_db(database_url: str) -> None:
    global _engine, _session_factory
    _engine = create_async_engine(database_url, echo=False)
    _session_factory = async_sessionmaker(
        _engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None

def session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the configured SQLAlchemy async session factory."""
    if _session_factory is None:
        raise RuntimeError("Database is not initialized")
    return _session_factory


def get_session() -> AsyncSession:
    """Create and return a new asynchronous database session."""
    return session_factory()()
