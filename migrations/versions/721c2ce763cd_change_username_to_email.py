"""Change username to email

Revision ID: 721c2ce763cd
Revises: 163e0de02fb6
Create Date: 2026-09-04 19:19:39.472924
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "721c2ce763cd"
down_revision = "163e0de02fb6"
branch_labels = None
depends_on = None


def upgrade():
    # Rename existing column without deleting its data.
    op.execute(
        "EXEC sp_rename 'dbo.users.username', 'email', 'COLUMN'"
    )

    # Increase the column length from 100 to 255.
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=100),
        type_=sa.String(length=255),
        existing_nullable=False,
        schema="dbo",
    )


def downgrade():
    # Restore the original column name.
    op.execute(
        "EXEC sp_rename 'dbo.users.email', 'username', 'COLUMN'"
    )

    # Restore the original column length.
    op.alter_column(
        "users",
        "username",
        existing_type=sa.String(length=255),
        type_=sa.String(length=100),
        existing_nullable=False,
        schema="dbo",
    )