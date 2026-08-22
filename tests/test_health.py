from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, datetime, timezone

from app.db.models import Dataset, SalesRecord, DataQualityLog, KPICache


def test_health_endpoint(client: TestClient):
    """Test that the health endpoint returns 200 OK with expected JSON structure."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


def test_database_models_initialization(db_session: Session):
    """Test creating and querying all Phase 1 SQLAlchemy models in SQLite."""
    # 1. Create Dataset
    dataset = Dataset(
        filename="test_sales_2024.csv",
        file_format="csv",
        total_raw_rows=100,
        total_cleaned_rows=98,
        status="ready",
    )
    db_session.add(dataset)
    db_session.flush()

    assert dataset.id is not None
    assert dataset.status == "ready"

    # 2. Create SalesRecord
    record = SalesRecord(
        dataset_id=dataset.id,
        order_id="ORD-1001",
        order_date=date(2024, 1, 15),
        customer_id="CUST-001",
        customer_name="Alice Smith",
        product_id="PROD-500",
        product_name="Wireless Mouse",
        category="Electronics",
        sub_category="Accessories",
        region="North America",
        quantity=2,
        unit_price=25.0,
        discount=0.1,
        total_revenue=45.0,
        total_cost=20.0,
        profit=25.0,
    )
    db_session.add(record)
    db_session.flush()

    assert record.id is not None
    assert record.dataset.filename == "test_sales_2024.csv"

    # 3. Create DataQualityLog
    quality_log = DataQualityLog(
        dataset_id=dataset.id,
        missing_values_count=2,
        duplicate_rows_count=2,
        type_coercions_count=5,
        anomalies_detected={"negative_values": 0},
        health_score=98.0,
    )
    db_session.add(quality_log)
    db_session.flush()

    assert dataset.data_quality_log.health_score == 98.0

    # 4. Create KPICache
    kpi_cache = KPICache(
        dataset_id=dataset.id,
        metric_key="total_revenue",
        metric_value={"value": 45.0, "currency": "USD"},
    )
    db_session.add(kpi_cache)
    db_session.flush()

    assert len(dataset.kpi_caches) == 1
    assert dataset.kpi_caches[0].metric_key == "total_revenue"
