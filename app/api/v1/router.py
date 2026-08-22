from fastapi import APIRouter
from app.api.v1.endpoints import health, upload, datasets, analytics, export

api_v1_router = APIRouter()

# Register endpoint routers
api_v1_router.include_router(health.router, prefix="", tags=["Health"])
api_v1_router.include_router(upload.router, prefix="", tags=["Upload & Ingestion"])
api_v1_router.include_router(datasets.router, prefix="", tags=["Datasets"])
api_v1_router.include_router(analytics.router, prefix="", tags=["Analytics & KPIs"])
api_v1_router.include_router(export.router, prefix="", tags=["Export"])
