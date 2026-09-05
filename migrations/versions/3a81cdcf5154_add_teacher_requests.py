"""Add teacher requests

Revision ID: 3a81cdcf5154
Revises: af0a2f431a64
Create Date: 2026-09-05 15:04:10.943307

"""
from alembic import op
import sqlalchemy as sa


revision = "3a81cdcf5154"
down_revision = "af0a2f431a64"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "teacher_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("experience", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("getdate()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["dbo.users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="dbo",
    )


def downgrade():
    op.drop_table("teacher_requests", schema="dbo")