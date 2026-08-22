"""Tests for Vectorized KPI Calculation Engine and Graceful Degradation on Incomplete Schemas."""

import pandas as pd
import numpy as np
import pytest

from app.core.kpi_engine import KPIEngine


def test_kpi_engine_full_dataset_calculations():
    """Verify exact mathematical calculations when all dimensions (cost, customer, category, region, product) are present."""
    data = {
        "order_id": ["ORD-1", "ORD-1", "ORD-2", "ORD-3"],
        "order_date": pd.to_datetime(["2024-01-15", "2024-01-15", "2024-02-10", "2024-02-20"]),
        "customer_id": ["CUST-1", "CUST-1", "CUST-2", "CUST-3"],
        "product_name": ["Mouse", "Keyboard", "Mouse", "Monitor"],
        "category": ["Electronics", "Electronics", "Electronics", "Displays"],
        "region": ["North", "North", "South", "North"],
        "quantity": [2, 1, 1, 1],
        "total_revenue": [50.0, 100.0, 25.0, 300.0],  # Total = 475.0
        "total_cost": [30.0, 60.0, 15.0, 180.0],       # Total = 285.0
        "profit": [20.0, 40.0, 10.0, 120.0],           # Total = 190.0
    }
    df = pd.DataFrame(data)
    available_dims = {
        "has_cost": True,
        "has_profit": True,
        "has_customer": True,
        "has_category": True,
        "has_region": True,
        "has_product": True,
        "has_quantity": True,
        "has_order_id": True,
    }

    engine = KPIEngine()
    kpi = engine.calculate(df, available_dims)

    # Financials
    assert kpi.total_revenue == 475.0
    assert kpi.total_cost == 285.0
    assert kpi.total_profit == 190.0
    assert pytest.approx(kpi.profit_margin_pct, 0.01) == (190.0 / 475.0) * 100.0  # 40.0%

    # Volumes
    assert kpi.total_orders == 3  # Distinct order IDs: ORD-1, ORD-2, ORD-3
    assert kpi.total_units_sold == 5  # 2 + 1 + 1 + 1
    assert kpi.total_unique_customers == 3  # CUST-1, CUST-2, CUST-3
    assert pytest.approx(kpi.average_order_value, 0.01) == 475.0 / 3

    # Monthly Trends
    assert len(kpi.monthly_trends) == 2  # 2024-01 and 2024-02
    assert kpi.monthly_trends[0].period == "2024-01"
    assert kpi.monthly_trends[0].revenue == 150.0  # 50 + 100
    assert kpi.monthly_trends[1].period == "2024-02"
    assert kpi.monthly_trends[1].revenue == 325.0  # 25 + 300

    # MoM Growth: (325 - 150) / 150 * 100 = 116.67%
    assert pytest.approx(kpi.mom_revenue_growth_pct, 0.01) == ((325.0 - 150.0) / 150.0) * 100.0

    # Category Performance
    assert kpi.category_performance is not None
    assert len(kpi.category_performance) == 2
    # Displays (300.0) > Electronics (175.0)
    assert kpi.category_performance[0].category == "Displays"
    assert kpi.category_performance[0].revenue == 300.0
    assert pytest.approx(kpi.category_performance[0].revenue_share_pct, 0.01) == (300.0 / 475.0) * 100.0

    # Regional Performance
    assert kpi.regional_performance is not None
    assert len(kpi.regional_performance) == 2
    # North (450.0) > South (25.0)
    assert kpi.regional_performance[0].region == "North"
    assert kpi.regional_performance[0].revenue == 450.0

    # Product Rankings
    assert kpi.top_products is not None
    assert kpi.top_products[0].product_name == "Monitor"
    assert kpi.top_products[0].revenue == 300.0


def test_kpi_engine_graceful_degradation_no_cost():
    """Verify that profit and profit margin are None and marked unavailable when cost is not present."""
    data = {
        "order_date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
        "total_revenue": [100.0, 200.0],
    }
    df = pd.DataFrame(data)
    available_dims = {
        "has_cost": False,
        "has_profit": False,
        "has_customer": False,
        "has_category": False,
        "has_region": False,
        "has_product": False,
        "has_quantity": False,
        "has_order_id": False,
    }

    engine = KPIEngine()
    kpi = engine.calculate(df, available_dims)

    assert kpi.total_revenue == 300.0
    assert kpi.total_cost is None
    assert kpi.total_profit is None
    assert kpi.profit_margin_pct is None
    assert kpi.total_unique_customers is None
    assert kpi.category_performance is None
    assert kpi.regional_performance is None
    assert kpi.top_products is None

    assert kpi.available_metrics["profit"] is False
    assert kpi.available_metrics["profit_margin"] is False
    assert kpi.available_metrics["category_analysis"] is False
    assert kpi.available_metrics["regional_analysis"] is False
    assert kpi.available_metrics["product_ranking"] is False


def test_kpi_engine_empty_dataframe():
    """Verify that an empty DataFrame returns zeroed revenue and safe default structures without crashing."""
    df = pd.DataFrame()
    available_dims = {}
    engine = KPIEngine()
    kpi = engine.calculate(df, available_dims)

    assert kpi.total_revenue == 0.0
    assert kpi.total_orders == 0
    assert kpi.average_order_value == 0.0
    assert kpi.mom_revenue_growth_pct is None
