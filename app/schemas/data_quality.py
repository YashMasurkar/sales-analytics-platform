from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class DataQualityReportResponse(BaseModel):
    dataset_id: str
    total_raw_rows: int
    valid_rows: int
    excluded_rows: int
    exact_duplicates_count: int
    missing_values_by_field: Optional[Dict[str, int]] = None
    missing_values_count: int
    invalid_dates_count: int
    invalid_numerics_count: int
    type_coercions_count: int
    derived_value_count: int
    anomalies_detected: Optional[Dict[str, int]] = None
    exclusion_reasons: Optional[Dict[str, int]] = None
    health_score: float
    changelog_summary: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)
