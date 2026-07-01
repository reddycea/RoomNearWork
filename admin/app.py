from __future__ import annotations

import hmac
import json
import os
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from werkzeug.security import check_password_hash

try:
    import pyotp
except Exception:
    pyotp = None


APP_NAME = "Room Near Work Admin"


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🏠",
    layout="wide",
)



def env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    return value if value not in (None, "") else default


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


@st.cache_resource(show_spinner=False)
def db_engine() -> Engine:
    database_url = env("DATABASE_URL")
    if not database_url:
        st.error("DATABASE_URL is missing.")
        st.stop()

    return create_engine(
        normalize_database_url(database_url),
        pool_pre_ping=True,
        future=True,
    )


def password_is_valid(password: str) -> bool:
    password_hash = env("ADMIN_PASSWORD_HASH")
    plain_password = env("ADMIN_PASSWORD")

    if password_hash:
        return check_password_hash(password_hash, password)

    if plain_password:
        return hmac.compare_digest(password, plain_password)

    st.error("Set ADMIN_PASSWORD_HASH or ADMIN_PASSWORD.")
    return False


def totp_is_valid(code: str | None) -> bool:
    secret = env("ADMIN_TOTP_SECRET")

    if not secret:
        return True

    if pyotp is None:
        st.error("pyotp is required when ADMIN_TOTP_SECRET is set.")
        return False

    if not code:
        return False

    return bool(pyotp.TOTP(secret).verify(code.strip(), valid_window=1))


def verify_login(username: str, password: str, totp_code: str | None) -> bool:
    expected_username = env("ADMIN_USERNAME", "admin") or "admin"

    return (
        hmac.compare_digest(username.strip(), expected_username)
        and password_is_valid(password)
        and totp_is_valid(totp_code)
    )


def login_page() -> None:
    st.title("🏠 Room Near Work Admin")
    st.caption("Separate Streamlit admin app. Admin is not a tenant or landlord.")

    with st.form("login"):
        username = st.text_input("Username", value=env("ADMIN_USERNAME", "admin") or "admin")
        password = st.text_input("Password", type="password")
        totp_code = None

        if env("ADMIN_TOTP_SECRET"):
            totp_code = st.text_input("Authenticator code", placeholder="123456")

        submitted = st.form_submit_button("Sign in", type="primary")

    if submitted:
        if verify_login(username, password, totp_code):
            st.session_state["admin_ok"] = True
            st.session_state["admin_username"] = username.strip()
            st.rerun()
        else:
            st.error("Invalid admin login.")


def require_login() -> None:
    if not st.session_state.get("admin_ok"):
        login_page()
        st.stop()


# -----------------------------
# DB helpers
# -----------------------------

def query_df(sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    with db_engine().connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params or {})


def execute(sql: str, params: dict[str, Any] | None = None) -> None:
    with db_engine().begin() as conn:
        conn.execute(text(sql), params or {})


def execute_many(items: list[tuple[str, dict[str, Any]]]) -> None:
    with db_engine().begin() as conn:
        for sql, params in items:
            conn.execute(text(sql), params)


def count_rows(table: str, where: str = "1=1") -> int:
    try:
        df = query_df(f"SELECT COUNT(*) AS total FROM {table} WHERE {where}")
        return int(df.iloc[0]["total"])
    except Exception:
        return 0


def audit(action: str, target_type: str, target_id: int | str | None, metadata: dict[str, Any] | None = None) -> None:
    try:
        execute(
            """
            INSERT INTO user_audit_logs
                (actor_id, action, target_type, target_id, metadata_json, created_at, updated_at)
            VALUES
                (NULL, :action, :target_type, :target_id, :metadata_json, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            {
                "action": action,
                "target_type": target_type,
                "target_id": str(target_id) if target_id is not None else None,
                "metadata_json": json.dumps(metadata or {}),
            },
        )
    except Exception:
        # Never block admin work because audit logging failed.
        pass


def refresh_success(message: str) -> None:
    st.success(message)
    st.cache_data.clear()


def show_df(df: pd.DataFrame, empty_message: str) -> bool:
    if df.empty:
        st.info(empty_message)
        return False

    st.dataframe(df, use_container_width=True, hide_index=True)
    return True


# -----------------------------
# Pages
# -----------------------------

def dashboard_page() -> None:
    st.header("Dashboard")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Users", count_rows("users"))
    c2.metric("Active listings", count_rows("properties", "is_active = TRUE AND status = 'available'"))
    c3.metric("Landlord applications", count_rows("landlord_applications", "status = 'pending'"))
    c4.metric("Reviews pending", count_rows("rental_reviews", "status = 'pending'"))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Listings under review", count_rows("properties", "status = 'under_review'"))
    c6.metric("Private docs pending", count_rows("property_assets", "review_status = 'pending' AND kind IN ('proof_registration', 'id_document')"))
    c7.metric("Open reports", count_rows("listing_reports", "status = 'open'"))
    c8.metric("Open support tickets", count_rows("support_tickets", "status = 'open'"))

    st.subheader("Latest listings")
    df = query_df(
        """
        SELECT
            p.id,
            p.title,
            p.status,
            p.is_active,
            p.listing_verified,
            p.city,
            p.province,
            p.suburb,
            p.price AS rent,
            p.bedrooms,
            p.bathrooms,
            p.created_at,
            u.full_name AS landlord,
            u.email AS landlord_email
        FROM properties p
        JOIN users u ON u.id = p.landlord_id
        ORDER BY p.created_at DESC
        LIMIT 20
        """
    )
    show_df(df, "No listings yet.")


def users_page() -> None:
    st.header("Users")
    st.caption("Only tenant and landlord accounts belong here. Admin login is controlled by Streamlit environment variables.")

    search = st.text_input("Search users", placeholder="email, name, phone")
    params: dict[str, Any] = {}
    where = ""

    if search.strip():
        where = """
        WHERE lower(email) LIKE :q
           OR lower(full_name) LIKE :q
           OR lower(phone) LIKE :q
        """
        params["q"] = f"%{search.strip().lower()}%"

    df = query_df(
        f"""
        SELECT
            id,
            email,
            full_name,
            phone,
            role,
            can_act_as_tenant,
            can_act_as_landlord,
            is_admin,
            is_active_account,
            email_verified,
            last_login_at,
            created_at
        FROM users
        {where}
        ORDER BY created_at DESC
        LIMIT 300
        """,
        params,
    )

    if not show_df(df, "No users found."):
        return

    st.subheader("User actions")
    user_id = st.number_input("User ID", min_value=1, step=1)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("Deactivate"):
            execute("UPDATE users SET is_active_account = FALSE, updated_at = CURRENT_TIMESTAMP WHERE id = :id", {"id": user_id})
            audit("admin.deactivate_user", "user", user_id)
            refresh_success("User deactivated.")

    with c2:
        if st.button("Reactivate"):
            execute("UPDATE users SET is_active_account = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = :id", {"id": user_id})
            audit("admin.reactivate_user", "user", user_id)
            refresh_success("User reactivated.")

    with c3:
        if st.button("Grant landlord"):
            execute(
                """
                UPDATE users
                SET can_act_as_landlord = TRUE,
                    landlord_approved_at = CURRENT_TIMESTAMP,
                    landlord_approved_by_id = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {"id": user_id},
            )
            audit("admin.grant_landlord", "user", user_id)
            refresh_success("Landlord permission granted.")

    with c4:
        if st.button("Revoke landlord"):
            execute(
                """
                UPDATE users
                SET can_act_as_landlord = FALSE,
                    landlord_approved_at = NULL,
                    landlord_approved_by_id = NULL,
                    role = CASE WHEN role = 'landlord' THEN 'tenant' ELSE role END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {"id": user_id},
            )
            audit("admin.revoke_landlord", "user", user_id)
            refresh_success("Landlord permission revoked.")


def landlord_applications_page() -> None:
    st.header("Landlord applications")

    status = st.selectbox("Status", ["pending", "approved", "rejected", "all"])
    params: dict[str, Any] = {}
    where = ""

    if status != "all":
        where = "WHERE la.status = :status"
        params["status"] = status

    df = query_df(
        f"""
        SELECT
            la.id,
            la.status,
            la.message,
            la.admin_note,
            la.created_at,
            la.reviewed_at,
            u.id AS applicant_id,
            u.full_name,
            u.email,
            u.phone,
            p.id AS property_id,
            p.title AS property_title
        FROM landlord_applications la
        JOIN users u ON u.id = la.applicant_id
        LEFT JOIN properties p ON p.id = la.property_id
        {where}
        ORDER BY la.created_at DESC
        LIMIT 300
        """,
        params,
    )

    if not show_df(df, "No landlord applications found."):
        return

    st.subheader("Review application")
    app_id = st.number_input("Application ID", min_value=1, step=1)
    note = st.text_area("Admin note")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Approve", type="primary"):
            app_df = query_df("SELECT applicant_id FROM landlord_applications WHERE id = :id", {"id": app_id})

            if app_df.empty:
                st.error("Application not found.")
                return

            applicant_id = int(app_df.iloc[0]["applicant_id"])

            execute_many(
                [
                    (
                        """
                        UPDATE landlord_applications
                        SET status = 'approved',
                            admin_note = :note,
                            reviewed_by_id = NULL,
                            reviewed_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                        """,
                        {"id": app_id, "note": note},
                    ),
                    (
                        """
                        UPDATE users
                        SET can_act_as_landlord = TRUE,
                            landlord_approved_at = CURRENT_TIMESTAMP,
                            landlord_approved_by_id = NULL,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :applicant_id
                        """,
                        {"applicant_id": applicant_id},
                    ),
                ]
            )
            audit("admin.approve_landlord_application", "landlord_application", app_id, {"note": note})
            refresh_success("Landlord application approved.")

    with c2:
        if st.button("Reject"):
            execute(
                """
                UPDATE landlord_applications
                SET status = 'rejected',
                    admin_note = :note,
                    reviewed_by_id = NULL,
                    reviewed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {"id": app_id, "note": note},
            )
            audit("admin.reject_landlord_application", "landlord_application", app_id, {"note": note})
            refresh_success("Landlord application rejected.")


def listings_page() -> None:
    st.header("Listings")

    status = st.selectbox("Status", ["under_review", "available", "rejected", "archived", "expired", "all"])
    params: dict[str, Any] = {}
    where = ""

    if status != "all":
        where = "WHERE p.status = :status"
        params["status"] = status

    df = query_df(
        f"""
        SELECT
            p.id,
            p.title,
            p.status,
            p.status_reason,
            p.is_active,
            p.listing_verified,
            p.verified_at,
            p.city,
            p.province,
            p.suburb,
            p.price AS rent,
            p.deposit_amount,
            p.bedrooms,
            p.bathrooms,
            p.quality_score,
            p.view_count,
            p.created_at,
            p.expires_at,
            u.full_name AS landlord,
            u.email AS landlord_email
        FROM properties p
        JOIN users u ON u.id = p.landlord_id
        {where}
        ORDER BY p.created_at DESC
        LIMIT 300
        """,
        params,
    )

    if not show_df(df, "No listings found."):
        return

    st.subheader("Moderate listing")
    property_id = st.number_input("Property ID", min_value=1, step=1)
    reason = st.text_area("Reason / note")
    expiry_days = st.number_input("Listing expiry days after approval", min_value=1, max_value=365, value=30)

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Approve listing", type="primary"):
            expires_at = datetime.utcnow() + timedelta(days=int(expiry_days))
            execute(
                """
                UPDATE properties
                SET status = 'available',
                    status_reason = :reason,
                    is_active = TRUE,
                    listing_verified = TRUE,
                    verified_at = CURRENT_TIMESTAMP,
                    verified_by_id = NULL,
                    expires_at = :expires_at,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {"id": property_id, "reason": reason, "expires_at": expires_at},
            )
            audit("admin.approve_listing", "property", property_id, {"reason": reason})
            refresh_success("Listing approved.")

    with c2:
        if st.button("Reject listing"):
            execute(
                """
                UPDATE properties
                SET status = 'rejected',
                    status_reason = :reason,
                    is_active = FALSE,
                    listing_verified = FALSE,
                    verified_at = NULL,
                    verified_by_id = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {"id": property_id, "reason": reason},
            )
            audit("admin.reject_listing", "property", property_id, {"reason": reason})
            refresh_success("Listing rejected.")

    with c3:
        if st.button("Archive listing"):
            execute(
                """
                UPDATE properties
                SET status = 'archived',
                    status_reason = :reason,
                    is_active = FALSE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {"id": property_id, "reason": reason},
            )
            audit("admin.archive_listing", "property", property_id, {"reason": reason})
            refresh_success("Listing archived.")


def documents_page() -> None:
    st.header("Property private documents")
    st.caption("Proof of registration and ID document review.")

    status = st.selectbox("Review status", ["pending", "approved", "rejected", "all"])
    params: dict[str, Any] = {}
    status_filter = ""

    if status != "all":
        status_filter = "AND pa.review_status = :status"
        params["status"] = status

    df = query_df(
        f"""
        SELECT
            pa.id,
            pa.property_id,
            p.title AS property_title,
            pa.kind,
            pa.original_filename,
            pa.relative_path,
            pa.mime_type,
            pa.size_bytes,
            pa.review_status,
            pa.review_note,
            pa.virus_scan_status,
            pa.created_at,
            u.full_name AS uploaded_by,
            u.email AS uploaded_by_email
        FROM property_assets pa
        JOIN properties p ON p.id = pa.property_id
        JOIN users u ON u.id = pa.uploaded_by_id
        WHERE pa.kind IN ('proof_registration', 'id_document')
        {status_filter}
        ORDER BY pa.created_at DESC
        LIMIT 300
        """,
        params,
    )

    if not show_df(df, "No private documents found."):
        return

    st.subheader("Review document")
    asset_id = st.number_input("Asset ID", min_value=1, step=1)
    note = st.text_area("Review note")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Approve document", type="primary"):
            execute(
                """
                UPDATE property_assets
                SET review_status = 'approved',
                    review_note = :note,
                    reviewed_by_id = NULL,
                    reviewed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {"id": asset_id, "note": note},
            )
            audit("admin.approve_document", "property_asset", asset_id, {"note": note})
            refresh_success("Document approved.")

    with c2:
        if st.button("Reject document"):
            execute(
                """
                UPDATE property_assets
                SET review_status = 'rejected',
                    review_note = :note,
                    reviewed_by_id = NULL,
                    reviewed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {"id": asset_id, "note": note},
            )
            audit("admin.reject_document", "property_asset", asset_id, {"note": note})
            refresh_success("Document rejected.")


def landlord_verifications_page() -> None:
    st.header("Landlord verification documents")

    status = st.selectbox("Status", ["pending", "approved", "rejected", "all"])
    params: dict[str, Any] = {}
    where = ""

    if status != "all":
        where = "WHERE lv.status = :status"
        params["status"] = status

    df = query_df(
        f"""
        SELECT
            lv.id,
            lv.landlord_id,
            u.full_name AS landlord,
            u.email AS landlord_email,
            lv.document_path,
            lv.status,
            lv.notes,
            lv.created_at,
            lv.updated_at
        FROM landlord_verifications lv
        JOIN users u ON u.id = lv.landlord_id
        {where}
        ORDER BY lv.created_at DESC
        LIMIT 300
        """,
        params,
    )

    if not show_df(df, "No landlord verification documents found."):
        return

    st.subheader("Review landlord verification")
    verification_id = st.number_input("Verification ID", min_value=1, step=1)
    notes = st.text_area("Notes")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Approve verification", type="primary"):
            execute(
                """
                UPDATE landlord_verifications
                SET status = 'approved',
                    notes = :notes,
                    reviewed_by_id = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {"id": verification_id, "notes": notes},
            )
            audit("admin.approve_landlord_verification", "landlord_verification", verification_id, {"notes": notes})
            refresh_success("Verification approved.")

    with c2:
        if st.button("Reject verification"):
            execute(
                """
                UPDATE landlord_verifications
                SET status = 'rejected',
                    notes = :notes,
                    reviewed_by_id = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {"id": verification_id, "notes": notes},
            )
            audit("admin.reject_landlord_verification", "landlord_verification", verification_id, {"notes": notes})
            refresh_success("Verification rejected.")


def reviews_page() -> None:
    st.header("Tenant rental reviews")

    status = st.selectbox("Status", ["pending", "approved", "rejected", "all"])
    params: dict[str, Any] = {}
    where = ""

    if status != "all":
        where = "WHERE rr.status = :status"
        params["status"] = status

    df = query_df(
        f"""
        SELECT
            rr.id,
            rr.status,
            rr.rating,
            rr.accuracy_rating,
            rr.safety_rating,
            rr.commute_rating,
            rr.landlord_communication_rating,
            rr.title,
            rr.comment,
            rr.admin_note,
            rr.created_at,
            rr.reviewed_at,
            p.id AS property_id,
            p.title AS property_title,
            tenant.full_name AS tenant,
            tenant.email AS tenant_email,
            landlord.full_name AS landlord,
            landlord.email AS landlord_email
        FROM rental_reviews rr
        JOIN properties p ON p.id = rr.property_id
        JOIN users tenant ON tenant.id = rr.tenant_id
        JOIN users landlord ON landlord.id = rr.landlord_id
        {where}
        ORDER BY rr.created_at DESC
        LIMIT 300
        """,
        params,
    )

    if not show_df(df, "No rental reviews found."):
        return

    st.subheader("Moderate review")
    review_id = st.number_input("Review ID", min_value=1, step=1)
    note = st.text_area("Admin note")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Approve review", type="primary"):
            execute(
                """
                UPDATE rental_reviews
                SET status = 'approved',
                    admin_note = :note,
                    reviewed_by_id = NULL,
                    reviewed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {"id": review_id, "note": note},
            )
            audit("admin.approve_review", "rental_review", review_id, {"note": note})
            refresh_success("Review approved.")

    with c2:
        if st.button("Reject review"):
            execute(
                """
                UPDATE rental_reviews
                SET status = 'rejected',
                    admin_note = :note,
                    reviewed_by_id = NULL,
                    reviewed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {"id": review_id, "note": note},
            )
            audit("admin.reject_review", "rental_review", review_id, {"note": note})
            refresh_success("Review rejected.")


def reports_page() -> None:
    st.header("Listing reports")

    status = st.selectbox("Status", ["open", "resolved", "dismissed", "all"])
    params: dict[str, Any] = {}
    where = ""

    if status != "all":
        where = "WHERE lr.status = :status"
        params["status"] = status

    df = query_df(
        f"""
        SELECT
            lr.id,
            lr.status,
            lr.reason,
            lr.details,
            lr.created_at,
            p.id AS property_id,
            p.title AS property_title,
            reporter.full_name AS reporter,
            reporter.email AS reporter_email
        FROM listing_reports lr
        JOIN properties p ON p.id = lr.property_id
        LEFT JOIN users reporter ON reporter.id = lr.reporter_id
        {where}
        ORDER BY lr.created_at DESC
        LIMIT 300
        """,
        params,
    )

    if not show_df(df, "No listing reports found."):
        return

    st.subheader("Update report")
    report_id = st.number_input("Report ID", min_value=1, step=1)
    new_status = st.selectbox("New status", ["open", "resolved", "dismissed"])

    if st.button("Save report status", type="primary"):
        execute(
            """
            UPDATE listing_reports
            SET status = :status,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """,
            {"id": report_id, "status": new_status},
        )
        audit("admin.update_listing_report", "listing_report", report_id, {"status": new_status})
        refresh_success("Report updated.")


def support_page() -> None:
    st.header("Support tickets")

    status = st.selectbox("Status", ["open", "resolved", "closed", "all"])
    params: dict[str, Any] = {}
    where = ""

    if status != "all":
        where = "WHERE st.status = :status"
        params["status"] = status

    df = query_df(
        f"""
        SELECT
            st.id,
            st.status,
            st.email,
            st.subject,
            st.message,
            st.public_token,
            st.created_at,
            st.updated_at,
            u.full_name AS user_name
        FROM support_tickets st
        LEFT JOIN users u ON u.id = st.user_id
        {where}
        ORDER BY st.created_at DESC
        LIMIT 300
        """,
        params,
    )

    if not show_df(df, "No support tickets found."):
        return

    st.subheader("Update ticket")
    ticket_id = st.number_input("Ticket ID", min_value=1, step=1)
    new_status = st.selectbox("New ticket status", ["open", "resolved", "closed"])

    if st.button("Save ticket status", type="primary"):
        execute(
            """
            UPDATE support_tickets
            SET status = :status,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """,
            {"id": ticket_id, "status": new_status},
        )
        audit("admin.update_support_ticket", "support_ticket", ticket_id, {"status": new_status})
        refresh_success("Ticket updated.")


def rental_applications_page() -> None:
    st.header("Rental applications")

    status = st.selectbox("Status", ["pending", "approved", "rejected", "all"])
    params: dict[str, Any] = {}
    where = ""

    if status != "all":
        where = "WHERE ra.status = :status"
        params["status"] = status

    df = query_df(
        f"""
        SELECT
            ra.id,
            ra.status,
            ra.message,
            ra.created_at,
            p.id AS property_id,
            p.title AS property_title,
            tenant.full_name AS tenant,
            tenant.email AS tenant_email,
            landlord.full_name AS landlord,
            landlord.email AS landlord_email
        FROM rental_applications ra
        JOIN properties p ON p.id = ra.property_id
        JOIN users tenant ON tenant.id = ra.applicant_id
        JOIN users landlord ON landlord.id = p.landlord_id
        {where}
        ORDER BY ra.created_at DESC
        LIMIT 300
        """,
        params,
    )

    show_df(df, "No rental applications found.")


def audit_page() -> None:
    st.header("Audit logs")

    df = query_df(
        """
        SELECT
            id,
            action,
            target_type,
            target_id,
            metadata_json,
            ip_address,
            user_agent,
            created_at
        FROM user_audit_logs
        ORDER BY created_at DESC
        LIMIT 500
        """
    )

    show_df(df, "No audit logs found.")


def read_only_sql_page() -> None:
    st.header("Read-only SQL")
    st.warning("Only SELECT statements are allowed.")

    sql = st.text_area(
        "SQL",
        value="SELECT id, title, status, price, city, province FROM properties ORDER BY created_at DESC LIMIT 20",
        height=180,
    )

    if st.button("Run"):
        if not sql.strip().lower().startswith("select"):
            st.error("Only SELECT queries are allowed.")
            return

        try:
            df = query_df(sql)
            show_df(df, "Query returned no rows.")
        except Exception as exc:
            st.error(f"Query failed: {exc}")



def main() -> None:
    require_login()

    with st.sidebar:
        st.title("🏠 RNW Admin")
        st.caption(f"Signed in as {st.session_state.get('admin_username', 'admin')}")

        page = st.radio(
            "Menu",
            [
                "Dashboard",
                "Users",
                "Landlord applications",
                "Listings",
                "Property private documents",
                "Landlord verifications",
                "Tenant reviews",
                "Listing reports",
                "Support tickets",
                "Rental applications",
                "Audit logs",
                "Read-only SQL",
            ],
        )

        st.divider()

        if st.button("Refresh"):
            st.cache_data.clear()
            st.rerun()

        if st.button("Sign out"):
            st.session_state.clear()
            st.rerun()

    if page == "Dashboard":
        dashboard_page()
    elif page == "Users":
        users_page()
    elif page == "Landlord applications":
        landlord_applications_page()
    elif page == "Listings":
        listings_page()
    elif page == "Property private documents":
        documents_page()
    elif page == "Landlord verifications":
        landlord_verifications_page()
    elif page == "Tenant reviews":
        reviews_page()
    elif page == "Listing reports":
        reports_page()
    elif page == "Support tickets":
        support_page()
    elif page == "Rental applications":
        rental_applications_page()
    elif page == "Audit logs":
        audit_page()
    elif page == "Read-only SQL":
        read_only_sql_page()


if __name__ == "__main__":
    main()
