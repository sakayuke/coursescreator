"""Track when a student viewed a graded submission

Revision ID: c1b7d3e4f509
Revises: af0a2f431a64
Create Date: 2026-09-11
"""

from alembic import op
import sqlalchemy as sa


revision = "c1b7d3e4f509"
down_revision = "af0a2f431a64"
branch_labels = None
depends_on = None


def upgrade():
    # Keep this migration safe to rerun after a manual hotfix in SQL Server.
    op.execute(
        "IF COL_LENGTH('dbo.submissions', 'grade_seen_at') IS NULL "
        "BEGIN ALTER TABLE dbo.submissions "
        "ADD grade_seen_at DATETIME NULL; END"
    )


def downgrade():
    op.execute(
        "IF COL_LENGTH('dbo.submissions', 'grade_seen_at') IS NOT NULL "
        "BEGIN ALTER TABLE dbo.submissions "
        "DROP COLUMN grade_seen_at; END"
    )
