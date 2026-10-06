import { NextRequest, NextResponse } from "next/server"
import type Stripe from "stripe"
import { getStripe } from "@/lib/stripe"
import { finalizePaidSession, markSessionFailed } from "@/lib/orders"

export async function POST(request: NextRequest) {
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET
  if (!webhookSecret) {
    console.error("STRIPE_WEBHOOK_SECRET is not set; cannot verify webhook.")
    return NextResponse.json({ error: "Webhook not configured" }, { status: 500 })
  }

  const signature = request.headers.get("stripe-signature")
  if (!signature) {
    return NextResponse.json({ error: "Missing stripe-signature header" }, { status: 400 })
  }

  let event: Stripe.Event
  try {
    event = getStripe().webhooks.constructEvent(await request.text(), signature, webhookSecret)
  } catch (error) {
    console.error("Webhook signature verification failed:", error)
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 })
  }

  try {
    switch (event.type) {
      // `completed` may still be unpaid for delayed payment methods; finalizePaidSession checks payment_status.
      case "checkout.session.completed":
      case "checkout.session.async_payment_succeeded": {
        const { order, newlyPaid } = await finalizePaidSession(event.data.object)
        console.log(`${event.type}: order ${order?.id ?? "n/a"}${newlyPaid ? " marked PAID" : ""}`)
        break
      }

      case "checkout.session.expired":
      case "checkout.session.async_payment_failed": {
        await markSessionFailed(event.data.object)
        console.log(`${event.type}: session ${event.data.object.id}`)
        break
      }

      default:
        console.log(`Unhandled event type: ${event.type}`)
    }

    return NextResponse.json({ received: true })
  } catch (error) {
    // A 5xx makes Stripe retry, which is safe because order finalization is idempotent.
    console.error("Webhook processing error:", error)
    return NextResponse.json({ error: "Webhook processing failed" }, { status: 500 })
  }
}
