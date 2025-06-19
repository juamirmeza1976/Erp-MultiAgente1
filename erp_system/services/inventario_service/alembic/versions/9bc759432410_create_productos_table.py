"""create_productos_table

Revision ID: 9bc759432410
Revises:
Create Date: 2025-06-19 00:44:40.247180

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql # For UUID type


# revision identifiers, used by Alembic.
revision: str = '9bc759432410'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'productos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")), # Or use uuid.uuid4 if server_default is not preferred for some reason and handle in app. For now, using a PG function.
        sa.Column('nombre', sa.String(), nullable=False, index=True),
        sa.Column('descripcion', sa.String(), nullable=True),
        sa.Column('precio_costo', sa.Float(), nullable=False),
        sa.Column('precio_venta', sa.Float(), nullable=False),
        sa.Column('stock_actual', sa.Integer(), nullable=False, default=0),
        sa.Column('categoria', sa.String(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('productos')
