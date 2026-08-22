from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class DatasetBase(BaseModel):
    filename: str
    file_format: str


class DatasetListItem(DatasetBase):
    id: str
    upload_timestamp: datetime
    total_raw_rows: int
    total_cleaned_rows: int
    status: str
    health_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class DatasetDetailResponse(DatasetBase):
    id: str
    total_raw_rows: int
    total_cleaned_rows: int
    upload_timestamp: datetime
    status: str
    error_message: Optional[str] = None
    available_dimensions: Optional[Dict[str, bool]] = None
    health_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class DatasetUploadResponse(BaseModel):
    dataset_id: str
    filename: str
    file_format: str
    total_raw_rows: int
    valid_rows: int
    excluded_rows: int
    health_score: float
    available_dimensions: Dict[str, bool]
    derived_value_count: int
    anomalies_detected: Dict[str, int]
    changelog_summary: List[str]


class DatasetDeleteResponse(BaseModel):
    message: str
    dataset_id: str
