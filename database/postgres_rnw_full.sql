-- RNW Production Database Schema - PostgreSQL 14+
-- Generated for the upgraded RNW Flask SaaS project.

DROP TABLE IF EXISTS admin_audit_logs CASCADE;
DROP TABLE IF EXISTS billing_invoices CASCADE;
DROP TABLE IF EXISTS user_subscriptions CASCADE;
DROP TABLE IF EXISTS landlord_subscriptions CASCADE;
DROP TABLE IF EXISTS rental_applications CASCADE;
DROP TABLE IF EXISTS inquiries CASCADE;
DROP TABLE IF EXISTS search_history CASCADE;
DROP TABLE IF EXISTS saved_properties CASCADE;
DROP TABLE IF EXISTS property_photos CASCADE;
DROP TABLE IF EXISTS properties CASCADE;
DROP TABLE IF EXISTS landlord_verifications CASCADE;
DROP TABLE IF EXISTS login_attempts CASCADE;
DROP TABLE IF EXISTS auth_tokens CASCADE;
DROP TABLE IF EXISTS subscription_plans CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    id_number VARCHAR(13) UNIQUE,
    role VARCHAR(20) NOT NULL DEFAULT 'tenant',
    province VARCHAR(50),
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    email_verified_at TIMESTAMP NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMP NULL,
    last_password_reset_at TIMESTAMP NULL,
    profile_picture VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

CREATE TABLE subscription_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    role VARCHAR(20) NOT NULL DEFAULT 'landlord',
    price DOUBLE PRECISION NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'ZAR',
    billing_period VARCHAR(20) NOT NULL DEFAULT 'monthly',
    max_listings INTEGER NOT NULL DEFAULT 0,
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    support_level VARCHAR(50) DEFAULT 'Basic',
    features TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_subscription_plans_role ON subscription_plans(role);

CREATE TABLE auth_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(128) NOT NULL UNIQUE,
    purpose VARCHAR(30) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_auth_tokens_user_id ON auth_tokens(user_id);
CREATE INDEX idx_auth_tokens_token_hash ON auth_tokens(token_hash);
CREATE INDEX idx_auth_tokens_purpose ON auth_tokens(purpose);

CREATE TABLE login_attempts (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) NOT NULL,
    ip_address VARCHAR(45),
    success BOOLEAN NOT NULL DEFAULT FALSE,
    attempted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_login_attempts_email ON login_attempts(email);
CREATE INDEX idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX idx_login_attempts_success ON login_attempts(success);
CREATE INDEX idx_login_attempts_time ON login_attempts(attempted_at);

CREATE TABLE landlord_verifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    id_document_url VARCHAR(255) NOT NULL,
    proof_of_address_url VARCHAR(255) NOT NULL,
    tax_clearance_url VARCHAR(255),
    business_registration_url VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    verified_by INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    verified_at TIMESTAMP NULL,
    rejection_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_landlord_verifications_status ON landlord_verifications(status);

CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    landlord_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    property_type VARCHAR(50) NOT NULL,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    province VARCHAR(50) NOT NULL,
    postal_code VARCHAR(10),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    price DOUBLE PRECISION NOT NULL,
    deposit_amount DOUBLE PRECISION,
    bedrooms INTEGER DEFAULT 0,
    bathrooms DOUBLE PRECISION DEFAULT 0,
    parking INTEGER DEFAULT 0,
    area_sqm DOUBLE PRECISION,
    pets_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    furnished BOOLEAN NOT NULL DEFAULT FALSE,
    transport_access VARCHAR(255),
    available_date DATE,
    minimum_lease INTEGER DEFAULT 12,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    view_count INTEGER NOT NULL DEFAULT 0,
    featured_until TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_properties_landlord_id ON properties(landlord_id);
CREATE INDEX idx_properties_type ON properties(property_type);
CREATE INDEX idx_properties_city ON properties(city);
CREATE INDEX idx_properties_province ON properties(province);
CREATE INDEX idx_properties_price ON properties(price);
CREATE INDEX idx_properties_deposit_amount ON properties(deposit_amount);
CREATE INDEX idx_properties_furnished ON properties(furnished);
CREATE INDEX idx_properties_status ON properties(status);
CREATE INDEX idx_properties_location ON properties(latitude, longitude);
CREATE INDEX idx_properties_search ON properties(status, is_available, city, province, price);

CREATE TABLE property_photos (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    photo_url VARCHAR(255) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_property_photos_property_id ON property_photos(property_id);

CREATE TABLE saved_properties (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_saved_property UNIQUE(user_id, property_id)
);
CREATE INDEX idx_saved_properties_user_id ON saved_properties(user_id);
CREATE INDEX idx_saved_properties_property_id ON saved_properties(property_id);

CREATE TABLE search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    search_address VARCHAR(255),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    radius_km DOUBLE PRECISION DEFAULT 5,
    min_price DOUBLE PRECISION,
    max_price DOUBLE PRECISION,
    bedrooms INTEGER,
    property_type VARCHAR(50),
    result_count INTEGER DEFAULT 0,
    session_id VARCHAR(100),
    searched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_search_history_user_id ON search_history(user_id);
CREATE INDEX idx_search_history_searched_at ON search_history(searched_at);

CREATE TABLE inquiries (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_inquiries_property_id ON inquiries(property_id);
CREATE INDEX idx_inquiries_sender_id ON inquiries(sender_id);
CREATE INDEX idx_inquiries_recipient_id ON inquiries(recipient_id);

CREATE TABLE rental_applications (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    applicant_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    message TEXT,
    monthly_income DOUBLE PRECISION,
    employment_status VARCHAR(50),
    employer_name VARCHAR(100),
    years_employed DOUBLE PRECISION,
    has_pets BOOLEAN NOT NULL DEFAULT FALSE,
    number_of_occupants INTEGER DEFAULT 1,
    move_in_date DATE,
    lease_term INTEGER DEFAULT 12,
    rating INTEGER,
    review_text TEXT,
    reviewed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_property_applicant UNIQUE(property_id, applicant_id)
);
CREATE INDEX idx_rental_applications_status ON rental_applications(status);
CREATE INDEX idx_rental_applications_property_id ON rental_applications(property_id);
CREATE INDEX idx_rental_applications_applicant_id ON rental_applications(applicant_id);

CREATE TABLE user_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id INTEGER NOT NULL REFERENCES subscription_plans(id) ON DELETE RESTRICT,
    provider VARCHAR(30) NOT NULL DEFAULT 'manual',
    reference VARCHAR(120) UNIQUE,
    amount DOUBLE PRECISION NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'ZAR',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP NULL,
    auto_renew BOOLEAN NOT NULL DEFAULT TRUE,
    cancelled_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_status ON user_subscriptions(status);

CREATE TABLE billing_invoices (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id INTEGER NOT NULL REFERENCES subscription_plans(id) ON DELETE RESTRICT,
    subscription_id INTEGER NULL REFERENCES user_subscriptions(id) ON DELETE SET NULL,
    provider VARCHAR(30) NOT NULL DEFAULT 'manual',
    reference VARCHAR(120) NOT NULL UNIQUE,
    external_id VARCHAR(120),
    amount DOUBLE PRECISION NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'ZAR',
    description VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    checkout_url TEXT,
    due_date TIMESTAMP NULL,
    paid_at TIMESTAMP NULL,
    failed_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_billing_invoices_user_id ON billing_invoices(user_id);
CREATE INDEX idx_billing_invoices_reference ON billing_invoices(reference);
CREATE INDEX idx_billing_invoices_status ON billing_invoices(status);

CREATE TABLE landlord_subscriptions (
    id SERIAL PRIMARY KEY,
    landlord_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id INTEGER NOT NULL REFERENCES subscription_plans(id) ON DELETE RESTRICT,
    start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    auto_renew BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admin_audit_logs (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id INTEGER,
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_admin_audit_logs_admin_id ON admin_audit_logs(admin_id);

-- RNW Demo Seed Data - PostgreSQL 14+
-- Demo login details:
--   Admin:    admin@rnw.local / AdminPass123!
--   Landlord: landlord@rnw.local / LandlordPass123!
--   Tenant:   tenant@rnw.local / TenantPass123!

INSERT INTO subscription_plans
(id, name, role, price, currency, billing_period, max_listings, is_featured, support_level, features, is_active, created_at, updated_at)
VALUES
(1, 'Tenant Plus', 'tenant', 50.00, 'ZAR', 'monthly', 0, false, 'Basic', 'Save properties;Apply for rentals;AI recommendations;Application tracking', true, NOW(), NOW()),
(2, 'Landlord Pro', 'landlord', 100.00, 'ZAR', 'monthly', 25, true, 'Priority', 'Create listings;Receive rental applications;Landlord analytics;Verification support;Up to 25 active listings', true, NOW(), NOW())
ON CONFLICT (name) DO UPDATE SET
    price = EXCLUDED.price,
    max_listings = EXCLUDED.max_listings,
    features = EXCLUDED.features,
    updated_at = NOW();

INSERT INTO users
(id, email, password_hash, first_name, last_name, phone, id_number, role, province, is_verified, email_verified_at, is_active, last_password_reset_at, created_at, updated_at)
VALUES
(1, 'admin@rnw.local', 'pbkdf2:sha256:1000000$rnwAdminSalt$118207af89a54c186596b1e673004510d29b99a2535cdf2916c07136271b9c94', 'RNW', 'Admin', '0710000001', NULL, 'admin', 'Gauteng', true, NOW(), true, NOW(), NOW(), NOW()),
(2, 'landlord@rnw.local', 'pbkdf2:sha256:1000000$rnwLandlordSalt$7d22098e9916894f8dcb209751a6eb719d36e0b51c9f770b03a6d49b576085e1', 'Lindiwe', 'Mkhize', '0710000002', NULL, 'landlord', 'KwaZulu-Natal', true, NOW(), true, NOW(), NOW(), NOW()),
(3, 'tenant@rnw.local', 'pbkdf2:sha256:1000000$rnwTenantSalt$a12aa2a7715bad3e9378a42853b262153c36495d0f2acd9937673acd3bcbf196', 'Thabo', 'Dlamini', '0710000003', NULL, 'tenant', 'KwaZulu-Natal', false, NOW(), true, NOW(), NOW(), NOW())
ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    role = EXCLUDED.role,
    is_active = true,
    email_verified_at = EXCLUDED.email_verified_at,
    updated_at = NOW();

INSERT INTO user_subscriptions
(id, user_id, plan_id, provider, reference, amount, currency, status, start_date, end_date, auto_renew, created_at, updated_at)
VALUES
(1, 3, 1, 'seed', 'SEED-TENANT-PLUS-001', 50.00, 'ZAR', 'active', NOW(), NOW() + INTERVAL '30 days', true, NOW(), NOW()),
(2, 2, 2, 'seed', 'SEED-LANDLORD-PRO-001', 100.00, 'ZAR', 'active', NOW(), NOW() + INTERVAL '30 days', true, NOW(), NOW())
ON CONFLICT (reference) DO UPDATE SET
    status = 'active',
    end_date = NOW() + INTERVAL '30 days',
    updated_at = NOW();

INSERT INTO billing_invoices
(id, user_id, plan_id, subscription_id, provider, reference, amount, currency, description, status, paid_at, created_at, updated_at)
VALUES
(1, 3, 1, 1, 'seed', 'INV-SEED-TENANT-001', 50.00, 'ZAR', 'Tenant Plus monthly subscription', 'paid', NOW(), NOW(), NOW()),
(2, 2, 2, 'seed', 'INV-SEED-LANDLORD-001', 100.00, 'ZAR', 'Landlord Pro monthly subscription', 'paid', NOW(), NOW(), NOW())
ON CONFLICT (reference) DO UPDATE SET
    status = 'paid',
    paid_at = EXCLUDED.paid_at,
    updated_at = NOW();

INSERT INTO landlord_verifications
(id, user_id, id_document_url, proof_of_address_url, tax_clearance_url, business_registration_url, status, verified_by, verified_at, created_at, updated_at)
VALUES
(1, 2, 'private/landlord_verifications/demo/id_document.pdf', 'private/landlord_verifications/demo/proof_of_address.pdf', NULL, NULL, 'verified', 1, NOW(), NOW(), NOW())
ON CONFLICT (user_id) DO UPDATE SET
    status = 'verified',
    verified_by = 1,
    verified_at = NOW(),
    updated_at = NOW();

INSERT INTO properties
(id, landlord_id, title, description, property_type, address, city, province, postal_code, latitude, longitude, price, deposit_amount, bedrooms, bathrooms, parking, area_sqm, pets_allowed, furnished, transport_access, available_date, minimum_lease, is_available, status, view_count, created_at, updated_at)
VALUES
(1, 2, 'Modern Room Near Empangeni CBD', 'Secure furnished room close to transport, shops, and workplaces.', 'room', 'Main Road, Empangeni', 'Empangeni', 'KwaZulu-Natal', '3880', -28.7619, 31.8932, 3200.00, 3200.00, 1, 1.0, 1, 28.0, false, true, 'Taxi rank 500m away; close to CBD', CURRENT_DATE, 12, true, 'approved', 18, NOW(), NOW()),
(2, 2, 'Two Bedroom Apartment in Richards Bay', 'Family-friendly apartment with parking and quick access to industrial areas.', 'apartment', 'Meerensee, Richards Bay', 'Richards Bay', 'KwaZulu-Natal', '3901', -28.7807, 32.0383, 7200.00, 7200.00, 2, 1.5, 1, 68.0, true, false, 'Quick access to industrial areas and public transport', CURRENT_DATE, 12, true, 'approved', 11, NOW(), NOW()),
(3, 2, 'Studio Apartment in Sandton', 'Compact studio for professionals near offices and Gautrain.', 'studio', 'Rivonia Road, Sandton', 'Sandton', 'Gauteng', '2196', -26.1076, 28.0567, 8500.00, 8500.00, 0, 1.0, 1, 38.0, false, true, 'Near Gautrain and office nodes', CURRENT_DATE, 12, true, 'approved', 23, NOW(), NOW()),
(4, 2, 'Affordable Cottage Near University of Zululand', 'Quiet cottage suitable for students or young professionals, close to transport.', 'cottage', 'KwaDlangezwa Road', 'Empangeni', 'KwaZulu-Natal', '3886', -28.8503, 31.8492, 4100.00, 4100.00, 1, 1.0, 1, 35.0, false, false, 'Taxi route nearby; short drive to university', CURRENT_DATE, 6, true, 'approved', 7, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    price = EXCLUDED.price,
    deposit_amount = EXCLUDED.deposit_amount,
    status = EXCLUDED.status,
    updated_at = NOW();

INSERT INTO property_photos
(id, property_id, photo_url, is_primary, uploaded_at)
VALUES
(1, 1, '/static/img/demo/empangeni-room.jpg', true, NOW()),
(2, 2, '/static/img/demo/richards-bay-apartment.jpg', true, NOW()),
(3, 3, '/static/img/demo/sandton-studio.jpg', true, NOW()),
(4, 4, '/static/img/demo/unizulu-cottage.jpg', true, NOW())
ON CONFLICT (id) DO UPDATE SET
    photo_url = EXCLUDED.photo_url,
    is_primary = EXCLUDED.is_primary;

INSERT INTO saved_properties
(id, user_id, property_id, saved_at)
VALUES
(1, 3, 1, NOW()),
(2, 3, 4, NOW())
ON CONFLICT (user_id, property_id) DO UPDATE SET saved_at = EXCLUDED.saved_at;

INSERT INTO rental_applications
(id, property_id, applicant_id, status, message, monthly_income, employment_status, employer_name, years_employed, has_pets, number_of_occupants, move_in_date, lease_term, created_at, updated_at)
VALUES
(1, 1, 3, 'pending', 'I work near Empangeni CBD and would like to view this room.', 12500.00, 'employed', 'Empangeni Retail Group', 2.0, false, 1, CURRENT_DATE + INTERVAL '14 days', 12, NOW(), NOW())
ON CONFLICT (property_id, applicant_id) DO UPDATE SET
    status = EXCLUDED.status,
    message = EXCLUDED.message,
    updated_at = NOW();

INSERT INTO inquiries
(id, property_id, sender_id, recipient_id, message, is_read, created_at, updated_at)
VALUES
(1, 1, 3, 2, 'Hi, is this room still available for viewing this weekend?', false, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    message = EXCLUDED.message,
    is_read = EXCLUDED.is_read,
    updated_at = NOW();

INSERT INTO search_history
(id, user_id, search_address, latitude, longitude, radius_km, min_price, max_price, bedrooms, property_type, result_count, session_id, searched_at)
VALUES
(1, 3, 'Empangeni CBD', -28.7619, 31.8932, 10, 2500.00, 5000.00, 1, 'room', 2, 'demo-session', NOW())
ON CONFLICT (id) DO UPDATE SET searched_at = NOW();

INSERT INTO admin_audit_logs
(id, admin_id, action, target_type, target_id, details, ip_address, created_at, updated_at)
VALUES
(1, 1, 'seed_database', 'system', NULL, 'Demo RNW database seeded successfully.', '127.0.0.1', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET updated_at = NOW();

SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE(MAX(id), 1), true) FROM users;
SELECT setval(pg_get_serial_sequence('subscription_plans', 'id'), COALESCE(MAX(id), 1), true) FROM subscription_plans;
SELECT setval(pg_get_serial_sequence('properties', 'id'), COALESCE(MAX(id), 1), true) FROM properties;
SELECT setval(pg_get_serial_sequence('property_photos', 'id'), COALESCE(MAX(id), 1), true) FROM property_photos;
SELECT setval(pg_get_serial_sequence('user_subscriptions', 'id'), COALESCE(MAX(id), 1), true) FROM user_subscriptions;
SELECT setval(pg_get_serial_sequence('billing_invoices', 'id'), COALESCE(MAX(id), 1), true) FROM billing_invoices;

-- Real launch / trust layer tables
CREATE TABLE IF NOT EXISTS property_reviews (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    reviewer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    landlord_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rental_application_id INTEGER NULL REFERENCES rental_applications(id) ON DELETE SET NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(120) NOT NULL,
    comment TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    landlord_response TEXT,
    landlord_responded_at TIMESTAMP NULL,
    moderated_by INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    moderated_at TIMESTAMP NULL,
    rejection_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_property_reviewer UNIQUE (property_id, reviewer_id)
);
CREATE INDEX IF NOT EXISTS idx_property_reviews_status ON property_reviews(status);
CREATE INDEX IF NOT EXISTS idx_property_reviews_property_id ON property_reviews(property_id);

CREATE TABLE IF NOT EXISTS listing_reports (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    reporter_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    reporter_name VARCHAR(120),
    reporter_email VARCHAR(120),
    reason VARCHAR(80) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    admin_notes TEXT,
    resolved_by INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_listing_reports_status ON listing_reports(status);
CREATE INDEX IF NOT EXISTS idx_listing_reports_property_id ON listing_reports(property_id);

CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'general',
    subject VARCHAR(160) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    assigned_to INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    admin_response TEXT,
    responded_at TIMESTAMP NULL,
    closed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_support_tickets_email ON support_tickets(email);

CREATE TABLE IF NOT EXISTS legal_consents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(120),
    consent_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL DEFAULT '2026-06',
    accepted BOOLEAN NOT NULL DEFAULT TRUE,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    accepted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_legal_consents_user_id ON legal_consents(user_id);
CREATE INDEX IF NOT EXISTS idx_legal_consents_type ON legal_consents(consent_type);

CREATE TABLE IF NOT EXISTS payment_webhook_logs (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(30) NOT NULL,
    reference VARCHAR(120),
    external_id VARCHAR(120),
    status VARCHAR(50),
    valid_signature BOOLEAN NOT NULL DEFAULT FALSE,
    payload TEXT NOT NULL,
    processed_at TIMESTAMP NULL,
    error TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_payment_webhook_logs_provider ON payment_webhook_logs(provider);
CREATE INDEX IF NOT EXISTS idx_payment_webhook_logs_reference ON payment_webhook_logs(reference);
CREATE INDEX IF NOT EXISTS idx_payment_webhook_logs_status ON payment_webhook_logs(status);

-- Real launch demo trust/review data
INSERT INTO rental_applications
(id, property_id, applicant_id, status, message, monthly_income, employment_status, employer_name, years_employed, has_pets, number_of_occupants, lease_term, created_at, updated_at)
VALUES
(1, 1, 3, 'approved', 'I work near Empangeni CBD and need a safe room.', 12500.00, 'employed', 'Demo Employer', 2.0, FALSE, 1, 12, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (property_id, applicant_id) DO UPDATE SET status='approved', updated_at=CURRENT_TIMESTAMP;

INSERT INTO property_reviews
(id, property_id, reviewer_id, landlord_id, rental_application_id, rating, title, comment, status, created_at, updated_at)
VALUES
(1, 1, 3, 2, 1, 5, 'Great location for work', 'The room is close to transport and the listing details were accurate.', 'approved', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (property_id, reviewer_id) DO UPDATE SET rating=EXCLUDED.rating, status='approved', updated_at=CURRENT_TIMESTAMP;

INSERT INTO support_tickets
(id, user_id, name, email, category, subject, message, status, priority, created_at, updated_at)
VALUES
(1, 3, 'Thabo Dlamini', 'tenant@rnw.local', 'billing', 'Demo payment question', 'I want to confirm my Tenant Plus subscription.', 'open', 'high', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (id) DO NOTHING;
