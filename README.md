# Sales Analytics & Business Intelligence Platform

A portfolio-grade web application built to automate sales dataset ingestion, rigorous data quality auditing, financial and volume KPI computation, and interactive visual business intelligence exploration.

---

## 🌐 Live Demo

**Live Application:** https://sales-analytics-platform-qjum.onrender.com/

The deployed application is live and allows users to:

- **Upload sales datasets** in CSV, XLSX, or XLS formats
- **Load the built-in demo dataset** for immediate exploration
- **Review automated data-quality results**, anomaly detection logs, schema mappings, and health scores
- **Explore executive KPIs and interactive analytics**, including revenue/profit trends, category distributions, regional breakdowns, and product rankings
- **Apply date, category, and region filters**, individually or in combination
- **Remove datasets** using an interactive confirmation modal with Cancel and Delete actions
- **Export cleaned datasets** as standardized CSV files

---

## 🎯 Project Overview & Purpose

Designed as a flagship project for a **Data Analyst → Data Scientist** career path, this platform demonstrates data engineering, deterministic data cleaning, backend API development, database persistence, and full-stack analytical visualization.

### Key Pillars

- **Analytical Integrity & Non-Fabrication**: Missing numerical values are not blindly replaced with zeros or invented values. The platform explicitly identifies missing, invalid, excluded, and derived data.

- **Graceful Analytical Degradation**: Missing optional dimensions such as cost, customer ID, category, or region do not crash the analytical pipeline. Dependent metrics are clearly marked as unavailable while valid analytics continue to work.

- **Deterministic Revenue Derivation**: When raw revenue is missing, the engine derives it when valid quantity and unit price values are available, accounting for discounts and recording the derivation in the quality audit.

- **Zero-Build Frontend Architecture**: FastAPI serves both the REST API and the responsive Vanilla JavaScript dashboard using HTML, Tailwind CSS, and Chart.js.

- **Database & Migration Layer**: SQLAlchemy 2.0 provides the ORM layer while Alembic manages database migrations. SQLite is the current database implementation.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3.14, FastAPI, Pydantic v2, Pydantic-Settings |
| **Data Processing** | Pandas 2.2+, NumPy, openpyxl, xlrd, xlwt |
| **Database & ORM** | SQLite, SQLAlchemy 2.0, Alembic 1.13+ |
| **Testing Suite** | Pytest, HTTPX, 70 automated tests |
| **Frontend UI** | HTML5, Tailwind CSS, Vanilla JavaScript ES Modules, Chart.js 4.4+ |
| **ASGI Server** | Uvicorn |
| **Deployment** | Render Web Service |

---

## 🏛️ System Architecture & Project Structure

```text
sales-analytics-platform/

├── alembic/
│   ├── versions/
│   │   └── 0001_initial_schema.py
│   └── env.py
│
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── analytics.py
│   │       │   ├── datasets.py
│   │       │   ├── export.py
│   │       │   ├── health.py
│   │       │   └── upload.py
│   │       └── router.py
│   │
│   ├── core/
│   │   ├── cleaner.py
│   │   ├── exceptions.py
│   │   ├── ingestion.py
│   │   ├── kpi_engine.py
│   │   └── schema_mapper.py
│   │
│   ├── db/
│   │   ├── models/
│   │   │   ├── data_quality.py
│   │   │   ├── dataset.py
│   │   │   ├── kpi_cache.py
│   │   │   └── sales_record.py
│   │   └── session.py
│   │
│   ├── schemas/
│   │   ├── analytics.py
│   │   ├── data_quality.py
│   │   ├── dataset.py
│   │   └── upload.py
│   │
│   ├── static/
│   │   ├── css/
│   │   ├── data/
│   │   ├── js/
│   │   └── index.html
│   │
│   ├── config.py
│   └── main.py
│
├── data/
│   ├── demo/
│   │   └── demo_sales.csv
│   └── test/
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_cleaner.py
│   ├── test_health.py
│   ├── test_ingestion.py
│   ├── test_kpi_engine.py
│   ├── test_pipeline_fixtures.py
│   ├── test_schema_mapper.py
│   └── verify_real_db.py
│
├── .env.example
├── .gitignore
├── .python-version
├── alembic.ini
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites

- **Python 3.14**
- **Git**

### 2. Clone the Repository

```bash
git clone https://github.com/YashMasurkar/sales-analytics-platform.git
cd sales-analytics-platform
```

### 3. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

**Windows PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

**Linux / macOS**

```bash
cp .env.example .env
```

Review the configuration:

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

### 6. Database Initialization & Migrations

Run the Alembic migration:

```bash
alembic upgrade head
```

### 7. Run the Application

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The application will be available at:

- **Web UI:** http://127.0.0.1:8000
- **Swagger API Docs:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc
- **Health Check:** http://127.0.0.1:8000/api/v1/health

---

## ☁️ Deployment

The application is deployed as a **Render Web Service**.

- **Live URL:** https://sales-analytics-platform-qjum.onrender.com/
- **Platform:** Render
- **Runtime:** Python 3.14
- **Python Version:** Pinned using `.python-version`
- **Branch:** `main`

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

> [!NOTE]
> The current live deployment uses SQLite and local filesystem storage and is intended for portfolio evaluation, demonstration, and single-instance usage. It should not be treated as a highly available production storage architecture. For multi-user or horizontally scalable production deployments, the application can be migrated to hosted PostgreSQL with cloud object storage.

---

## 📊 Core Data Engine & Analytical Methodology

### Ingestion & Schema Mapping

The platform supports multiple sales dataset formats:

- CSV
- XLSX
- XLS

The ingestion layer validates the uploaded file and converts it into a standardized Pandas DataFrame.

### Conservative Schema Mapping

The schema mapper identifies canonical business fields using known column-name synonyms.

Examples include:

- `order_date`
- `transaction_date`
- `date`
- `revenue`
- `sales_amount`
- `unit_price`
- `selling_price`
- `quantity`
- `cost`
- `profit`

Ambiguous mappings are rejected instead of making unsafe guesses.

### Data Cleansing & Quality Auditing

The cleaning engine performs deterministic transformations including:

- Date parsing and validation
- Numeric value coercion
- Exact full-row duplicate detection
- Missing-value analysis
- Revenue validation
- Revenue derivation
- Optional categorical handling
- Business anomaly detection
- Health-score calculation
- Transformation changelog generation

### No Numerical Value Fabrication

The platform does not blindly replace missing numerical values with zero or statistical estimates.

Records with missing mandatory information may be excluded when the required analytical value cannot be established.

The exclusion reason is recorded in the data-quality audit.

### Deterministic Revenue Derivation

If `total_revenue` is missing but valid `quantity` and `unit_price` values are available, revenue can be derived.

The calculation is:

$$
\text{Revenue} =
\text{Quantity}
\times
\text{Unit Price}
\times
(1-\text{Discount})
$$

Discount values are interpreted according to the platform's supported discount representation.

Every derived revenue value is tracked through the data-quality audit.

### Explicit Categorical Placeholders

Missing optional categorical dimensions are represented using:

```text
Unspecified
```

rather than being statistically imputed.

### Business Anomaly Detection

The platform identifies business anomalies including:

- Negative quantities
- Negative revenue
- Invalid discounts
- Suspicious unit prices
- Out-of-range dates

Returns and other valid business anomalies are preserved rather than automatically deleted.

### Health Score

The platform calculates a bounded data-quality health score between:

```text
0.0 and 100.0
```

The score reflects the quality of the uploaded dataset based on detected issues and exclusions.

---

## 📈 Executive KPI Calculations

The dashboard calculates:

### Revenue

```text
Total Revenue = Sum of Total Revenue
```

### Cost

```text
Total Cost = Sum of Total Cost
```

### Profit

```text
Profit = Revenue - Cost
```

### Profit Margin

```text
Profit Margin % = (Profit / Revenue) × 100
```

### Average Order Value

```text
AOV = Revenue / Orders
```

### Units Sold

```text
Units Sold = Sum of Quantity
```

### Unique Customers

Unique customer count is calculated when customer IDs are available.

If customer IDs are not provided, the platform displays:

```text
Unavailable: Customer ID not provided
```

### Graceful Analytical Degradation

The platform does not fabricate missing financial information.

For example, if cost information is unavailable, profit is displayed as unavailable rather than being incorrectly calculated.

---

## 📉 Interactive Analytics

### Revenue Trend

Monthly chronological revenue aggregation is displayed through an interactive line chart.

The chart can switch between:

- Revenue
- Profit
- Orders

### Category Performance

Revenue is aggregated by product category and displayed through a horizontal bar chart.

### Regional Performance

Revenue is aggregated by region and displayed through a horizontal bar chart.

### Product Performance

Products are ranked by revenue.

The dashboard supports:

- Top Revenue
- Lowest Revenue

### Multi-Dimensional Filtering

Analytics can be filtered using:

- Start date
- End date
- Category
- Region

Filters can be applied individually or together.

For example:

```text
Category = Electronics
Region = North
```

will return analytics for only that business segment.

---

## 🗂️ Dataset Management

### Dataset Upload

Users can upload:

- CSV
- XLSX
- XLS

Each upload passes through the ingestion, schema mapping, cleaning, quality audit, and database persistence pipeline.

### Dataset Quality Review

After processing, the platform provides:

- Overall health score
- Total raw rows
- Valid cleaned rows
- Excluded rows
- Exact duplicates
- Invalid dates
- Invalid numerics
- Derived values
- Detected anomalies

### Dataset Deletion

Datasets can be removed through the dashboard.

The deletion flow includes a confirmation modal with:

- Cancel
- Delete

The deletion process cleans up the associated database records and uploaded file.

### Cleaned Dataset Export

Users can export the processed dataset as a standardized CSV file.

---

## 📡 REST API Reference

The platform currently exposes 13 REST API endpoints covering health checks, dataset ingestion and management, data-quality auditing, analytics, filtering, and cleaned-data export.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service health status and database connectivity check |
| `POST` | `/api/v1/upload` | Upload and process CSV/XLSX/XLS datasets |
| `GET` | `/api/v1/datasets` | List uploaded datasets |
| `GET` | `/api/v1/datasets/{id}` | Retrieve dataset metadata |
| `DELETE` | `/api/v1/datasets/{id}` | Delete a dataset and associated records/files |
| `GET` | `/api/v1/datasets/{id}/quality-audit` | Retrieve detailed data-quality audit |
| `GET` | `/api/v1/analytics/{id}/kpis` | Retrieve executive KPIs |
| `GET` | `/api/v1/analytics/{id}/trends` | Retrieve monthly revenue/profit/order trends |
| `GET` | `/api/v1/analytics/{id}/categories` | Retrieve category performance |
| `GET` | `/api/v1/analytics/{id}/regions` | Retrieve regional performance |
| `GET` | `/api/v1/analytics/{id}/products` | Retrieve product performance rankings |
| `GET` | `/api/v1/analytics/{id}/filter-options` | Retrieve available filter options |
| `GET` | `/api/v1/export/{id}/cleaned` | Export cleaned dataset as CSV |

---

## 🧪 Testing Strategy & Verification

The project contains **70 automated tests** across 7 test suites.

### `test_api.py` — 21 tests

Tests REST API behavior including:

- Dataset upload
- Dataset listing
- Dataset retrieval
- Dataset deletion
- KPI endpoints
- Filtering
- Export
- Error handling
- SPA serving

### `test_cleaner.py` — 11 tests

Tests:

- Numeric coercion
- Date parsing
- Duplicate detection
- Revenue derivation
- Discount handling
- Returns
- Negative anomalies
- Optional categorical fields
- Health-score boundaries

### `test_health.py` — 2 tests

Tests:

- API health
- Database/model initialization

### `test_ingestion.py` — 9 tests

Tests:

- File validation
- File-size enforcement
- Filename handling
- CSV ingestion
- XLSX ingestion
- XLS ingestion

### `test_kpi_engine.py` — 3 tests

Tests:

- Financial aggregations
- Graceful degradation
- Empty datasets

### `test_pipeline_fixtures.py` — 17 tests

End-to-end edge-case tests covering:

- Missing dates
- Ambiguous schemas
- Discounts
- Returns
- Suspicious values
- Missing dimensions
- Revenue derivation

### `test_schema_mapper.py` — 7 tests

Tests:

- Canonical mappings
- Column synonyms
- Quantity/unit-price fallback
- Ambiguous column detection

### Run the Test Suite

```bash
python -m pytest -q
```

Expected result:

```text
70 passed
```

### Physical Database Verification

The project also includes:

```bash
python tests/verify_real_db.py
```

This verifies the physical SQLite database and tests persistence against:

```text
sales_analytics.db
```

---

## 💡 Demo Dataset

The repository includes a representative demo dataset:

[`data/demo/demo_sales.csv`](data/demo/demo_sales.csv)

The demo dataset contains multi-category and multi-region sales records suitable for demonstrating:

- Data ingestion
- Data-quality auditing
- KPI calculations
- Category analysis
- Regional analysis
- Product rankings
- Filtering
- Export

Users can also load the demo dataset directly from the application's upload interface.

---

## 🗄️ Database

The current application uses:

```text
SQLite
```

with:

```text
SQLAlchemy 2.0
```

and:

```text
Alembic
```

The baseline database schema is maintained through the Alembic migration:

```text
alembic/versions/0001_initial_schema.py
```

The database contains tables for:

- Datasets
- Sales records
- Data-quality logs
- KPI cache
- Alembic migration tracking

SQLite is appropriate for the current portfolio/demo deployment and single-instance architecture.

---

## 🔐 Configuration & Security

Runtime configuration is handled through environment variables using Pydantic Settings.

The repository provides:

```text
.env.example
```

Sensitive local configuration is excluded from Git using:

```text
.gitignore
```

The following runtime artifacts are intentionally ignored:

```text
.env
*.db
*.sqlite
*.sqlite3
uploads/
.venv/
```

This prevents local environment secrets, databases, uploaded files, and virtual environments from being committed to the repository.

---

## 🔮 Known Limitations & Future Scope

### Current Implementation

The current platform intentionally uses:

- SQLite
- Local filesystem storage
- Single-instance deployment
- Deterministic rule-based data cleaning
- Synchronous analytical processing

The current implementation is designed for portfolio evaluation, demonstrations, and small-to-medium sales datasets.

### Future Scope

#### Production Database

Migration to hosted PostgreSQL for:

- Multi-user workloads
- Higher concurrency
- Horizontal scalability
- Production-grade persistence

#### Cloud Object Storage

Integration with:

- AWS S3
- Google Cloud Storage

for scalable uploaded-file storage.

#### Authentication & Authorization

Future implementation could include:

- User authentication
- Role-based access control
- Dataset ownership
- Dataset sharing permissions

#### Automated Narrative Summaries

The platform could later generate natural-language summaries explaining:

- Revenue changes
- Profitability
- Top-performing products
- Regional performance
- Detected anomalies

#### Forecasting

Future analytical extensions could include:

- ARIMA
- Prophet
- Other time-series forecasting models

for projected:

- Revenue
- Sales volume
- Product demand

#### Advanced Machine Learning

Potential future improvements include machine-learning-assisted anomaly detection and more advanced analytical modeling.

---

## 👨‍💻 Author

**Yash Masurkar**

B.Sc. Computer Science

GitHub: https://github.com/YashMasurkar

---

## 📄 License

This project is developed as an academic and portfolio project for demonstrating practical skills in:

- Data Analytics
- Data Engineering
- Python
- FastAPI
- Pandas
- SQLAlchemy
- Database Design
- REST API Development
- Data Visualization
- Full-Stack Application Development