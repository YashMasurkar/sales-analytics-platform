"""Endpoint for dataset ingestion, schema validation, cleaning, and persistence."""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session


from app.config import get_settings
from app.api.deps import get_db
from app.db.models import Dataset, SalesRecord, DataQualityLog
from app.schemas.dataset import DatasetUploadResponse
from app.core.exceptions import (
    UnsupportedFileFormatError,
    FileSizeExceededError,
    FileCorruptedError,
    MissingRequiredSchemaError,
    SchemaAmbiguityError,
)
from app.core.ingestion import (
    extract_and_validate_format,
    validate_file_size,
    generate_safe_storage_path,
    save_uploaded_bytes,
    read_file_to_dataframe,
)
from app.core.schema_mapper import SchemaMapper
from app.core.cleaner import DataCleaner

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload & Process Dataset",
    description="Upload a CSV or Excel dataset, validate format and size, perform conservative schema mapping, execute data quality auditing, and persist clean analytical records.",
)
async def upload_dataset(
    file: UploadFile = File(..., description="CSV, XLSX, or XLS file to upload (Max 50MB)"),
    db: Session = Depends(get_db),
) -> DatasetUploadResponse:
    """Handle dataset upload and pipeline execution."""
    raw_filename = file.filename or "unknown"

    # Step 1: Validate file extension
    try:
        file_format = extract_and_validate_format(raw_filename)
    except UnsupportedFileFormatError as err:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=err.message)

    # Step 2: Read content and validate file size
    content = await file.read()
    try:
        validate_file_size(len(content), max_mb=settings.MAX_UPLOAD_SIZE_MB)
    except FileSizeExceededError as err:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=err.message)

    # Step 3: Save file safely to disk
    safe_path, dataset_id = generate_safe_storage_path(settings.UPLOAD_DIR, file_format)
    save_uploaded_bytes(content, safe_path)

    # Step 4: Parse into DataFrame
    try:
        raw_df = read_file_to_dataframe(safe_path, file_format)
    except (UnsupportedFileFormatError, FileCorruptedError) as err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err.message)
    except Exception as exc:
        logger.error(f"Failed to read uploaded file into DataFrame: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while parsing uploaded file.",
        )

    # Step 5: Conservative Schema Mapping
    mapper = SchemaMapper()
    try:
        mapping_result = mapper.map_columns(list(raw_df.columns))
    except (MissingRequiredSchemaError, SchemaAmbiguityError) as err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err.message)

    # Step 6: Data Cleaning & Quality Audit
    cleaner = DataCleaner()
    try:
        clean_result = cleaner.clean_dataset(raw_df, mapping_result)
    except Exception as exc:
        logger.error(f"Data cleaning pipeline error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred during data cleansing.",
        )

    audit = clean_result.audit_report
    cleaned_df = clean_result.cleaned_df

    # Step 7: Persist Dataset, Sales Records, and Data Quality Log
    try:
        dataset_record = Dataset(
            id=dataset_id,
            filename=raw_filename,
            file_format=file_format,
            storage_path=safe_path,
            total_raw_rows=audit.total_raw_rows,
            total_cleaned_rows=audit.valid_rows,
            available_dimensions=clean_result.available_dimensions,
            status="ready",
        )
        db.add(dataset_record)
        db.flush()

        # Bulk insert cleaned sales records
        sales_records = []
        for _, row in cleaned_df.iterrows():
            rec = SalesRecord(
                dataset_id=dataset_id,
                order_id=str(row["order_id"]) if "order_id" in row and row["order_id"] is not None and str(row["order_id"]) != "Unspecified" else None,
                order_date=row["order_date"].date() if hasattr(row["order_date"], "date") else row["order_date"],
                customer_id=str(row["customer_id"]) if "customer_id" in row and row["customer_id"] is not None else None,
                customer_name=str(row["customer_name"]) if "customer_name" in row and row["customer_name"] is not None else None,
                product_id=str(row["product_id"]) if "product_id" in row and row["product_id"] is not None else None,
                product_name=str(row["product_name"]) if "product_name" in row and row["product_name"] is not None else None,
                category=str(row["category"]) if "category" in row and row["category"] is not None else None,
                sub_category=str(row["sub_category"]) if "sub_category" in row and row["sub_category"] is not None else None,
                region=str(row["region"]) if "region" in row and row["region"] is not None else None,
                quantity=int(row["quantity"]) if "quantity" in row and row["quantity"] is not None and not (isinstance(row["quantity"], float) and row["quantity"] != row["quantity"]) else None,
                unit_price=float(row["unit_price"]) if "unit_price" in row and row["unit_price"] is not None and not (isinstance(row["unit_price"], float) and row["unit_price"] != row["unit_price"]) else None,
                discount=float(row["discount"]) if "discount" in row and row["discount"] is not None and not (isinstance(row["discount"], float) and row["discount"] != row["discount"]) else 0.0,
                total_revenue=float(row["total_revenue"]),
                total_cost=float(row["total_cost"]) if "total_cost" in row and row["total_cost"] is not None and not (isinstance(row["total_cost"], float) and row["total_cost"] != row["total_cost"]) else None,
                profit=float(row["profit"]) if "profit" in row and row["profit"] is not None and not (isinstance(row["profit"], float) and row["profit"] != row["profit"]) else None,
            )
            sales_records.append(rec)

        if sales_records:
            db.bulk_save_objects(sales_records)

        # Persist Data Quality Log
        quality_log = DataQualityLog(
            dataset_id=dataset_id,
            total_raw_rows=audit.total_raw_rows,
            valid_rows=audit.valid_rows,
            excluded_rows=audit.excluded_rows,
            duplicate_rows_count=audit.exact_duplicates_count,
            exact_duplicates_count=audit.exact_duplicates_count,
            missing_values_by_field=audit.missing_values_by_field,
            missing_values_count=sum(audit.missing_values_by_field.values()),
            invalid_dates_count=audit.invalid_dates_count,
            invalid_numerics_count=audit.invalid_numerics_count,
            type_coercions_count=audit.type_coercions_count,
            derived_value_count=audit.derived_value_count,
            anomalies_detected=audit.anomalies_detected,
            exclusion_reasons=audit.exclusion_reasons,
            health_score=audit.health_score,
            changelog_summary=audit.changelog_summary,
        )
        db.add(quality_log)
        db.commit()

    except Exception as exc:
        db.rollback()
        if safe_path and os.path.exists(safe_path):
            try:
                os.remove(safe_path)
            except OSError as cleanup_err:
                logger.warning(f"Could not remove physical file '{safe_path}' on transaction rollback: {cleanup_err}")
        logger.error(f"Failed to persist dataset and sales records to database: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred while persisting data.",
        )

    return DatasetUploadResponse(
        dataset_id=dataset_id,
        filename=raw_filename,
        file_format=file_format,
        total_raw_rows=audit.total_raw_rows,
        valid_rows=audit.valid_rows,
        excluded_rows=audit.excluded_rows,
        health_score=round(audit.health_score, 1),
        available_dimensions=clean_result.available_dimensions,
        derived_value_count=audit.derived_value_count,
        anomalies_detected=audit.anomalies_detected,
        changelog_summary=audit.changelog_summary,
    )
