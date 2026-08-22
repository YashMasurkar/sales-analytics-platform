"""Module for safe file ingestion, size validation, and DataFrame loading."""

import os
import uuid
from typing import Tuple, List
import pandas as pd

from app.core.exceptions import (
    UnsupportedFileFormatError,
    FileSizeExceededError,
    FileCorruptedError,
)

SUPPORTED_FORMATS: List[str] = ["csv", "xlsx", "xls"]


def extract_and_validate_format(filename: str) -> str:
    """Validate file extension and return normalized lowercase format."""
    if not filename or "." not in filename:
        raise UnsupportedFileFormatError("unknown", SUPPORTED_FORMATS)
    
    ext = filename.rsplit(".", 1)[1].lower().strip()
    if ext not in SUPPORTED_FORMATS:
        raise UnsupportedFileFormatError(ext, SUPPORTED_FORMATS)
    
    return ext


def validate_file_size(size_in_bytes: int, max_mb: int = 50) -> None:
    """Validate that file size does not exceed the allowed threshold."""
    size_mb = size_in_bytes / (1024 * 1024)
    if size_mb > max_mb:
        raise FileSizeExceededError(size_mb, float(max_mb))


def generate_safe_storage_path(upload_dir: str, file_format: str) -> Tuple[str, str]:
    """Generate a collision-free UUID filename and absolute path for safe storage."""
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}.{file_format}"
    os.makedirs(upload_dir, exist_ok=True)
    full_path = os.path.join(upload_dir, safe_filename)
    return full_path, file_id


def save_uploaded_bytes(content: bytes, destination_path: str) -> None:
    """Save raw file bytes to the local filesystem path."""
    with open(destination_path, "wb") as f:
        f.write(content)


def read_file_to_dataframe(file_path: str, file_format: str) -> pd.DataFrame:
    """
    Read CSV or Excel dataset into a Pandas DataFrame.
    Preserves raw rows without silent dropping.
    """
    if not os.path.exists(file_path):
        raise FileCorruptedError(file_path, "File does not exist on disk.")

    try:
        if file_format == "csv":
            # Attempt UTF-8 with latin1 fallback for legacy retail exports
            try:
                df = pd.read_csv(file_path, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding="latin1")
        elif file_format == "xlsx":
            df = pd.read_excel(file_path, engine="openpyxl")
        elif file_format == "xls":
            df = pd.read_excel(file_path, engine="xlrd")
        else:
            raise UnsupportedFileFormatError(file_format, SUPPORTED_FORMATS)

        if df.empty:
            raise FileCorruptedError(os.path.basename(file_path), "Uploaded file contains no data rows.")

        return df

    except UnsupportedFileFormatError:
        raise
    except FileCorruptedError:
        raise
    except Exception as exc:
        raise FileCorruptedError(os.path.basename(file_path), str(exc)) from exc
