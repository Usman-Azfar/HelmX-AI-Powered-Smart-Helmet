import { describe, expect, it } from "vitest"
import { ALL_PART_IDS, PARTS, STORAGE_OPTIONS, priceOrder } from "@/lib/catalog"

describe("priceOrder", () => {
  it("prices the full build from the catalog", () => {
    const result = priceOrder(ALL_PART_IDS, null)
    expect(result.ok).toBe(true)
    if (!result.ok) return
    expect(result.order.total).toBe(PARTS.reduce((sum, part) => sum + part.price, 0))
    expect(result.order.parts).toHaveLength(PARTS.length)
  })

  it("adds the selected storage option", () => {
    const storage = STORAGE_OPTIONS[2]
    const result = priceOrder(["shell"], storage.id)
    expect(result.ok && result.order.total).toBe(11000 + storage.price)
  })

  it("counts duplicated IDs only once", () => {
    const result = priceOrder(["shell", "shell", "shell"], null)
    expect(result.ok && result.order.total).toBe(11000)
  })

  it("rejects unknown part IDs instead of dropping them", () => {
    expect(priceOrder(["shell", "free-helmet"], null)).toEqual({ ok: false, error: "Unknown part: free-helmet" })
  })

  it("rejects unknown storage IDs", () => {
    expect(priceOrder(["shell"], "storage-9tb").ok).toBe(false)
  })

  it("rejects an empty order", () => {
    expect(priceOrder([], null).ok).toBe(false)
  })

  it("returns parts in catalog order regardless of request order", () => {
    const result = priceOrder(["battery", "shell"], null)
    expect(result.ok && result.order.parts.map((part) => part.id)).toEqual(["shell", "battery"])
  })
})
