BEGIN;
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(160) NOT NULL,
    id_number VARCHAR(13) UNIQUE,
    reference_code VARCHAR(80),
    phone VARCHAR(40),
    password_hash VARCHAR(255) NOT NULL,

    role VARCHAR(30) NOT NULL DEFAULT 'tenant',
    can_act_as_tenant BOOLEAN NOT NULL DEFAULT TRUE,
    can_act_as_landlord BOOLEAN NOT NULL DEFAULT FALSE,

    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_active_account BOOLEAN NOT NULL DEFAULT TRUE,

    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    email_verified_at TIMESTAMP NULL,

    failed_login_count INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMP NULL,
    last_login_at TIMESTAMP NULL,
    last_login_ip VARCHAR(64),

    two_factor_secret VARCHAR(64),
    two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE,

    landlord_approved_at TIMESTAMP NULL,
    landlord_approved_by_id INTEGER NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email
ON users(email);

ALTER TABLE users
ADD COLUMN IF NOT EXISTS phone VARCHAR(40);

ALTER TABLE users
ADD COLUMN IF NOT EXISTS can_act_as_tenant BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS can_act_as_landlord BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS is_active_account BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMP NULL;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS failed_login_count INTEGER NOT NULL DEFAULT 0;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP NULL;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP NULL;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS last_login_ip VARCHAR(64);

ALTER TABLE users
ADD COLUMN IF NOT EXISTS two_factor_secret VARCHAR(64);

ALTER TABLE users
ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS landlord_approved_at TIMESTAMP NULL;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS landlord_approved_by_id INTEGER NULL;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE users
ALTER COLUMN can_act_as_landlord SET DEFAULT FALSE;

UPDATE users
SET can_act_as_landlord = FALSE
WHERE COALESCE(is_admin, FALSE) = FALSE
  AND role <> 'landlord'
  AND id NOT IN (
      SELECT DISTINCT landlord_id
      FROM properties
      WHERE landlord_id IS NOT NULL
  );

UPDATE users
SET landlord_approved_by_id = NULL
WHERE landlord_approved_by_id IS NOT NULL
  AND landlord_approved_by_id NOT IN (
      SELECT id FROM users
  );

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_users_landlord_approved_by'
    ) THEN
        ALTER TABLE users
        ADD CONSTRAINT fk_users_landlord_approved_by
        FOREIGN KEY (landlord_approved_by_id)
        REFERENCES users(id)
        ON DELETE SET NULL;
    END IF;
END $$;


CREATE TABLE IF NOT EXISTS subscription_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    role VARCHAR(30) NOT NULL,
    price_cents INTEGER NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'ZAR',
    max_active_listings INTEGER NULL,

    -- New field required by current code
    max_rental_applications INTEGER NOT NULL DEFAULT 0,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_subscription_plans_name UNIQUE (name)
);

CREATE INDEX IF NOT EXISTS ix_subscription_plans_role
ON subscription_plans(role);

ALTER TABLE subscription_plans
ADD COLUMN IF NOT EXISTS currency VARCHAR(10) NOT NULL DEFAULT 'ZAR';

ALTER TABLE subscription_plans
ADD COLUMN IF NOT EXISTS max_active_listings INTEGER NULL;

ALTER TABLE subscription_plans
ADD COLUMN IF NOT EXISTS max_rental_applications INTEGER NOT NULL DEFAULT 0;

ALTER TABLE subscription_plans
ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE subscription_plans
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE subscription_plans
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

UPDATE subscription_plans
SET max_rental_applications = 10
WHERE role = 'tenant';

UPDATE subscription_plans
SET max_rental_applications = 0
WHERE role = 'landlord';


CREATE TABLE IF NOT EXISTS payment_webhook_logs (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(40) NOT NULL,
    payload TEXT NOT NULL,
    signature_valid BOOLEAN NOT NULL DEFAULT FALSE,
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    message TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS taxi_ranks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(160) NOT NULL,
    suburb VARCHAR(120),
    city VARCHAR(120),
    province VARCHAR(120),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_taxi_ranks_suburb
ON taxi_ranks(suburb);

CREATE INDEX IF NOT EXISTS ix_taxi_ranks_city
ON taxi_ranks(city);

CREATE INDEX IF NOT EXISTS ix_taxi_ranks_province
ON taxi_ranks(province);

CREATE INDEX IF NOT EXISTS ix_taxi_ranks_latitude
ON taxi_ranks(latitude);

CREATE INDEX IF NOT EXISTS ix_taxi_ranks_longitude
ON taxi_ranks(longitude);

CREATE INDEX IF NOT EXISTS ix_taxi_ranks_is_active
ON taxi_ranks(is_active);


CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NULL REFERENCES users(id),
    public_token VARCHAR(96) NOT NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'open',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_support_tickets_user_id
ON support_tickets(user_id);

CREATE UNIQUE INDEX IF NOT EXISTS ix_support_tickets_public_token
ON support_tickets(public_token);


CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    landlord_id INTEGER NOT NULL REFERENCES users(id),

    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,

    rent_amount INTEGER NOT NULL DEFAULT 0,

    -- Compatibility column for older deployed code/logs
    price INTEGER NOT NULL DEFAULT 0,

    deposit_amount INTEGER NOT NULL DEFAULT 0,
    bedrooms INTEGER NOT NULL DEFAULT 1,
    bathrooms INTEGER NOT NULL DEFAULT 1,

    city VARCHAR(120) NOT NULL,
    province VARCHAR(120) NOT NULL,
    suburb VARCHAR(120),
    address_line VARCHAR(255),
    formatted_address VARCHAR(500),
    google_place_id VARCHAR(255),
    approximate_address VARCHAR(255),

    address_visibility VARCHAR(40) NOT NULL DEFAULT 'approved_viewing',

    latitude DOUBLE PRECISION NULL,
    longitude DOUBLE PRECISION NULL,

    workplace_distance_km DOUBLE PRECISION NULL,
    nearest_transport VARCHAR(160),
    commute_notes TEXT,

    furnished BOOLEAN NOT NULL DEFAULT FALSE,
    pets_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    transport_access BOOLEAN NOT NULL DEFAULT FALSE,

    image_url VARCHAR(500),

    status VARCHAR(40) NOT NULL DEFAULT 'under_review',
    status_reason TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    view_count INTEGER NOT NULL DEFAULT 0,
    quality_score INTEGER NOT NULL DEFAULT 0,
    quality_score_details TEXT,

    expires_at TIMESTAMP NULL,
    renewed_at TIMESTAMP NULL,

    listing_verified BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at TIMESTAMP NULL,
    verified_by_id INTEGER NULL REFERENCES users(id),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS rent_amount INTEGER NOT NULL DEFAULT 0;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS price INTEGER NOT NULL DEFAULT 0;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS deposit_amount INTEGER NOT NULL DEFAULT 0;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS bedrooms INTEGER NOT NULL DEFAULT 1;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS bathrooms INTEGER NOT NULL DEFAULT 1;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS formatted_address VARCHAR(500);

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS google_place_id VARCHAR(255);

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS approximate_address VARCHAR(255);

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS address_visibility VARCHAR(40) NOT NULL DEFAULT 'approved_viewing';

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS workplace_distance_km DOUBLE PRECISION NULL;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS nearest_transport VARCHAR(160);

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS commute_notes TEXT;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS furnished BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS pets_allowed BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS transport_access BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS image_url VARCHAR(500);

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS status_reason TEXT;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS view_count INTEGER NOT NULL DEFAULT 0;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS quality_score INTEGER NOT NULL DEFAULT 0;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS quality_score_details TEXT;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP NULL;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS renewed_at TIMESTAMP NULL;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS listing_verified BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP NULL;

ALTER TABLE properties
ADD COLUMN IF NOT EXISTS verified_by_id INTEGER NULL;

CREATE INDEX IF NOT EXISTS ix_properties_landlord_id
ON properties(landlord_id);

CREATE INDEX IF NOT EXISTS ix_properties_city
ON properties(city);

CREATE INDEX IF NOT EXISTS ix_properties_province
ON properties(province);

CREATE INDEX IF NOT EXISTS ix_properties_google_place_id
ON properties(google_place_id);

CREATE INDEX IF NOT EXISTS ix_properties_latitude
ON properties(latitude);

CREATE INDEX IF NOT EXISTS ix_properties_longitude
ON properties(longitude);

CREATE INDEX IF NOT EXISTS ix_properties_status
ON properties(status);

CREATE INDEX IF NOT EXISTS ix_properties_is_active
ON properties(is_active);

CREATE INDEX IF NOT EXISTS ix_properties_search
ON properties(status, is_active, city, province, rent_amount);

CREATE INDEX IF NOT EXISTS ix_properties_geo
ON properties(latitude, longitude);


CREATE TABLE IF NOT EXISTS property_assets (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id),
    uploaded_by_id INTEGER NOT NULL REFERENCES users(id),

    kind VARCHAR(40) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    relative_path VARCHAR(500) NOT NULL,
    mime_type VARCHAR(120),
    size_bytes INTEGER NOT NULL DEFAULT 0,

    is_private BOOLEAN NOT NULL DEFAULT TRUE,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,

    review_status VARCHAR(40) NOT NULL DEFAULT 'pending',
    review_note TEXT,
    reviewed_by_id INTEGER NULL REFERENCES users(id),
    reviewed_at TIMESTAMP NULL,

    virus_scan_status VARCHAR(40) NOT NULL DEFAULT 'not_scanned',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_property_assets_stored_filename UNIQUE (stored_filename),
    CONSTRAINT uq_property_assets_relative_path UNIQUE (relative_path)
);

CREATE INDEX IF NOT EXISTS ix_property_assets_property_id
ON property_assets(property_id);

CREATE INDEX IF NOT EXISTS ix_property_assets_uploaded_by_id
ON property_assets(uploaded_by_id);

CREATE INDEX IF NOT EXISTS ix_property_assets_kind
ON property_assets(kind);

CREATE INDEX IF NOT EXISTS ix_property_assets_review_status
ON property_assets(review_status);

CREATE INDEX IF NOT EXISTS ix_property_assets_kind_property
ON property_assets(property_id, kind);

CREATE INDEX IF NOT EXISTS ix_property_assets_review
ON property_assets(kind, review_status);


CREATE TABLE IF NOT EXISTS rental_applications (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id),
    applicant_id INTEGER NOT NULL REFERENCES users(id),

    message TEXT,
    status VARCHAR(40) NOT NULL DEFAULT 'pending',

    -- New tenant subscription tracking field
    tenant_subscription_id INTEGER NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_application_property_applicant UNIQUE (property_id, applicant_id)
);

ALTER TABLE rental_applications
ADD COLUMN IF NOT EXISTS tenant_subscription_id INTEGER NULL;

CREATE INDEX IF NOT EXISTS ix_rental_applications_property_id
ON rental_applications(property_id);

CREATE INDEX IF NOT EXISTS ix_rental_applications_applicant_id
ON rental_applications(applicant_id);

CREATE INDEX IF NOT EXISTS ix_rental_applications_status
ON rental_applications(status);

CREATE INDEX IF NOT EXISTS ix_rental_applications_tenant_subscription_id
ON rental_applications(tenant_subscription_id);


CREATE TABLE IF NOT EXISTS user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    plan_id INTEGER NOT NULL REFERENCES subscription_plans(id),
    role VARCHAR(30) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'active',
    current_period_end TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_user_subscriptions_user_id
ON user_subscriptions(user_id);

CREATE INDEX IF NOT EXISTS ix_user_subscriptions_role
ON user_subscriptions(role);

CREATE INDEX IF NOT EXISTS ix_user_subscriptions_status
ON user_subscriptions(status);

UPDATE rental_applications
SET tenant_subscription_id = NULL
WHERE tenant_subscription_id IS NOT NULL
  AND tenant_subscription_id NOT IN (
      SELECT id FROM user_subscriptions
  );

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_rental_applications_tenant_subscription'
    ) THEN
        ALTER TABLE rental_applications
        ADD CONSTRAINT fk_rental_applications_tenant_subscription
        FOREIGN KEY (tenant_subscription_id)
        REFERENCES user_subscriptions(id)
        ON DELETE SET NULL;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    plan_id INTEGER NOT NULL REFERENCES subscription_plans(id),
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'ZAR',
    provider VARCHAR(40) NOT NULL DEFAULT 'disabled',
    provider_reference VARCHAR(160),
    status VARCHAR(40) NOT NULL DEFAULT 'pending',
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_invoices_user_id
ON invoices(user_id);

CREATE UNIQUE INDEX IF NOT EXISTS ix_invoices_provider_reference
ON invoices(provider_reference);

CREATE INDEX IF NOT EXISTS ix_invoices_status
ON invoices(status);


CREATE TABLE IF NOT EXISTS listing_reports (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id),
    reporter_id INTEGER NULL REFERENCES users(id),
    reason VARCHAR(120) NOT NULL,
    details TEXT,
    status VARCHAR(40) NOT NULL DEFAULT 'open',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_listing_reports_property_id
ON listing_reports(property_id);

CREATE INDEX IF NOT EXISTS ix_listing_reports_reporter_id
ON listing_reports(reporter_id);

CREATE INDEX IF NOT EXISTS ix_listing_reports_status
ON listing_reports(status);


CREATE TABLE IF NOT EXISTS landlord_verifications (
    id SERIAL PRIMARY KEY,
    landlord_id INTEGER NOT NULL REFERENCES users(id),
    document_path VARCHAR(500) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'pending',
    reviewed_by_id INTEGER NULL REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_landlord_verifications_landlord_id
ON landlord_verifications(landlord_id);

CREATE INDEX IF NOT EXISTS ix_landlord_verifications_status
ON landlord_verifications(status);


CREATE TABLE IF NOT EXISTS landlord_applications (
    id SERIAL PRIMARY KEY,
    applicant_id INTEGER NOT NULL,
    property_id INTEGER NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'pending',
    message TEXT NULL,
    admin_note TEXT NULL,
    reviewed_by_id INTEGER NULL,
    reviewed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DELETE FROM landlord_applications
WHERE applicant_id IS NOT NULL
  AND applicant_id NOT IN (
      SELECT id FROM users
  );

UPDATE landlord_applications
SET property_id = NULL
WHERE property_id IS NOT NULL
  AND property_id NOT IN (
      SELECT id FROM properties
  );

UPDATE landlord_applications
SET reviewed_by_id = NULL
WHERE reviewed_by_id IS NOT NULL
  AND reviewed_by_id NOT IN (
      SELECT id FROM users
  );

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_landlord_applications_applicant'
    ) THEN
        ALTER TABLE landlord_applications
        ADD CONSTRAINT fk_landlord_applications_applicant
        FOREIGN KEY (applicant_id)
        REFERENCES users(id)
        ON DELETE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_landlord_applications_property'
    ) THEN
        ALTER TABLE landlord_applications
        ADD CONSTRAINT fk_landlord_applications_property
        FOREIGN KEY (property_id)
        REFERENCES properties(id)
        ON DELETE SET NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_landlord_applications_reviewed_by'
    ) THEN
        ALTER TABLE landlord_applications
        ADD CONSTRAINT fk_landlord_applications_reviewed_by
        FOREIGN KEY (reviewed_by_id)
        REFERENCES users(id)
        ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_landlord_applications_applicant_id
ON landlord_applications(applicant_id);

CREATE INDEX IF NOT EXISTS ix_landlord_applications_property_id
ON landlord_applications(property_id);

CREATE INDEX IF NOT EXISTS ix_landlord_applications_status
ON landlord_applications(status);

CREATE INDEX IF NOT EXISTS ix_landlord_applications_applicant_status
ON landlord_applications(applicant_id, status);

CREATE INDEX IF NOT EXISTS ix_landlord_applications_status_created
ON landlord_applications(status, created_at);


CREATE TABLE IF NOT EXISTS saved_searches (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    name VARCHAR(120) NOT NULL,

    city VARCHAR(120),
    province VARCHAR(120),
    max_rent INTEGER,
    min_bedrooms INTEGER,
    furnished BOOLEAN,
    pets_allowed BOOLEAN,
    transport_access BOOLEAN,

    workplace_address VARCHAR(500),
    workplace_formatted_address VARCHAR(500),
    workplace_place_id VARCHAR(255),
    workplace_area VARCHAR(160),
    workplace_latitude DOUBLE PRECISION,
    workplace_longitude DOUBLE PRECISION,

    travel_mode VARCHAR(40) NOT NULL DEFAULT 'all',
    max_distance_km DOUBLE PRECISION,
    max_travel_minutes INTEGER,

    alerts_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_alerted_at TIMESTAMP NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_saved_search_user_name UNIQUE (user_id, name)
);

CREATE INDEX IF NOT EXISTS ix_saved_searches_user_id
ON saved_searches(user_id);

CREATE INDEX IF NOT EXISTS ix_saved_searches_city
ON saved_searches(city);

CREATE INDEX IF NOT EXISTS ix_saved_searches_province
ON saved_searches(province);

CREATE INDEX IF NOT EXISTS ix_saved_searches_workplace_place_id
ON saved_searches(workplace_place_id);

CREATE INDEX IF NOT EXISTS ix_saved_searches_workplace_area
ON saved_searches(workplace_area);


CREATE TABLE IF NOT EXISTS conversation_threads (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id),
    tenant_id INTEGER NOT NULL REFERENCES users(id),
    landlord_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(40) NOT NULL DEFAULT 'open',
    last_message_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_thread_property_tenant_landlord
    UNIQUE (property_id, tenant_id, landlord_id)
);

CREATE INDEX IF NOT EXISTS ix_conversation_threads_property_id
ON conversation_threads(property_id);

CREATE INDEX IF NOT EXISTS ix_conversation_threads_tenant_id
ON conversation_threads(tenant_id);

CREATE INDEX IF NOT EXISTS ix_conversation_threads_landlord_id
ON conversation_threads(landlord_id);


CREATE TABLE IF NOT EXISTS conversation_messages (
    id SERIAL PRIMARY KEY,
    thread_id INTEGER NOT NULL REFERENCES conversation_threads(id),
    sender_id INTEGER NOT NULL REFERENCES users(id),
    body TEXT NOT NULL,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_conversation_messages_thread_id
ON conversation_messages(thread_id);

CREATE INDEX IF NOT EXISTS ix_conversation_messages_sender_id
ON conversation_messages(sender_id);


CREATE TABLE IF NOT EXISTS viewing_appointments (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id),
    tenant_id INTEGER NOT NULL REFERENCES users(id),
    landlord_id INTEGER NOT NULL REFERENCES users(id),
    requested_start TIMESTAMP NOT NULL,
    requested_end TIMESTAMP NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'pending',
    tenant_note TEXT,
    landlord_note TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_viewing_appointments_property_id
ON viewing_appointments(property_id);

CREATE INDEX IF NOT EXISTS ix_viewing_appointments_tenant_id
ON viewing_appointments(tenant_id);

CREATE INDEX IF NOT EXISTS ix_viewing_appointments_landlord_id
ON viewing_appointments(landlord_id);

CREATE INDEX IF NOT EXISTS ix_viewing_appointments_status
ON viewing_appointments(status);


CREATE TABLE IF NOT EXISTS user_audit_logs (
    id SERIAL PRIMARY KEY,
    actor_id INTEGER NULL REFERENCES users(id),
    action VARCHAR(120) NOT NULL,
    target_type VARCHAR(80),
    target_id VARCHAR(80),
    ip_address VARCHAR(64),
    user_agent VARCHAR(255),
    metadata_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_user_audit_logs_actor_id
ON user_audit_logs(actor_id);

CREATE INDEX IF NOT EXISTS ix_user_audit_logs_action
ON user_audit_logs(action);


CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token_hash VARCHAR(64) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_email_verification_tokens_user_id
ON email_verification_tokens(user_id);

CREATE UNIQUE INDEX IF NOT EXISTS ix_email_verification_tokens_token_hash
ON email_verification_tokens(token_hash);


CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token_hash VARCHAR(64) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_user_id
ON password_reset_tokens(user_id);

CREATE UNIQUE INDEX IF NOT EXISTS ix_password_reset_tokens_token_hash
ON password_reset_tokens(token_hash);


CREATE TABLE IF NOT EXISTS places_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NULL REFERENCES users(id),
    token_hash VARCHAR(64) NOT NULL,
    purpose VARCHAR(80) NOT NULL DEFAULT 'workplace_search',
    selected_place_id VARCHAR(255),
    selected_description VARCHAR(500),
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_places_sessions_user_id
ON places_sessions(user_id);

CREATE UNIQUE INDEX IF NOT EXISTS ix_places_sessions_token_hash
ON places_sessions(token_hash);


CREATE TABLE IF NOT EXISTS rental_reviews (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id),
    tenant_id INTEGER NOT NULL REFERENCES users(id),
    landlord_id INTEGER NOT NULL REFERENCES users(id),

    rating INTEGER NOT NULL,
    accuracy_rating INTEGER NULL,
    safety_rating INTEGER NULL,
    commute_rating INTEGER NULL,
    landlord_communication_rating INTEGER NULL,

    title VARCHAR(140) NOT NULL,
    comment TEXT NOT NULL,

    status VARCHAR(40) NOT NULL DEFAULT 'pending',
    admin_note TEXT,
    reviewed_by_id INTEGER NULL REFERENCES users(id),
    reviewed_at TIMESTAMP NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_rental_review_property_tenant
    UNIQUE (property_id, tenant_id),

    CONSTRAINT ck_rental_reviews_rating_range
    CHECK (rating >= 1 AND rating <= 5)
);

CREATE INDEX IF NOT EXISTS ix_rental_reviews_property_id
ON rental_reviews(property_id);

CREATE INDEX IF NOT EXISTS ix_rental_reviews_tenant_id
ON rental_reviews(tenant_id);

CREATE INDEX IF NOT EXISTS ix_rental_reviews_landlord_id
ON rental_reviews(landlord_id);

CREATE INDEX IF NOT EXISTS ix_rental_reviews_status
ON rental_reviews(status);


INSERT INTO subscription_plans (
    name,
    role,
    price_cents,
    currency,
    max_active_listings,
    max_rental_applications,
    is_active,
    created_at,
    updated_at
)
VALUES
    (
        'Tenant Plus',
        'tenant',
        5000,
        'ZAR',
        NULL,
        10,
        TRUE,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ),
    (
        'Landlord Pro',
        'landlord',
        10000,
        'ZAR',
        25,
        0,
        TRUE,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
ON CONFLICT (name)
DO UPDATE SET
    role = EXCLUDED.role,
    price_cents = EXCLUDED.price_cents,
    currency = EXCLUDED.currency,
    max_active_listings = EXCLUDED.max_active_listings,
    max_rental_applications = EXCLUDED.max_rental_applications,
    is_active = TRUE,
    updated_at = CURRENT_TIMESTAMP;


UPDATE subscription_plans
SET currency = 'ZAR'
WHERE currency IS NULL;

UPDATE subscription_plans
SET max_rental_applications = 10
WHERE role = 'tenant';

UPDATE subscription_plans
SET max_rental_applications = 0
WHERE role = 'landlord';

UPDATE subscription_plans
SET is_active = TRUE
WHERE is_active IS NULL;

UPDATE users
SET can_act_as_tenant = TRUE
WHERE can_act_as_tenant IS NULL;

UPDATE users
SET can_act_as_landlord = FALSE
WHERE can_act_as_landlord IS NULL;

UPDATE users
SET is_admin = FALSE
WHERE is_admin IS NULL;

UPDATE users
SET is_active_account = TRUE
WHERE is_active_account IS NULL;

UPDATE users
SET email_verified = FALSE
WHERE email_verified IS NULL;

UPDATE properties
SET price = rent_amount
WHERE price = 0
  AND rent_amount IS NOT NULL
  AND rent_amount > 0;

UPDATE properties
SET rent_amount = price
WHERE rent_amount = 0
  AND price IS NOT NULL
  AND price > 0;


COMMIT;


SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

SELECT column_name
FROM information_schema.columns
WHERE table_name = 'subscription_plans'
ORDER BY ordinal_position;

SELECT column_name
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;

SELECT column_name
FROM information_schema.columns
WHERE table_name = 'rental_applications'
ORDER BY ordinal_position;

SELECT table_name
FROM information_schema.tables
WHERE table_name = 'landlord_applications';
