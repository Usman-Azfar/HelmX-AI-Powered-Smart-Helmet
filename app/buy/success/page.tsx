"use client"

import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { Suspense, useEffect, useState, type ReactNode } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Check, ArrowRight, Loader2, X, Clock } from "lucide-react"

type ConfirmState = "confirming" | "paid" | "pending" | "error"

function useConfirmPayment(sessionId: string | null, enabled: boolean) {
  const [state, setState] = useState<ConfirmState>("confirming")

  useEffect(() => {
    if (!enabled || !sessionId) return
    const controller = new AbortController()

    fetch(`/api/checkout-session?session_id=${encodeURIComponent(sessionId)}`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const data = (await response.json()) as { status?: string }
        setState(data.status === "PAID" ? "paid" : "pending")
      })
      .catch((error) => {
        if (controller.signal.aborted) return
        console.error("Payment confirmation failed:", error)
        setState("error")
      })

    return () => controller.abort()
  }, [sessionId, enabled])

  return state
}

function StatusIcon({ tone, children }: { tone: "success" | "warn" | "error"; children: ReactNode }) {
  const tones = {
    success: "bg-emerald-400/10 border-emerald-400/30 text-emerald-400",
    warn: "bg-amber-400/10 border-amber-400/30 text-amber-300",
    error: "bg-red-400/10 border-red-400/30 text-red-400",
  }
  return (
    <div className="flex justify-center">
      <div className={`flex h-24 w-24 items-center justify-center rounded-full border ${tones[tone]}`}>{children}</div>
    </div>
  )
}

function SuccessContent() {
  const searchParams = useSearchParams()
  const isSuccessRedirect = searchParams.get("payment") === "success"
  const sessionId = searchParams.get("session_id")
  const state = useConfirmPayment(sessionId, isSuccessRedirect)

  if (!isSuccessRedirect || !sessionId) {
    return (
      <div className="space-y-6 text-center">
        <StatusIcon tone="error">
          <X className="h-12 w-12" />
        </StatusIcon>
        <div className="space-y-2">
          <h1 className="text-4xl font-black">Payment Cancelled</h1>
          <p className="text-lg text-white/70">Your payment was not completed. No charges were made.</p>
        </div>
        <p className="text-white/70">You can return to the configurator and try again anytime.</p>
        <Button asChild className="group bg-cyan-400 text-slate-950 hover:bg-cyan-300">
          <Link href="/buy">
            Return to configurator
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
        </Button>
      </div>
    )
  }

  if (state === "confirming") {
    return (
      <div className="space-y-6 py-8 text-center">
        <Loader2 className="mx-auto h-12 w-12 animate-spin text-cyan-300" />
        <p className="text-lg text-white/70">Confirming your payment...</p>
      </div>
    )
  }

  const paid = state === "paid"

  return (
    <div className="space-y-6 text-center">
      {paid ? (
        <StatusIcon tone="success">
          <Check className="h-12 w-12" />
        </StatusIcon>
      ) : (
        <StatusIcon tone="warn">
          <Clock className="h-12 w-12" />
        </StatusIcon>
      )}

      <div className="space-y-2">
        <h1 className="text-4xl font-black">{paid ? "Payment Successful!" : "Payment Processing"}</h1>
        <p className="text-lg text-white/70">
          {paid
            ? "Your HelmX smart helmet order has been confirmed."
            : state === "pending"
              ? "Stripe has not confirmed your payment yet. This can take a few minutes for some payment methods."
              : "We couldn't confirm your payment right now. If you were charged, your order will be confirmed automatically."}
        </p>
      </div>

      <Card className="border-white/10 bg-white/[0.03] p-6 text-left">
        <p className="text-sm text-white/70">
          {paid
            ? "A receipt has been sent to the email address you entered at checkout."
            : "You'll receive a receipt by email as soon as the payment is confirmed. Contact support if it doesn't arrive."}
        </p>
      </Card>

      {paid && (
        <Card className="border-white/10 bg-white/[0.03] p-6">
          <h3 className="mb-3 text-left font-semibold">What happens next?</h3>
          <ul className="space-y-2 text-left text-sm text-white/70">
            {[
              "Our team will review your custom configuration",
              "We'll reach out within 24 hours with estimated delivery date",
              "Your helmet will be custom-built and tested before shipping",
            ].map((step) => (
              <li key={step} className="flex items-start gap-3">
                <Check className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-400" />
                <span>{step}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <div className="flex flex-col justify-center gap-3 sm:flex-row">
        <Button asChild className="group bg-cyan-400 text-slate-950 hover:bg-cyan-300">
          <Link href="/">
            Back to home
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
        </Button>
        <Button asChild variant="outline" className="border-white/15 bg-transparent text-white hover:bg-white/5">
          <Link href="/contact">Contact support</Link>
        </Button>
      </div>
    </div>
  )
}

export default function BuySuccessPage() {
  return (
    <div className="flex min-h-screen items-center justify-center overflow-hidden bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.16),transparent_28%),radial-gradient(circle_at_bottom_right,rgba(249,115,22,0.14),transparent_32%),linear-gradient(180deg,#020617_0%,#0b1220_100%)] py-24 text-white">
      <div className="container mx-auto max-w-2xl px-4">
        <Card className="border-white/10 bg-white/5 p-8 backdrop-blur-xl">
          <Suspense fallback={<Loader2 className="mx-auto h-12 w-12 animate-spin text-cyan-300" />}>
            <SuccessContent />
          </Suspense>
        </Card>
      </div>
    </div>
  )
}
