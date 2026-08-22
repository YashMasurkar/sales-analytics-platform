from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional, Any
from sqlalchemy import String, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.dataset import Dataset


class DataQualityLog(Base):
    __tablename__ = "data_quality_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    total_raw_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    excluded_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_rows_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    exact_duplicates_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missing_values_by_field: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    missing_values_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invalid_dates_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invalid_numerics_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    type_coercions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    derived_value_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    anomalies_detected: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    exclusion_reasons: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    health_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    changelog_summary: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Relationship
    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="data_quality_log")

    def __repr__(self) -> str:
        return f"<DataQualityLog(id={self.id}, dataset_id={self.dataset_id}, score={self.health_score})>"
