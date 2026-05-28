from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("vehicles.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    battery_pct: Mapped[float] = mapped_column(Float, nullable=False)
    speed_mps: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    error_codes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    zone_entered: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        # Primary query pattern: "anomalies for vehicle X between T1 and T2"
        # and "latest event per vehicle". Both want this composite index.
        Index(
            "ix_telemetry_vehicle_timestamp",
            "vehicle_id",
            text("timestamp DESC"),
        ),
        # For zone-entry queries (per-zone entry counts in your dashboard)
        # Partial index — only the rows where zone_entered is set, which is rare.
        Index(
            "ix_telemetry_zone_entered",
            "zone_entered",
            "timestamp",
            postgresql_where=text("zone_entered IS NOT NULL"),
        ),
        CheckConstraint(
            "battery_pct >= 0 AND battery_pct <= 100", name="ck_battery_range"
        ),
        CheckConstraint("speed_mps >= 0", name="ck_speed_nonneg"),
        CheckConstraint(
            "status IN ('idle', 'moving', 'charging', 'fault')",
            name="ck_status_valid",
        ),
    )
