# RNW Merged Working Project

This folder is the cleaned, merged RNW project to run first. It uses the latest upgraded Flask application and removes the older duplicate backups/archive zips.

## Run with Python

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
flask --app backend.app:create_app init-db
flask --app backend.app:create_app seed-db
flask --app backend.app:create_app ensure-plans
flask --app backend.app:create_app run
```

Open `http://localhost:5000`.

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost`.

Docker is set to auto-create database tables, ensure billing plans, and seed demo data for local testing.

## Demo logins

```text
Admin:    admin@rnw.local / AdminPass123!
Landlord: landlord@rnw.local / LandlordPass123!
Tenant:   tenant@rnw.local / TenantPass123!
```

## Change billing prices

Edit `.env`:

```env
TENANT_MONTHLY_PRICE=50
LANDLORD_MONTHLY_PRICE=100
LANDLORD_MAX_LISTINGS=25
PAYMENT_PROVIDER=disabled
```

Then run:

```bash
flask --app backend.app:create_app ensure-plans
```

Or update directly:

```bash
flask --app backend.app:create_app set-plan-prices --tenant 75 --landlord 150 --landlord-listings 50
```

## PayFast production settings

```env
PAYMENT_PROVIDER=payfast
PAYFAST_SANDBOX=false
PAYFAST_MERCHANT_ID=your_merchant_id
PAYFAST_MERCHANT_KEY=your_merchant_key
PAYFAST_PASSPHRASE=your_passphrase
APP_BASE_URL=https://your-domain.co.za
```

Webhook endpoint:

```text
POST /billing/webhooks/payfast
```

## What was improved in this merged version

- Removed duplicate old backups from the runnable project.
- Removed generated `__pycache__` files.
- Made tenant and landlord billing prices configurable through `.env`.
- Added `LANDLORD_MAX_LISTINGS` setting.
- Added `set-plan-prices` CLI command.
- Updated billing page text so it does not hard-code prices.
- Improved PayFast webhook validation for signature, amount, reference, status, and ZAR currency.
- Made invoice activation idempotent so duplicate PayFast webhook calls do not create duplicate subscriptions.
- Improved Docker first-run behavior with automatic DB/table setup and optional demo seed.
- Fixed `.env.example` so the local `APP_BASE_URL` is not accidentally overwritten by a production example.

## Single-file quick demo

The ZIP also includes:

```text
RNW_ONE_FILE_WORKING_APP.py
```

That file is a simplified all-in-one demo version. Use it only for quick testing or demos. Use this full folder for production work.
