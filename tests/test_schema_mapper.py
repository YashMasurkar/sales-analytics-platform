"""Tests for Schema Mapping, Ambiguity Detection, and Required vs. Optional Fields."""

import pytest
from app.core.exceptions import (
    MissingRequiredSchemaError,
    SchemaAmbiguityError,
)
from app.core.schema_mapper import SchemaMapper


def test_schema_mapper_standard_canonical_columns():
    """Verify mapping with canonical standard column headers."""
    mapper = SchemaMapper()
    raw_cols = ["order_date", "total_revenue", "quantity", "unit_price", "category", "region"]
    result = mapper.map_columns(raw_cols)

    assert result.column_mapping["order_date"] == "order_date"
    assert result.column_mapping["total_revenue"] == "total_revenue"
    assert result.column_mapping["quantity"] == "quantity"
    assert result.available_dimensions["has_category"] is True
    assert result.available_dimensions["has_region"] is True
    assert result.available_dimensions["has_cost"] is False
    assert result.revenue_derived_needed is False


def test_schema_mapper_synonyms():
    """Verify conservative synonym matching (e.g. 'Date', 'Sales', 'Units', 'Department')."""
    mapper = SchemaMapper()
    raw_cols = ["Date", "Sales", "Units", "Selling Price", "Department", "Territory", "Client ID"]
    result = mapper.map_columns(raw_cols)

    assert result.column_mapping["Date"] == "order_date"
    assert result.column_mapping["Sales"] == "total_revenue"
    assert result.column_mapping["Units"] == "quantity"
    assert result.column_mapping["Selling Price"] == "unit_price"
    assert result.column_mapping["Department"] == "category"
    assert result.column_mapping["Territory"] == "region"
    assert result.column_mapping["Client ID"] == "customer_id"


def test_schema_mapper_alternative_required_schema_qty_and_price():
    """Verify that Quantity + Unit Price satisfies minimum required schema when direct Revenue is missing."""
    mapper = SchemaMapper()
    raw_cols = ["transaction_date", "qty", "price", "product_name"]
    result = mapper.map_columns(raw_cols)

    assert result.revenue_derived_needed is True
    assert result.available_dimensions["has_revenue"] is True
    assert result.available_dimensions["has_quantity"] is True
    assert result.available_dimensions["has_unit_price"] is True


def test_schema_mapper_ambiguity_detection_multiple_dates():
    """Verify that multiple conflicting date columns raise SchemaAmbiguityError."""
    mapper = SchemaMapper()
    # Dataset contains both 'order_date' and 'invoice_date' matching 'order_date'
    raw_cols = ["order_date", "invoice_date", "revenue"]

    with pytest.raises(SchemaAmbiguityError) as exc_info:
        mapper.map_columns(raw_cols)

    err = exc_info.value
    assert err.details["canonical_field"] == "order_date"
    assert "order_date" in err.details["candidate_columns"]
    assert "invoice_date" in err.details["candidate_columns"]


def test_schema_mapper_ambiguity_detection_multiple_revenues():
    """Verify that multiple revenue columns raise SchemaAmbiguityError."""
    mapper = SchemaMapper()
    raw_cols = ["date", "sales", "revenue", "category"]

    with pytest.raises(SchemaAmbiguityError) as exc_info:
        mapper.map_columns(raw_cols)

    assert exc_info.value.details["canonical_field"] == "total_revenue"


def test_schema_mapper_missing_date_column():
    """Verify that missing date column raises MissingRequiredSchemaError."""
    mapper = SchemaMapper()
    raw_cols = ["revenue", "quantity", "customer_name"]

    with pytest.raises(MissingRequiredSchemaError) as exc_info:
        mapper.map_columns(raw_cols)

    assert any("Date" in s for s in exc_info.value.details["missing_fields"])


def test_schema_mapper_missing_revenue_and_unit_price():
    """Verify that missing revenue AND missing unit price raises MissingRequiredSchemaError."""
    mapper = SchemaMapper()
    raw_cols = ["order_date", "quantity", "product_name"]  # Missing revenue and price

    with pytest.raises(MissingRequiredSchemaError) as exc_info:
        mapper.map_columns(raw_cols)

    assert any("Revenue" in s for s in exc_info.value.details["missing_fields"])
