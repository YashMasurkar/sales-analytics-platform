"""Conservative Schema Mapping Engine with Ambiguity Detection and Required Schema Validation."""

import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from app.core.exceptions import (
    MissingRequiredSchemaError,
    SchemaAmbiguityError,
)

# Canonical field definitions
CANONICAL_REQUIRED_DATE = "order_date"
CANONICAL_REQUIRED_REVENUE = "total_revenue"
CANONICAL_QUANTITY = "quantity"
CANONICAL_UNIT_PRICE = "unit_price"

# Conservative Synonym Dictionary (case-insensitive, normalized)
SYNONYM_MAP: Dict[str, List[str]] = {
    "order_date": [
        "date", "order_date", "orderdate", "transaction_date", "trans_date",
        "sale_date", "sales_date", "invoice_date", "timestamp", "order_dt"
    ],
    "total_revenue": [
        "revenue", "sales", "total_sales", "sales_amount", "total_amount",
        "order_amount", "amount", "item_total", "line_total", "total_revenue", "turnover"
    ],
    "quantity": [
        "quantity", "qty", "units", "units_sold", "count", "item_count", "order_qty"
    ],
    "unit_price": [
        "unit_price", "unitprice", "price", "selling_price", "item_price",
        "price_per_unit", "sales_price"
    ],
    "discount": [
        "discount", "discount_rate", "discount_amount", "disc", "discount_pct",
        "discount_percent", "discount_val"
    ],
    "total_cost": [
        "cost", "total_cost", "cogs", "unit_cost", "product_cost", "cost_price"
    ],
    "profit": [
        "profit", "net_profit", "earnings", "margin_amount", "operating_profit"
    ],
    "order_id": [
        "order_id", "orderid", "invoice_id", "invoiceno", "invoice_no",
        "transaction_id", "order_number", "order_no"
    ],
    "customer_id": [
        "customer_id", "customerid", "client_id", "cust_id", "account_id"
    ],
    "customer_name": [
        "customer_name", "customername", "client_name", "cust_name",
        "buyer_name", "customer"
    ],
    "product_id": [
        "product_id", "productid", "item_id", "sku", "item_code", "product_code"
    ],
    "product_name": [
        "product_name", "productname", "item_name", "item_description",
        "title", "product_title", "description"
    ],
    "category": [
        "category", "product_category", "department", "segment", "product_line"
    ],
    "sub_category": [
        "sub_category", "subcategory", "sub_dept", "sub_segment", "product_sub_category"
    ],
    "region": [
        "region", "territory", "location", "zone", "state", "country", "market", "area"
    ],
}


def normalize_header(header: str) -> str:
    """Normalize column header: lowercase, strip whitespace, replace non-alphanumeric with underscore."""
    if not isinstance(header, str):
        header = str(header)
    cleaned = header.strip().lower()
    cleaned = re.sub(r"[\s\-\./\\]+", "_", cleaned)
    cleaned = re.sub(r"[^\w]", "", cleaned)
    return cleaned.strip("_")


@dataclass
class SchemaMappingResult:
    """Result of conservative schema resolution."""
    column_mapping: Dict[str, str]  # raw_column_name -> canonical_field_name
    canonical_to_raw: Dict[str, str]  # canonical_field_name -> raw_column_name
    detected_canonical_fields: List[str]
    available_dimensions: Dict[str, bool]
    unmapped_columns: List[str] = field(default_factory=list)
    revenue_derived_needed: bool = False


class SchemaMapper:
    """Deterministic schema mapper with ambiguity detection and minimum schema validation."""

    def __init__(self, synonym_map: Optional[Dict[str, List[str]]] = None):
        self.synonym_map = synonym_map or SYNONYM_MAP

    def map_columns(self, raw_columns: List[str]) -> SchemaMappingResult:
        """
        Map raw DataFrame columns to canonical schema fields conservatively.
        Raises SchemaAmbiguityError if multiple raw columns match the same canonical field.
        Raises MissingRequiredSchemaError if minimum required schema is missing.
        """
        # Step 1: Detect matches for each raw column
        canonical_candidates: Dict[str, List[str]] = {canonical: [] for canonical in self.synonym_map}
        unmapped_columns: List[str] = []

        for raw_col in raw_columns:
            normalized = normalize_header(raw_col)
            matched_canonical = None

            for canonical_field, synonyms in self.synonym_map.items():
                if normalized == canonical_field or normalized in synonyms:
                    matched_canonical = canonical_field
                    break

            if matched_canonical:
                canonical_candidates[matched_canonical].append(raw_col)
            else:
                unmapped_columns.append(raw_col)

        # Step 2: Ambiguity check — ensure at most one column mapped per canonical field
        for canonical_field, matching_cols in canonical_candidates.items():
            if len(matching_cols) > 1:
                raise SchemaAmbiguityError(canonical_field, matching_cols)

        # Step 3: Construct confirmed mappings
        raw_to_canonical: Dict[str, str] = {}
        canonical_to_raw: Dict[str, str] = {}

        for canonical_field, matching_cols in canonical_candidates.items():
            if len(matching_cols) == 1:
                raw_col = matching_cols[0]
                raw_to_canonical[raw_col] = canonical_field
                canonical_to_raw[canonical_field] = raw_col

        detected_canonical = list(canonical_to_raw.keys())

        # Step 4: Validate minimum required schema
        missing_required: List[str] = []

        # Check Date
        if CANONICAL_REQUIRED_DATE not in canonical_to_raw:
            missing_required.append("Date (e.g. 'date', 'order_date')")

        # Check Revenue OR (Quantity + Unit Price)
        has_revenue = CANONICAL_REQUIRED_REVENUE in canonical_to_raw
        has_qty_and_price = (CANONICAL_QUANTITY in canonical_to_raw) and (CANONICAL_UNIT_PRICE in canonical_to_raw)
        revenue_derived_needed = False

        if not has_revenue:
            if has_qty_and_price:
                revenue_derived_needed = True
            else:
                missing_required.append("Revenue (or both Quantity and Unit Price)")

        if missing_required:
            raise MissingRequiredSchemaError(missing_required, raw_columns)

        # Step 5: Construct available dimensions dictionary
        available_dims = {
            "has_cost": "total_cost" in canonical_to_raw,
            "has_profit": "profit" in canonical_to_raw or ("total_cost" in canonical_to_raw and (has_revenue or has_qty_and_price)),
            "has_customer": "customer_id" in canonical_to_raw,
            "has_customer_name": "customer_name" in canonical_to_raw,
            "has_category": "category" in canonical_to_raw,
            "has_sub_category": "sub_category" in canonical_to_raw,
            "has_region": "region" in canonical_to_raw,
            "has_product": "product_name" in canonical_to_raw or "product_id" in canonical_to_raw,
            "has_order_id": "order_id" in canonical_to_raw,
            "has_quantity": CANONICAL_QUANTITY in canonical_to_raw,
            "has_unit_price": CANONICAL_UNIT_PRICE in canonical_to_raw,
            "has_discount": "discount" in canonical_to_raw,
            "has_revenue": has_revenue or has_qty_and_price,
            "revenue_derived": revenue_derived_needed,
        }

        return SchemaMappingResult(
            column_mapping=raw_to_canonical,
            canonical_to_raw=canonical_to_raw,
            detected_canonical_fields=detected_canonical,
            available_dimensions=available_dims,
            unmapped_columns=unmapped_columns,
            revenue_derived_needed=revenue_derived_needed,
        )
