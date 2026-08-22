"""Vectorized KPI & Analytics Engine with strict Analytical Integrity and Graceful Degradation."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import numpy as np
import pandas as pd


@dataclass
class MonthlyTrendItem:
    period: str  # 'YYYY-MM'
    revenue: float
    profit: Optional[float] = None
    order_count: int = 0


@dataclass
class CategoryPerformanceItem:
    category: str
    revenue: float
    order_count: int
    revenue_share_pct: float
    profit: Optional[float] = None


@dataclass
class RegionalPerformanceItem:
    region: str
    revenue: float
    order_count: int
    revenue_share_pct: float


@dataclass
class ProductRankingItem:
    product_name: str
    revenue: float
    units_sold: Optional[int] = None
    order_count: int = 0


@dataclass
class KPISummary:
    # Financial metrics
    total_revenue: float
    total_cost: Optional[float]
    total_profit: Optional[float]
    profit_margin_pct: Optional[float]
    
    # Volume metrics
    total_orders: int
    total_units_sold: Optional[int]
    total_unique_customers: Optional[int]
    average_order_value: float
    
    # Trend metrics
    mom_revenue_growth_pct: Optional[float]
    monthly_trends: List[MonthlyTrendItem] = field(default_factory=list)
    
    # Segment metrics
    category_performance: Optional[List[CategoryPerformanceItem]] = None
    regional_performance: Optional[List[RegionalPerformanceItem]] = None
    top_products: Optional[List[ProductRankingItem]] = None
    bottom_products: Optional[List[ProductRankingItem]] = None
    
    # Dimension availability flags
    available_metrics: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "financials": {
                "total_revenue": round(self.total_revenue, 2),
                "total_cost": round(self.total_cost, 2) if self.total_cost is not None else None,
                "total_profit": round(self.total_profit, 2) if self.total_profit is not None else None,
                "profit_margin_pct": round(self.profit_margin_pct, 2) if self.profit_margin_pct is not None else None,
            },
            "volumes": {
                "total_orders": self.total_orders,
                "total_units_sold": self.total_units_sold,
                "total_unique_customers": self.total_unique_customers,
                "average_order_value": round(self.average_order_value, 2),
            },
            "trends": {
                "mom_revenue_growth_pct": round(self.mom_revenue_growth_pct, 2) if self.mom_revenue_growth_pct is not None else None,
                "monthly_trends": [
                    {
                        "period": t.period,
                        "revenue": round(t.revenue, 2),
                        "profit": round(t.profit, 2) if t.profit is not None else None,
                        "order_count": t.order_count,
                    }
                    for t in self.monthly_trends
                ],
            },
            "segments": {
                "category_performance": [
                    {
                        "category": c.category,
                        "revenue": round(c.revenue, 2),
                        "order_count": c.order_count,
                        "revenue_share_pct": round(c.revenue_share_pct, 2),
                        "profit": round(c.profit, 2) if c.profit is not None else None,
                    }
                    for c in (self.category_performance or [])
                ] if self.category_performance is not None else None,
                "regional_performance": [
                    {
                        "region": r.region,
                        "revenue": round(r.revenue, 2),
                        "order_count": r.order_count,
                        "revenue_share_pct": round(r.revenue_share_pct, 2),
                    }
                    for r in (self.regional_performance or [])
                ] if self.regional_performance is not None else None,
                "top_products": [
                    {
                        "product_name": p.product_name,
                        "revenue": round(p.revenue, 2),
                        "units_sold": p.units_sold,
                        "order_count": p.order_count,
                    }
                    for p in (self.top_products or [])
                ] if self.top_products is not None else None,
                "bottom_products": [
                    {
                        "product_name": p.product_name,
                        "revenue": round(p.revenue, 2),
                        "units_sold": p.units_sold,
                        "order_count": p.order_count,
                    }
                    for p in (self.bottom_products or [])
                ] if self.bottom_products is not None else None,
            },
            "available_metrics": self.available_metrics,
        }


class KPIEngine:
    """Vectorized calculation of sales analytics KPIs using Pandas & NumPy."""

    def calculate(
        self,
        df: pd.DataFrame,
        available_dims: Dict[str, bool],
    ) -> KPISummary:
        """Calculate high-level KPIs and segmented metrics on cleaned DataFrame."""
        if df.empty:
            return KPISummary(
                total_revenue=0.0,
                total_cost=None,
                total_profit=None,
                profit_margin_pct=None,
                total_orders=0,
                total_units_sold=None,
                total_unique_customers=None,
                average_order_value=0.0,
                mom_revenue_growth_pct=None,
                available_metrics={k: False for k in available_dims},
            )

        # 1. Financial KPIs
        total_revenue = float(df["total_revenue"].sum())

        has_cost = available_dims.get("has_cost", False) and ("total_cost" in df.columns) and df["total_cost"].notna().any()
        total_cost: Optional[float] = float(df["total_cost"].sum()) if has_cost else None

        has_profit = available_dims.get("has_profit", False) and ("profit" in df.columns) and df["profit"].notna().any()
        total_profit: Optional[float] = float(df["profit"].sum()) if has_profit else None

        profit_margin_pct: Optional[float] = None
        if total_profit is not None and total_revenue > 0:
            profit_margin_pct = (total_profit / total_revenue) * 100.0

        # 2. Volume KPIs
        has_order_id = "order_id" in df.columns and df["order_id"].notna().any()
        if has_order_id:
            total_orders = int(df["order_id"].nunique())
        else:
            total_orders = len(df)

        has_quantity = available_dims.get("has_quantity", False) and ("quantity" in df.columns) and df["quantity"].notna().any()
        total_units_sold: Optional[int] = int(df["quantity"].sum()) if has_quantity else None

        has_customer = available_dims.get("has_customer", False) and ("customer_id" in df.columns) and df["customer_id"].notna().any()
        total_unique_customers: Optional[int] = int(df["customer_id"].nunique()) if has_customer else None

        average_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0.0

        # 3. Monthly Trends & MoM Growth
        monthly_trends: List[MonthlyTrendItem] = []
        mom_growth_pct: Optional[float] = None

        if "order_date" in df.columns and df["order_date"].notna().any():
            df_trend = df.copy()
            df_trend["period"] = pd.to_datetime(df_trend["order_date"]).dt.to_period("M").astype(str)
            
            agg_dict: Dict[str, Any] = {"total_revenue": "sum"}
            if has_profit:
                agg_dict["profit"] = "sum"
            if has_order_id:
                agg_dict["order_id"] = "nunique"
            else:
                agg_dict["total_revenue"] = ["sum", "count"]

            grouped = df_trend.groupby("period")
            
            for period_str, group in grouped:
                rev = float(group["total_revenue"].sum())
                prof = float(group["profit"].sum()) if has_profit else None
                ords = int(group["order_id"].nunique()) if has_order_id else len(group)
                monthly_trends.append(MonthlyTrendItem(
                    period=str(period_str),
                    revenue=rev,
                    profit=prof,
                    order_count=ords,
                ))

            # Sort chronological
            monthly_trends.sort(key=lambda x: x.period)

            # Calculate Month-over-Month (MoM) growth if >= 2 periods
            if len(monthly_trends) >= 2:
                prev_rev = monthly_trends[-2].revenue
                curr_rev = monthly_trends[-1].revenue
                if prev_rev > 0:
                    mom_growth_pct = ((curr_rev - prev_rev) / prev_rev) * 100.0

        # 4. Category Performance
        category_perf: Optional[List[CategoryPerformanceItem]] = None
        has_category = available_dims.get("has_category", False) and ("category" in df.columns)
        if has_category:
            cat_grouped = df.groupby("category")
            items = []
            for cat_name, group in cat_grouped:
                cat_rev = float(group["total_revenue"].sum())
                cat_orders = int(group["order_id"].nunique()) if has_order_id else len(group)
                cat_share = (cat_rev / total_revenue * 100.0) if total_revenue > 0 else 0.0
                cat_prof = float(group["profit"].sum()) if has_profit else None
                items.append(CategoryPerformanceItem(
                    category=str(cat_name),
                    revenue=cat_rev,
                    order_count=cat_orders,
                    revenue_share_pct=cat_share,
                    profit=cat_prof,
                ))
            items.sort(key=lambda x: x.revenue, reverse=True)
            category_perf = items

        # 5. Regional Performance
        regional_perf: Optional[List[RegionalPerformanceItem]] = None
        has_region = available_dims.get("has_region", False) and ("region" in df.columns)
        if has_region:
            reg_grouped = df.groupby("region")
            items = []
            for reg_name, group in reg_grouped:
                reg_rev = float(group["total_revenue"].sum())
                reg_orders = int(group["order_id"].nunique()) if has_order_id else len(group)
                reg_share = (reg_rev / total_revenue * 100.0) if total_revenue > 0 else 0.0
                items.append(RegionalPerformanceItem(
                    region=str(reg_name),
                    revenue=reg_rev,
                    order_count=reg_orders,
                    revenue_share_pct=reg_share,
                ))
            items.sort(key=lambda x: x.revenue, reverse=True)
            regional_perf = items

        # 6. Product Rankings
        top_products: Optional[List[ProductRankingItem]] = None
        bottom_products: Optional[List[ProductRankingItem]] = None
        has_product = available_dims.get("has_product", False) and (
            ("product_name" in df.columns) or ("product_id" in df.columns)
        )
        if has_product:
            prod_col = "product_name" if "product_name" in df.columns else "product_id"
            prod_grouped = df.groupby(prod_col)
            items = []
            for p_name, group in prod_grouped:
                p_rev = float(group["total_revenue"].sum())
                p_units = int(group["quantity"].sum()) if has_quantity else None
                p_orders = int(group["order_id"].nunique()) if has_order_id else len(group)
                items.append(ProductRankingItem(
                    product_name=str(p_name),
                    revenue=p_rev,
                    units_sold=p_units,
                    order_count=p_orders,
                ))
            items.sort(key=lambda x: x.revenue, reverse=True)
            top_products = items[:10]
            bottom_products = items[-5:] if len(items) >= 5 else items

        # Available metrics summary flags
        available_metrics = {
            "revenue": True,
            "cost": has_cost,
            "profit": has_profit,
            "profit_margin": profit_margin_pct is not None,
            "orders": True,
            "units_sold": has_quantity,
            "unique_customers": has_customer,
            "average_order_value": True,
            "mom_growth": mom_growth_pct is not None,
            "category_analysis": category_perf is not None,
            "regional_analysis": regional_perf is not None,
            "product_ranking": top_products is not None,
        }

        return KPISummary(
            total_revenue=total_revenue,
            total_cost=total_cost,
            total_profit=total_profit,
            profit_margin_pct=profit_margin_pct,
            total_orders=total_orders,
            total_units_sold=total_units_sold,
            total_unique_customers=total_unique_customers,
            average_order_value=average_order_value,
            mom_revenue_growth_pct=mom_growth_pct,
            monthly_trends=monthly_trends,
            category_performance=category_perf,
            regional_performance=regional_perf,
            top_products=top_products,
            bottom_products=bottom_products,
            available_metrics=available_metrics,
        )
