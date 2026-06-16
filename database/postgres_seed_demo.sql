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
