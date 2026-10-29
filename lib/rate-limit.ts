// Simple in-memory fixed-window rate limiter: per server instance and reset on restart.
// Use a shared store (e.g. Redis/Upstash) if this runs on multiple instances.

export type RateLimiter = (key: string, now?: number) => boolean

export function createRateLimiter({ windowMs, max, maxKeys = 1000 }: { windowMs: number; max: number; maxKeys?: number }): RateLimiter {
  const hits = new Map<string, { count: number; resetTime: number }>()

  return (key, now = Date.now()) => {
    // Drop expired entries so the map cannot grow without bound.
    if (hits.size > maxKeys) {
      for (const [k, value] of hits) {
        if (now > value.resetTime) hits.delete(k)
      }
    }

    const entry = hits.get(key)
    if (!entry || now > entry.resetTime) {
      hits.set(key, { count: 1, resetTime: now + windowMs })
      return true
    }
    if (entry.count >= max) return false

    entry.count++
    return true
  }
}

export function clientIp(headers: Headers) {
  // x-forwarded-for may be a comma-separated chain; the first entry is the original client.
  const forwarded = headers.get("x-forwarded-for")?.split(",")[0]?.trim()
  return forwarded || headers.get("x-real-ip") || "unknown"
}
