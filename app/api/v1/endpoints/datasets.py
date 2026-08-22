"""Endpoints for dataset management, details, deletion, and quality audit retrieval."""

import os
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.db.models import Dataset, DataQualityLog
from app.schemas.dataset import (
    DatasetListItem,
    DatasetDetailResponse,
    DatasetDeleteResponse,
)
from app.schemas.data_quality import DataQualityReportResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/datasets",
    response_model=List[DatasetListItem],
    summary="List Uploaded Datasets",
    description="Retrieve a list of all uploaded datasets with metadata, row counts, and health scores.",
)
def list_datasets(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination limit"),
    db: Session = Depends(get_db),
) -> List[DatasetListItem]:
    """List datasets with metadata and quality scores."""
    datasets = (
        db.query(Dataset)
        .options(joinedload(Dataset.data_quality_log))
        .order_by(Dataset.upload_timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    results = []
    for d in datasets:
        health = d.data_quality_log.health_score if d.data_quality_log else None
        results.append(
            DatasetListItem(
                id=d.id,
                filename=d.filename,
                file_format=d.file_format,
                upload_timestamp=d.upload_timestamp,
                total_raw_rows=d.total_raw_rows,
                total_cleaned_rows=d.total_cleaned_rows,
                status=d.status,
                health_score=health,
            )
        )
    return results


@router.get(
    "/datasets/{id}",
    response_model=DatasetDetailResponse,
    summary="Get Dataset Details",
    description="Retrieve detailed metadata and dimensional availability for a specific dataset.",
)
def get_dataset(
    id: str,
    db: Session = Depends(get_db),
) -> DatasetDetailResponse:
    """Get single dataset details."""
    dataset = (
        db.query(Dataset)
        .options(joinedload(Dataset.data_quality_log))
        .filter(Dataset.id == id)
        .first()
    )

    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{id}' not found.")

    health = dataset.data_quality_log.health_score if dataset.data_quality_log else None
    return DatasetDetailResponse(
        id=dataset.id,
        filename=dataset.filename,
        file_format=dataset.file_format,
        total_raw_rows=dataset.total_raw_rows,
        total_cleaned_rows=dataset.total_cleaned_rows,
        upload_timestamp=dataset.upload_timestamp,
        status=dataset.status,
        error_message=dataset.error_message,
        available_dimensions=dataset.available_dimensions,
        health_score=health,
    )


@router.delete(
    "/datasets/{id}",
    response_model=DatasetDeleteResponse,
    summary="Delete Dataset",
    description="Permanently delete a dataset, all associated sales records, quality audit logs, and on-disk files.",
)
def delete_dataset(
    id: str,
    db: Session = Depends(get_db),
) -> DatasetDeleteResponse:
    """Delete a dataset and its associated resources."""
    dataset = db.query(Dataset).filter(Dataset.id == id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{id}' not found.")

    # Remove storage file if it exists
    if dataset.storage_path and os.path.exists(dataset.storage_path):
        try:
            os.remove(dataset.storage_path)
        except OSError as err:
            logger.warning(f"Could not delete storage file at {dataset.storage_path}: {err}")

    # SQLAlchemy cascade will delete associated sales_records, data_quality_log, and kpi_caches
    db.delete(dataset)
    db.commit()

    return DatasetDeleteResponse(
        message="Dataset deleted successfully.",
        dataset_id=id,
    )


@router.get(
    "/datasets/{id}/quality-audit",
    response_model=DataQualityReportResponse,
    summary="Get Data Quality Audit Report",
    description="Retrieve the complete, persisted Data Quality & Cleansing audit report for an uploaded dataset.",
)
def get_quality_audit(
    id: str,
    db: Session = Depends(get_db),
) -> DataQualityReportResponse:
    """Retrieve full persisted quality audit report."""
    dataset = db.query(Dataset).filter(Dataset.id == id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{id}' not found.")

    log = db.query(DataQualityLog).filter(DataQualityLog.dataset_id == id).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data Quality Audit for dataset '{id}' was not found.",
        )

    return DataQualityReportResponse(
        dataset_id=log.dataset_id,
        total_raw_rows=log.total_raw_rows,
        valid_rows=log.valid_rows,
        excluded_rows=log.excluded_rows,
        exact_duplicates_count=log.exact_duplicates_count,
        missing_values_by_field=log.missing_values_by_field or {},
        missing_values_count=log.missing_values_count,
        invalid_dates_count=log.invalid_dates_count,
        invalid_numerics_count=log.invalid_numerics_count,
        type_coercions_count=log.type_coercions_count,
        derived_value_count=log.derived_value_count,
        anomalies_detected=log.anomalies_detected or {},
        exclusion_reasons=log.exclusion_reasons or {},
        health_score=log.health_score,
        changelog_summary=log.changelog_summary or [],
    )
