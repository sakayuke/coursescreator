"""Track when a student opens an assignment

Revision ID: b08f31c79d4e
Revises: 7260505aa0d2
Create Date: 2026-09-17
"""

from alembic import op


revision = "b08f31c79d4e"
down_revision = "7260505aa0d2"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "IF OBJECT_ID(N'dbo.assignment_views', N'U') IS NULL "
        "BEGIN "
        "CREATE TABLE dbo.assignment_views ("
        "assignment_id INT NOT NULL, "
        "student_id INT NOT NULL, "
        "viewed_at DATETIME NOT NULL DEFAULT GETDATE(), "
        "CONSTRAINT PK_assignment_views PRIMARY KEY "
        "(assignment_id, student_id), "
        "CONSTRAINT FK_assignment_views_assignment FOREIGN KEY "
        "(assignment_id) REFERENCES dbo.assignments(id), "
        "CONSTRAINT FK_assignment_views_student FOREIGN KEY "
        "(student_id) REFERENCES dbo.users(id)"
        "); END"
    )


def downgrade():
    op.execute(
        "IF OBJECT_ID(N'dbo.assignment_views', N'U') IS NOT NULL "
        "BEGIN DROP TABLE dbo.assignment_views; END"
    )
