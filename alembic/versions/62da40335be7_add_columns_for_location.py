"""Add columns for location

Revision ID: 62da40335be7
Revises: 727bb6f1346b
Create Date: 2022-12-04 20:28:14.713488

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '62da40335be7'
down_revision = '727bb6f1346b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('metercount', sa.Column('latitude', sa.Float)),
    op.add_column('metercount', sa.Column('longitude', sa.Float)),
    op.add_column('metercount', sa.Column('geohash', sa.String(50)))


def downgrade() -> None:
    op.drop_column('metercount', 'latitude'),
    op.drop_column('metercount', 'longitude'),
    op.drop_column('metercount', 'geohash')