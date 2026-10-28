"""Documents by school/year/grade/area. Binary files stored in SQLite.

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "curriculum_documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("school_id", sa.Uuid(), sa.ForeignKey("schools.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("education_level", sa.String(16), nullable=False),
        sa.Column("grade_number", sa.Integer(), nullable=False),
        sa.Column("academic_year", sa.Integer(), nullable=False),
        sa.Column("area", sa.String(80), nullable=False),
        sa.Column("filename", sa.String(180), nullable=False),
        sa.Column("media_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("file_data", sa.LargeBinary(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime()),
        sa.CheckConstraint("education_level IN ('PRIMARIA','SECUNDARIA')", name="ck_currdoc_level"),
        sa.CheckConstraint("grade_number BETWEEN 1 AND 6", name="ck_currdoc_grade"),
        sa.CheckConstraint("academic_year BETWEEN 2020 AND 2100", name="ck_currdoc_year"),
        sa.CheckConstraint("file_size > 0 AND file_size <= 4194304", name="ck_currdoc_size"),
    )
    op.create_index("ix_currdoc_scope", "curriculum_documents",
                    ["school_id", "academic_year", "education_level", "grade_number", "area"])


def downgrade() -> None:
    op.drop_index("ix_currdoc_scope", table_name="curriculum_documents")
    op.drop_table("curriculum_documents")
