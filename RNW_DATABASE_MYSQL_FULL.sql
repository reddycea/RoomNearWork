-- RNW Production Database Schema - MySQL 8+
-- Generated for the upgraded RNW Flask SaaS project.
-- Default database name: rnw

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS admin_audit_logs;
DROP TABLE IF EXISTS billing_invoices;
DROP TABLE IF EXISTS user_subscriptions;
DROP TABLE IF EXISTS landlord_subscriptions;
DROP TABLE IF EXISTS rental_applications;
DROP TABLE IF EXISTS inquiries;
DROP TABLE IF EXISTS search_history;
DROP TABLE IF EXISTS saved_properties;
DROP TABLE IF EXISTS property_photos;
DROP TABLE IF EXISTS properties;
DROP TABLE IF EXISTS landlord_verifications;
DROP TABLE IF EXISTS login_attempts;
DROP TABLE IF EXISTS auth_tokens;
DROP TABLE IF EXISTS subscription_plans;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    id_number VARCHAR(13) UNIQUE,
    role VARCHAR(20) NOT NULL DEFAULT 'tenant',
    province VARCHAR(50),
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    email_verified_at DATETIME NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login DATETIME NULL,
    last_password_reset_at DATETIME NULL,
    profile_picture VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE subscription_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    role VARCHAR(20) NOT NULL DEFAULT 'landlord',
    price DOUBLE NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'ZAR',
    billing_period VARCHAR(20) NOT NULL DEFAULT 'monthly',
    max_listings INT NOT NULL DEFAULT 0,
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    support_level VARCHAR(50) DEFAULT 'Basic',
    features TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_subscription_plans_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE auth_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token_hash VARCHAR(128) NOT NULL UNIQUE,
    purpose VARCHAR(30) NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_auth_tokens_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_auth_tokens_user_id (user_id),
    INDEX idx_auth_tokens_token_hash (token_hash),
    INDEX idx_auth_tokens_purpose (purpose)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE login_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) NOT NULL,
    ip_address VARCHAR(45),
    success BOOLEAN NOT NULL DEFAULT FALSE,
    attempted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_login_attempts_email (email),
    INDEX idx_login_attempts_ip (ip_address),
    INDEX idx_login_attempts_success (success),
    INDEX idx_login_attempts_time (attempted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE landlord_verifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    id_document_url VARCHAR(255) NOT NULL,
    proof_of_address_url VARCHAR(255) NOT NULL,
    tax_clearance_url VARCHAR(255),
    business_registration_url VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    verified_by INT NULL,
    verified_at DATETIME NULL,
    rejection_reason TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_landlord_verifications_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_landlord_verifications_verified_by FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_landlord_verifications_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE properties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    landlord_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    property_type VARCHAR(50) NOT NULL,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    province VARCHAR(50) NOT NULL,
    postal_code VARCHAR(10),
    latitude DOUBLE,
    longitude DOUBLE,
    price DOUBLE NOT NULL,
    deposit_amount DOUBLE,
    bedrooms INT DEFAULT 0,
    bathrooms DOUBLE DEFAULT 0,
    parking INT DEFAULT 0,
    area_sqm DOUBLE,
    pets_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    furnished BOOLEAN NOT NULL DEFAULT FALSE,
    transport_access VARCHAR(255),
    available_date DATE,
    minimum_lease INT DEFAULT 12,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    view_count INT NOT NULL DEFAULT 0,
    featured_until DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_properties_landlord FOREIGN KEY (landlord_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_properties_landlord_id (landlord_id),
    INDEX idx_properties_type (property_type),
    INDEX idx_properties_city (city),
    INDEX idx_properties_province (province),
    INDEX idx_properties_price (price),
    INDEX idx_properties_deposit_amount (deposit_amount),
    INDEX idx_properties_furnished (furnished),
    INDEX idx_properties_status (status),
    INDEX idx_properties_location (latitude, longitude),
    INDEX idx_properties_search (status, is_available, city, province, price)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE property_photos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    photo_url VARCHAR(255) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_property_photos_property FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
    INDEX idx_property_photos_property_id (property_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE saved_properties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    property_id INT NOT NULL,
    saved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_saved_properties_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_saved_properties_property FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
    UNIQUE KEY uq_saved_property (user_id, property_id),
    INDEX idx_saved_properties_user_id (user_id),
    INDEX idx_saved_properties_property_id (property_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE search_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    search_address VARCHAR(255),
    latitude DOUBLE,
    longitude DOUBLE,
    radius_km DOUBLE DEFAULT 5,
    min_price DOUBLE,
    max_price DOUBLE,
    bedrooms INT,
    property_type VARCHAR(50),
    result_count INT DEFAULT 0,
    session_id VARCHAR(100),
    searched_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_search_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_search_history_user_id (user_id),
    INDEX idx_search_history_searched_at (searched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE inquiries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    sender_id INT NOT NULL,
    recipient_id INT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_inquiries_property FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
    CONSTRAINT fk_inquiries_sender FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_inquiries_recipient FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_inquiries_property_id (property_id),
    INDEX idx_inquiries_sender_id (sender_id),
    INDEX idx_inquiries_recipient_id (recipient_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE rental_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    applicant_id INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    message TEXT,
    monthly_income DOUBLE,
    employment_status VARCHAR(50),
    employer_name VARCHAR(100),
    years_employed DOUBLE,
    has_pets BOOLEAN NOT NULL DEFAULT FALSE,
    number_of_occupants INT DEFAULT 1,
    move_in_date DATE,
    lease_term INT DEFAULT 12,
    rating INT,
    review_text TEXT,
    reviewed_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_rental_applications_property FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
    CONSTRAINT fk_rental_applications_applicant FOREIGN KEY (applicant_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_property_applicant (property_id, applicant_id),
    INDEX idx_rental_applications_status (status),
    INDEX idx_rental_applications_property_id (property_id),
    INDEX idx_rental_applications_applicant_id (applicant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE user_subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    plan_id INT NOT NULL,
    provider VARCHAR(30) NOT NULL DEFAULT 'manual',
    reference VARCHAR(120) UNIQUE,
    amount DOUBLE NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'ZAR',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    start_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date DATETIME NULL,
    auto_renew BOOLEAN NOT NULL DEFAULT TRUE,
    cancelled_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_subscriptions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_subscriptions_plan FOREIGN KEY (plan_id) REFERENCES subscription_plans(id) ON DELETE RESTRICT,
    INDEX idx_user_subscriptions_user_id (user_id),
    INDEX idx_user_subscriptions_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE billing_invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    plan_id INT NOT NULL,
    subscription_id INT NULL,
    provider VARCHAR(30) NOT NULL DEFAULT 'manual',
    reference VARCHAR(120) NOT NULL UNIQUE,
    external_id VARCHAR(120),
    amount DOUBLE NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'ZAR',
    description VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    checkout_url TEXT,
    due_date DATETIME NULL,
    paid_at DATETIME NULL,
    failed_reason TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_billing_invoices_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_billing_invoices_plan FOREIGN KEY (plan_id) REFERENCES subscription_plans(id) ON DELETE RESTRICT,
    CONSTRAINT fk_billing_invoices_subscription FOREIGN KEY (subscription_id) REFERENCES user_subscriptions(id) ON DELETE SET NULL,
    INDEX idx_billing_invoices_user_id (user_id),
    INDEX idx_billing_invoices_reference (reference),
    INDEX idx_billing_invoices_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE landlord_subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    landlord_id INT NOT NULL,
    plan_id INT NOT NULL,
    start_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date DATETIME NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    auto_renew BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_landlord_subscriptions_landlord FOREIGN KEY (landlord_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_landlord_subscriptions_plan FOREIGN KEY (plan_id) REFERENCES subscription_plans(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE admin_audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NULL,
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id INT,
    details TEXT,
    ip_address VARCHAR(45),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_admin_audit_logs_admin FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_admin_audit_logs_admin_id (admin_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- RNW Demo Seed Data - MySQL 8+
-- Demo login details:
--   Admin:    admin@rnw.local / AdminPass123!
--   Landlord: landlord@rnw.local / LandlordPass123!
--   Tenant:   tenant@rnw.local / TenantPass123!

INSERT INTO subscription_plans
(id, name, role, price, currency, billing_period, max_listings, is_featured, support_level, features, is_active, created_at, updated_at)
VALUES
(1, 'Tenant Plus', 'tenant', 50.00, 'ZAR', 'monthly', 0, 0, 'Basic', 'Save properties;Apply for rentals;AI recommendations;Application tracking', 1, NOW(), NOW()),
(2, 'Landlord Pro', 'landlord', 100.00, 'ZAR', 'monthly', 25, 1, 'Priority', 'Create listings;Receive rental applications;Landlord analytics;Verification support;Up to 25 active listings', 1, NOW(), NOW())
ON DUPLICATE KEY UPDATE
    price = VALUES(price),
    max_listings = VALUES(max_listings),
    features = VALUES(features),
    updated_at = NOW();

INSERT INTO users
(id, email, password_hash, first_name, last_name, phone, id_number, role, province, is_verified, email_verified_at, is_active, last_password_reset_at, created_at, updated_at)
VALUES
(1, 'admin@rnw.local', 'pbkdf2:sha256:1000000$rnwAdminSalt$118207af89a54c186596b1e673004510d29b99a2535cdf2916c07136271b9c94', 'RNW', 'Admin', '0710000001', NULL, 'admin', 'Gauteng', 1, NOW(), 1, NOW(), NOW(), NOW()),
(2, 'landlord@rnw.local', 'pbkdf2:sha256:1000000$rnwLandlordSalt$7d22098e9916894f8dcb209751a6eb719d36e0b51c9f770b03a6d49b576085e1', 'Lindiwe', 'Mkhize', '0710000002', NULL, 'landlord', 'KwaZulu-Natal', 1, NOW(), 1, NOW(), NOW(), NOW()),
(3, 'tenant@rnw.local', 'pbkdf2:sha256:1000000$rnwTenantSalt$a12aa2a7715bad3e9378a42853b262153c36495d0f2acd9937673acd3bcbf196', 'Thabo', 'Dlamini', '0710000003', NULL, 'tenant', 'KwaZulu-Natal', 0, NOW(), 1, NOW(), NOW(), NOW())
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role = VALUES(role),
    is_active = 1,
    email_verified_at = VALUES(email_verified_at),
    updated_at = NOW();

INSERT INTO user_subscriptions
(id, user_id, plan_id, provider, reference, amount, currency, status, start_date, end_date, auto_renew, created_at, updated_at)
VALUES
(1, 3, 1, 'seed', 'SEED-TENANT-PLUS-001', 50.00, 'ZAR', 'active', NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY), 1, NOW(), NOW()),
(2, 2, 2, 'seed', 'SEED-LANDLORD-PRO-001', 100.00, 'ZAR', 'active', NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY), 1, NOW(), NOW())
ON DUPLICATE KEY UPDATE
    status = 'active',
    end_date = DATE_ADD(NOW(), INTERVAL 30 DAY),
    updated_at = NOW();

INSERT INTO billing_invoices
(id, user_id, plan_id, subscription_id, provider, reference, amount, currency, description, status, paid_at, created_at, updated_at)
VALUES
(1, 3, 1, 1, 'seed', 'INV-SEED-TENANT-001', 50.00, 'ZAR', 'Tenant Plus monthly subscription', 'paid', NOW(), NOW(), NOW()),
(2, 2, 2, 2, 'seed', 'INV-SEED-LANDLORD-001', 100.00, 'ZAR', 'Landlord Pro monthly subscription', 'paid', NOW(), NOW(), NOW())
ON DUPLICATE KEY UPDATE
    status = 'paid',
    paid_at = VALUES(paid_at),
    updated_at = NOW();

INSERT INTO landlord_verifications
(id, user_id, id_document_url, proof_of_address_url, tax_clearance_url, business_registration_url, status, verified_by, verified_at, created_at, updated_at)
VALUES
(1, 2, 'private/landlord_verifications/demo/id_document.pdf', 'private/landlord_verifications/demo/proof_of_address.pdf', NULL, NULL, 'verified', 1, NOW(), NOW(), NOW())
ON DUPLICATE KEY UPDATE
    status = 'verified',
    verified_by = 1,
    verified_at = NOW(),
    updated_at = NOW();

INSERT INTO properties
(id, landlord_id, title, description, property_type, address, city, province, postal_code, latitude, longitude, price, deposit_amount, bedrooms, bathrooms, parking, area_sqm, pets_allowed, furnished, transport_access, available_date, minimum_lease, is_available, status, view_count, created_at, updated_at)
VALUES
(1, 2, 'Modern Room Near Empangeni CBD', 'Secure furnished room close to transport, shops, and workplaces.', 'room', 'Main Road, Empangeni', 'Empangeni', 'KwaZulu-Natal', '3880', -28.7619, 31.8932, 3200.00, 3200.00, 1, 1.0, 1, 28.0, 0, 1, 'Taxi rank 500m away; close to CBD', CURDATE(), 12, 1, 'approved', 18, NOW(), NOW()),
(2, 2, 'Two Bedroom Apartment in Richards Bay', 'Family-friendly apartment with parking and quick access to industrial areas.', 'apartment', 'Meerensee, Richards Bay', 'Richards Bay', 'KwaZulu-Natal', '3901', -28.7807, 32.0383, 7200.00, 7200.00, 2, 1.5, 1, 68.0, 1, 0, 'Quick access to industrial areas and public transport', CURDATE(), 12, 1, 'approved', 11, NOW(), NOW()),
(3, 2, 'Studio Apartment in Sandton', 'Compact studio for professionals near offices and Gautrain.', 'studio', 'Rivonia Road, Sandton', 'Sandton', 'Gauteng', '2196', -26.1076, 28.0567, 8500.00, 8500.00, 0, 1.0, 1, 38.0, 0, 1, 'Near Gautrain and office nodes', CURDATE(), 12, 1, 'approved', 23, NOW(), NOW()),
(4, 2, 'Affordable Cottage Near University of Zululand', 'Quiet cottage suitable for students or young professionals, close to transport.', 'cottage', 'KwaDlangezwa Road', 'Empangeni', 'KwaZulu-Natal', '3886', -28.8503, 31.8492, 4100.00, 4100.00, 1, 1.0, 1, 35.0, 0, 0, 'Taxi route nearby; short drive to university', CURDATE(), 6, 1, 'approved', 7, NOW(), NOW())
ON DUPLICATE KEY UPDATE
    price = VALUES(price),
    deposit_amount = VALUES(deposit_amount),
    status = VALUES(status),
    updated_at = NOW();

INSERT INTO property_photos
(id, property_id, photo_url, is_primary, uploaded_at)
VALUES
(1, 1, '/static/img/demo/empangeni-room.jpg', 1, NOW()),
(2, 2, '/static/img/demo/richards-bay-apartment.jpg', 1, NOW()),
(3, 3, '/static/img/demo/sandton-studio.jpg', 1, NOW()),
(4, 4, '/static/img/demo/unizulu-cottage.jpg', 1, NOW())
ON DUPLICATE KEY UPDATE
    photo_url = VALUES(photo_url),
    is_primary = VALUES(is_primary);

INSERT INTO saved_properties
(id, user_id, property_id, saved_at)
VALUES
(1, 3, 1, NOW()),
(2, 3, 4, NOW())
ON DUPLICATE KEY UPDATE saved_at = VALUES(saved_at);

INSERT INTO rental_applications
(id, property_id, applicant_id, status, message, monthly_income, employment_status, employer_name, years_employed, has_pets, number_of_occupants, move_in_date, lease_term, created_at, updated_at)
VALUES
(1, 1, 3, 'pending', 'I work near Empangeni CBD and would like to view this room.', 12500.00, 'employed', 'Empangeni Retail Group', 2.0, 0, 1, DATE_ADD(CURDATE(), INTERVAL 14 DAY), 12, NOW(), NOW())
ON DUPLICATE KEY UPDATE
    status = VALUES(status),
    message = VALUES(message),
    updated_at = NOW();

INSERT INTO inquiries
(id, property_id, sender_id, recipient_id, message, is_read, created_at, updated_at)
VALUES
(1, 1, 3, 2, 'Hi, is this room still available for viewing this weekend?', 0, NOW(), NOW())
ON DUPLICATE KEY UPDATE
    message = VALUES(message),
    is_read = VALUES(is_read),
    updated_at = NOW();

INSERT INTO search_history
(id, user_id, search_address, latitude, longitude, radius_km, min_price, max_price, bedrooms, property_type, result_count, session_id, searched_at)
VALUES
(1, 3, 'Empangeni CBD', -28.7619, 31.8932, 10, 2500.00, 5000.00, 1, 'room', 2, 'demo-session', NOW())
ON DUPLICATE KEY UPDATE searched_at = NOW();

INSERT INTO admin_audit_logs
(id, admin_id, action, target_type, target_id, details, ip_address, created_at, updated_at)
VALUES
(1, 1, 'seed_database', 'system', NULL, 'Demo RNW database seeded successfully.', '127.0.0.1', NOW(), NOW())
ON DUPLICATE KEY UPDATE updated_at = NOW();

-- Real launch / trust layer tables
CREATE TABLE IF NOT EXISTS property_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    reviewer_id INT NOT NULL,
    landlord_id INT NOT NULL,
    rental_application_id INT NULL,
    rating INT NOT NULL,
    title VARCHAR(120) NOT NULL,
    comment TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    landlord_response TEXT,
    landlord_responded_at DATETIME NULL,
    moderated_by INT NULL,
    moderated_at DATETIME NULL,
    rejection_reason TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_property_reviews_property FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
    CONSTRAINT fk_property_reviews_reviewer FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_property_reviews_landlord FOREIGN KEY (landlord_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_property_reviews_application FOREIGN KEY (rental_application_id) REFERENCES rental_applications(id) ON DELETE SET NULL,
    UNIQUE KEY uq_property_reviewer (property_id, reviewer_id),
    CHECK (rating >= 1 AND rating <= 5),
    INDEX idx_property_reviews_status (status),
    INDEX idx_property_reviews_property_id (property_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS listing_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    reporter_id INT NULL,
    reporter_name VARCHAR(120),
    reporter_email VARCHAR(120),
    reason VARCHAR(80) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    admin_notes TEXT,
    resolved_by INT NULL,
    resolved_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_listing_reports_property FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
    CONSTRAINT fk_listing_reports_reporter FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_listing_reports_status (status),
    INDEX idx_listing_reports_property_id (property_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS support_tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'general',
    subject VARCHAR(160) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    assigned_to INT NULL,
    admin_response TEXT,
    responded_at DATETIME NULL,
    closed_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_support_tickets_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_support_tickets_assignee FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_support_tickets_status (status),
    INDEX idx_support_tickets_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS legal_consents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    email VARCHAR(120),
    consent_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL DEFAULT '2026-06',
    accepted BOOLEAN NOT NULL DEFAULT TRUE,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    accepted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_legal_consents_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_legal_consents_user_id (user_id),
    INDEX idx_legal_consents_type (consent_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS payment_webhook_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    provider VARCHAR(30) NOT NULL,
    reference VARCHAR(120),
    external_id VARCHAR(120),
    status VARCHAR(50),
    valid_signature BOOLEAN NOT NULL DEFAULT FALSE,
    payload TEXT NOT NULL,
    processed_at DATETIME NULL,
    error TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_payment_webhook_logs_provider (provider),
    INDEX idx_payment_webhook_logs_reference (reference),
    INDEX idx_payment_webhook_logs_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Real launch demo trust/review data
INSERT INTO rental_applications
(id, property_id, applicant_id, status, message, monthly_income, employment_status, employer_name, years_employed, has_pets, number_of_occupants, lease_term, created_at, updated_at)
VALUES
(1, 1, 3, 'approved', 'I work near Empangeni CBD and need a safe room.', 12500.00, 'employed', 'Demo Employer', 2.0, 0, 1, 12, NOW(), NOW())
ON DUPLICATE KEY UPDATE status='approved', updated_at=NOW();

INSERT INTO property_reviews
(id, property_id, reviewer_id, landlord_id, rental_application_id, rating, title, comment, status, created_at, updated_at)
VALUES
(1, 1, 3, 2, 1, 5, 'Great location for work', 'The room is close to transport and the listing details were accurate.', 'approved', NOW(), NOW())
ON DUPLICATE KEY UPDATE rating=VALUES(rating), status='approved', updated_at=NOW();

INSERT INTO support_tickets
(id, user_id, name, email, category, subject, message, status, priority, created_at, updated_at)
VALUES
(1, 3, 'Thabo Dlamini', 'tenant@rnw.local', 'billing', 'Demo payment question', 'I want to confirm my Tenant Plus subscription.', 'open', 'high', NOW(), NOW())
ON DUPLICATE KEY UPDATE status=VALUES(status), updated_at=NOW();
