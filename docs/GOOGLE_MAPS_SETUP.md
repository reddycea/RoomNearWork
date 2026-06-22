# Google Maps setup for Room Near Work

Room Near Work uses two Google Maps Platform APIs:

1. **Geocoding API**: resolves tenant workplace addresses and landlord rental addresses into coordinates and suburb/city/province data.
2. **Routes API Compute Route Matrix**: calculates travel distance and duration from one workplace to many rental listings.

Required environment variables:

```env
GOOGLE_MAPS_API_KEY=your-key
GOOGLE_MAPS_REGION=ZA
GOOGLE_MAPS_LANGUAGE=en-ZA
GOOGLE_ROUTE_MATRIX_ENABLED=true
DEFAULT_SEARCH_RADIUS_KM=20
DEFAULT_MAX_TRAVEL_MINUTES=45
```

Restrict the API key in Google Cloud. Use HTTP referrer restrictions for browser keys and IP/app restrictions for server keys. This app uses the key server-side.

Travel modes in RNW:

- `walking` -> Google `WALK`
- `car` -> Google `DRIVE`
- `taxi` -> Google `TRANSIT` where available, with fallback estimates when transit data is unavailable

Google does not have a dedicated South African minibus taxi travel mode, so the UI labels it as `Taxi / public transport` and the README explains this limitation.
