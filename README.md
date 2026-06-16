# RNW Production Upgrade

RNW is a production-style Flask SaaS rental marketplace for finding rooms and apartments near work, transport, and opportunity.

## What is included

- Modular Flask application factory
- Tenant, landlord, and admin roles
- Tenant Plus subscription at **R50/month**
- Landlord Pro subscription at **R100/month**
- Subscription dashboard, invoice records, cancellation, and admin billing controls
- PayFast-ready South African checkout/webhook flow plus disabled sandbox mode for development
- Landlord limit enforcement: Landlord Pro allows **25 active listings**
- Email verification, password reset, password strength rules, and login lockout tracking
- Private landlord verification document storage
- Property search by price, deposit, furnished, pets, transport access, workplace distance, and sorting
- Explainable recommendations using search history, saved properties, applications, budget, location, and transport
- Docker, Nginx, CI, migrations template, tests, and deployment scripts

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
flask --app backend.app:create_app init-db
flask --app backend.app:create_app seed-db
flask --app backend.app:create_app run
```

Demo users after seeding:

```text
admin@rnw.local / AdminPass123!
landlord@rnw.local / LandlordPass123!
tenant@rnw.local / TenantPass123!
```

## Billing

Default plans are created by `flask ensure-plans` or `seed-db`:

| Plan | Role | Price | Main limits |
|---|---:|---:|---|
| Tenant Plus | tenant | R50pm | applications, saved properties, AI recommendations |
| Landlord Pro | landlord | R100pm | up to 25 active listings, tenant applications, verification, analytics |

Local development uses:

```env
PAYMENT_PROVIDER=disabled
```

This activates paid plans immediately and records paid invoices. For production South African billing, configure:

```env
PAYMENT_PROVIDER=payfast
PAYFAST_SANDBOX=false
PAYFAST_MERCHANT_ID=...
PAYFAST_MERCHANT_KEY=...
PAYFAST_PASSPHRASE=...
APP_BASE_URL=https://your-domain.example
```

PayFast webhooks are received at:

```text
POST /billing/webhooks/payfast
```

## Database migrations

For production, use Flask-Migrate instead of dropping tables:

```bash
flask --app backend.app:create_app db init
flask --app backend.app:create_app db migrate -m "initial schema"
flask --app backend.app:create_app db upgrade
```

A migration template and an example initial migration are included under `backend/migrations`.

## Tests

```bash
pytest backend/tests
```

## Docker

```bash
docker compose up --build
```

## Production checklist

- Change all secrets in `.env`
- Use MySQL or Postgres instead of local SQLite
- Set `PAYMENT_PROVIDER=payfast` and configure PayFast merchant credentials
- Set `EMAIL_VERIFICATION_REQUIRED=true`
- Use HTTPS behind Nginx
- Configure Redis for cache and rate limiting
- Store uploads in private object storage for large deployments
- Schedule `scripts/backup_db.sh`


## Real Launch Additions

This ZIP includes the production-readiness layer for RNW:

- Legal pages: Terms, Privacy, Refunds, POPIA, Safety Rules
- Support ticket system for public/authenticated users
- Listing reporting and admin moderation
- Property reviews with admin approval and landlord responses
- Payment webhook logs for PayFast IPN auditing
- Storage abstraction for local, Cloudinary, S3, or DigitalOcean Spaces
- Legal consent records captured during registration
- Admin dashboards for reviews, reports, support, billing, and webhook logs

Before launch, replace the legal templates with lawyer-reviewed policies, configure real SMTP, configure PayFast production credentials, connect a domain, and move uploads to object storage.

## Merged package improvements

This merged version also adds environment-configurable subscription prices:

```env
TENANT_MONTHLY_PRICE=50
LANDLORD_MONTHLY_PRICE=100
LANDLORD_MAX_LISTINGS=25
SUBSCRIPTION_CURRENCY=ZAR
```

After changing those values, run:

```bash
flask --app backend.app:create_app ensure-plans
```

You can also update plan prices directly:

```bash
flask --app backend.app:create_app set-plan-prices --tenant 75 --landlord 150 --landlord-listings 50
```
