"""landlord subscription flow

Revision ID: 20260626_0004
Revises: 
Create Date: 2026-06-26
"""

from alembic import op
import sqlalchemy as sa


revision = "20260626_0004"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "users",
        "can_act_as_landlord",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
    )

    op.execute("""
        UPDATE users
        SET can_act_as_landlord = FALSE
        WHERE COALESCE(is_admin, FALSE) = FALSE
          AND role <> 'landlord'
          AND id NOT IN (
            SELECT DISTINCT landlord_id
            FROM properties
            WHERE landlord_id IS NOT NULL
          )
    """)

    op.add_column(
        "users",
        sa.Column("landlord_approved_at", sa.DateTime(), nullable=True),
    )

    op.add_column(
        "users",
        sa.Column("landlord_approved_by_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "fk_users_landlord_approved_by",
        "users",
        "users",
        ["landlord_approved_by_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "landlord_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("applicant_id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="pending"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["applicant_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_index(
        "ix_landlord_applications_applicant_id",
        "landlord_applications",
        ["applicant_id"],
    )

    op.create_index(
        "ix_landlord_applications_property_id",
        "landlord_applications",
        ["property_id"],
    )

    op.create_index(
        "ix_landlord_applications_status",
        "landlord_applications",
        ["status"],
    )

    op.create_index(
        "ix_landlord_applications_applicant_status",
        "landlord_applications",
        ["applicant_id", "status"],
    )

    op.create_index(
        "ix_landlord_applications_status_created",
        "landlord_applications",
        ["status", "created_at"],
    )

    op.add_column(
        "subscription_plans",
        sa.Column(
            "max_rental_applications",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.execute("""
        UPDATE subscription_plans
        SET max_rental_applications = 10
        WHERE role = 'tenant'
    """)

    op.add_column(
        "rental_applications",
        sa.Column("tenant_subscription_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "fk_rental_applications_tenant_subscription",
        "rental_applications",
        "user_subscriptions",
        ["tenant_subscription_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index(
        "ix_rental_applications_tenant_subscription_id",
        "rental_applications",
        ["tenant_subscription_id"],
    )


def downgrade():
    op.drop_index(
        "ix_rental_applications_tenant_subscription_id",
        table_name="rental_applications",
    )
    op.drop_constraint(
        "fk_rental_applications_tenant_subscription",
        "rental_applications",
        type_="foreignkey",
    )
    op.drop_column("rental_applications", "tenant_subscription_id")

    op.drop_column("subscription_plans", "max_rental_applications")

    op.drop_index(
        "ix_landlord_applications_status_created",
        table_name="landlord_applications",
    )
    op.drop_index(
        "ix_landlord_applications_applicant_status",
        table_name="landlord_applications",
    )
    op.drop_index(
        "ix_landlord_applications_status",
        table_name="landlord_applications",
    )
    op.drop_index(
        "ix_landlord_applications_property_id",
        table_name="landlord_applications",
    )
    op.drop_index(
        "ix_landlord_applications_applicant_id",
        table_name="landlord_applications",
    )
    op.drop_table("landlord_applications")

    op.drop_constraint(
        "fk_users_landlord_approved_by",
        "users",
        type_="foreignkey",
    )
    op.drop_column("users", "landlord_approved_by_id")
    op.drop_column("users", "landlord_approved_at")

    op.alter_column(
        "users",
        "can_act_as_landlord",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.true(),
    )
