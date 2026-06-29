-- Room Near Work schema helper for MySQL 8+
-- Source of truth: backend/migrations/versions/20260620_0001_rnw_full_upgrade.py
-- For production, prefer Flask-Migrate/Alembic: flask --app backend.app:create_app db upgrade

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  full_name VARCHAR(160) NOT NULL,
  phone VARCHAR(40),
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(30) NOT NULL DEFAULT 'tenant',
  can_act_as_tenant TINYINT(1) NOT NULL DEFAULT 1,
  can_act_as_landlord TINYINT(1) NOT NULL DEFAULT 0,
  landlord_approved_at DATETIME NULL,
  landlord_approved_by_id INT NULL,
  is_admin TINYINT(1) NOT NULL DEFAULT 0,
  is_active_account TINYINT(1) NOT NULL DEFAULT 1,
  email_verified TINYINT(1) NOT NULL DEFAULT 0,
  email_verified_at DATETIME NULL,
  failed_login_count INT NOT NULL DEFAULT 0,
  locked_until DATETIME NULL,
  last_login_at DATETIME NULL,
  last_login_ip VARCHAR(64),
  two_factor_secret VARCHAR(64),
  two_factor_enabled TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX ix_users_email (email)
);

CREATE TABLE IF NOT EXISTS properties (
  id INT AUTO_INCREMENT PRIMARY KEY,
  landlord_id INT NOT NULL,
  title VARCHAR(200) NOT NULL,
  description TEXT NOT NULL,
  rent_amount INT NOT NULL,
  deposit_amount INT NOT NULL DEFAULT 0,
  bedrooms INT NOT NULL DEFAULT 1,
  bathrooms INT NOT NULL DEFAULT 1,
  city VARCHAR(120) NOT NULL,
  province VARCHAR(120) NOT NULL,
  suburb VARCHAR(120),
  address_line VARCHAR(255),
  formatted_address VARCHAR(500),
  google_place_id VARCHAR(255),
  approximate_address VARCHAR(255),
  address_visibility VARCHAR(40) NOT NULL DEFAULT 'approved_viewing',
  latitude DOUBLE,
  longitude DOUBLE,
  workplace_distance_km DOUBLE,
  nearest_transport VARCHAR(160),
  commute_notes TEXT,
  furnished TINYINT(1) NOT NULL DEFAULT 0,
  pets_allowed TINYINT(1) NOT NULL DEFAULT 0,
  transport_access TINYINT(1) NOT NULL DEFAULT 0,
  image_url VARCHAR(500),
  status VARCHAR(40) NOT NULL DEFAULT 'under_review',
  status_reason TEXT,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  view_count INT NOT NULL DEFAULT 0,
  quality_score INT NOT NULL DEFAULT 0,
  quality_score_details TEXT,
  expires_at DATETIME NULL,
  renewed_at DATETIME NULL,
  listing_verified TINYINT(1) NOT NULL DEFAULT 0,
  verified_at DATETIME NULL,
  verified_by_id INT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX ix_properties_landlord_id (landlord_id),
  INDEX ix_properties_search (status, is_active, city, province, rent_amount),
  INDEX ix_properties_geo (latitude, longitude),
  CONSTRAINT fk_properties_landlord FOREIGN KEY (landlord_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS property_assets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  property_id INT NOT NULL,
  uploaded_by_id INT NOT NULL,
  kind VARCHAR(40) NOT NULL,
  original_filename VARCHAR(255) NOT NULL,
  stored_filename VARCHAR(255) NOT NULL UNIQUE,
  relative_path VARCHAR(500) NOT NULL UNIQUE,
  mime_type VARCHAR(120),
  size_bytes INT NOT NULL DEFAULT 0,
  is_private TINYINT(1) NOT NULL DEFAULT 1,
  is_primary TINYINT(1) NOT NULL DEFAULT 0,
  review_status VARCHAR(40) NOT NULL DEFAULT 'pending',
  review_note TEXT,
  reviewed_by_id INT NULL,
  reviewed_at DATETIME NULL,
  virus_scan_status VARCHAR(40) NOT NULL DEFAULT 'not_scanned',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX ix_property_assets_kind_property (property_id, kind),
  INDEX ix_property_assets_review (kind, review_status),
  CONSTRAINT fk_property_assets_property FOREIGN KEY (property_id) REFERENCES properties(id),
  CONSTRAINT fk_property_assets_user FOREIGN KEY (uploaded_by_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS rental_applications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  property_id INT NOT NULL,
  applicant_id INT NOT NULL,
  tenant_subscription_id INT NULL,
  message TEXT,
  status VARCHAR(40) NOT NULL DEFAULT 'pending',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_application_property_applicant (property_id, applicant_id),
  INDEX ix_rental_applications_property_id (property_id),
  INDEX ix_rental_applications_applicant_id (applicant_id)
);

CREATE TABLE IF NOT EXISTS landlord_applications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  applicant_id INT NOT NULL,
  property_id INT NULL,
  status VARCHAR(40) NOT NULL DEFAULT 'pending',
  message TEXT,
  admin_note TEXT,
  reviewed_by_id INT NULL,
  reviewed_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX ix_landlord_applications_applicant_id (applicant_id),
  INDEX ix_landlord_applications_property_id (property_id),
  INDEX ix_landlord_applications_status (status),
  INDEX ix_landlord_applications_applicant_status (applicant_id, status),
  INDEX ix_landlord_applications_status_created (status, created_at),

  CONSTRAINT fk_landlord_applications_applicant
    FOREIGN KEY (applicant_id) REFERENCES users(id)
    ON DELETE CASCADE,

  CONSTRAINT fk_landlord_applications_property
    FOREIGN KEY (property_id) REFERENCES properties(id)
    ON DELETE SET NULL,

  CONSTRAINT fk_landlord_applications_reviewed_by
    FOREIGN KEY (reviewed_by_id) REFERENCES users(id)
    ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS subscription_plans (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  role VARCHAR(30) NOT NULL,
  price_cents INT NOT NULL,
  currency VARCHAR(10) NOT NULL DEFAULT 'ZAR',
  max_active_listings INT NULL,
  max_rental_applications INT NOT NULL DEFAULT 0,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_subscriptions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  plan_id INT NOT NULL,
  role VARCHAR(30) NOT NULL,
  status VARCHAR(40) NOT NULL DEFAULT 'active',
  current_period_end DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invoices (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  plan_id INT NOT NULL,
  amount_cents INT NOT NULL,
  currency VARCHAR(10) NOT NULL DEFAULT 'ZAR',
  provider VARCHAR(40) NOT NULL,
  provider_reference VARCHAR(160) UNIQUE,
  status VARCHAR(40) NOT NULL DEFAULT 'pending',
  paid_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS saved_searches (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  name VARCHAR(120) NOT NULL,
  city VARCHAR(120),
  province VARCHAR(120),
  max_rent INT,
  min_bedrooms INT,
  furnished TINYINT(1),
  pets_allowed TINYINT(1),
  transport_access TINYINT(1),
  workplace_address VARCHAR(500),
  workplace_formatted_address VARCHAR(500),
  workplace_place_id VARCHAR(255),
  workplace_area VARCHAR(160),
  workplace_latitude DOUBLE,
  workplace_longitude DOUBLE,
  travel_mode VARCHAR(40) NOT NULL DEFAULT 'taxi',
  max_distance_km DOUBLE,
  max_travel_minutes INT,
  alerts_enabled TINYINT(1) NOT NULL DEFAULT 1,
  last_alerted_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_saved_search_user_name (user_id, name)
);

CREATE TABLE IF NOT EXISTS conversation_threads (
  id INT AUTO_INCREMENT PRIMARY KEY,
  property_id INT NOT NULL,
  tenant_id INT NOT NULL,
  landlord_id INT NOT NULL,
  status VARCHAR(40) NOT NULL DEFAULT 'open',
  last_message_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_thread_property_tenant_landlord (property_id, tenant_id, landlord_id)
);

CREATE TABLE IF NOT EXISTS conversation_messages (
  id INT AUTO_INCREMENT PRIMARY KEY,
  thread_id INT NOT NULL,
  sender_id INT NOT NULL,
  body TEXT NOT NULL,
  read_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS viewing_appointments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  property_id INT NOT NULL,
  tenant_id INT NOT NULL,
  landlord_id INT NOT NULL,
  requested_start DATETIME NOT NULL,
  requested_end DATETIME NOT NULL,
  status VARCHAR(40) NOT NULL DEFAULT 'requested',
  tenant_note TEXT,
  landlord_note TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS support_tickets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NULL,
  public_token VARCHAR(96) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL,
  subject VARCHAR(200) NOT NULL,
  message TEXT NOT NULL,
  status VARCHAR(40) NOT NULL DEFAULT 'open',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS listing_reports (
  id INT AUTO_INCREMENT PRIMARY KEY,
  property_id INT NOT NULL,
  reporter_id INT NULL,
  reason VARCHAR(120) NOT NULL,
  details TEXT,
  status VARCHAR(40) NOT NULL DEFAULT 'open',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_audit_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  actor_id INT NULL,
  action VARCHAR(120) NOT NULL,
  target_type VARCHAR(80),
  target_id VARCHAR(80),
  ip_address VARCHAR(64),
  user_agent VARCHAR(255),
  metadata_json TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_verification_tokens (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  token_hash VARCHAR(64) NOT NULL UNIQUE,
  expires_at DATETIME NOT NULL,
  used_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  token_hash VARCHAR(64) NOT NULL UNIQUE,
  expires_at DATETIME NOT NULL,
  used_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


-- Demo seed helper
-- Prefer: flask --app backend.app:create_app seed-db
-- The Flask command creates secure password hashes and demo records that match the current models.


-- Added in 20260620_0003_reviews_places_taxi
CREATE TABLE IF NOT EXISTS taxi_ranks (
  id INTEGER PRIMARY KEY,
  name VARCHAR(160) NOT NULL,
  suburb VARCHAR(120),
  city VARCHAR(120),
  province VARCHAR(120),
  latitude FLOAT NOT NULL,
  longitude FLOAT NOT NULL,
  notes TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS places_sessions (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  token_hash VARCHAR(64) UNIQUE NOT NULL,
  purpose VARCHAR(80) NOT NULL,
  selected_place_id VARCHAR(255),
  selected_description VARCHAR(500),
  expires_at DATETIME NOT NULL,
  used_at DATETIME,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS rental_reviews (
  id INTEGER PRIMARY KEY,
  property_id INTEGER NOT NULL,
  tenant_id INTEGER NOT NULL,
  landlord_id INTEGER NOT NULL,
  rating INTEGER NOT NULL,
  accuracy_rating INTEGER,
  safety_rating INTEGER,
  commute_rating INTEGER,
  landlord_communication_rating INTEGER,
  title VARCHAR(140) NOT NULL,
  comment TEXT NOT NULL,
  status VARCHAR(40) NOT NULL DEFAULT 'pending',
  admin_note TEXT,
  reviewed_by_id INTEGER,
  reviewed_at DATETIME,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  UNIQUE(property_id, tenant_id)
);

ALTER TABLE subscription_plans
ADD COLUMN IF NOT EXISTS max_rental_applications INTEGER NOT NULL DEFAULT 0;

UPDATE subscription_plans
SET max_rental_applications = 10
WHERE role = 'tenant';

UPDATE subscription_plans
SET max_rental_applications = 0
WHERE role = 'landlord';
