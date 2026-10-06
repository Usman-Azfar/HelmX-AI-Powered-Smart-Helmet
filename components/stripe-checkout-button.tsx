"use client"

import { Button } from "@/components/ui/button"
import { Loader2, CreditCard } from "lucide-react"
import { useState } from "react"
import { isValidEmail } from "@/lib/validation"

interface StripeCheckoutButtonProps {
  email: string
  partIds: string[]
  storageId: string | null
  disabled?: boolean
}

export function StripeCheckoutButton({ email, partIds, storageId, disabled }: StripeCheckoutButtonProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCheckout = async () => {
    setError(null)
    if (!isValidEmail(email.trim())) {
      setError("Please enter a valid email address.")
      return
    }

    setLoading(true)
    try {
      const response = await fetch("/api/checkout-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // Only IDs are sent; the server prices the order from the catalog.
        body: JSON.stringify({ email: email.trim(), partIds, storageId }),
      })
      const data = (await response.json().catch(() => ({}))) as { url?: string; error?: string }

      if (response.ok && data.url) {
        window.location.assign(data.url)
        return // keep the spinner while the browser navigates to Stripe
      }
      setError(data.error || "Failed to start checkout. Please try again.")
    } catch (err) {
      console.error("Checkout error:", err)
      setError("Failed to start checkout. Please check your connection and try again.")
    }
    setLoading(false)
  }

  return (
    <div className="space-y-2">
      <Button
        type="button"
        onClick={handleCheckout}
        disabled={loading || disabled || !email}
        className="group w-full bg-cyan-400 text-slate-950 hover:bg-cyan-300 disabled:opacity-50"
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Redirecting to Stripe...
          </>
        ) : (
          <>
            <CreditCard className="mr-2 h-4 w-4" />
            Pay with Stripe
          </>
        )}
      </Button>
      {error && (
        <p role="alert" className="text-sm text-amber-300">
          {error}
        </p>
      )}
    </div>
  )
}
