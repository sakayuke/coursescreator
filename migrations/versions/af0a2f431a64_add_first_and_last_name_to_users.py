"""Add first and last name to users

Revision ID: af0a2f431a64
Revises: 721c2ce763cd
Create Date: 2026-09-05 13:19:05.567558
"""

from alembic import op
import sqlalchemy as sa


revision = "af0a2f431a64"
down_revision = "721c2ce763cd"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("first_name", sa.String(100), nullable=True),
        schema="dbo",
    )

    op.add_column(
        "users",
        sa.Column("last_name", sa.String(100), nullable=True),
        schema="dbo",
    )

    op.execute(
        "UPDATE dbo.users "
        "SET first_name = 'Unknown', last_name = 'User' "
        "WHERE first_name IS NULL OR last_name IS NULL"
    )

    op.alter_column(
        "users",
        "first_name",
        existing_type=sa.String(100),
        nullable=False,
        schema="dbo",
    )

    op.alter_column(
        "users",
        "last_name",
        existing_type=sa.String(100),
        nullable=False,
        schema="dbo",
    )


def downgrade():
    op.drop_column(
        "users",
        "last_name",
        schema="dbo",
    )

    op.drop_column(
        "users",
        "first_name",
        schema="dbo",
    )