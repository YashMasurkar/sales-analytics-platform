"""Endpoint for exporting cleaned analytical dataset as CSV."""

import io
import csv
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Dataset, SalesRecord

router = APIRouter()


@router.get(
    "/export/{id}/cleaned",
    summary="Export Cleaned Dataset CSV",
    description="Download the validated, cleansed analytical sales dataset as a standard CSV file.",
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "Cleaned CSV file download",
        },
        404: {"description": "Dataset not found"},
    },
)
def export_cleaned_csv(
    id: str,
    db: Session = Depends(get_db),
) -> Response:
    """Generate and return cleaned dataset CSV attachment."""
    dataset = db.query(Dataset).filter(Dataset.id == id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{id}' not found.")

    records = (
        db.query(SalesRecord)
        .filter(SalesRecord.dataset_id == id)
        .order_by(SalesRecord.order_date.asc(), SalesRecord.id.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Header columns (business analytical fields only, omitting internal database keys)
    headers = [
        "order_date",
        "order_id",
        "customer_id",
        "customer_name",
        "product_id",
        "product_name",
        "category",
        "sub_category",
        "region",
        "quantity",
        "unit_price",
        "discount",
        "total_revenue",
        "total_cost",
        "profit",
    ]
    writer.writerow(headers)

    for r in records:
        writer.writerow([
            r.order_date.isoformat() if r.order_date else "",
            r.order_id or "",
            r.customer_id or "",
            r.customer_name or "",
            r.product_id or "",
            r.product_name or "",
            r.category or "",
            r.sub_category or "",
            r.region or "",
            r.quantity if r.quantity is not None else "",
            f"{r.unit_price:.2f}" if r.unit_price is not None else "",
            f"{r.discount:.4f}" if r.discount is not None else "",
            f"{r.total_revenue:.2f}",
            f"{r.total_cost:.2f}" if r.total_cost is not None else "",
            f"{r.profit:.2f}" if r.profit is not None else "",
        ])

    csv_content = output.getvalue()
    clean_name = dataset.filename.rsplit(".", 1)[0] if "." in dataset.filename else dataset.filename
    export_filename = f"cleaned_{clean_name}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{export_filename}"',
            "Content-Type": "text/csv; charset=utf-8",
        },
    )
