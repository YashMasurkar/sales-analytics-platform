"""initial_baseline_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-22 20:36:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema to initial baseline."""
    # 1. Create datasets table
    op.create_table(
        'datasets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_format', sa.String(length=10), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=True),
        sa.Column('total_raw_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_cleaned_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('available_dimensions', sa.JSON(), nullable=True),
        sa.Column('upload_timestamp', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='processing'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('datasets', schema=None) as batch_op:
        batch_op.create_index('ix_datasets_id', ['id'], unique=False)

    # 2. Create sales_records table
    op.create_table(
        'sales_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dataset_id', sa.String(length=36), nullable=False),
        sa.Column('order_id', sa.String(length=100), nullable=True),
        sa.Column('order_date', sa.Date(), nullable=False),
        sa.Column('customer_id', sa.String(length=100), nullable=True),
        sa.Column('customer_name', sa.String(length=255), nullable=True),
        sa.Column('product_id', sa.String(length=100), nullable=True),
        sa.Column('product_name', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('sub_category', sa.String(length=100), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('discount', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('total_revenue', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('profit', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('sales_records', schema=None) as batch_op:
        batch_op.create_index('ix_sales_records_category', ['category'], unique=False)
        batch_op.create_index('ix_sales_records_customer_id', ['customer_id'], unique=False)
        batch_op.create_index('ix_sales_records_dataset_id', ['dataset_id'], unique=False)
        batch_op.create_index('ix_sales_records_order_date', ['order_date'], unique=False)
        batch_op.create_index('ix_sales_records_order_id', ['order_id'], unique=False)
        batch_op.create_index('ix_sales_records_product_id', ['product_id'], unique=False)
        batch_op.create_index('ix_sales_records_region', ['region'], unique=False)

    # 3. Create data_quality_logs table
    op.create_table(
        'data_quality_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dataset_id', sa.String(length=36), nullable=False),
        sa.Column('total_raw_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('valid_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('excluded_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duplicate_rows_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('exact_duplicates_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('missing_values_by_field', sa.JSON(), nullable=True),
        sa.Column('missing_values_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('invalid_dates_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('invalid_numerics_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('type_coercions_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('derived_value_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('anomalies_detected', sa.JSON(), nullable=True),
        sa.Column('exclusion_reasons', sa.JSON(), nullable=True),
        sa.Column('health_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('changelog_summary', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dataset_id')
    )
    with op.batch_alter_table('data_quality_logs', schema=None) as batch_op:
        batch_op.create_index('ix_data_quality_logs_dataset_id', ['dataset_id'], unique=True)
        batch_op.create_index('ix_data_quality_logs_id', ['id'], unique=False)

    # 4. Create kpi_cache table
    op.create_table(
        'kpi_cache',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dataset_id', sa.String(length=36), nullable=False),
        sa.Column('metric_key', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.JSON(), nullable=False),
        sa.Column('calculated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('kpi_cache', schema=None) as batch_op:
        batch_op.create_index('ix_kpi_cache_dataset_id', ['dataset_id'], unique=False)
        batch_op.create_index('ix_kpi_cache_id', ['id'], unique=False)
        batch_op.create_index('ix_kpi_cache_metric_key', ['metric_key'], unique=False)


def downgrade() -> None:
    """Downgrade database schema by dropping tables in reverse order."""
    op.drop_table('kpi_cache')
    op.drop_table('data_quality_logs')
    op.drop_table('sales_records')
    op.drop_table('datasets')
