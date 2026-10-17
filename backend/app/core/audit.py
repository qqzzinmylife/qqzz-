from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, JSON, String, func
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db.base import Base, BigInt


class AuditLog(Base):
    """操作审计：只写不改，因此没有 updated_at。"""

    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_target", "target_type", "target_id"),
        Index("ix_audit_log_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    actor_id: Mapped[int | None] = mapped_column(BigInt)
    actor_role: Mapped[str | None] = mapped_column(String(20))
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(50))
    target_id: Mapped[int | None] = mapped_column(BigInt)
    detail: Mapped[dict | None] = mapped_column(JSON)
    ip: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


def record_audit(
    db: Session,
    *,
    action: str,
    actor_id: int | None = None,
    actor_role: str | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
    detail: dict[str, Any] | None = None,
    ip: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip=ip,
    )
    db.add(entry)
    return entry
