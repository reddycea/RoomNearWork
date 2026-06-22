# Reviews, taxi layer and Google Places upgrade

## Tenant rental reviews

Tenants can review a property after either:

- submitting a rental application, or
- receiving an approved/completed viewing appointment.

Reviews are submitted as `pending`, then an admin approves or rejects them in `/admin/verifications`.
Approved reviews appear on the public property detail page and contribute to the listing average rating.

## Google Places session tokens

The frontend now creates a short-lived Places session token before autocomplete requests. The token is sent to:

- `/api/places/autocomplete`
- `/api/places/confirm`

The database stores only the token hash in `places_sessions` for audit/cost-control tracking.

## Address confirmation

Autocomplete suggestions now show a “Did you mean this workplace address?” panel. This protects against ambiguous searches like `11 Park Avenue`.

## Taxi-rank layer

Google has no dedicated South African minibus-taxi mode. RNW now includes a `taxi_ranks` table and `taxi_route_service.py` to estimate:

- walking distance to/from ranks,
- rank-to-rank route distance,
- rough travel minutes,
- rough fare range.

Seed data is demo-only and should be verified before launch.
