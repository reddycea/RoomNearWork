# RNW Architecture

```text
backend/rnw/
  models/          SQLAlchemy models
  routes/          Flask blueprints
  services/        billing, auth, email, geo, recommendation logic
  templates/       server-rendered SaaS UI
  static/          CSS/assets
```

## Important flows

### Subscription flow

1. User selects Tenant Plus or Landlord Pro.
2. RNW creates a `BillingInvoice`.
3. `PaymentService` creates checkout.
4. Sandbox mode marks the invoice paid immediately.
5. PayFast mode redirects the customer and waits for `/billing/webhooks/payfast`.
6. Paid invoice activates `UserSubscription`.

### Landlord listing limit

Landlord Pro includes 25 active listings. RNW checks active `pending` and `approved` listings before creating a new property.

### Private landlord verification

Verification documents are saved under `UPLOAD_FOLDER/private/verification`. They are referenced as `private://...` and only served through admin-only routes.

### Recommendation engine

Recommendations combine budget, workplace distance, saved properties, application history, city similarity, furnished status, transport access, and popularity. Every result returns reasons so the UI can explain why it was recommended.
