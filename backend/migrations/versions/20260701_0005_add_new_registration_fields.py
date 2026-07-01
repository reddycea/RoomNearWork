"""add new registration fields

Revision ID: 20260701_0005
Revises: 20260626_0004
Create Date: 2026-07-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260701_0005"
down_revision = "20260626_0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("first_name", sa.String(length=80), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(length=80), nullable=True))
    op.add_column("users", sa.Column("id_number", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("reference_code", sa.String(length=80), nullable=True))

    op.create_index("ix_users_id_number", "users", ["id_number"], unique=True)
    op.create_index("ix_users_reference_code", "users", ["reference_code"], unique=False)


def downgrade():
    op.drop_index("ix_users_reference_code", table_name="users")
    op.drop_index("ix_users_id_number", table_name="users")

    op.drop_column("users", "reference_code")
    op.drop_column("users", "id_number")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
