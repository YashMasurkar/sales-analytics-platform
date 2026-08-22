# Sales Analytics & Business Intelligence Platform

A portfolio-grade web application built to automate sales dataset ingestion, rigorous data quality auditing, financial/volume KPI computation, and interactive visual business intelligence exploration.

---

## 🎯 Project Overview & Purpose

Designed as a flagship project for a **Data Analyst → Data Scientist** career path, this platform demonstrates production-level data engineering, deterministic data cleaning, and full-stack analytical architecture.

### Key Pillars
- **Analytical Integrity & Non-Fabrication**: Unlike superficial dashboards that blindly impute zeros or invent missing values, this engine detects and isolates missing financials, tracking explicit data exclusion reasons and anomaly classifications.
- **Graceful Analytical Degradation**: Missing optional dimensions (e.g., cost, customer ID, category, region) do not crash calculations; the UI cleanly disables dependent metrics while preserving valid core analytics.
- **Zero-Build Frontend Architecture**: A single-runtime deployment leveraging FastAPI to serve both the REST API and the responsive single-page Vanilla JS/Tailwind CSS dashboard with Chart.js visualization.
- **Database & Migration Layer**: Built on SQLAlchemy 2.0 with Alembic batch migrations supporting local SQLite and cloud PostgreSQL.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3.10+, FastAPI, Pydantic v2, Pydantic-Settings |
| **Data Processing** | Pandas 2.2+, NumPy, openpyxl, xlrd |
| **Database & ORM** | SQLAlchemy 2.0, SQLite (Dev) / PostgreSQL (Prod), Alembic 1.13+ |
| **Testing** | Pytest, HTTPX (FastAPI TestClient) |
| **Frontend** | HTML5, Tailwind CSS (via CDN), Vanilla JavaScript ES Modules, Chart.js 4.4+ |
| **ASGI Server** | Uvicorn |

---

## 🏛️ System Architecture & Project Structure

```
sales-analytics-platform/
├── alembic/                      # Alembic database migration scripts
│   ├── versions/                 # Version migration definitions
│   └── env.py                    # Migration environment configuration
├── app/                          # Core application package
│   ├── api/                      # API routing layer
│   │   └── v1/                   # API Version 1 endpoints
│   │       ├── endpoints/        # Focused route modules (upload, datasets, analytics, export, health)
│   │       └── router.py         # Master API v1 router
│   ├── core/                     # Business logic and analytical processing engines
│   │   ├── cleaner.py            # Cleansing, deduplication, and quality scoring
│   │   ├── exceptions.py         # Domain-specific exception definitions
│   │   ├── ingestion.py          # File validation and dataframe parsing (CSV/XLSX/XLS)
│   │   ├── kpi_engine.py         # Vectorized KPI calculation and trend aggregations
│   │   └── schema_mapper.py      # Conservative canonical column mapper
│   ├── db/                       # Database session and ORM models
│   │   ├── models/               # SQLAlchemy models (Dataset, SalesRecord, DataQualityLog, KPICache)
│   │   └── session.py            # Engine, session factory, and table initializers
│   ├── schemas/                  # Pydantic validation and serialization schemas
│   ├── static/                   # Static frontend application assets
│   │   ├── css/                  # Custom CSS styles and scrollbars
│   │   ├── data/                 # Demo dataset copy for client-side loading
│   │   ├── js/                   # Modular Vanilla JS controllers (api, charts, dashboard, audit, etc.)
│   │   └── index.html            # Single-page application shell
│   ├── config.py                 # Application configuration via pydantic-settings
│   └── main.py                   # FastAPI application factory and entry point
├── data/                         # Data fixtures
│   ├── demo/                     # Representative demo sales CSV
│   └── test/                     # Edge-case regression test datasets
├── tests/                        # Automated Pytest suite (66 tests)
│   ├── test_api.py               # REST endpoint integration tests
│   ├── test_cleaner.py           # Data cleaner and deduplication unit tests
│   ├── test_health.py            # Server health and model initialization tests
│   ├── test_ingestion.py         # File ingestion and parsing tests
│   ├── test_kpi_engine.py        # Vectorized KPI calculations and degradation tests
│   ├── test_pipeline_fixtures.py # End-to-end pipeline edge case fixture tests
│   └── test_schema_mapper.py     # Column synonym mapping and ambiguity tests
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git tracking rules
├── alembic.ini                   # Alembic configuration
├── pytest.ini                    # Pytest settings
├── requirements.txt              # Production and development dependencies
└── README.md                     # Project documentation
```

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- **Python 3.10+** (tested on Python 3.10, 3.11, 3.12, 3.13, 3.14)
- Git

### 2. Environment Setup
```powershell
# Clone the repository
git clone https://github.com/username/sales-analytics-platform.git
cd sales-analytics-platform

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```powershell
# Windows PowerShell:
Copy-Item .env.example .env

# Linux / macOS:
cp .env.example .env
```

Review `.env` parameters:
```ini
APP_NAME="Sales Analytics & Business Intelligence Platform"
APP_ENV=development
DEBUG=True
HOST=127.0.0.1
PORT=8000
DATABASE_URL=sqlite:///./sales_analytics.db
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=50
```

### 4. Database Initialization & Migrations
```powershell
# Run database migrations using Alembic
alembic upgrade head
```

### 5. Running the Application
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- **Web UI & Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative Documentation (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### 6. Running the Automated Test Suite
```powershell
pytest -v
```

---

## 📊 Core Data Engine & Analytical Methodology

### Ingestion & Schema Mapping
- Supports `.csv`, `.xlsx` (via `openpyxl`), and `.xls` (via `xlrd`).
- **Conservative Synonym Matching**: Resolves column variations (e.g. `order_date`, `transaction_date`, `revenue`, `sales_amount`) without aggressive fuzzy matching.
- **Ambiguity Rejection**: Conflicting candidate columns trigger an explicit `SchemaAmbiguityError` (HTTP 422) instead of guessing.

### Data Cleansing & Quality Auditing
- **Exact Full-Row Deduplication**: Removes duplicate transactions while distinguishing deduplication from invalid record rejection.
- **No Numerical Value Fabrication**: Missing mandatory dates or revenues (where unit price and quantity cannot compute them) are excluded with explicit reasoning, never zero-imputed.
- **Explicit Categorical Placeholders**: Missing optional string dimensions (category, region, customer) are assigned an explicit `'Unspecified'` label rather than undergoing statistical imputation.
- **Anomaly Classification**: Negative quantities (returns) and negative revenues are preserved in cleaned data and audited as business anomalies.
- **Bounded Health Score ($[0.0, 100.0]$)**:
  $$\text{Health Score} = 100 \times \left(1 - \frac{\text{Penalties}}{\max(\text{Total Raw Rows}, 1)}\right)$$

### Executive KPI Calculations & Graceful Degradation
- **Financial Metrics**: Total Revenue, Total Cost, Total Profit ($\text{Revenue} - \text{Cost}$), Profit Margin % ($\frac{\text{Profit}}{\text{Revenue}} \times 100$), Average Order Value ($\frac{\text{Revenue}}{\text{Orders}}$).
- **Graceful Degradation**: If cost data is omitted, Profit and Profit Margin display `"Unavailable: Cost data not provided"`. If customer ID is omitted, Unique Customers displays `"Unavailable: Customer ID not provided"`.
- **Month-over-Month (MoM) Growth**:
  $$\text{MoM Growth} = \frac{\text{Revenue}_{\text{Current Month}} - \text{Revenue}_{\text{Prior Month}}}{\text{Revenue}_{\text{Prior Month}}} \times 100$$
- **Revenue Trend Switching**: Dynamic line charts supporting metric toggling across Revenue, Profit, and Order Volume.
- **Category & Regional Performance**: Horizontal bar charts displaying absolute revenue and percentage share of total business volume.
- **Product Performance Rankings**: Segmented tables displaying Top 10 and Lowest 5 products ranked by total revenue.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service health status and database connectivity check. |
| `POST` | `/api/v1/upload` | Upload and process CSV/XLSX/XLS dataset with automated cleansing. |
| `GET` | `/api/v1/datasets` | List all uploaded datasets with record counts and health scores. |
| `GET` | `/api/v1/datasets/{id}` | Retrieve dataset metadata and available dimension flags. |
| `DELETE` | `/api/v1/datasets/{id}` | Delete a dataset, its sales records, and its quality logs. |
| `GET` | `/api/v1/datasets/{id}/quality-audit` | Detailed data quality audit report (missing fields, anomalies, changelog). |
| `GET` | `/api/v1/analytics/{id}/kpis` | Executive financial and volume KPIs with MoM growth rates. |
| `GET` | `/api/v1/analytics/{id}/trends` | Chronological monthly aggregated sales and profit trends. |
| `GET` | `/api/v1/analytics/{id}/categories` | Revenue breakdown and percentage share by product category. |
| `GET` | `/api/v1/analytics/{id}/regions` | Revenue breakdown and percentage share by sales region. |
| `GET` | `/api/v1/analytics/{id}/products` | Product performance rankings (Top Revenue and Lowest Revenue). |
| `GET` | `/api/v1/analytics/{id}/filter-options` | Available filter options (unique categories, regions, date bounds). |
| `GET` | `/api/v1/export/{id}/cleaned` | Stream download cleaned dataset as standard CSV format. |

---

## 🧪 Testing Strategy & Verification

The platform includes **66 comprehensive automated tests** across 7 test suites:
- **`test_api.py`**: Integration testing of all 12 API endpoints, error responses (404, 413, 422), and SPA asset serving.
- **`test_cleaner.py`**: Numeric coercion, date parsing, duplicate row accounting, and health score bounds.
- **`test_ingestion.py`**: Extension validation, file size limits, safe filepath generation, and multi-format parsing.
- **`test_kpi_engine.py`**: Financial aggregations, graceful degradation when dimensions are absent, and empty data handling.
- **`test_pipeline_fixtures.py`**: 17 edge-case fixtures covering missing dates, ambiguous schemas, discount types, and return anomalies.
- **`test_schema_mapper.py`**: Canonical mappings, synonyms, and conflicting column ambiguity detection.
- **`test_health.py`**: Database connectivity and model relation initialization.

---

## 💡 Demo Dataset

The platform includes a built-in demo dataset at [`data/demo/demo_sales.csv`](file:///e:/projects/sales-analytics-platform/data/demo/demo_sales.csv) containing 40 multi-category, multi-region transactions spanning 6 months.

Recruiters and evaluators can explore full platform functionality instantly via the **"Try Demo Dataset"** button on the upload page, which runs the file through the live data processing pipeline.

---

## 🔮 Known Limitations & Future Scope

### Current Scope & Limitations
- Single-node in-process analytical execution via Pandas (optimized for sales spreadsheets up to 50MB).
- Deterministic heuristic data cleansing without machine learning imputation.

### Future Scope
- Automated Narrative Executive Summary generator summarizing key trends from computed KPIs.
- Multi-user authentication, dataset sharing permissions, and role-based access control.
- Scheduled recurring automated imports from cloud storage (AWS S3, Google Cloud Storage).
- Advanced forecasting models (ARIMA / Prophet) for projected revenue trajectories.
