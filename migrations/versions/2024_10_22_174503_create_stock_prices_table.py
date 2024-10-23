"""create stock_prices table

Revision ID: e7d2b7c2871f
Revises: c6b516e182b2
Create Date: 2024-10-22 17:45:03.909055

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7d2b7c2871f'
down_revision: Union[str, None] = 'c6b516e182b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Create stock_prices table
    op.create_table(
        'stock_prices',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('stock_symbol', sa.String(length=10), nullable=False),
        sa.Column('stock_price', sa.Numeric(10, 2), nullable=False),
        sa.Column(
            'timestamp',
            sa.TIMESTAMP,
            server_default=sa.func.current_timestamp(),
            nullable=False
        )
    )

def downgrade():
    # Drop stock_prices table
    op.drop_table('stock_prices')
