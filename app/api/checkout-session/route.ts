import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/prisma"
import { getStripe } from "@/lib/stripe"
import { isValidEmail } from "@/lib/validation"
import { CURRENCY, priceOrder } from "@/lib/catalog"
import { finalizePaidSession, type OrderCart } from "@/lib/orders"

function appUrl(request: NextRequest) {
  return (process.env.NEXT_PUBLIC_APP_URL || request.nextUrl.origin).replace(/\/$/, "")
}

/**
 * Confirms a Checkout Session after Stripe redirects back to /buy/success.
 * Acts as a fallback for the webhook (e.g. local development without `stripe listen`).
 */
export async function GET(request: NextRequest) {
  const sessionId = request.nextUrl.searchParams.get("session_id")
  if (!sessionId || !sessionId.startsWith("cs_")) {
    return NextResponse.json({ error: "A valid session_id is required" }, { status: 400 })
  }

  try {
    const session = await getStripe().checkout.sessions.retrieve(sessionId)
    const { order } = await finalizePaidSession(session)

    return NextResponse.json({
      paymentStatus: session.payment_status,
      status: order?.status ?? (session.payment_status === "paid" ? "PAID" : "PENDING"),
      orderId: order?.id ?? null,
    })
  } catch (error) {
    console.error("Session confirmation error:", error)
    return NextResponse.json({ error: "Failed to confirm checkout session" }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  let body: { partIds?: unknown; storageId?: unknown; email?: unknown }
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 })
  }

  const email = typeof body.email === "string" ? body.email.trim() : ""
  if (!isValidEmail(email)) {
    return NextResponse.json({ error: "Please provide a valid email address" }, { status: 400 })
  }

  if (!Array.isArray(body.partIds) || !body.partIds.every((id) => typeof id === "string")) {
    return NextResponse.json({ error: "partIds must be an array of part IDs" }, { status: 400 })
  }
  const storageId = typeof body.storageId === "string" && body.storageId ? body.storageId : null

  // Price is always computed on the server from the catalog; the client never sends a total.
  const priced = priceOrder(body.partIds as string[], storageId)
  if (!priced.ok) {
    return NextResponse.json({ error: priced.error }, { status: 400 })
  }
  const { parts, storage, total } = priced.order
  const amountMinor = total * 100

  const cart: OrderCart = {
    parts: parts.map(({ id, name, price, description }) => ({ id, name, price, description })),
    storage,
  }

  let orderId: string | null = null
  try {
    const order = await prisma.order.create({
      data: {
        email,
        amountMinor,
        currency: CURRENCY,
        status: "PENDING",
        cartItems: cart,
        selectedStorage: storage?.name ?? null,
      },
    })
    orderId = order.id

    const baseUrl = appUrl(request)
    const session = await getStripe().checkout.sessions.create({
      mode: "payment",
      customer_email: email,
      line_items: [
        ...parts.map((part) => ({
          price_data: {
            currency: CURRENCY.toLowerCase(),
            product_data: { name: part.name, description: part.description },
            unit_amount: part.price * 100,
          },
          quantity: 1,
        })),
        ...(storage
          ? [
              {
                price_data: {
                  currency: CURRENCY.toLowerCase(),
                  product_data: { name: `Storage: ${storage.name}` },
                  unit_amount: storage.price * 100,
                },
                quantity: 1,
              },
            ]
          : []),
      ],
      success_url: `${baseUrl}/buy/success?payment=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${baseUrl}/buy/success?payment=cancelled`,
      metadata: { orderId: order.id },
      client_reference_id: order.id,
    })

    await prisma.order.update({
      where: { id: order.id },
      data: { stripeSessionId: session.id },
    })

    return NextResponse.json({ url: session.url })
  } catch (error) {
    console.error("Checkout session error:", error)
    if (orderId) {
      await prisma.order.update({ where: { id: orderId }, data: { status: "FAILED" } }).catch(() => null)
    }
    return NextResponse.json({ error: "Failed to create checkout session" }, { status: 500 })
  }
}
