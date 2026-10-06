/**
 * File: catalog.ts
 * Purpose: Single source of truth for the HelmX configurator catalog and pricing.
 *          Shared by the buy page (display) and the checkout API (authoritative pricing),
 *          so the server never trusts a client-supplied total.
 */

export type CatalogPart = {
  id: string
  name: string
  price: number
  description: string
  group: "core" | "sensors" | "interaction"
}

export type StorageOption = {
  id: string
  name: string
  price: number
}

/** Prices are whole PKR. */
export const PARTS: readonly CatalogPart[] = [
  { id: "shell", name: "Helmet", price: 11000, description: "Outer shell and mounting frame", group: "core" },
  { id: "compute", name: "Raspberry Pi", price: 33500, description: "Main compute board", group: "core" },
  { id: "power", name: "Charger", price: 4000, description: "Charging and power handling", group: "core" },
  { id: "case", name: "Protective case", price: 1000, description: "Internal case and protection", group: "core" },
  { id: "picam", name: "Pi Camera Module v2", price: 7000, description: "Primary rear camera", group: "sensors" },
  { id: "usbcam", name: "USB Camera Module", price: 4000, description: "Secondary camera module", group: "sensors" },
  { id: "imu", name: "MPU 6050", price: 700, description: "Motion / impact sensing", group: "sensors" },
  { id: "air", name: "MQ 135", price: 500, description: "Air quality sensing", group: "sensors" },
  { id: "temp", name: "DHT 22", price: 600, description: "Temperature and humidity", group: "sensors" },
  { id: "gps", name: "GPS NEO 6M", price: 1800, description: "Navigation and location", group: "sensors" },
  { id: "gsm", name: "GSM SIM 800L", price: 2500, description: "Emergency messaging", group: "sensors" },
  { id: "voice", name: "Voice recognition mic", price: 6500, description: "Hands-free voice commands", group: "interaction" },
  { id: "speakers", name: "2 speakers", price: 1000, description: "Audio output for alerts", group: "interaction" },
  { id: "battery", name: "3 lithium-ion batteries", price: 6000, description: "Standard power pack", group: "interaction" },
]

export const STORAGE_OPTIONS: readonly StorageOption[] = [
  { id: "storage-32gb", name: "32 GB", price: 900 },
  { id: "storage-64gb", name: "64 GB", price: 1200 },
  { id: "storage-128gb", name: "128 GB", price: 1800 },
  { id: "storage-256gb", name: "256 GB", price: 2400 },
  { id: "storage-512gb", name: "512 GB", price: 3300 },
  { id: "storage-1tb", name: "1 TB", price: 4500 },
]

export const CURRENCY = "PKR"

export const ALL_PART_IDS = PARTS.map((part) => part.id)

const partsById = new Map(PARTS.map((part) => [part.id, part]))
const storageById = new Map(STORAGE_OPTIONS.map((option) => [option.id, option]))

export function getStorageOption(id: string | null | undefined): StorageOption | null {
  return id ? storageById.get(id) ?? null : null
}

export type PricedOrder = {
  parts: CatalogPart[]
  storage: StorageOption | null
  total: number
}

/**
 * Resolves part and storage IDs against the catalog and computes the total.
 * Unknown IDs are rejected (not silently dropped) so a tampered request fails loudly.
 */
export function priceOrder(
  partIds: readonly string[],
  storageId: string | null | undefined,
): { ok: true; order: PricedOrder } | { ok: false; error: string } {
  const uniqueIds = [...new Set(partIds)]
  const parts: CatalogPart[] = []

  for (const id of uniqueIds) {
    const part = partsById.get(id)
    if (!part) {
      return { ok: false, error: `Unknown part: ${id}` }
    }
    parts.push(part)
  }

  let storage: StorageOption | null = null
  if (storageId) {
    storage = storageById.get(storageId) ?? null
    if (!storage) {
      return { ok: false, error: `Unknown storage option: ${storageId}` }
    }
  }

  if (parts.length === 0 && !storage) {
    return { ok: false, error: "Select at least one item" }
  }

  // Keep catalog order regardless of request order.
  parts.sort((a, b) => PARTS.indexOf(a) - PARTS.indexOf(b))

  const total = parts.reduce((sum, part) => sum + part.price, 0) + (storage?.price ?? 0)
  return { ok: true, order: { parts, storage, total } }
}

export function formatMoney(amount: number) {
  return `₨ ${amount.toLocaleString("en-PK")}`
}
