"""Data Quality & Cleansing Engine: Type Validation, Missing Value Handling, Deduplication, Anomaly Detection, and Quality Auditing."""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date
import numpy as np
import pandas as pd

from app.core.schema_mapper import SchemaMappingResult


@dataclass
class DataQualityAuditResult:
    """Comprehensive, auditable Data Quality Report."""
    total_raw_rows: int
    valid_rows: int
    excluded_rows: int
    exact_duplicates_count: int
    missing_values_by_field: Dict[str, int]
    invalid_dates_count: int
    invalid_numerics_count: int
    type_coercions_count: int
    derived_value_count: int
    anomalies_detected: Dict[str, int]
    exclusion_reasons: Dict[str, int]
    health_score: float
    changelog_summary: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_raw_rows": self.total_raw_rows,
            "valid_rows": self.valid_rows,
            "excluded_rows": self.excluded_rows,
            "exact_duplicates_count": self.exact_duplicates_count,
            "missing_values_by_field": self.missing_values_by_field,
            "invalid_dates_count": self.invalid_dates_count,
            "invalid_numerics_count": self.invalid_numerics_count,
            "type_coercions_count": self.type_coercions_count,
            "derived_value_count": self.derived_value_count,
            "anomalies_detected": self.anomalies_detected,
            "exclusion_reasons": self.exclusion_reasons,
            "health_score": round(self.health_score, 1),
            "changelog_summary": self.changelog_summary,
        }


@dataclass
class CleanedDatasetResult:
    """Output bundle of the data cleansing pipeline."""
    cleaned_df: pd.DataFrame
    audit_report: DataQualityAuditResult
    available_dimensions: Dict[str, bool]


def clean_numeric_string(val: Any) -> Tuple[Optional[float], bool]:
    """
    Parse a numeric value from string/float/int, safely stripping currency symbols, commas, and percentage signs.
    Returns (parsed_float, was_coerced).
    """
    if pd.isna(val) or val is None or str(val).strip() == "":
        return None, False

    if isinstance(val, (int, float)):
        if np.isnan(val):
            return None, False
        return float(val), False

    val_str = str(val).strip()

    # Check for percentage
    is_percent = False
    if val_str.endswith("%"):
        is_percent = True
        val_str = val_str[:-1].strip()

    # Remove currency symbols and formatting commas
    cleaned = re.sub(r"[$\u20ac\u00a3\u00a5, ]", "", val_str)

    # Check for accounting parentheses for negative numbers e.g. (100.50)
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]

    try:
        num = float(cleaned)
        if is_percent:
            num = num / 100.0
        # If the string was modified to extract the number, count as coerced
        was_coerced = (val_str != cleaned) or is_percent
        return num, was_coerced
    except (ValueError, TypeError):
        return None, False


class DataCleaner:
    """Executes deterministic data validation, cleansing, and quality scoring."""

    def clean_dataset(
        self,
        raw_df: pd.DataFrame,
        mapping_result: SchemaMappingResult,
    ) -> CleanedDatasetResult:
        """
        Execute the full cleansing pipeline:
        1. Select and rename columns to canonical names.
        2. Detect & remove exact full-row duplicates.
        3. Parse and validate dates.
        4. Validate and coerce numerical fields.
        5. Handle missing values and derive revenue where appropriate.
        6. Detect anomalies.
        7. Calculate bounded health score and compile audit report.
        """
        total_raw_rows = len(raw_df)
        changelog: List[str] = []
        exclusion_reasons: Dict[str, int] = {}
        missing_by_field: Dict[str, int] = {}
        anomalies: Dict[str, int] = {
            "negative_quantity": 0,
            "negative_revenue": 0,
            "invalid_discount": 0,
            "suspicious_unit_price": 0,
            "out_of_range_dates": 0,
        }

        type_coercions_count = 0
        invalid_dates_count = 0
        invalid_numerics_count = 0
        derived_revenue_count = 0

        # Step 1: Map raw columns to canonical subset
        col_mapping = mapping_result.column_mapping
        df = raw_df[list(col_mapping.keys())].rename(columns=col_mapping).copy()

        # Step 2: Detect & remove exact duplicate rows
        exact_dupes_mask = df.duplicated(keep="first")
        exact_duplicates_count = int(exact_dupes_mask.sum())
        if exact_duplicates_count > 0:
            df = df[~exact_dupes_mask].copy()
            changelog.append(f"Removed {exact_duplicates_count} exact full-row duplicate records.")

        # Step 3: Parse and validate order_date
        raw_dates = df["order_date"].copy()
        missing_date_initial = int(raw_dates.isna().sum())
        if missing_date_initial > 0:
            missing_by_field["order_date"] = missing_date_initial

        # Coerce dates using mixed format parsing
        parsed_dates = pd.to_datetime(df["order_date"], format="mixed", errors="coerce")
        unparseable_dates_mask = raw_dates.notna() & parsed_dates.isna()
        invalid_dates_count = int(unparseable_dates_mask.sum())

        df["order_date"] = parsed_dates

        # Identify rows with valid dates
        valid_date_mask = df["order_date"].notna()
        excluded_for_date = len(df) - int(valid_date_mask.sum())
        if excluded_for_date > 0:
            exclusion_reasons["Missing or unparseable order date"] = excluded_for_date
            changelog.append(f"Excluded {excluded_for_date} records due to missing or invalid date.")

        # Step 4: Validate and coerce numerical fields
        numeric_fields = ["quantity", "unit_price", "discount", "total_revenue", "total_cost", "profit"]

        for col in numeric_fields:
            if col in df.columns:
                raw_col = df[col].copy()
                null_count = int(raw_col.isna().sum())
                if null_count > 0:
                    missing_by_field[col] = missing_by_field.get(col, 0) + null_count

                cleaned_vals = []
                coerced_in_col = 0
                invalid_in_col = 0

                for val in raw_col:
                    parsed_num, was_coerced = clean_numeric_string(val)
                    if was_coerced:
                        coerced_in_col += 1
                    if val is not None and not pd.isna(val) and parsed_num is None:
                        invalid_in_col += 1
                    cleaned_vals.append(parsed_num)

                df[col] = pd.Series(cleaned_vals, index=df.index, dtype="float64")
                type_coercions_count += coerced_in_col
                invalid_numerics_count += invalid_in_col

                if coerced_in_col > 0:
                    changelog.append(f"Standardized formatting for {coerced_in_col} values in '{col}'.")

        # Step 5: Revenue Validation & Derivation
        # Determine whether revenue needs to be derived
        has_direct_revenue = "total_revenue" in df.columns
        has_qty_and_price = ("quantity" in df.columns) and ("unit_price" in df.columns)
        has_discount = "discount" in df.columns

        if not has_direct_revenue:
            df["total_revenue"] = np.nan

        # Vectorized revenue check and derivation
        direct_rev_mask = df["total_revenue"].notna()
        revenue_valid_mask = direct_rev_mask.copy()

        if has_qty_and_price:
            derivable_mask = (~direct_rev_mask) & df["quantity"].notna() & df["unit_price"].notna()
            derived_revenue_count = int(derivable_mask.sum())

            if derived_revenue_count > 0:
                qty = df.loc[derivable_mask, "quantity"]
                price = df.loc[derivable_mask, "unit_price"]

                if has_discount:
                    disc = df.loc[derivable_mask, "discount"].fillna(0.0)
                else:
                    disc = pd.Series(0.0, index=qty.index)

                # Discount logic: 0 <= disc <= 1.0 is fractional; 1.0 < disc <= 100 is percentage
                conditions = [
                    (disc >= 0.0) & (disc <= 1.0),
                    (disc > 1.0) & (disc <= 100.0),
                ]
                choices = [
                    1.0 - disc,
                    1.0 - (disc / 100.0),
                ]
                disc_factor = np.select(conditions, choices, default=1.0)
                eff_price = price * disc_factor
                derived_rev = (qty * eff_price).round(2)

                df.loc[derivable_mask, "total_revenue"] = derived_rev
                revenue_valid_mask = revenue_valid_mask | derivable_mask

        if derived_revenue_count > 0:
            changelog.append(f"Derived revenue for {derived_revenue_count} records using Quantity \u00d7 UnitPrice (accounting for discount).")

        excluded_for_revenue = int((valid_date_mask & (~revenue_valid_mask)).sum())
        if excluded_for_revenue > 0:
            exclusion_reasons["Missing or unresolvable revenue"] = excluded_for_revenue
            changelog.append(f"Excluded {excluded_for_revenue} records where revenue could not be established.")

        # Step 6: Filter valid rows (must have valid date AND valid revenue)
        valid_rows_mask = valid_date_mask & revenue_valid_mask
        df_valid = df[valid_rows_mask].copy()

        # Step 7: Handle optional string fields (Explicit 'Unspecified' categorical placeholder)
        optional_str_fields = ["category", "sub_category", "region", "product_name", "product_id", "customer_name"]
        for col in optional_str_fields:
            if col in df_valid.columns:
                null_str_count = int(df_valid[col].isna().sum())
                if null_str_count > 0:
                    missing_by_field[col] = missing_by_field.get(col, 0) + null_str_count
                    df_valid[col] = df_valid[col].fillna("Unspecified").astype(str).str.strip()
                    changelog.append(f"Assigned explicit 'Unspecified' categorical placeholder to {null_str_count} missing '{col}' entries.")

        # Step 8: Profit derivation if cost is available but profit is not
        if "total_cost" in df_valid.columns:
            if "profit" not in df_valid.columns or df_valid["profit"].isna().all():
                df_valid["profit"] = df_valid["total_revenue"] - df_valid["total_cost"]
                changelog.append("Calculated Profit as Revenue - Total Cost for valid cost rows.")

        # Step 9: Anomaly detection on valid rows (vectorized boolean masks)
        if len(df_valid) > 0:
            if "quantity" in df_valid.columns:
                anomalies["negative_quantity"] = int((df_valid["quantity"].notna() & (df_valid["quantity"] < 0)).sum())
            if "total_revenue" in df_valid.columns:
                anomalies["negative_revenue"] = int((df_valid["total_revenue"].notna() & (df_valid["total_revenue"] < 0)).sum())
            if "discount" in df_valid.columns:
                anomalies["invalid_discount"] = int(
                    (df_valid["discount"].notna() & ((df_valid["discount"] < 0) | (df_valid["discount"] > 100.0))).sum()
                )
            if "unit_price" in df_valid.columns:
                anomalies["suspicious_unit_price"] = int(
                    (df_valid["unit_price"].notna() & (df_valid["unit_price"] < 0)).sum()
                )
            if "order_date" in df_valid.columns:
                years = pd.to_datetime(df_valid["order_date"]).dt.year
                anomalies["out_of_range_dates"] = int(
                    (years.notna() & ((years < 1990) | (years > 2050))).sum()
                )

        total_anomalies = sum(anomalies.values())
        if total_anomalies > 0:
            changelog.append(f"Detected {total_anomalies} business anomalies (e.g. negative quantities, extreme discounts) for review.")

        # Step 10: Final counts and Health Score Calculation
        valid_rows_count = len(df_valid)
        excluded_rows_count = sum(exclusion_reasons.values())

        # Safe health score computation: Bounded in [0.0, 100.0]
        if total_raw_rows == 0:
            health_score = 0.0
        else:
            # Excluded rows have weight 1.0; minor coercions/derivatives have small penalty weights
            penalties = (
                excluded_rows_count * 1.0
                + exact_duplicates_count * 0.5
                + invalid_dates_count * 0.5
                + invalid_numerics_count * 0.5
                + type_coercions_count * 0.05
            )
            score = 100.0 * (1.0 - (penalties / max(total_raw_rows, 1)))
            health_score = max(0.0, min(100.0, score))

        audit_report = DataQualityAuditResult(
            total_raw_rows=total_raw_rows,
            valid_rows=valid_rows_count,
            excluded_rows=excluded_rows_count,
            exact_duplicates_count=exact_duplicates_count,
            missing_values_by_field=missing_by_field,
            invalid_dates_count=invalid_dates_count,
            invalid_numerics_count=invalid_numerics_count,
            type_coercions_count=type_coercions_count,
            derived_value_count=derived_revenue_count,
            anomalies_detected=anomalies,
            exclusion_reasons=exclusion_reasons,
            health_score=health_score,
            changelog_summary=changelog,
        )

        return CleanedDatasetResult(
            cleaned_df=df_valid,
            audit_report=audit_report,
            available_dimensions=mapping_result.available_dimensions,
        )
