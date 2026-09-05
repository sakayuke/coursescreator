"""Add assignments and submissions

Revision ID: 58ccea599b98
Revises: 3a81cdcf5154
Create Date: 2026-09-05 16:00:53.505137

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "58ccea599b98"
down_revision = "3a81cdcf5154"
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "assignments",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "topic_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["dbo.topics.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="dbo",
    )

    op.create_table(
        "submissions",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "assignment_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "grade",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "feedback",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "submitted_at",
            sa.DateTime(),
            server_default=sa.text("getdate()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["dbo.assignments.id"],
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["dbo.users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="dbo",
    )


def downgrade():

    op.drop_table(
        "submissions",
        schema="dbo",
    )

    op.drop_table(
        "assignments",
        schema="dbo",
    )