import { describe, expect, it } from "vitest"
import { formatOrderReceiptHtml } from "@/lib/orders"

const baseOrder = {
  id: "order_1",
  email: "rider@helmx.com",
  amountMinor: 1_290_000,
  currency: "PKR",
  paidAt: new Date("2026-01-01T10:00:00Z"),
}

describe("formatOrderReceiptHtml", () => {
  it("lists parts and charges the real storage price", () => {
    const html = formatOrderReceiptHtml({
      ...baseOrder,
      cartItems: {
        parts: [{ id: "shell", name: "Helmet", price: 11000, description: "Outer shell" }],
        storage: { id: "storage-128gb", name: "128 GB", price: 1800 },
      },
    })
    expect(html).toContain("Helmet")
    expect(html).toContain("Storage: 128 GB")
    expect(html).toContain("1,800 PKR")
    expect(html).toContain("12,900.00 PKR")
  })

  it("still renders orders saved in the legacy cart shape", () => {
    const html = formatOrderReceiptHtml({
      ...baseOrder,
      cartItems: {
        activeParts: [{ id: "gps", name: "GPS NEO 6M", price: 1800 }],
        selectedExtras: [],
        selectedStorage: { name: "64 GB", price: 1200 },
      },
    })
    expect(html).toContain("GPS NEO 6M")
    expect(html).toContain("Storage: 64 GB")
  })

  it("escapes stored values", () => {
    const html = formatOrderReceiptHtml({
      ...baseOrder,
      email: "<script>x</script>@evil.com",
      cartItems: { parts: [{ id: "x", name: "<img src=x onerror=alert(1)>", price: 1 }], storage: null },
    })
    expect(html).not.toContain("<script>")
    expect(html).not.toContain("<img")
  })
})
