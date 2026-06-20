# Room Near Work

Room Near Work is a blue-and-white, app-like rental marketplace for helping tenants find rooms and apartments close to work, transport and opportunity.

## Major features included

- Exact workplace address search, for example `11 Park Avenue`.
- Google geocoding, Places autocomplete, and Routes matrix integration with local South African demo fallback.
- Search by walking, taxi/public transport, or car travel time.
- Tenant saved searches with commute filters and email alerts.
- One account can act as both tenant and landlord after registration.
- Landlords can create, edit, renew, archive and manage rentals.
- Landlords can upload apartment photos, property/house registration proof and ID documents.
- Private document access is restricted to the landlord and admin.
- Admin verification queue for listings and private documents.
- In-app messaging and viewing appointments.
- Listing quality score, expiry and renewal.
- CSRF, rate limiting, secure cookies, Talisman security headers, audit logs and login lockout.
- Email verification and password reset flows.
- Docker, Nginx, Redis worker, scheduler and CI workflow.
- Legal starter pages for privacy, terms, safety, POPIA and data requests.

## Local quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app backend.app:create_app init-db
flask --app backend.app:create_app seed-db
flask --app backend.app:create_app run
```

Open `http://localhost:5000`.

## Demo accounts

- `admin@rnw.local` / `AdminPass123!`
- `landlord@rnw.local` / `LandlordPass123!`
- `tenant@rnw.local` / `TenantPass123!`

## Google Maps setup

Set these in `.env`:

```env
GOOGLE_MAPS_API_KEY=your-server-key
GOOGLE_MAPS_BROWSER_KEY=your-browser-key
GOOGLE_MAPS_REGION=ZA
GOOGLE_MAPS_LANGUAGE=en-ZA
GOOGLE_ROUTE_MATRIX_ENABLED=true
```

Enable Geocoding API, Places API and Routes API in Google Cloud.

## Production notes

- Replace all development secrets.
- Use PostgreSQL and Redis.
- Set `RATELIMIT_STORAGE_URI=redis://redis:6379/1`.
- Use HTTPS and set secure cookies.
- Review legal pages with a qualified legal professional before launch.
- Add virus scanning and private object storage for uploaded documents before handling real ID documents.
