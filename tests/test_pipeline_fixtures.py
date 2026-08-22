"""End-to-end fixture tests covering all 17 required data ingestion, quality audit, and KPI scenarios."""

import pandas as pd
import pytest

from app.core.exceptions import (
    MissingRequiredSchemaError,
    SchemaAmbiguityError,
)
from app.core.schema_mapper import SchemaMapper
from app.core.cleaner import DataCleaner
from app.core.kpi_engine import KPIEngine


@pytest.fixture
def pipeline():
    """Helper fixture providing schema mapper, cleaner, and KPI engine."""
    return {
        "mapper": SchemaMapper(),
        "cleaner": DataCleaner(),
        "kpi_engine": KPIEngine(),
    }


def test_scenario_1_clean_valid_dataset(pipeline):
    """Scenario 1: Clean, complete valid dataset."""
    df = pd.DataFrame({
        "order_id": ["ORD-1", "ORD-2"],
        "order_date": ["2024-01-10", "2024-01-11"],
        "customer_id": ["C1", "C2"],
        "product_name": ["Widget A", "Widget B"],
        "category": ["Tools", "Tools"],
        "region": ["East", "West"],
        "quantity": [2, 3],
        "unit_price": [10.0, 20.0],
        "total_revenue": [20.0, 60.0],
        "total_cost": [10.0, 30.0],
        "profit": [10.0, 30.0],
    })

    mapping = pipeline["mapper"].map_columns(list(df.columns))
    cleaned = pipeline["cleaner"].clean_dataset(df, mapping)
    kpi = pipeline["kpi_engine"].calculate(cleaned.cleaned_df, cleaned.available_dimensions)

    assert cleaned.audit_report.total_raw_rows == 2
    assert cleaned.audit_report.valid_rows == 2
    assert cleaned.audit_report.excluded_rows == 0
    assert cleaned.audit_report.health_score == 100.0
    assert kpi.total_revenue == 80.0
    assert kpi.total_profit == 40.0
    assert kpi.profit_margin_pct == 50.0
    assert kpi.total_orders == 2


def test_scenario_2_missing_required_date(pipeline):
    """Scenario 2: Rows with missing required date must be excluded and tracked."""
    df = pd.DataFrame({
        "order_date": ["2024-01-10", None, "2024-01-12"],
        "total_revenue": [100.0, 200.0, 300.0],
    })

    mapping = pipeline["mapper"].map_columns(list(df.columns))
    cleaned = pipeline["cleaner"].clean_dataset(df, mapping)

    assert cleaned.audit_report.total_raw_rows == 3
    assert cleaned.audit_report.valid_rows == 2
    assert cleaned.audit_report.excluded_rows == 1
    assert "Missing or unparseable order date" in cleaned.audit_report.exclusion_reasons


def test_scenario_3_missing_revenue_without_derivation(pipeline):
    """Scenario 3: Missing revenue where derivation is impossible -> row excluded."""
    df = pd.DataFrame({
        "order_date": ["2024-01-10", "2024-01-11"],
        "total_revenue": [100.0, None],  # Row 2 has null revenue and no qty/price
    })

    mapping = pipeline["mapper"].map_columns(list(df.columns))
    cleaned = pipeline["cleaner"].clean_dataset(df, mapping)

    assert cleaned.audit_report.valid_rows == 1
    assert cleaned.audit_report.excluded_rows == 1


def test_scenario_4_valid_revenue_derivation(pipeline):
    """Scenario 4: Missing revenue column with valid Quantity and UnitPrice -> derived cleanly."""
    df = pd.DataFrame({
        "order_date": ["2024-01-10", "2024-01-11"],
        "quantity": [3, 5],
        "unit_price": [10.0, 20.0],
    })

    mapping = pipeline["mapper"].map_columns(list(df.columns))
    cleaned = pipeline["cleaner"].clean_dataset(df, mapping)
    kpi = pipeline["kpi_engine"].calculate(cleaned.cleaned_df, cleaned.available_dimensions)

    assert cleaned.audit_report.derived_value_count == 2
    assert cleaned.cleaned_df.iloc[0]["total_revenue"] == 30.0
    assert cleaned.cleaned_df.iloc[1]["total_revenue"] == 100.0
    assert kpi.total_revenue == 130.0


def test_scenario_5_invalid_revenue_derivation_scenario(pipeline):
    """Scenario 5: Derivation attempted with missing/unparseable unit price -> excluded."""
    df = pd.DataFrame({
        "order_date": ["2024-01-10", "2024-01-11"],
        "quantity": [2, 5],
        "unit_price": [15.0, None],  # Row 2 missing unit price, cannot derive revenue
    })

    mapping = pipeline["mapper"].map_columns(list(df.columns))
    cleaned = pipeline["cleaner"].clean_dataset(df, mapping)

    assert cleaned.audit_report.valid_rows == 1
    assert cleaned.audit_report.excluded_rows == 1


def test_scenario_6_missing_optional_fields(pipeline):
    """Scenario 6: Missing optional dimensions (category, region) filled with 'Unspecified'."""
    df = pd.DataFrame({
        "order_date": ["2024-01-10", "2024-01-11"],
        "total_revenue": [50.0, 75.0],
        "category": [None, "Electronics"],
        "region": ["North", None],
    })

    mapping = pipeline["mapper"].map_columns(list(df.columns))
    cleaned = pipeline["cleaner"].clean_dataset(df, mapping)

    assert cleaned.cleaned_df.iloc[0]["category"] == "Unspecified"
    assert cleaned.cleaned_df.iloc[1]["region"] == "Unspecified"
    assert cleaned.audit_report.valid_rows == 2


def test_scenario_7_exact_duplicate_rows(pipeline):
    """Scenario 7: Full duplicate records are removed and counted."""
    df = pd.DataFrame({
        "order_date": ["2024-01-10", "2024-01-10", "2024-01-11"],
        "total_revenue": [50.0, 50.0, 75.0],
        "category": ["Food", "Food", "Beverage"],
    })

    mapping = pipeline["mapper"].map_columns(list(df.columns))
    cleaned = pipeline["cleaner"].clean_dataset(df, mapping)

    assert cleaned.audit_report.exact_duplicates_count == 1
    assert cleaned.audit_report.valid_rows == 2


def test_scenario_8_ambiguous_schema(pipeline):
    """Scenario 8: Multiple conflicting columns for canonical field raise SchemaAmbiguityError."""
    df = pd.DataFrame({
        "order_date": ["2024-01-10"],
        "sales": [100.0],
        "revenue": [100.0],  # Both 'sales' and 'revenue' candidate for total_revenue
    })

    with pytest.raises(SchemaAmbiguityError) as exc_info:
        pipeline["mapper"].map_columns(list(df.columns))
    assert exc_info.value.details["canonical_field"] == "total_revenue"


def test_scenario_9_missing_required_columns(pipeline):
    """Scenario 9: Entirely missing required date or revenue column raises MissingRequiredSchemaError."""
    df = pd.DataFrame({
        "customer_name": ["Alice"],
        "product_name": ["Widget"],
    })

    with pytest.raises(MissingRequiredSchemaError):
        pipeline["mapper"].map_columns(list(df.columns))


def test_scenario_10_invalid_dates(pipeline):
    """Scenario 10: Invalid date strings like '31/02/2024' or 'corrupt' are excluded."""
    df = pd.DataFrame({
        "order_date": ["2024-01-10", "corrupt_date_val", "2024-02-31"],
        "total_revenue": [100.0, 200.0, 300.0],
    })

    mapping = pipeline["mapper"].map_columns(list(df.columns))
    cleaned = pipeline["cleaner"].clean_dataset(df, mapping)

    assert cleaned.audit_report.invalid_dates_count == 2
    assert cleaned.audit_report.valid_rows == 1


def test_scenario_11_invalid_numeric_values(pipeline):
    """Scenario 11: Currency symbols and percentage characters are cleaned with coercions tracked."""
    df = pd.DataFrame({
        "order_date": ["2024-01-10", "2024-01-11"],
        "total_revenue": ["$1,000.50", "\u20ac500.00"],
    })

    mapping = pipeline["mapper"].map_columns(list(df.columns))
    cleaned = pipeline["cleaner"].clean_dataset(df, mapping)

    assert cleaned.audit_report.valid_rows == 2
    assert cleaned.cleaned_df.iloc[0]["total_revenue"] == 1000.50
    assert cleaned.cleaned_df.iloc[1]["total_revenue"] == 500.00
    assert cleaned.audit_report.type_coercions_count == 2


def test_scenario_12_discounts_calculation(pipeline):
    """Scenario 12: Discounts correctly reduce derived revenue."""
    df = pd.DataFrame({
        "order_date": ["2024-01-10"],
        "quantity": [10],
        "unit_price": [20.0],
        "discount": ["15%"],  # 15% discount
    })

    mapping = pipeline["mapper"].map_columns(list(df.columns))
    cleaned = pipeline["cleaner"].clean_dataset(df, mapping)

    # 10 * 20 * (1 - 0.15) = 170.0
    assert cleaned.cleaned_df.iloc[0]["total_revenue"] == 170.0


def test_scenario_13_negative_and_suspicious_values(pipeline):
    """Scenario 13: Negative quantities and revenues are flagged as anomalies in audit report."""
    df = pd.DataFrame({
        "order_date": ["2024-01-10", "2024-01-11"],
        "total_revenue": [-100.0, 200.0],
        "quantity": [-5, 10],
    })

    mapping = pipeline["mapper"].map_columns(list(df.columns))
    cleaned = pipeline["cleaner"].clean_dataset(df, mapping)

    assert cleaned.audit_report.anomalies_detected["negative_revenue"] == 1
    assert cleaned.audit_report.anomalies_detected["negative_quantity"] == 1


def test_scenario_14_dataset_without_cost(pipeline):
    """Scenario 14: Dataset without cost -> Profit and Margin are None (Never fabricated)."""
    df = pd.DataFrame({
        "order_date": ["2024-01-10", "2024-01-11"],
        "total_revenue": [100.0, 200.0],
    })

    mapping = pipeline["mapper"].map_columns(list(df.columns))
    cleaned = pipeline["cleaner"].clean_dataset(df, mapping)
    kpi = pipeline["kpi_engine"].calculate(cleaned.cleaned_df, cleaned.available_dimensions)

    assert kpi.total_cost is None
    assert kpi.total_profit is None
    assert kpi.profit_margin_pct is None
    assert kpi.available_metrics["profit"] is False


def test_scenario_15_dataset_without_customer_id(pipeline):
    """Scenario 15: Dataset without customer ID -> Unique Customers is None."""
    df = pd.DataFrame({
        "order_date": ["2024-01-10", "2024-01-11"],
        "total_revenue": [100.0, 200.0],
    })

    mapping = pipeline["mapper"].map_columns(list(df.columns))
    cleaned = pipeline["cleaner"].clean_dataset(df, mapping)
    kpi = pipeline["kpi_engine"].calculate(cleaned.cleaned_df, cleaned.available_dimensions)

    assert kpi.total_unique_customers is None
    assert kpi.available_metrics["unique_customers"] is False


def test_scenario_16_dataset_without_category(pipeline):
    """Scenario 16: Dataset without category -> category_performance is None."""
    df = pd.DataFrame({
        "order_date": ["2024-01-10", "2024-01-11"],
        "total_revenue": [100.0, 200.0],
    })

    mapping = pipeline["mapper"].map_columns(list(df.columns))
    cleaned = pipeline["cleaner"].clean_dataset(df, mapping)
    kpi = pipeline["kpi_engine"].calculate(cleaned.cleaned_df, cleaned.available_dimensions)

    assert kpi.category_performance is None
    assert kpi.available_metrics["category_analysis"] is False


def test_scenario_17_dataset_without_product_info(pipeline):
    """Scenario 17: Dataset without product -> product rankings are None."""
    df = pd.DataFrame({
        "order_date": ["2024-01-10", "2024-01-11"],
        "total_revenue": [100.0, 200.0],
    })

    mapping = pipeline["mapper"].map_columns(list(df.columns))
    cleaned = pipeline["cleaner"].clean_dataset(df, mapping)
    kpi = pipeline["kpi_engine"].calculate(cleaned.cleaned_df, cleaned.available_dimensions)

    assert kpi.top_products is None
    assert kpi.bottom_products is None
    assert kpi.available_metrics["product_ranking"] is False
