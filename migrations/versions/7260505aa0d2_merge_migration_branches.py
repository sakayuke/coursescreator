"""Merge migration branches

Revision ID: 7260505aa0d2
Revises: 58ccea599b98, c1b7d3e4f509
Create Date: 2026-09-11 13:38:21.759988

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7260505aa0d2'
down_revision = ('58ccea599b98', 'c1b7d3e4f509')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
