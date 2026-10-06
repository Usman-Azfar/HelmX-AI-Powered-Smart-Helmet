import { NextResponse } from "next/server"
import { sendSmtpEmail } from "@/lib/email"
import { isValidEmail } from "@/lib/validation"

/**
 * Development-only SMTP check. Disabled in production because an unauthenticated
 * "send arbitrary email" endpoint would turn the SMTP account into an open spam relay.
 * It only ever sends a fixed message to ADMIN_EMAIL / SMTP_USER.
 */
export async function POST() {
  if (process.env.NODE_ENV === "production") {
    return NextResponse.json({ error: "Not found" }, { status: 404 })
  }

  const to = process.env.ADMIN_EMAIL || process.env.SMTP_USER
  if (!isValidEmail(to)) {
    return NextResponse.json({ ok: false, error: "Set ADMIN_EMAIL or SMTP_USER to a valid address" }, { status: 400 })
  }

  try {
    const result = await sendSmtpEmail({
      to,
      subject: "HelmX test email",
      html: `<p>Test email from HelmX at ${new Date().toISOString()}</p>`,
    })
    return NextResponse.json({ ok: true, messageId: result.messageId })
  } catch (err) {
    console.error("Test email failed:", err)
    return NextResponse.json({ ok: false, error: String(err) }, { status: 500 })
  }
}
