# Stripe Integration Setup Guide

HelmX uses **Stripe Checkout** (Stripe's hosted payment page). The browser never touches card data, and no client-side Stripe library or publishable key is needed.

## 1. Get your keys

1. Open the [Stripe Dashboard → API keys](https://dashboard.stripe.com/apikeys) (use test mode while developing).
2. Copy the **Secret key** (`sk_test_...`) into `STRIPE_SECRET_KEY` in `.env.local`.
3. Set `NEXT_PUBLIC_APP_URL` to the site's public URL (e.g. `http://localhost:3000`).

## 2. Webhooks

### Local development

```bash
stripe listen --forward-to localhost:3000/api/webhook
```

Copy the printed `whsec_...` secret into `STRIPE_WEBHOOK_SECRET` and restart `npm run dev`.

### Production

In **Developers → Webhooks → Add endpoint**:

- URL: `https://<your-domain>/api/webhook`
- Events:
  - `checkout.session.completed`
  - `checkout.session.async_payment_succeeded`
  - `checkout.session.async_payment_failed`
  - `checkout.session.expired`

Put that endpoint's signing secret in `STRIPE_WEBHOOK_SECRET`.

## 3. How it works

1. The user configures a helmet on `/buy`, enters an email and clicks **Pay with Stripe**.
2. The browser sends the selected **part IDs** (never a price) to `POST /api/checkout-session`.
3. The server prices the order from [`lib/catalog.ts`](lib/catalog.ts), saves a `PENDING` order, and creates a Checkout Session with one line item per part. The order ID is stored in the session metadata.
4. The user pays on Stripe and is redirected to `/buy/success?session_id=...`.
5. The webhook, and the success page as a fallback, call `finalizePaidSession` in [`lib/orders.ts`](lib/orders.ts). It marks the order `PAID` and emails the receipt **once**, no matter how many times it runs.
6. Sessions that expire unpaid are marked `FAILED`.

## 4. Changing prices or parts

Edit [`lib/catalog.ts`](lib/catalog.ts). The configurator and the checkout API both read from it, so they always agree. Prices are whole PKR; Stripe receives them in minor units (×100).

## 5. Test cards

| Card | Number |
| --- | --- |
| Visa | `4242 4242 4242 4242` |
| Visa (debit) | `4000 0566 5566 5556` |
| Mastercard | `5555 5555 5555 4444` |
| Declined | `4000 0000 0000 0002` |

Use any future expiry date and any CVC. See [Stripe's testing docs](https://docs.stripe.com/testing) for more.

## 6. Going live

1. Replace `sk_test_...` with the live secret key.
2. Create the live webhook endpoint (step 2) and use its signing secret.
3. Set `NEXT_PUBLIC_APP_URL` to the production domain.
4. Make a real low-value payment to confirm the whole flow.

## 7. Troubleshooting

**"Failed to create checkout session"**: check the server logs. Usually `STRIPE_SECRET_KEY` or `DATABASE_URL` is missing or wrong.

**Webhook returns 400 "Invalid signature"**: `STRIPE_WEBHOOK_SECRET` doesn't match the endpoint, or a proxy changed the request body.

**Webhook returns 500 "Webhook not configured"**: `STRIPE_WEBHOOK_SECRET` is not set.

**Order stays `PENDING` after paying**: the webhook isn't reaching the server (run `stripe listen` locally). Opening the success page also confirms the order.
