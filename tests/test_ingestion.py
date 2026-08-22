"""Tests for Data Ingestion, File Type & Size Validation, and DataFrame Reading."""

import os
import pytest
import pandas as pd
import xlwt

from app.core.exceptions import (
    UnsupportedFileFormatError,
    FileSizeExceededError,
    FileCorruptedError,
)
from app.core.ingestion import (
    extract_and_validate_format,
    validate_file_size,
    generate_safe_storage_path,
    save_uploaded_bytes,
    read_file_to_dataframe,
)


def test_validate_file_extension_valid():
    """Verify that supported extensions (.csv, .xlsx, .xls) are validated correctly."""
    assert extract_and_validate_format("sales_2024.csv") == "csv"
    assert extract_and_validate_format("Q3_REPORT.XLSX") == "xlsx"
    assert extract_and_validate_format("legacy_data.XLS") == "xls"


def test_validate_file_extension_unsupported():
    """Verify that unsupported extensions raise UnsupportedFileFormatError."""
    with pytest.raises(UnsupportedFileFormatError) as exc_info:
        extract_and_validate_format("malicious.exe")
    assert "exe" in str(exc_info.value)

    with pytest.raises(UnsupportedFileFormatError):
        extract_and_validate_format("sales.json")

    with pytest.raises(UnsupportedFileFormatError):
        extract_and_validate_format("no_extension")


def test_validate_file_size_within_limit():
    """Verify that files within 50MB limit pass validation."""
    validate_file_size(size_in_bytes=10 * 1024 * 1024, max_mb=50)  # 10MB passes


def test_validate_file_size_exceeded():
    """Verify that files exceeding the limit raise FileSizeExceededError."""
    with pytest.raises(FileSizeExceededError) as exc_info:
        validate_file_size(size_in_bytes=55 * 1024 * 1024, max_mb=50)  # 55MB fails
    assert "55.00 MB" in str(exc_info.value)


def test_generate_safe_storage_path(tmp_path):
    """Verify that safe storage path generates unique UUID filenames without trusting user input."""
    upload_dir = str(tmp_path / "uploads")
    path1, id1 = generate_safe_storage_path(upload_dir, "csv")
    path2, id2 = generate_safe_storage_path(upload_dir, "csv")

    assert id1 != id2
    assert path1.endswith(".csv")
    assert os.path.dirname(path1) == upload_dir
    assert os.path.exists(upload_dir)


def test_read_csv_to_dataframe(tmp_path):
    """Verify reading a clean CSV file into a DataFrame."""
    csv_file = tmp_path / "test_sales.csv"
    csv_file.write_text("order_date,revenue,quantity\n2024-01-01,100.50,2\n2024-01-02,200.00,4\n")

    df = read_file_to_dataframe(str(csv_file), "csv")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ["order_date", "revenue", "quantity"]


def test_read_xlsx_to_dataframe(tmp_path):
    """Verify reading modern Excel (.xlsx) files using openpyxl engine."""
    xlsx_file = str(tmp_path / "test_sales.xlsx")
    sample_df = pd.DataFrame({
        "order_date": ["2024-01-01", "2024-01-02"],
        "revenue": [150.0, 300.0],
        "category": ["Electronics", "Furniture"],
    })
    sample_df.to_excel(xlsx_file, index=False, engine="openpyxl")

    df = read_file_to_dataframe(xlsx_file, "xlsx")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ["order_date", "revenue", "category"]
    assert df.iloc[0]["revenue"] == 150.0


def test_read_legacy_xls_to_dataframe(tmp_path):
    """Verify reading legacy Excel (.xls) files using xlrd engine."""
    xls_file = str(tmp_path / "legacy_sales.xls")

    # Generate a real binary BIFF8 .xls file using xlwt
    wb = xlwt.Workbook()
    ws = wb.add_sheet("Sales")
    ws.write(0, 0, "order_date")
    ws.write(0, 1, "revenue")
    ws.write(0, 2, "quantity")

    ws.write(1, 0, "2024-01-01")
    ws.write(1, 1, 250.0)
    ws.write(1, 2, 5)

    wb.save(xls_file)

    df = read_file_to_dataframe(xls_file, "xls")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == ["order_date", "revenue", "quantity"]
    assert df.iloc[0]["revenue"] == 250.0
    assert df.iloc[0]["quantity"] == 5


def test_read_corrupted_empty_file(tmp_path):
    """Verify that empty files raise FileCorruptedError."""
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("")

    with pytest.raises(FileCorruptedError):
        read_file_to_dataframe(str(empty_file), "csv")
