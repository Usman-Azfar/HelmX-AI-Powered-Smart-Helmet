/**
 * File: orders.ts
 * Purpose: Order lifecycle helpers shared by the Stripe webhook and the checkout confirmation route.
 *          Marking an order paid is an atomic PENDING/FAILED -> PAID transition, and only the caller
 *          that performs the transition sends the receipt, so webhook retries and the success-page
 *          confirmation can never produce duplicate receipts.
 */
import type Stripe from "stripe"
import type { Order } from "@prisma/client"
import { prisma } from "@/lib/prisma"
import { escapeHtml, sendSmtpEmail } from "@/lib/email"
import { getPaymentIntentId } from "@/lib/stripe"

/** Shape persisted in Order.cartItems. */
export type OrderCart = {
  parts: Array<{ id: string; name: string; price: number; description?: string }>
  storage: { id: string; name: string; price: number } | null
}

type LineItem = { name: string; description: string; price: number }

/** Normalizes the current cart shape as well as the legacy one (activeParts/selectedExtras/selectedStorage). */
function cartLineItems(cartItems: unknown): LineItem[] {
  const cart = (cartItems ?? {}) as Record<string, unknown>
  const items: LineItem[] = []

  const pushAll = (list: unknown, fallbackDescription: string) => {
    if (!Array.isArray(list)) return
    for (const item of list as Array<Record<string, unknown>>) {
      items.push({
        name: String(item.name ?? "Item"),
        description: String(item.description ?? fallbackDescription),
        price: Number(item.price ?? 0),
      })
    }
  }

  pushAll(cart.parts, "Included in your build")
  pushAll(cart.activeParts, "Included in your build")
  pushAll(cart.selectedExtras, "Optional add-on")

  const storage = cart.storage ?? cart.selectedStorage
  if (storage && typeof storage === "object") {
    const s = storage as Record<string, unknown>
    items.push({ name: `Storage: ${s.name ?? ""}`, description: "Storage option for your HelmX build", price: Number(s.price ?? 0) })
  }

  return items
}

function formatAmount(amountMinor: number, currency: string) {
  return `${(amountMinor / 100).toLocaleString("en-PK", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${escapeHtml(currency)}`
}

export function formatOrderReceiptHtml(order: Pick<Order, "id" | "email" | "amountMinor" | "currency" | "cartItems" | "paidAt">) {
  const receiptDate = (order.paidAt ?? new Date()).toLocaleString("en-PK", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
  const email = escapeHtml(order.email)
  const total = formatAmount(order.amountMinor, order.currency)

  const lineItemsHtml = cartLineItems(order.cartItems)
    .map(
      (item) => `
        <tr>
          <td style="padding: 10px 16px; border-bottom: 1px solid #E5E7EB;">
            <div style="font-weight: 600; font-size: 13px; line-height: 1.35; color: #111827;">${escapeHtml(item.name)}</div>
            <div style="font-size: 11px; line-height: 1.35; color: #6B7280; margin-top: 3px;">${escapeHtml(item.description)}</div>
          </td>
          <td style="padding: 10px 16px; border-bottom: 1px solid #E5E7EB; text-align: right; font-weight: 600; font-size: 13px; color: #111827; white-space: nowrap;">
            ${item.price.toLocaleString("en-PK")} ${escapeHtml(order.currency)}
          </td>
        </tr>`,
    )
    .join("")

  const infoCell = (label: string, value: string, color = "#111827") => `
    <td style="width: 50%; padding: 6px;">
      <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px;">
        <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: #6B7280;">${label}</div>
        <div style="margin-top: 6px; font-weight: 700; color: ${color}; word-break: break-word;">${value}</div>
      </div>
    </td>`

  // Table-based layout: many email clients (notably Outlook) do not support CSS grid.
  return `
    <div style="font-family: Arial, sans-serif; max-width: 720px; margin: 0 auto; background: #ffffff; color: #111827; border: 1px solid #E5E7EB; border-radius: 16px; overflow: hidden;">
      <div style="background: #0F172A; color: #ffffff; padding: 28px 32px;">
        <div style="font-size: 13px; letter-spacing: 0.14em; text-transform: uppercase; color: #93C5FD;">HelmX Receipt</div>
        <h1 style="margin: 8px 0 0; font-size: 28px; line-height: 1.2; color: #FFFFFF;">Payment received</h1>
        <p style="margin: 10px 0 0; font-size: 15px; color: #F8FAFC;">Thank you for your purchase. Your order has been confirmed.</p>
      </div>

      <div style="padding: 32px;">
        <p style="margin: 0 0 20px; font-size: 15px; color: #111827;">Hi ${email},</p>

        <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 18px;">
          <tr>${infoCell("Receipt Date", escapeHtml(receiptDate))}${infoCell("Order ID", escapeHtml(order.id))}</tr>
          <tr>${infoCell("Payment Status", "Paid", "#047857")}${infoCell("Order Total", total)}</tr>
        </table>

        <div style="border: 1px solid #E5E7EB; border-radius: 12px; overflow: hidden; margin-bottom: 24px;">
          <table style="width: 100%; border-collapse: collapse;">
            <thead>
              <tr style="background: #F9FAFB; text-align: left;">
                <th style="padding: 12px 16px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #6B7280;">Description</th>
                <th style="padding: 12px 16px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #6B7280; text-align: right;">Amount</th>
              </tr>
            </thead>
            <tbody>
              ${
                lineItemsHtml ||
                `<tr><td colspan="2" style="padding: 18px 16px; color: #6B7280; font-size: 12px;">No item details were attached to this order.</td></tr>`
              }
            </tbody>
            <tfoot>
              <tr>
                <td style="padding: 14px 16px; font-weight: 700; color: #111827; font-size: 13px;">Total</td>
                <td style="padding: 14px 16px; font-weight: 800; text-align: right; color: #111827; font-size: 13px; white-space: nowrap;">${total}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div style="background: #F9FAFB; border-radius: 12px; padding: 16px 18px; color: #374151; line-height: 1.6; font-size: 13px;">
          <strong>What happens next:</strong> We are preparing your order and will contact you if we need any further details.
        </div>

        <p style="margin: 24px 0 0; color: #374151;">Best regards,<br/>The HelmX Team</p>
      </div>
    </div>
  `
}

function orderIdFromSession(session: Stripe.Checkout.Session): string | null {
  return session.metadata?.orderId ?? session.client_reference_id ?? null
}

/**
 * Marks the order behind a paid Checkout Session as PAID and sends the receipt exactly once.
 * Safe to call any number of times for the same session.
 */
export async function finalizePaidSession(session: Stripe.Checkout.Session) {
  if (session.payment_status !== "paid") {
    return { order: null, newlyPaid: false }
  }

  const orderId = orderIdFromSession(session)
  const where = orderId ? { id: orderId } : { stripeSessionId: session.id }

  const { count } = await prisma.order.updateMany({
    where: { ...where, status: { not: "PAID" } },
    data: {
      status: "PAID",
      stripeSessionId: session.id,
      stripePaymentIntentId: getPaymentIntentId(session.payment_intent),
      paidAt: new Date(),
    },
  })

  const order = await prisma.order.findFirst({ where })
  if (!order) {
    console.error(`Paid Checkout Session ${session.id} has no matching order.`)
    return { order: null, newlyPaid: false }
  }

  if (session.amount_total !== null && session.amount_total !== order.amountMinor) {
    console.error(
      `Amount mismatch for order ${order.id}: Stripe charged ${session.amount_total}, order expects ${order.amountMinor}.`,
    )
  }

  const newlyPaid = count > 0
  if (newlyPaid) {
    try {
      await sendSmtpEmail({
        to: order.email,
        subject: "HelmX Receipt - Payment Confirmed",
        html: formatOrderReceiptHtml(order),
      })
    } catch (error) {
      console.error(`Failed to send receipt for order ${order.id}:`, error)
    }
  }

  return { order, newlyPaid }
}

/** Marks a still-pending order as FAILED (expired session or failed async payment). Never downgrades a PAID order. */
export async function markSessionFailed(session: Stripe.Checkout.Session) {
  const orderId = orderIdFromSession(session)
  await prisma.order.updateMany({
    where: { ...(orderId ? { id: orderId } : { stripeSessionId: session.id }), status: "PENDING" },
    data: { status: "FAILED" },
  })
}
