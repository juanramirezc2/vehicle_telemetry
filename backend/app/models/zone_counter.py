from datetime import datetime

from sqlalchemy import DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class ZoneCounter(Base):
    __tablename__ = "zone_counters"

    zone_id: Mapped[str] = mapped_column(String, primary_key=True)
    entry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
