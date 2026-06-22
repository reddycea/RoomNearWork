# RNW Production SaaS

RNW is an upgraded production-style version of your RoomNearWork / RentNearWork rental marketplace. It converts the original single-file Flask project into a modular SaaS architecture with role-based auth, property management, tenant applications, landlord verification, AI-style recommendations, admin audit logging, Docker, Nginx, tests, and deployment documentation.

## What changed from the original ZIP

The original project had most logic in `app.py` plus helper files such as `distance.py`, `geocoding.py`, `recommandation.py`, SQL scripts, Docker config, and Nginx config. This version reorganizes those responsibilities into clear modules:

- `backend/rnw/models/` — database models
- `backend/rnw/routes/` — web/API routes split by feature
- `backend/rnw/services/` — recommendation, geolocation, email, payments, storage
- `backend/rnw/utils/` — security, validators, decorators
- `backend/rnw/templates/` — server-rendered pages
- `backend/tests/` — pytest test suite
- `docker/` and `nginx/` — production deployment assets
- `.github/workflows/ci.yml` — CI checks

## Main SaaS features

- Tenant, landlord, and admin roles
- Session login for web pages
- JWT login for API clients
- CSRF protection for forms
- Rate limiting
- Redis-ready caching
- Property CRUD for landlords
- Search by city, price, bedrooms, type, and distance
- Tenant saved properties and rental applications
- Landlord application review workflow
- Admin approval/rejection workflow
- Landlord verification workflow
- Recommendation scoring engine
- Email service wrapper
- Payment service abstraction for future Stripe/PayPal integration
- Docker Compose stack with Flask, MySQL, Redis, and Nginx
- Seed script and tests

## Quick start: local development

```bash
cd RNW_Production
cp .env.example .env
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export FLASK_APP=backend.app:create_app
flask --app backend.app:create_app init-db
flask --app backend.app:create_app seed-db
flask --app backend.app:create_app run --debug
```

Then open:

```text
http://127.0.0.1:5000
```

Seed users:

```text
admin@rnw.local / AdminPass123!
landlord@rnw.local / LandlordPass123!
tenant@rnw.local / TenantPass123!
```

## Docker start

```bash
cp .env.example .env
docker compose up --build
```

The app is exposed through Nginx on:

```text
http://localhost
```

## Useful commands

```bash
# Run tests
pytest

# Format/check idea
python -m compileall backend

# Initialize database
flask --app backend.app:create_app init-db

# Add demo records
flask --app backend.app:create_app seed-db
```

## Production notes

Before deploying:

1. Replace all values in `.env`.
2. Use a managed MySQL/PostgreSQL database.
3. Set `FLASK_ENV=production` and `DEBUG=false`.
4. Use Redis for rate-limit and cache storage.
5. Configure HTTPS at your reverse proxy/load balancer.
6. Store uploaded files in S3/Azure Blob/Cloudinary instead of local disk.
7. Replace the placeholder payment provider with Stripe/PayPal production keys.
8. Run migrations using Flask-Migrate/Alembic.

## Folder layout

```text
RNW_Production/
├── backend/
│   ├── app.py
│   ├── rnw/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── extensions.py
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── static/
│   │   ├── templates/
│   │   └── utils/
│   └── tests/
├── docker/
├── nginx/
├── scripts/
├── docs/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```
