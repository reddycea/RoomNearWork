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
