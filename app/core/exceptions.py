"""Domain exceptions for Data Ingestion, Schema Mapping, and Data Processing."""

from typing import List, Optional


class DataPlatformError(Exception):
    """Base domain exception for the Sales Analytics Platform."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DataIngestionError(DataPlatformError):
    """Raised when file upload, format validation, or file parsing fails."""
    pass


class UnsupportedFileFormatError(DataIngestionError):
    """Raised when the uploaded file extension or MIME type is not supported."""
    def __init__(self, file_extension: str, supported_formats: List[str]):
        message = f"Unsupported file format '{file_extension}'. Supported formats: {', '.join(supported_formats)}"
        super().__init__(message, {"file_extension": file_extension, "supported_formats": supported_formats})


class FileSizeExceededError(DataIngestionError):
    """Raised when the uploaded file exceeds the configured maximum size limit."""
    def __init__(self, file_size_mb: float, max_size_mb: float):
        message = f"File size ({file_size_mb:.2f} MB) exceeds the maximum allowed limit of {max_size_mb:.2f} MB."
        super().__init__(message, {"file_size_mb": file_size_mb, "max_size_mb": max_size_mb})


class FileCorruptedError(DataIngestionError):
    """Raised when an uploaded file cannot be parsed or is corrupted."""
    def __init__(self, filename: str, reason: str):
        message = f"Failed to parse file '{filename}': {reason}"
        super().__init__(message, {"filename": filename, "reason": reason})


class SchemaError(DataPlatformError):
    """Base exception for schema validation and mapping failures."""
    pass


class MissingRequiredSchemaError(SchemaError):
    """Raised when the dataset is missing mandatory business fields (e.g. date, revenue/quantity+unit_price)."""
    def __init__(self, missing_fields: List[str], detected_columns: List[str]):
        message = f"Dataset is missing required dimensions: {', '.join(missing_fields)}. Detected columns: {', '.join(detected_columns)}"
        super().__init__(message, {"missing_fields": missing_fields, "detected_columns": detected_columns})


class SchemaAmbiguityError(SchemaError):
    """Raised when multiple columns match the same canonical field unambiguously."""
    def __init__(self, canonical_field: str, candidate_columns: List[str]):
        message = f"Ambiguous schema mapping for field '{canonical_field}': Multiple candidate columns detected: {', '.join(candidate_columns)}. Please resolve column naming."
        super().__init__(message, {"canonical_field": canonical_field, "candidate_columns": candidate_columns})
