from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional, Any
from sqlalchemy import String, Integer, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.sales_record import SalesRecord
    from app.db.models.data_quality import DataQualityLog
    from app.db.models.kpi_cache import KPICache


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[str] = mapped_column(String(10), nullable=False)
    storage_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    total_raw_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cleaned_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_dimensions: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    upload_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="processing",
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships with cascade delete
    sales_records: Mapped[List[SalesRecord]] = relationship(
        "SalesRecord",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )
    data_quality_log: Mapped[Optional[DataQualityLog]] = relationship(
        "DataQualityLog",
        back_populates="dataset",
        uselist=False,
        cascade="all, delete-orphan",
    )
    kpi_caches: Mapped[List[KPICache]] = relationship(
        "KPICache",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, filename='{self.filename}', status='{self.status}')>"
