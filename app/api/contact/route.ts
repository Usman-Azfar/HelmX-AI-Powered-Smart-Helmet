/**
 * File: api/contact/route.ts
 * Purpose: API route for handling contact form submissions with database storage and SMTP email notifications
 * Author: GitHub Copilot
 */

import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/prisma"
import { escapeHtml, sendSmtpEmail } from "@/lib/email"
import { isValidEmail } from "@/lib/validation"

const ADMIN_EMAIL = process.env.ADMIN_EMAIL || "support@helmx.com"

const LIMITS = { name: 100, subject: 200, message: 5000 } as const

// Simple in-memory rate limiter: per server instance and reset on restart.
// Use a shared store (e.g. Redis/Upstash) if this runs on multiple instances.
const RATE_LIMIT_WINDOW_MS = 60_000
const RATE_LIMIT_MAX = 5
const rateLimitMap = new Map<string, { count: number; resetTime: number }>()

function checkRateLimit(ip: string): boolean {
  const now = Date.now()

  // Drop expired entries so the map cannot grow without bound.
  if (rateLimitMap.size > 1000) {
    for (const [key, value] of rateLimitMap) {
      if (now > value.resetTime) rateLimitMap.delete(key)
    }
  }

  const limit = rateLimitMap.get(ip)
  if (!limit || now > limit.resetTime) {
    rateLimitMap.set(ip, { count: 1, resetTime: now + RATE_LIMIT_WINDOW_MS })
    return true
  }
  if (limit.count >= RATE_LIMIT_MAX) return false

  limit.count++
  return true
}

function clientIp(request: NextRequest) {
  // x-forwarded-for may be a comma-separated chain; the first entry is the original client.
  const forwarded = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim()
  return forwarded || request.headers.get("x-real-ip") || "unknown"
}

function readField(body: Record<string, unknown>, key: keyof typeof LIMITS | "email") {
  const value = body[key]
  return typeof value === "string" ? value.trim() : ""
}

export async function POST(request: NextRequest) {
  if (!checkRateLimit(clientIp(request))) {
    return NextResponse.json({ error: "Too many requests. Please try again later." }, { status: 429 })
  }

  let body: Record<string, unknown>
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 })
  }

  const name = readField(body, "name")
  const email = readField(body, "email")
  const subject = readField(body, "subject")
  const message = readField(body, "message")

  if (!name || !email || !subject || !message) {
    return NextResponse.json({ error: "All fields are required" }, { status: 400 })
  }
  if (!isValidEmail(email)) {
    return NextResponse.json({ error: "Invalid email address" }, { status: 400 })
  }
  for (const [field, max] of Object.entries(LIMITS)) {
    if ({ name, subject, message }[field as keyof typeof LIMITS].length > max) {
      return NextResponse.json({ error: `${field} must be at most ${max} characters` }, { status: 400 })
    }
  }

  try {
    const submission = await prisma.contactSubmission.create({
      data: { name, email, subject, message },
    })

    const safe = {
      name: escapeHtml(name),
      email: escapeHtml(email),
      subject: escapeHtml(subject),
      message: escapeHtml(message),
    }

    const [adminResult, userResult] = await Promise.allSettled([
      sendSmtpEmail({
        to: ADMIN_EMAIL,
        // Strip newlines so user input cannot affect mail headers.
        subject: `New Contact Form Submission: ${subject.replace(/[\r\n]+/g, " ")}`,
        replyTo: email,
        html: `
          <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #A855F7;">New Contact Form Submission</h2>
            <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
              <p><strong>Name:</strong> ${safe.name}</p>
              <p><strong>Email:</strong> <a href="mailto:${safe.email}">${safe.email}</a></p>
              <p><strong>Subject:</strong> ${safe.subject}</p>
              <p><strong>Message:</strong></p>
              <p style="white-space: pre-wrap; color: #333;">${safe.message}</p>
            </div>
            <p style="color: #666; font-size: 12px;">
              Submission ID: ${submission.id}<br/>
              Submitted at: ${submission.createdAt.toISOString()}
            </p>
          </div>
        `,
      }),
      sendSmtpEmail({
        to: email,
        subject: "We've received your message",
        html: `
          <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #A855F7;">Thank you for contacting HelmX</h2>
            <p>Hi ${safe.name},</p>
            <p>We've received your message and will get back to you as soon as possible. Here's a summary of what you sent:</p>
            <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
              <p><strong>Subject:</strong> ${safe.subject}</p>
              <p><strong>Your Message:</strong></p>
              <p style="white-space: pre-wrap; color: #333;">${safe.message}</p>
            </div>
            <p>We typically respond within 24 hours during business days.</p>
            <p>Best regards,<br/>The HelmX Team</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">Reference ID: ${submission.id}</p>
          </div>
        `,
      }),
    ])

    if (adminResult.status === "rejected") console.error("Failed to send admin notification:", adminResult.reason)
    if (userResult.status === "rejected") console.error("Failed to send user confirmation:", userResult.reason)

    return NextResponse.json({
      message: "Message received successfully",
      submissionId: submission.id,
      emailStatus: {
        admin: adminResult.status === "fulfilled",
        user: userResult.status === "fulfilled",
      },
    })
  } catch (error) {
    console.error("Contact form error:", error)
    return NextResponse.json({ error: "Failed to process your request" }, { status: 500 })
  }
}
