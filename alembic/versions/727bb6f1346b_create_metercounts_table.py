"""create metercounts table

Revision ID: 727bb6f1346b
Revises: 
Create Date: 2022-12-02 20:51:13.115442

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '727bb6f1346b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
        op.create_table(
        # period state stateName technology sector sectorName meters units
        'metercount',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('period', sa.Integer, nullable=False),
        sa.Column('state', sa.String(2), nullable=False),
        sa.Column('stateName', sa.String(50), nullable=True),
        sa.Column('technology', sa.String(50), nullable=True),
        sa.Column('sector', sa.String(50), nullable=True),
        sa.Column('sectorName', sa.String(80), nullable=True),
        sa.Column('meterCount', sa.Integer, nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('metercount')
