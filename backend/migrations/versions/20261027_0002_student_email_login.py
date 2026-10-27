"""Acceso opcional de estudiantes por correo, compatible con código/PIN.

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_email_logins",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_student_email_login_email"),
    )
    op.create_index("ix_student_email_logins_email", "student_email_logins", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_student_email_logins_email", table_name="student_email_logins")
    op.drop_table("student_email_logins")
