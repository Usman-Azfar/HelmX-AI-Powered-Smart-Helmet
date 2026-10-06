import nodemailer, { type Transporter } from "nodemailer"

export const EMAIL_FROM = process.env.EMAIL_FROM || process.env.SMTP_USER || "HelmX <no-reply@helmx.com>"

let transporter: Transporter | null | undefined

function getTransporter(): Transporter | null {
  if (transporter !== undefined) return transporter

  const { SMTP_HOST, SMTP_USER, SMTP_PASS } = process.env
  if (!SMTP_HOST || !SMTP_USER || !SMTP_PASS) {
    console.warn("SMTP not configured. Emails will not be sent until SMTP env vars are set.")
    transporter = null
    return transporter
  }

  transporter = nodemailer.createTransport({
    host: SMTP_HOST,
    port: Number(process.env.SMTP_PORT || "465"),
    secure: process.env.SMTP_SECURE !== "false",
    auth: { user: SMTP_USER, pass: SMTP_PASS },
  })
  return transporter
}

/** Escapes user-controlled text before it is interpolated into an HTML email. */
export function escapeHtml(value: unknown): string {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
}

export async function sendSmtpEmail(options: { to: string; subject: string; html: string; replyTo?: string }) {
  const smtp = getTransporter()
  if (!smtp) {
    throw new Error("SMTP is not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER, and SMTP_PASS.")
  }

  const info = await smtp.sendMail({
    from: EMAIL_FROM,
    to: options.to,
    subject: options.subject,
    html: options.html,
    replyTo: options.replyTo,
  })
  console.log(`Email sent to ${options.to}: ${info.messageId}`)
  return info
}
