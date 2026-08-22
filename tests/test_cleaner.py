"""Tests for Data Quality, Cleansing Engine, Deduplication, and Health Score Calculation."""

import pandas as pd
import numpy as np
import pytest

from app.core.schema_mapper import SchemaMapper
from app.core.cleaner import DataCleaner, clean_numeric_string


def test_clean_numeric_string_formats():
    """Verify numeric parser correctly strips currency, commas, percentages, and accounting brackets."""
    # Standard numbers
    assert clean_numeric_string(100.5) == (100.5, False)
    assert clean_numeric_string("100.5") == (100.5, False)

    # Coerced strings
    assert clean_numeric_string("$1,250.50") == (1250.5, True)
    assert clean_numeric_string("\u20ac45.00") == (45.0, True)
    assert clean_numeric_string("15%") == (0.15, True)
    assert clean_numeric_string("(50.00)") == (-50.0, True)

    # Invalid / Nulls
    assert clean_numeric_string(None) == (None, False)
    assert clean_numeric_string("N/A") == (None, False)
    assert clean_numeric_string("corrupted_text") == (None, False)


def test_cleaner_exact_duplicate_detection():
    """Verify that exact full-row duplicate records are identified, removed, and logged in the audit report."""
    raw_data = {
        "order_date": ["2024-01-01", "2024-01-01", "2024-01-02"],
        "total_revenue": [100.0, 100.0, 200.0],
        "quantity": [2, 2, 4],
    }
    df = pd.DataFrame(raw_data)
    mapper = SchemaMapper()
    mapping_res = mapper.map_columns(list(df.columns))

    cleaner = DataCleaner()
    res = cleaner.clean_dataset(df, mapping_res)

    assert res.audit_report.total_raw_rows == 3
    assert res.audit_report.valid_rows == 2
    assert res.audit_report.exact_duplicates_count == 1
    assert res.audit_report.excluded_rows == 0
    assert res.audit_report.exclusion_reasons == {}
    assert res.audit_report.valid_rows + res.audit_report.exact_duplicates_count + res.audit_report.excluded_rows == res.audit_report.total_raw_rows
    assert len(res.cleaned_df) == 2


def test_cleaner_row_accounting_consistency_11_rows():
    """Verify exact row accounting for 11 raw rows with 1 duplicate and 10 valid records."""
    raw_data = {
        "order_date": [f"2024-01-{i:02d}" for i in range(1, 11)] + ["2024-01-10"],
        "total_revenue": [100.0 * i for i in range(1, 11)] + [1000.0],
    }
    df = pd.DataFrame(raw_data)
    mapper = SchemaMapper()
    mapping_res = mapper.map_columns(list(df.columns))

    cleaner = DataCleaner()
    res = cleaner.clean_dataset(df, mapping_res)

    assert res.audit_report.total_raw_rows == 11
    assert res.audit_report.valid_rows == 10
    assert res.audit_report.exact_duplicates_count == 1
    assert res.audit_report.excluded_rows == 0
    assert res.audit_report.exclusion_reasons == {}
    assert res.audit_report.valid_rows + res.audit_report.exact_duplicates_count + res.audit_report.excluded_rows == 11


def test_cleaner_missing_and_invalid_dates_exclusion():
    """Verify that missing and corrupt unparseable dates cause records to be excluded with audit logging."""
    raw_data = {
        "order_date": ["2024-01-01", None, "invalid-date-string", "2024-01-04"],
        "total_revenue": [100.0, 200.0, 300.0, 400.0],
    }
    df = pd.DataFrame(raw_data)
    mapper = SchemaMapper()
    mapping_res = mapper.map_columns(list(df.columns))

    cleaner = DataCleaner()
    res = cleaner.clean_dataset(df, mapping_res)

    assert res.audit_report.total_raw_rows == 4
    assert res.audit_report.valid_rows == 2
    assert res.audit_report.excluded_rows == 2
    assert res.audit_report.invalid_dates_count == 1
    assert "Missing or unparseable order date" in res.audit_report.exclusion_reasons


def test_cleaner_valid_revenue_derivation_with_discount():
    """Verify revenue derivation from Quantity \u00d7 UnitPrice with discount."""
    raw_data = {
        "order_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "quantity": [2, 4, 10],
        "unit_price": [50.0, 25.0, 10.0],
        "discount": [0.0, 0.10, 20.0],  # 0%, 10% (0.10), 20% (20.0)
    }
    df = pd.DataFrame(raw_data)
    mapper = SchemaMapper()
    mapping_res = mapper.map_columns(list(df.columns))

    cleaner = DataCleaner()
    res = cleaner.clean_dataset(df, mapping_res)

    assert res.audit_report.valid_rows == 3
    assert res.audit_report.derived_value_count == 3

    # Row 1: 2 * 50 = 100.0
    assert res.cleaned_df.iloc[0]["total_revenue"] == 100.0
    # Row 2: 4 * 25 * (1 - 0.10) = 90.0
    assert res.cleaned_df.iloc[1]["total_revenue"] == 90.0
    # Row 3: 10 * 10 * (1 - 20/100) = 80.0
    assert res.cleaned_df.iloc[2]["total_revenue"] == 80.0


def test_cleaner_zero_unit_price_transaction():
    """Verify that zero-price transactions (e.g. promotional items) are valid and not discarded."""
    raw_data = {
        "order_date": ["2024-01-01", "2024-01-02"],
        "quantity": [1, 2],
        "unit_price": [0.0, 50.0],  # Row 1 is a free item ($0.0)
    }
    df = pd.DataFrame(raw_data)
    mapper = SchemaMapper()
    mapping_res = mapper.map_columns(list(df.columns))

    cleaner = DataCleaner()
    res = cleaner.clean_dataset(df, mapping_res)

    assert res.audit_report.valid_rows == 2
    assert res.audit_report.excluded_rows == 0
    assert res.cleaned_df.iloc[0]["total_revenue"] == 0.0
    assert res.cleaned_df.iloc[1]["total_revenue"] == 100.0


def test_cleaner_returns_and_negative_values_preserved_as_anomalies():
    """Verify that negative quantities (returns) are preserved in the dataset and flagged as anomalies for review."""
    raw_data = {
        "order_date": ["2024-01-01", "2024-01-02"],
        "quantity": [-2, 5],        # Row 1 is a return (-2 units)
        "unit_price": [50.0, 20.0],
    }
    df = pd.DataFrame(raw_data)
    mapper = SchemaMapper()
    mapping_res = mapper.map_columns(list(df.columns))

    cleaner = DataCleaner()
    res = cleaner.clean_dataset(df, mapping_res)

    # Returns are not deleted
    assert res.audit_report.valid_rows == 2
    assert res.audit_report.excluded_rows == 0
    # Row 1 revenue is derived as -100.0
    assert res.cleaned_df.iloc[0]["total_revenue"] == -100.0
    # Anomaly report records the negative quantity and negative revenue
    assert res.audit_report.anomalies_detected["negative_quantity"] == 1
    assert res.audit_report.anomalies_detected["negative_revenue"] == 1


def test_cleaner_invalid_revenue_derivation_excluded():
    """Verify that rows with missing revenue AND missing/corrupted unit price are excluded rather than imputed with 0."""
    raw_data = {
        "order_date": ["2024-01-01", "2024-01-02"],
        "quantity": [2, 5],
        "unit_price": [50.0, None],  # Row 2 has null price, cannot derive revenue
    }
    df = pd.DataFrame(raw_data)
    mapper = SchemaMapper()
    mapping_res = mapper.map_columns(list(df.columns))

    cleaner = DataCleaner()
    res = cleaner.clean_dataset(df, mapping_res)

    assert res.audit_report.total_raw_rows == 2
    assert res.audit_report.valid_rows == 1
    assert res.audit_report.excluded_rows == 1
    assert "Missing or unresolvable revenue" in res.audit_report.exclusion_reasons


def test_cleaner_optional_category_filled_with_unspecified():
    """Verify that missing optional categorical fields are filled with 'Unspecified' without excluding rows."""
    raw_data = {
        "order_date": ["2024-01-01", "2024-01-02"],
        "total_revenue": [100.0, 200.0],
        "category": ["Electronics", None],
        "region": [None, "West"],
    }
    df = pd.DataFrame(raw_data)
    mapper = SchemaMapper()
    mapping_res = mapper.map_columns(list(df.columns))

    cleaner = DataCleaner()
    res = cleaner.clean_dataset(df, mapping_res)

    assert res.audit_report.valid_rows == 2
    assert res.cleaned_df.iloc[0]["region"] == "Unspecified"
    assert res.cleaned_df.iloc[1]["category"] == "Unspecified"


def test_cleaner_anomaly_detection():
    """Verify that business logic anomalies (negative qty, invalid discount) are counted and reported."""
    raw_data = {
        "order_date": ["2024-01-01", "2024-01-02"],
        "total_revenue": [100.0, -50.0],  # Negative revenue anomaly
        "quantity": [-2, 4],              # Negative quantity anomaly
        "discount": [150.0, 0.0],         # Discount > 100% anomaly
    }
    df = pd.DataFrame(raw_data)
    mapper = SchemaMapper()
    mapping_res = mapper.map_columns(list(df.columns))

    cleaner = DataCleaner()
    res = cleaner.clean_dataset(df, mapping_res)

    anomalies = res.audit_report.anomalies_detected
    assert anomalies["negative_quantity"] == 1
    assert anomalies["negative_revenue"] == 1
    assert anomalies["invalid_discount"] == 1


def test_cleaner_health_score_boundaries():
    """Verify that health score is always strictly bounded between 0.0 and 100.0."""
    # Perfect dataset -> 100.0
    perfect_df = pd.DataFrame({
        "order_date": ["2024-01-01", "2024-01-02"],
        "total_revenue": [100.0, 200.0],
    })
    mapper = SchemaMapper()
    cleaner = DataCleaner()
    res_perfect = cleaner.clean_dataset(perfect_df, mapper.map_columns(list(perfect_df.columns)))
    assert res_perfect.audit_report.health_score == 100.0

    # Highly corrupt dataset with many exclusions
    messy_df = pd.DataFrame({
        "order_date": [None, None, "2024-01-01"],
        "total_revenue": [None, None, 100.0],
    })
    res_messy = cleaner.clean_dataset(messy_df, mapper.map_columns(list(messy_df.columns)))
    assert 0.0 <= res_messy.audit_report.health_score <= 100.0
