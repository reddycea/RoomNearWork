```python
"""Initial RNW schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-25
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def timestamps():
    return [
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    ]


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False, server_default="tenant"),
        sa.Column("can_act_as_tenant", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("can_act_as_landlord", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active_account", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("email_verified_at", sa.DateTime(), nullable=True),
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("last_login_ip", sa.String(length=64), nullable=True),
        sa.Column("two_factor_secret", sa.String(length=64), nullable=True),
        sa.Column("two_factor_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        *timestamps(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="ZAR"),
        sa.Column("max_active_listings", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *timestamps(),
        sa.UniqueConstraint("name", name="uq_subscription_plans_name"),
    )
    op.create_index("ix_subscription_plans_role", "subscription_plans", ["role"], unique=False)

    op.create_table(
        "payment_webhook_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("signature_valid", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("message", sa.Text(), nullable=True),
        *timestamps(),
    )

    op.create_table(
        "taxi_ranks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("suburb", sa.String(length=120), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("province", sa.String(length=120), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *timestamps(),
    )
    op.create_index("ix_taxi_ranks_suburb", "taxi_ranks", ["suburb"], unique=False)
    op.create_index("ix_taxi_ranks_city", "taxi_ranks", ["city"], unique=False)
    op.create_index("ix_taxi_ranks_province", "taxi_ranks", ["province"], unique=False)
    op.create_index("ix_taxi_ranks_latitude", "taxi_ranks", ["latitude"], unique=False)
    op.create_index("ix_taxi_ranks_longitude", "taxi_ranks", ["longitude"], unique=False)
    op.create_index("ix_taxi_ranks_is_active", "taxi_ranks", ["is_active"], unique=False)

    op.create_table(
        "support_tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("public_token", sa.String(length=96), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="open"),
        *timestamps(),
    )
    op.create_index("ix_support_tickets_user_id", "support_tickets", ["user_id"], unique=False)
    op.create_index("ix_support_tickets_public_token", "support_tickets", ["public_token"], unique=True)

    op.create_table(
        "properties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("landlord_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),

        # Current GitHub model uses rent_amount.
        sa.Column("rent_amount", sa.Integer(), nullable=False, server_default="0"),

        # Compatibility for your deployed log, which still queries properties.price.
        sa.Column("price", sa.Integer(), nullable=False, server_default="0"),

        sa.Column("deposit_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bedrooms", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("bathrooms", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("province", sa.String(length=120), nullable=False),
        sa.Column("suburb", sa.String(length=120), nullable=True),
        sa.Column("address_line", sa.String(length=255), nullable=True),
        sa.Column("formatted_address", sa.String(length=500), nullable=True),
        sa.Column("google_place_id", sa.String(length=255), nullable=True),
        sa.Column("approximate_address", sa.String(length=255), nullable=True),
        sa.Column("address_visibility", sa.String(length=40), nullable=False, server_default="approved_viewing"),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("workplace_distance_km", sa.Float(), nullable=True),
        sa.Column("nearest_transport", sa.String(length=160), nullable=True),
        sa.Column("commute_notes", sa.Text(), nullable=True),
        sa.Column("furnished", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("pets_allowed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("transport_access", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="under_review"),
        sa.Column("status_reason", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quality_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quality_score_details", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("renewed_at", sa.DateTime(), nullable=True),
        sa.Column("listing_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("verified_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_properties_landlord_id", "properties", ["landlord_id"], unique=False)
    op.create_index("ix_properties_city", "properties", ["city"], unique=False)
    op.create_index("ix_properties_province", "properties", ["province"], unique=False)
    op.create_index("ix_properties_google_place_id", "properties", ["google_place_id"], unique=False)
    op.create_index("ix_properties_latitude", "properties", ["latitude"], unique=False)
    op.create_index("ix_properties_longitude", "properties", ["longitude"], unique=False)
    op.create_index("ix_properties_status", "properties", ["status"], unique=False)
    op.create_index("ix_properties_is_active", "properties", ["is_active"], unique=False)
    op.create_index("ix_properties_search", "properties", ["status", "is_active", "city", "province", "rent_amount"], unique=False)
    op.create_index("ix_properties_geo", "properties", ["latitude", "longitude"], unique=False)

    op.create_table(
        "property_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("relative_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_private", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("review_status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("virus_scan_status", sa.String(length=40), nullable=False, server_default="not_scanned"),
        *timestamps(),
        sa.UniqueConstraint("stored_filename", name="uq_property_assets_stored_filename"),
        sa.UniqueConstraint("relative_path", name="uq_property_assets_relative_path"),
    )
    op.create_index("ix_property_assets_property_id", "property_assets", ["property_id"], unique=False)
    op.create_index("ix_property_assets_uploaded_by_id", "property_assets", ["uploaded_by_id"], unique=False)
    op.create_index("ix_property_assets_kind", "property_assets", ["kind"], unique=False)
    op.create_index("ix_property_assets_review_status", "property_assets", ["review_status"], unique=False)
    op.create_index("ix_property_assets_kind_property", "property_assets", ["property_id", "kind"], unique=False)
    op.create_index("ix_property_assets_review", "property_assets", ["kind", "review_status"], unique=False)

    op.create_table(
        "rental_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("applicant_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        *timestamps(),
        sa.UniqueConstraint("property_id", "applicant_id", name="uq_application_property_applicant"),
    )
    op.create_index("ix_rental_applications_property_id", "rental_applications", ["property_id"], unique=False)
    op.create_index("ix_rental_applications_applicant_id", "rental_applications", ["applicant_id"], unique=False)
    op.create_index("ix_rental_applications_status", "rental_applications", ["status"], unique=False)

    op.create_table(
        "user_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("subscription_plans.id"), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_user_subscriptions_user_id", "user_subscriptions", ["user_id"], unique=False)
    op.create_index("ix_user_subscriptions_role", "user_subscriptions", ["role"], unique=False)
    op.create_index("ix_user_subscriptions_status", "user_subscriptions", ["status"], unique=False)

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("subscription_plans.id"), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="ZAR"),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="disabled"),
        sa.Column("provider_reference", sa.String(length=160), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_invoices_user_id", "invoices", ["user_id"], unique=False)
    op.create_index("ix_invoices_provider_reference", "invoices", ["provider_reference"], unique=True)
    op.create_index("ix_invoices_status", "invoices", ["status"], unique=False)

    op.create_table(
        "listing_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("reporter_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reason", sa.String(length=120), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="open"),
        *timestamps(),
    )
    op.create_index("ix_listing_reports_property_id", "listing_reports", ["property_id"], unique=False)
    op.create_index("ix_listing_reports_reporter_id", "listing_reports", ["reporter_id"], unique=False)
    op.create_index("ix_listing_reports_status", "listing_reports", ["status"], unique=False)

    op.create_table(
        "landlord_verifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("landlord_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("document_path", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("reviewed_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_landlord_verifications_landlord_id", "landlord_verifications", ["landlord_id"], unique=False)
    op.create_index("ix_landlord_verifications_status", "landlord_verifications", ["status"], unique=False)

    op.create_table(
        "saved_searches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("province", sa.String(length=120), nullable=True),
        sa.Column("max_rent", sa.Integer(), nullable=True),
        sa.Column("min_bedrooms", sa.Integer(), nullable=True),
        sa.Column("furnished", sa.Boolean(), nullable=True),
        sa.Column("pets_allowed", sa.Boolean(), nullable=True),
        sa.Column("transport_access", sa.Boolean(), nullable=True),
        sa.Column("workplace_address", sa.String(length=500), nullable=True),
        sa.Column("workplace_formatted_address", sa.String(length=500), nullable=True),
        sa.Column("workplace_place_id", sa.String(length=255), nullable=True),
        sa.Column("workplace_area", sa.String(length=160), nullable=True),
        sa.Column("workplace_latitude", sa.Float(), nullable=True),
        sa.Column("workplace_longitude", sa.Float(), nullable=True),
        sa.Column("travel_mode", sa.String(length=40), nullable=False, server_default="all"),
        sa.Column("max_distance_km", sa.Float(), nullable=True),
        sa.Column("max_travel_minutes", sa.Integer(), nullable=True),
        sa.Column("alerts_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_alerted_at", sa.DateTime(), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("user_id", "name", name="uq_saved_search_user_name"),
    )
    op.create_index("ix_saved_searches_user_id", "saved_searches", ["user_id"], unique=False)
    op.create_index("ix_saved_searches_city", "saved_searches", ["city"], unique=False)
    op.create_index("ix_saved_searches_province", "saved_searches", ["province"], unique=False)
    op.create_index("ix_saved_searches_workplace_place_id", "saved_searches", ["workplace_place_id"], unique=False)
    op.create_index("ix_saved_searches_workplace_area", "saved_searches", ["workplace_area"], unique=False)

    op.create_table(
        "conversation_threads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("landlord_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="open"),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("property_id", "tenant_id", "landlord_id", name="uq_thread_property_tenant_landlord"),
    )
    op.create_index("ix_conversation_threads_property_id", "conversation_threads", ["property_id"], unique=False)
    op.create_index("ix_conversation_threads_tenant_id", "conversation_threads", ["tenant_id"], unique=False)
    op.create_index("ix_conversation_threads_landlord_id", "conversation_threads", ["landlord_id"], unique=False)

    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("thread_id", sa.Integer(), sa.ForeignKey("conversation_threads.id"), nullable=False),
        sa.Column("sender_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_conversation_messages_thread_id", "conversation_messages", ["thread_id"], unique=False)
    op.create_index("ix_conversation_messages_sender_id", "conversation_messages", ["sender_id"], unique=False)

    op.create_table(
        "viewing_appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("landlord_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("requested_start", sa.DateTime(), nullable=False),
        sa.Column("requested_end", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("tenant_note", sa.Text(), nullable=True),
        sa.Column("landlord_note", sa.Text(), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_viewing_appointments_property_id", "viewing_appointments", ["property_id"], unique=False)
    op.create_index("ix_viewing_appointments_tenant_id", "viewing_appointments", ["tenant_id"], unique=False)
    op.create_index("ix_viewing_appointments_landlord_id", "viewing_appointments", ["landlord_id"], unique=False)
    op.create_index("ix_viewing_appointments_status", "viewing_appointments", ["status"], unique=False)

    op.create_table(
        "user_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=True),
        sa.Column("target_id", sa.String(length=80), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_user_audit_logs_actor_id", "user_audit_logs", ["actor_id"], unique=False)
    op.create_index("ix_user_audit_logs_action", "user_audit_logs", ["action"], unique=False)

    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_email_verification_tokens_user_id", "email_verification_tokens", ["user_id"], unique=False)
    op.create_index("ix_email_verification_tokens_token_hash", "email_verification_tokens", ["token_hash"], unique=True)

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"], unique=False)
    op.create_index("ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"], unique=True)

    op.create_table(
        "places_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=80), nullable=False, server_default="workplace_search"),
        sa.Column("selected_place_id", sa.String(length=255), nullable=True),
        sa.Column("selected_description", sa.String(length=500), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_places_sessions_user_id", "places_sessions", ["user_id"], unique=False)
    op.create_index("ix_places_sessions_token_hash", "places_sessions", ["token_hash"], unique=True)

    op.create_table(
        "rental_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("landlord_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("accuracy_rating", sa.Integer(), nullable=True),
        sa.Column("safety_rating", sa.Integer(), nullable=True),
        sa.Column("commute_rating", sa.Integer(), nullable=True),
        sa.Column("landlord_communication_rating", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=140), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("property_id", "tenant_id", name="uq_rental_review_property_tenant"),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_rental_reviews_rating_range"),
    )
    op.create_index("ix_rental_reviews_property_id", "rental_reviews", ["property_id"], unique=False)
    op.create_index("ix_rental_reviews_tenant_id", "rental_reviews", ["tenant_id"], unique=False)
    op.create_index("ix_rental_reviews_landlord_id", "rental_reviews", ["landlord_id"], unique=False)
    op.create_index("ix_rental_reviews_status", "rental_reviews", ["status"], unique=False)


def downgrade():
    op.drop_table("rental_reviews")
    op.drop_table("places_sessions")
    op.drop_table("password_reset_tokens")
    op.drop_table("email_verification_tokens")
    op.drop_table("user_audit_logs")
    op.drop_table("viewing_appointments")
    op.drop_table("conversation_messages")
    op.drop_table("conversation_threads")
    op.drop_table("saved_searches")
    op.drop_table("landlord_verifications")
    op.drop_table("listing_reports")
    op.drop_table("invoices")
    op.drop_table("user_subscriptions")
    op.drop_table("rental_applications")
    op.drop_table("property_assets")
    op.drop_table("properties")
    op.drop_table("support_tickets")
    op.drop_table("taxi_ranks")
    op.drop_table("payment_webhook_logs")
    op.drop_table("subscription_plans")
    op.drop_table("users")
```
