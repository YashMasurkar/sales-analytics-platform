"""Analytics & KPI endpoints with dynamic filtering, trend analysis, and graceful degradation."""

from datetime import date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
import pandas as pd

from app.api.deps import get_db
from app.db.models import Dataset, SalesRecord
from app.core.kpi_engine import KPIEngine
from app.schemas.analytics import (
    KPIResponse,
    KPIFinancials,
    KPIVolumes,
    TrendsResponse,
    TrendItem,
    CategoriesResponse,
    CategoryItem,
    RegionsResponse,
    RegionItem,
    ProductsResponse,
    ProductItem,
    FilterOptionsResponse,
)

router = APIRouter()
kpi_engine = KPIEngine()


def parse_and_validate_date(date_str: Optional[str], param_name: str) -> Optional[date]:
    """Parse an ISO date string (YYYY-MM-DD) or raise HTTP 422."""
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str.strip())
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid {param_name} format '{date_str}'. Expected ISO format 'YYYY-MM-DD'.",
        )


def query_filtered_dataframe(
    dataset_id: str,
    start_date: Optional[str],
    end_date: Optional[str],
    category: Optional[str],
    region: Optional[str],
    db: Session,
) -> tuple[pd.DataFrame, Dict[str, bool]]:
    """Fetch dataset, apply parameterized filters, and return a Pandas DataFrame with dimension flags."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    parsed_start = parse_and_validate_date(start_date, "start_date")
    parsed_end = parse_and_validate_date(end_date, "end_date")

    if parsed_start and parsed_end and parsed_start > parsed_end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"start_date ({start_date}) cannot be after end_date ({end_date}).",
        )

    query = db.query(SalesRecord).filter(SalesRecord.dataset_id == dataset_id)

    if parsed_start:
        query = query.filter(SalesRecord.order_date >= parsed_start)
    if parsed_end:
        query = query.filter(SalesRecord.order_date <= parsed_end)
    if category:
        query = query.filter(SalesRecord.category == category.strip())
    if region:
        query = query.filter(SalesRecord.region == region.strip())

    records = query.all()
    available_dims = dataset.available_dimensions or {}

    if not records:
        return pd.DataFrame(), available_dims

    data = [
        {
            "order_id": r.order_id,
            "order_date": pd.to_datetime(r.order_date),
            "customer_id": r.customer_id,
            "customer_name": r.customer_name,
            "product_id": r.product_id,
            "product_name": r.product_name,
            "category": r.category,
            "sub_category": r.sub_category,
            "region": r.region,
            "quantity": r.quantity,
            "unit_price": r.unit_price,
            "discount": r.discount,
            "total_revenue": r.total_revenue,
            "total_cost": r.total_cost,
            "profit": r.profit,
        }
        for r in records
    ]
    return pd.DataFrame(data), available_dims


@router.get(
    "/analytics/{id}/kpis",
    response_model=KPIResponse,
    summary="Get Executive KPI Metrics",
    description="Calculate top-level financial, volume, and growth KPIs for a dataset with optional multidimensional filters.",
)
def get_kpis(
    id: str,
    start_date: Optional[str] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter end date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filter by Category"),
    region: Optional[str] = Query(None, description="Filter by Region"),
    db: Session = Depends(get_db),
) -> KPIResponse:
    """Compute executive KPI cards."""
    df, available_dims = query_filtered_dataframe(id, start_date, end_date, category, region, db)
    kpis = kpi_engine.calculate(df, available_dims)

    return KPIResponse(
        financials=KPIFinancials(
            total_revenue=kpis.total_revenue,
            total_cost=kpis.total_cost,
            total_profit=kpis.total_profit,
            profit_margin_pct=kpis.profit_margin_pct,
        ),
        volumes=KPIVolumes(
            total_orders=kpis.total_orders,
            total_units_sold=kpis.total_units_sold,
            total_unique_customers=kpis.total_unique_customers,
            average_order_value=kpis.average_order_value,
        ),
        mom_revenue_growth_pct=kpis.mom_revenue_growth_pct,
        available_metrics=kpis.available_metrics,
    )


@router.get(
    "/analytics/{id}/trends",
    response_model=TrendsResponse,
    summary="Get Time-Series Revenue & Profit Trends",
    description="Retrieve chronological monthly aggregated revenue, profit, and order volume metrics.",
)
def get_trends(
    id: str,
    start_date: Optional[str] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter end date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filter by Category"),
    region: Optional[str] = Query(None, description="Filter by Region"),
    db: Session = Depends(get_db),
) -> TrendsResponse:
    """Retrieve monthly trend time-series."""
    df, available_dims = query_filtered_dataframe(id, start_date, end_date, category, region, db)
    kpis = kpi_engine.calculate(df, available_dims)

    trend_items = [
        TrendItem(
            period=t.period,
            revenue=t.revenue,
            profit=t.profit,
            order_count=t.order_count,
        )
        for t in kpis.monthly_trends
    ]

    return TrendsResponse(
        available=len(trend_items) > 0,
        trends=trend_items,
        mom_growth_pct=kpis.mom_revenue_growth_pct,
    )


@router.get(
    "/analytics/{id}/categories",
    response_model=CategoriesResponse,
    summary="Get Category Performance Breakdown",
    description="Retrieve revenue, order count, and revenue share grouped by category.",
)
def get_categories(
    id: str,
    start_date: Optional[str] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter end date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filter by Category"),
    region: Optional[str] = Query(None, description="Filter by Region"),
    db: Session = Depends(get_db),
) -> CategoriesResponse:
    """Retrieve category performance breakdown."""
    df, available_dims = query_filtered_dataframe(id, start_date, end_date, category, region, db)
    kpis = kpi_engine.calculate(df, available_dims)

    if kpis.category_performance is None:
        return CategoriesResponse(available=False, categories=[])

    items = [
        CategoryItem(
            category=c.category,
            revenue=c.revenue,
            order_count=c.order_count,
            revenue_share_pct=c.revenue_share_pct,
            profit=c.profit,
        )
        for c in kpis.category_performance
    ]
    return CategoriesResponse(available=True, categories=items)


@router.get(
    "/analytics/{id}/regions",
    response_model=RegionsResponse,
    summary="Get Regional Sales Performance",
    description="Retrieve revenue, order volume, and revenue share grouped by region.",
)
def get_regions(
    id: str,
    start_date: Optional[str] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter end date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filter by Category"),
    region: Optional[str] = Query(None, description="Filter by Region"),
    db: Session = Depends(get_db),
) -> RegionsResponse:
    """Retrieve regional performance breakdown."""
    df, available_dims = query_filtered_dataframe(id, start_date, end_date, category, region, db)
    kpis = kpi_engine.calculate(df, available_dims)

    if kpis.regional_performance is None:
        return RegionsResponse(available=False, regions=[])

    items = [
        RegionItem(
            region=r.region,
            revenue=r.revenue,
            order_count=r.order_count,
            revenue_share_pct=r.revenue_share_pct,
        )
        for r in kpis.regional_performance
    ]
    return RegionsResponse(available=True, regions=items)


@router.get(
    "/analytics/{id}/products",
    response_model=ProductsResponse,
    summary="Get Top & Bottom Product Rankings",
    description="Retrieve top 10 best-selling and bottom 5 underperforming products by revenue.",
)
def get_products(
    id: str,
    start_date: Optional[str] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter end date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filter by Category"),
    region: Optional[str] = Query(None, description="Filter by Region"),
    db: Session = Depends(get_db),
) -> ProductsResponse:
    """Retrieve product rankings."""
    df, available_dims = query_filtered_dataframe(id, start_date, end_date, category, region, db)
    kpis = kpi_engine.calculate(df, available_dims)

    if kpis.top_products is None or kpis.bottom_products is None:
        return ProductsResponse(available=False, top_products=[], bottom_products=[])

    top_items = [
        ProductItem(
            product_name=p.product_name,
            revenue=p.revenue,
            units_sold=p.units_sold,
            order_count=p.order_count,
        )
        for p in kpis.top_products
    ]
    bottom_items = [
        ProductItem(
            product_name=p.product_name,
            revenue=p.revenue,
            units_sold=p.units_sold,
            order_count=p.order_count,
        )
        for p in kpis.bottom_products
    ]
    return ProductsResponse(available=True, top_products=top_items, bottom_products=bottom_items)


@router.get(
    "/analytics/{id}/filter-options",
    response_model=FilterOptionsResponse,
    summary="Get Filter Options",
    description="Retrieve available date bounds, distinct categories, and regions for dynamic UI filtering.",
)
def get_filter_options(
    id: str,
    db: Session = Depends(get_db),
) -> FilterOptionsResponse:
    """Retrieve available filter dimensions."""
    dataset = db.query(Dataset).filter(Dataset.id == id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{id}' not found.")

    # Date bounds
    min_date, max_date = db.query(
        func.min(SalesRecord.order_date),
        func.max(SalesRecord.order_date),
    ).filter(SalesRecord.dataset_id == id).first()

    # Distinct categories
    categories = [
        c[0]
        for c in db.query(SalesRecord.category)
        .filter(SalesRecord.dataset_id == id, SalesRecord.category.isnot(None), SalesRecord.category != "Unspecified")
        .distinct()
        .order_by(SalesRecord.category)
        .all()
    ]

    # Distinct regions
    regions = [
        r[0]
        for r in db.query(SalesRecord.region)
        .filter(SalesRecord.dataset_id == id, SalesRecord.region.isnot(None), SalesRecord.region != "Unspecified")
        .distinct()
        .order_by(SalesRecord.region)
        .all()
    ]

    return FilterOptionsResponse(
        min_date=min_date.isoformat() if min_date else None,
        max_date=max_date.isoformat() if max_date else None,
        categories=categories,
        regions=regions,
    )
