import Stripe from "stripe"

let client: Stripe | null = null

/**
 * Lazily creates the Stripe client so a missing key produces a clear error at request
 * time instead of an opaque failure (or a crash) when the module is first imported.
 */
export function getStripe(): Stripe {
  if (client) return client

  const secretKey = process.env.STRIPE_SECRET_KEY
  if (!secretKey) {
    throw new Error("STRIPE_SECRET_KEY is not set.")
  }

  client = new Stripe(secretKey)
  return client
}

export function getPaymentIntentId(paymentIntent: Stripe.Checkout.Session["payment_intent"]): string | null {
  if (!paymentIntent) return null
  return typeof paymentIntent === "string" ? paymentIntent : paymentIntent.id
}
