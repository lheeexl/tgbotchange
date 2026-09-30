from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class ProjectChange(Base):
    __tablename__ = "project_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    affected_area: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    schedule_impact: Mapped[str] = mapped_column(String(50), nullable=False)
    cost_impact: Mapped[str] = mapped_column(String(50), nullable=False)
    responsible_person: Mapped[str] = mapped_column(String(200), nullable=False)
    responsible_telegram_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    comment: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="new", nullable=False)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    creator_username: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    creator_full_name: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    history: Mapped[list["ChangeHistory"]] = relationship(
        back_populates="change",
        cascade="all, delete-orphan",
        order_by="ChangeHistory.changed_at",
    )

class ChangeHistory(Base):
    __tablename__ = "change_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    change_id: Mapped[int] = mapped_column(
        ForeignKey("project_changes.id", ondelete="CASCADE"),
        nullable=False,
    )
    old_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    changed_by_name: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    comment: Mapped[str] = mapped_column(Text, default="", nullable=False)

    change: Mapped[ProjectChange] = relationship(back_populates="history")
