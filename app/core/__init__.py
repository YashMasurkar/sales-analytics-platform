"""Core data processing, ingestion, schema mapping, cleaning, and analytics modules."""

from app.core.exceptions import (
    DataPlatformError,
    DataIngestionError,
    UnsupportedFileFormatError,
    FileSizeExceededError,
    FileCorruptedError,
    SchemaError,
    MissingRequiredSchemaError,
    SchemaAmbiguityError,
)
from app.core.ingestion import (
    SUPPORTED_FORMATS,
    extract_and_validate_format,
    validate_file_size,
    generate_safe_storage_path,
    save_uploaded_bytes,
    read_file_to_dataframe,
)
from app.core.schema_mapper import (
    SchemaMapper,
    SchemaMappingResult,
    SYNONYM_MAP,
    normalize_header,
)
from app.core.cleaner import (
    DataCleaner,
    DataQualityAuditResult,
    CleanedDatasetResult,
)
from app.core.kpi_engine import (
    KPIEngine,
    KPISummary,
    MonthlyTrendItem,
    CategoryPerformanceItem,
    RegionalPerformanceItem,
    ProductRankingItem,
)

__all__ = [
    "DataPlatformError",
    "DataIngestionError",
    "UnsupportedFileFormatError",
    "FileSizeExceededError",
    "FileCorruptedError",
    "SchemaError",
    "MissingRequiredSchemaError",
    "SchemaAmbiguityError",
    "SUPPORTED_FORMATS",
    "extract_and_validate_format",
    "validate_file_size",
    "generate_safe_storage_path",
    "save_uploaded_bytes",
    "read_file_to_dataframe",
    "SchemaMapper",
    "SchemaMappingResult",
    "SYNONYM_MAP",
    "normalize_header",
    "DataCleaner",
    "DataQualityAuditResult",
    "CleanedDatasetResult",
    "KPIEngine",
    "KPISummary",
    "MonthlyTrendItem",
    "CategoryPerformanceItem",
    "RegionalPerformanceItem",
    "ProductRankingItem",
]
