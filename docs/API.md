# RNW API

## Auth

`POST /auth/api/token`

```json
{"email":"tenant@rnw.local","password":"TenantPass123!"}
```

Returns access/refresh JWT tokens.

`POST /auth/api/refresh` requires a refresh token.

## Properties

`GET /api/properties`

Supported filters:

- `city`
- `province`
- `max_price`
- `max_deposit`
- `bedrooms`
- `furnished=1`
- `transport_access`
- `workplace`
- `radius_km`

`GET /api/properties/<id>` returns approved property details.

## Recommendations

`GET /api/recommendations`

Optional query parameters:

- `workplace`
- `lat`
- `lng`
- `max_price`
- `bedrooms`
- `city`
- `limit`

Response includes a score and explainable reasons.

## Billing

`GET /billing/api/plans`

Returns Tenant Plus R50pm and Landlord Pro R100pm.

`POST /billing/api/subscribe`

Requires JWT. Body:

```json
{"plan_id":1}
```

In sandbox mode the subscription activates immediately. In PayFast mode the response contains `checkout_url` and `reference`.

`GET /billing/api/subscription`

Returns the current subscription and latest invoices.

## Webhooks

`POST /billing/webhooks/payfast`

Receives PayFast payment/IPN notifications and activates the matching subscription invoice when payment is complete and the signature is valid.
