"""Script to verify end-to-end API execution against the physical SQLite database."""

import os
import sys
sys.path.insert(0, os.path.abspath("."))

import io
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.main import app
from app.config import get_settings

def run_verification():
    client = TestClient(app)

    csv_content = """order_date,order_id,customer_id,product_name,category,region,quantity,unit_price,total_revenue,total_cost,profit
2024-01-10,ORD-101,CUST-A,Laptop,Electronics,North,1,1200.0,1200.0,800.0,400.0
2024-01-15,ORD-102,CUST-B,Desk,Furniture,South,2,250.0,500.0,300.0,200.0
2024-02-01,ORD-103,CUST-A,Monitor,Electronics,North,2,300.0,600.0,350.0,250.0
"""

    print("1. Testing POST /api/v1/upload against real SQLite database...")
    files = {"file": ("real_sales_upload.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/upload", files=files)
    print("Upload Status Code:", upload_res.status_code)
    assert upload_res.status_code == 201, f"Expected 201, got {upload_res.status_code}: {upload_res.text}"
    upload_data = upload_res.json()
    dataset_id = upload_data["dataset_id"]
    print("Upload Result:", json.dumps(upload_data, indent=2))

    print("\n2. Verifying physical SQLite database persistence via SQL...")
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        ds_row = conn.execute(text("SELECT id, filename, total_raw_rows, total_cleaned_rows, status, storage_path FROM datasets WHERE id = :id"), {"id": dataset_id}).fetchone()
        print("Persisted Dataset Row in SQLite:", ds_row)
        assert ds_row is not None
        
        sr_count = conn.execute(text("SELECT COUNT(*) FROM sales_records WHERE dataset_id = :id"), {"id": dataset_id}).scalar()
        print("Persisted SalesRecords Count in SQLite:", sr_count)
        assert sr_count == 3
        
        dq_row = conn.execute(text("SELECT total_raw_rows, valid_rows, health_score FROM data_quality_logs WHERE dataset_id = :id"), {"id": dataset_id}).fetchone()
        print("Persisted DataQualityLog Row in SQLite:", dq_row)
        assert dq_row is not None

    print("\n3. Testing GET /api/v1/datasets...")
    list_res = client.get("/api/v1/datasets")
    print("List Datasets Status:", list_res.status_code)
    assert list_res.status_code == 200

    print("\n4. Testing GET /api/v1/datasets/{id}...")
    detail_res = client.get(f"/api/v1/datasets/{dataset_id}")
    print("Detail Status:", detail_res.status_code)
    assert detail_res.status_code == 200

    print("\n5. Testing GET /api/v1/datasets/{id}/quality-audit...")
    audit_res = client.get(f"/api/v1/datasets/{dataset_id}/quality-audit")
    print("Quality Audit Status:", audit_res.status_code)
    assert audit_res.status_code == 200
    print("Audit Report Summary:", json.dumps(audit_res.json(), indent=2))

    print("\n6. Testing GET /api/v1/analytics/{id}/kpis...")
    kpi_res = client.get(f"/api/v1/analytics/{dataset_id}/kpis")
    print("KPI Status:", kpi_res.status_code)
    assert kpi_res.status_code == 200
    print("KPI Summary:", json.dumps(kpi_res.json(), indent=2))

    print("\nAll Real SQLite Database & HTTP Endpoint tests passed successfully!")

if __name__ == "__main__":
    run_verification()
