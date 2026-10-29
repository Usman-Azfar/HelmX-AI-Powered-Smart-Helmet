import { describe, expect, it } from "vitest"
import { clientIp, createRateLimiter } from "@/lib/rate-limit"

describe("createRateLimiter", () => {
  it("allows up to max requests per window", () => {
    const limit = createRateLimiter({ windowMs: 1000, max: 3 })
    expect([limit("a", 0), limit("a", 1), limit("a", 2), limit("a", 3)]).toEqual([true, true, true, false])
  })

  it("resets once the window has passed", () => {
    const limit = createRateLimiter({ windowMs: 1000, max: 1 })
    expect(limit("a", 0)).toBe(true)
    expect(limit("a", 500)).toBe(false)
    expect(limit("a", 1001)).toBe(true)
  })

  it("tracks each key separately", () => {
    const limit = createRateLimiter({ windowMs: 1000, max: 1 })
    expect(limit("a", 0)).toBe(true)
    expect(limit("b", 0)).toBe(true)
    expect(limit("a", 0)).toBe(false)
  })

  it("evicts expired keys once the map is full", () => {
    const limit = createRateLimiter({ windowMs: 10, max: 1, maxKeys: 2 })
    limit("a", 0)
    limit("b", 0)
    limit("c", 0)
    // All three expired; the sweep must not affect a fresh request for a new key.
    expect(limit("d", 100)).toBe(true)
    expect(limit("a", 100)).toBe(true)
  })
})

describe("clientIp", () => {
  it("uses the first x-forwarded-for entry", () => {
    expect(clientIp(new Headers({ "x-forwarded-for": "203.0.113.7, 10.0.0.1" }))).toBe("203.0.113.7")
  })

  it("falls back to x-real-ip, then unknown", () => {
    expect(clientIp(new Headers({ "x-real-ip": "198.51.100.2" }))).toBe("198.51.100.2")
    expect(clientIp(new Headers())).toBe("unknown")
  })
})
