"""Comprehensive End-to-End REST API Test Suite for Phase 3."""

import io
import pytest
import pandas as pd
import xlwt
from fastapi.testclient import TestClient


def create_csv_bytes(content: str) -> bytes:
    """Helper to encode CSV string to bytes."""
    return content.encode("utf-8")


def create_xlsx_bytes(df: pd.DataFrame) -> bytes:
    """Helper to encode DataFrame into XLSX bytes."""
    output = io.BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    return output.getvalue()


def create_xls_bytes() -> bytes:
    """Helper to encode DataFrame into binary BIFF8 XLS bytes."""
    wb = xlwt.Workbook()
    ws = wb.add_sheet("Sales")
    ws.write(0, 0, "order_date")
    ws.write(0, 1, "revenue")
    ws.write(0, 2, "quantity")
    ws.write(1, 0, "2024-01-15")
    ws.write(1, 1, 300.0)
    ws.write(1, 2, 3)

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


# 1. Health Endpoint
def test_api_health_endpoint(client: TestClient):
    """Test 1: Health endpoint returns 200 OK and status 'ok'."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


# 2. Successful CSV Upload
def test_api_upload_csv_success(client: TestClient):
    """Test 2: Successful CSV upload with complete processing and database persistence."""
    csv_data = """order_date,order_id,customer_id,product_name,category,region,quantity,unit_price,total_revenue,total_cost,profit
2024-01-10,ORD-1,CUST-1,Widget Pro,Hardware,North,2,50.0,100.0,60.0,40.0
2024-02-15,ORD-2,CUST-2,Gadget Lite,Hardware,South,1,150.0,150.0,90.0,60.0
2024-02-20,ORD-3,CUST-1,Mouse Basic,Accessories,North,4,25.0,100.0,40.0,60.0
"""
    files = {"file": ("test_sales.csv", create_csv_bytes(csv_data), "text/csv")}
    res = client.post("/api/v1/upload", files=files)

    assert res.status_code == 201
    data = res.json()
    assert "dataset_id" in data
    assert data["filename"] == "test_sales.csv"
    assert data["file_format"] == "csv"
    assert data["total_raw_rows"] == 3
    assert data["valid_rows"] == 3
    assert data["excluded_rows"] == 0
    assert data["health_score"] == 100.0
    assert data["available_dimensions"]["has_cost"] is True
    assert data["available_dimensions"]["has_profit"] is True


# 3. Successful XLSX Upload
def test_api_upload_xlsx_success(client: TestClient):
    """Test 3: Successful modern Excel (.xlsx) upload."""
    df = pd.DataFrame({
        "order_date": ["2024-03-01", "2024-03-05"],
        "total_revenue": [500.0, 750.0],
        "category": ["Cloud", "Software"],
    })
    xlsx_bytes = create_xlsx_bytes(df)
    files = {"file": ("enterprise_sales.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    res = client.post("/api/v1/upload", files=files)

    assert res.status_code == 201
    data = res.json()
    assert data["filename"] == "enterprise_sales.xlsx"
    assert data["file_format"] == "xlsx"
    assert data["valid_rows"] == 2


# 4. Successful XLS Upload
def test_api_upload_xls_success(client: TestClient):
    """Test 4: Successful legacy Excel (.xls) upload via xlrd engine."""
    xls_bytes = create_xls_bytes()
    files = {"file": ("legacy_archive.xls", xls_bytes, "application/vnd.ms-excel")}
    res = client.post("/api/v1/upload", files=files)

    assert res.status_code == 201
    data = res.json()
    assert data["filename"] == "legacy_archive.xls"
    assert data["file_format"] == "xls"
    assert data["valid_rows"] == 1


# 5. Unsupported File Type (415)
def test_api_upload_unsupported_format(client: TestClient):
    """Test 5: Uploading an unsupported file format returns 415."""
    files = {"file": ("script.py", b"print('hello')", "text/x-python")}
    res = client.post("/api/v1/upload", files=files)

    assert res.status_code == 415
    assert "Unsupported file format" in res.json()["detail"]


# 6. Oversized File Simulation (413)
def test_api_upload_oversized_file(client: TestClient, monkeypatch):
    """Test 6: Files exceeding the max upload size return 413."""
    from app.api.v1.endpoints import upload
    monkeypatch.setattr(upload.settings, "MAX_UPLOAD_SIZE_MB", 0.0001)  # Set tiny limit for test

    csv_data = "order_date,total_revenue\n2024-01-01,100.0\n" * 100
    files = {"file": ("large_file.csv", create_csv_bytes(csv_data), "text/csv")}
    res = client.post("/api/v1/upload", files=files)

    assert res.status_code == 413
    assert "exceeds the maximum allowed limit" in res.json()["detail"]


# 7. Missing Required Schema (422)
def test_api_upload_missing_required_schema(client: TestClient):
    """Test 7: Missing required columns (e.g. no Date column) returns 422 with diagnostic error."""
    csv_data = "product_name,category\nWidget,Hardware\n"
    files = {"file": ("invalid_schema.csv", create_csv_bytes(csv_data), "text/csv")}
    res = client.post("/api/v1/upload", files=files)

    assert res.status_code == 422
    assert "missing required dimensions" in res.json()["detail"].lower()


# 8. Ambiguous Schema (422)
def test_api_upload_ambiguous_schema(client: TestClient):
    """Test 8: Conflicting candidate columns return 422 SchemaAmbiguityError."""
    csv_data = "order_date,invoice_date,sales\n2024-01-01,2024-01-02,100.0\n"
    files = {"file": ("ambiguous.csv", create_csv_bytes(csv_data), "text/csv")}
    res = client.post("/api/v1/upload", files=files)

    assert res.status_code == 422
    assert "ambiguous" in res.json()["detail"].lower()


# 9. Dataset Listing & Detail & Not Found (404)
def test_api_dataset_crud_and_not_found(client: TestClient):
    """Test 9-11: List datasets, retrieve details, handle 404, and delete dataset."""
    # Upload dataset
    csv_data = "date,sales,category,region\n2024-01-01,100.0,Tech,North\n"
    files = {"file": ("dataset_crud.csv", create_csv_bytes(csv_data), "text/csv")}
    upload_res = client.post("/api/v1/upload", files=files)
    dataset_id = upload_res.json()["dataset_id"]

    # List datasets
    list_res = client.get("/api/v1/datasets")
    assert list_res.status_code == 200
    dataset_ids = [d["id"] for d in list_res.json()]
    assert dataset_id in dataset_ids

    # Get dataset detail
    detail_res = client.get(f"/api/v1/datasets/{dataset_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["filename"] == "dataset_crud.csv"

    # Get non-existent dataset -> 404
    nf_res = client.get("/api/v1/datasets/non-existent-uuid-12345")
    assert nf_res.status_code == 404

    # Delete dataset
    del_res = client.delete(f"/api/v1/datasets/{dataset_id}")
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Dataset deleted successfully."

    # Confirm deletion
    recheck_res = client.get(f"/api/v1/datasets/{dataset_id}")
    assert recheck_res.status_code == 404


# 12. Quality Audit Retrieval Endpoint
def test_api_quality_audit_endpoint(client: TestClient):
    """Test 12: Retrieve persisted Data Quality Audit report."""
    csv_data = """date,sales,category
2024-01-01,100.0,Tech
2024-01-01,100.0,Tech
corrupted-date,50.0,Tech
"""
    files = {"file": ("audit_test.csv", create_csv_bytes(csv_data), "text/csv")}
    upload_res = client.post("/api/v1/upload", files=files)
    dataset_id = upload_res.json()["dataset_id"]

    audit_res = client.get(f"/api/v1/datasets/{dataset_id}/quality-audit")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()

    assert audit_data["dataset_id"] == dataset_id
    assert audit_data["total_raw_rows"] == 3
    assert audit_data["valid_rows"] == 1
    assert audit_data["exact_duplicates_count"] == 1
    assert audit_data["invalid_dates_count"] == 1
    assert len(audit_data["changelog_summary"]) > 0


# 13. KPIs & Dynamic Filtering Endpoint
def test_api_kpis_and_filters(client: TestClient):
    """Test 13-15: KPI calculation, date filtering, and category/region filtering."""
    csv_data = """order_date,order_id,customer_id,category,region,quantity,unit_price,total_revenue,total_cost,profit
2024-01-15,ORD-1,C1,Electronics,North,2,50.0,100.0,60.0,40.0
2024-01-20,ORD-2,C2,Electronics,South,1,100.0,100.0,50.0,50.0
2024-02-10,ORD-3,C1,Furniture,North,1,200.0,200.0,120.0,80.0
2024-03-05,ORD-4,C3,Furniture,West,2,150.0,300.0,180.0,120.0
"""
    files = {"file": ("kpi_filters.csv", create_csv_bytes(csv_data), "text/csv")}
    upload_res = client.post("/api/v1/upload", files=files)
    dataset_id = upload_res.json()["dataset_id"]

    # All data KPIs
    kpi_res = client.get(f"/api/v1/analytics/{dataset_id}/kpis")
    assert kpi_res.status_code == 200
    kpi_data = kpi_res.json()
    assert kpi_data["financials"]["total_revenue"] == 700.0
    assert kpi_data["financials"]["total_cost"] == 410.0
    assert kpi_data["financials"]["total_profit"] == 290.0
    assert kpi_data["volumes"]["total_orders"] == 4
    assert kpi_data["volumes"]["total_unique_customers"] == 3

    # Filtered by Category = 'Electronics'
    cat_filtered = client.get(f"/api/v1/analytics/{dataset_id}/kpis?category=Electronics")
    assert cat_filtered.status_code == 200
    assert cat_filtered.json()["financials"]["total_revenue"] == 200.0
    assert cat_filtered.json()["volumes"]["total_orders"] == 2

    # Filtered by Date Range (January only)
    date_filtered = client.get(f"/api/v1/analytics/{dataset_id}/kpis?start_date=2024-01-01&end_date=2024-01-31")
    assert date_filtered.status_code == 200
    assert date_filtered.json()["financials"]["total_revenue"] == 200.0

    # Invalid date range (start > end) -> 422
    invalid_range = client.get(f"/api/v1/analytics/{dataset_id}/kpis?start_date=2024-12-01&end_date=2024-01-01")
    assert invalid_range.status_code == 422

    # Invalid date string -> 422
    invalid_date_str = client.get(f"/api/v1/analytics/{dataset_id}/kpis?start_date=invalid-date")
    assert invalid_date_str.status_code == 422


# 16. Trends, Categories, Regions, and Products Endpoints
def test_api_analytics_sub_endpoints(client: TestClient):
    """Test 16-20: Trends, Category Breakdown, Regional Performance, Product Rankings, Filter Options."""
    csv_data = """order_date,order_id,product_name,category,region,total_revenue,total_cost,profit
2024-01-10,ORD-1,MacBook,Electronics,North,2000.0,1200.0,800.0
2024-01-15,ORD-2,Chair,Furniture,South,150.0,80.0,70.0
2024-02-10,ORD-3,iPhone,Electronics,North,1000.0,600.0,400.0
2024-02-15,ORD-4,Desk,Furniture,South,350.0,200.0,150.0
"""
    files = {"file": ("analytics_grid.csv", create_csv_bytes(csv_data), "text/csv")}
    upload_res = client.post("/api/v1/upload", files=files)
    dataset_id = upload_res.json()["dataset_id"]

    # 1. Trends
    trends_res = client.get(f"/api/v1/analytics/{dataset_id}/trends")
    assert trends_res.status_code == 200
    trends_data = trends_res.json()
    assert trends_data["available"] is True
    assert len(trends_data["trends"]) == 2
    assert trends_data["trends"][0]["period"] == "2024-01"
    assert trends_data["trends"][0]["revenue"] == 2150.0

    # 2. Categories
    cat_res = client.get(f"/api/v1/analytics/{dataset_id}/categories")
    assert cat_res.status_code == 200
    cat_data = cat_res.json()
    assert cat_data["available"] is True
    assert cat_data["categories"][0]["category"] == "Electronics"
    assert cat_data["categories"][0]["revenue"] == 3000.0

    # 3. Regions
    reg_res = client.get(f"/api/v1/analytics/{dataset_id}/regions")
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["available"] is True
    assert reg_data["regions"][0]["region"] == "North"
    assert reg_data["regions"][0]["revenue"] == 3000.0

    # 4. Products
    prod_res = client.get(f"/api/v1/analytics/{dataset_id}/products")
    assert prod_res.status_code == 200
    prod_data = prod_res.json()
    assert prod_data["available"] is True
    assert prod_data["top_products"][0]["product_name"] == "MacBook"
    assert prod_data["top_products"][0]["revenue"] == 2000.0

    # 5. Filter Options
    opt_res = client.get(f"/api/v1/analytics/{dataset_id}/filter-options")
    assert opt_res.status_code == 200
    opt_data = opt_res.json()
    assert opt_data["min_date"] == "2024-01-10"
    assert opt_data["max_date"] == "2024-02-15"
    assert "Electronics" in opt_data["categories"]
    assert "North" in opt_data["regions"]


# 21. Cleaned CSV Export
def test_api_export_cleaned_csv(client: TestClient):
    """Test 21: Export cleaned CSV attachment."""
    csv_data = "date,sales,category\n2024-01-01,100.0,Tech\n2024-01-02,200.0,Tech\n"
    files = {"file": ("export_source.csv", create_csv_bytes(csv_data), "text/csv")}
    upload_res = client.post("/api/v1/upload", files=files)
    dataset_id = upload_res.json()["dataset_id"]

    export_res = client.get(f"/api/v1/export/{dataset_id}/cleaned")
    assert export_res.status_code == 200
    assert export_res.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=\"cleaned_export_source.csv\"" in export_res.headers["content-disposition"]
    assert "2024-01-01" in export_res.text
    assert "100.00" in export_res.text


# 22. Unavailable Optional Dimensions (Graceful Degradation in API)
def test_api_unavailable_optional_dimensions(client: TestClient):
    """Test 22-24: When optional fields (cost, category, region, product) are missing, API returns clean unavailable structures."""
    csv_data = "order_date,total_revenue\n2024-01-01,100.0\n2024-01-02,200.0\n"
    files = {"file": ("minimal_sales.csv", create_csv_bytes(csv_data), "text/csv")}
    upload_res = client.post("/api/v1/upload", files=files)
    dataset_id = upload_res.json()["dataset_id"]

    # KPIs without cost/customers
    kpis = client.get(f"/api/v1/analytics/{dataset_id}/kpis").json()
    assert kpis["financials"]["total_cost"] is None
    assert kpis["financials"]["total_profit"] is None
    assert kpis["financials"]["profit_margin_pct"] is None
    assert kpis["volumes"]["total_unique_customers"] is None
    assert kpis["available_metrics"]["profit"] is False

    # Categories when no category column exists
    cats = client.get(f"/api/v1/analytics/{dataset_id}/categories").json()
    assert cats["available"] is False
    assert cats["categories"] == []

    # Regions when no region column exists
    regs = client.get(f"/api/v1/analytics/{dataset_id}/regions").json()
    assert regs["available"] is False
    assert regs["regions"] == []

    # Products when no product column exists
    prods = client.get(f"/api/v1/analytics/{dataset_id}/products").json()
    assert prods["available"] is False
    assert prods["top_products"] == []


# 25. OpenAPI Documentation Verification
def test_api_openapi_documentation(client: TestClient):
    """Test 25: OpenAPI documentation endpoint loads and contains all Phase 3 paths."""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    assert "/api/v1/upload" in schema["paths"]
    assert "/api/v1/datasets" in schema["paths"]
    assert "/api/v1/datasets/{id}" in schema["paths"]
    assert "/api/v1/datasets/{id}/quality-audit" in schema["paths"]
    assert "/api/v1/analytics/{id}/kpis" in schema["paths"]
    assert "/api/v1/analytics/{id}/trends" in schema["paths"]
    assert "/api/v1/analytics/{id}/categories" in schema["paths"]
    assert "/api/v1/analytics/{id}/regions" in schema["paths"]
    assert "/api/v1/analytics/{id}/products" in schema["paths"]
    assert "/api/v1/analytics/{id}/filter-options" in schema["paths"]
    assert "/api/v1/export/{id}/cleaned" in schema["paths"]


# 26. Frontend Root & Static Assets Verification
def test_root_serves_frontend_html(client: TestClient):
    """Test 26: Root URL '/' serves the Single Page Application index.html."""
    res = client.get("/")
    assert res.status_code == 200
    assert "Sales Analytics & Business Intelligence Platform" in res.text
    assert "Sales Overview" in res.text
    assert "/static/js/app.js" in res.text


def test_demo_dataset_static_asset_served(client: TestClient):
    """Test 27: Demo dataset CSV is reachable at /static/data/demo_sales.csv."""
    res = client.get("/static/data/demo_sales.csv")
    assert res.status_code == 200
    assert "MacBook Pro" in res.text
    assert "Ergonomic Chair" in res.text


def test_api_upload_database_failure_cleans_up_orphaned_file(client: TestClient, monkeypatch):
    """Test 28: Verify that when database persistence fails, physical upload file is removed."""
    import os
    from unittest.mock import patch
    from sqlalchemy.orm import Session

    # Count files in uploads before test
    upload_dir = "./uploads"
    os.makedirs(upload_dir, exist_ok=True)
    before_files = set(os.listdir(upload_dir))

    # Mock Session.commit to simulate database failure during upload
    def mock_commit(self):
        raise RuntimeError("Simulated database failure during commit")

    with patch.object(Session, "commit", mock_commit):
        csv_content = "order_date,total_revenue\n2024-01-01,100.0\n"
        res = client.post(
            "/api/v1/upload",
            files={"file": ("simulated_failure.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        )
        assert res.status_code == 500
        assert "Unexpected error occurred while persisting data" in res.json()["detail"]

    # Verify no orphaned files remain in upload_dir
    after_files = set(os.listdir(upload_dir))
    assert after_files == before_files, f"Orphaned files detected: {after_files - before_files}"


def test_api_upload_success_preserves_physical_file(client: TestClient):
    """Test 29: Verify that a successful upload keeps the physical file intact on disk."""
    import os
    csv_content = "order_date,total_revenue\n2024-01-01,100.0\n"
    res = client.post(
        "/api/v1/upload",
        files={"file": ("persist_test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    assert res.status_code == 201
    dataset_id = res.json()["dataset_id"]

    detail_res = client.get(f"/api/v1/datasets/{dataset_id}")
    assert detail_res.status_code == 200
    
    # Check dataset in list_datasets
    list_res = client.get("/api/v1/datasets")
    assert list_res.status_code == 200
    item = next((d for d in list_res.json() if d["id"] == dataset_id), None)
    assert item is not None
    assert item["health_score"] == 100.0

    # Cleanup
    del_res = client.delete(f"/api/v1/datasets/{dataset_id}")
    assert del_res.status_code == 200

