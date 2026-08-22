from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class KPIFinancials(BaseModel):
    total_revenue: float
    total_cost: Optional[float] = None
    total_profit: Optional[float] = None
    profit_margin_pct: Optional[float] = None


class KPIVolumes(BaseModel):
    total_orders: int
    total_units_sold: Optional[int] = None
    total_unique_customers: Optional[int] = None
    average_order_value: float


class KPIResponse(BaseModel):
    financials: KPIFinancials
    volumes: KPIVolumes
    mom_revenue_growth_pct: Optional[float] = None
    available_metrics: Dict[str, bool]


class TrendItem(BaseModel):
    period: str
    revenue: float
    profit: Optional[float] = None
    order_count: int


class TrendsResponse(BaseModel):
    available: bool
    trends: List[TrendItem]
    mom_growth_pct: Optional[float] = None


class CategoryItem(BaseModel):
    category: str
    revenue: float
    order_count: int
    revenue_share_pct: float
    profit: Optional[float] = None


class CategoriesResponse(BaseModel):
    available: bool
    categories: List[CategoryItem]


class RegionItem(BaseModel):
    region: str
    revenue: float
    order_count: int
    revenue_share_pct: float


class RegionsResponse(BaseModel):
    available: bool
    regions: List[RegionItem]


class ProductItem(BaseModel):
    product_name: str
    revenue: float
    units_sold: Optional[int] = None
    order_count: int


class ProductsResponse(BaseModel):
    available: bool
    top_products: List[ProductItem]
    bottom_products: List[ProductItem]


class FilterOptionsResponse(BaseModel):
    min_date: Optional[str] = None
    max_date: Optional[str] = None
    categories: List[str]
    regions: List[str]
