"use client"

import Link from "next/link"
import dynamic from "next/dynamic"
import { useMemo, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { StripeCheckoutButton } from "@/components/stripe-checkout-button"
import { Card } from "@/components/ui/card"
import { ALL_PART_IDS, PARTS, STORAGE_OPTIONS, formatMoney, getStorageOption, type CatalogPart } from "@/lib/catalog"
import { Check, Gauge, Package, Shield, Sparkles } from "lucide-react"

// three.js + the 10 MB model are only needed on this page and only in the browser,
// so load them after the configurator UI is interactive.
const HelmetScene = dynamic(() => import("@/components/helmet-scene").then((mod) => mod.HelmetScene), {
  ssr: false,
  loading: () => <SceneSkeleton />,
})

function SceneSkeleton() {
  return (
    <div className="flex h-[480px] items-center justify-center rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_center,rgba(56,189,248,0.14),rgba(2,6,23,0.98)_58%)] md:h-[580px]">
      <span className="animate-pulse text-xs uppercase tracking-[0.3em] text-white/50">Loading 3D preview</span>
    </div>
  )
}

const PART_GROUPS: Array<{ id: CatalogPart["group"]; label: string }> = [
  { id: "core", label: "Core parts" },
  { id: "sensors", label: "Sensors & connectivity" },
  { id: "interaction", label: "Audio, voice & power" },
]

export function BuyPage() {
  const [removedParts, setRemovedParts] = useState<string[]>([])
  const [selectedStorage, setSelectedStorage] = useState<string | null>(null)
  const [email, setEmail] = useState("")

  const activeParts = useMemo(() => PARTS.filter((part) => !removedParts.includes(part.id)), [removedParts])
  const storage = getStorageOption(selectedStorage)
  const total = activeParts.reduce((sum, part) => sum + part.price, 0) + (storage?.price ?? 0)
  const partIds = useMemo(() => activeParts.map((part) => part.id), [activeParts])
  const allSelected = removedParts.length === 0

  const toggleRemovedPart = (id: string) => {
    setRemovedParts((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]))
  }

  const toggleAll = () => setRemovedParts(allSelected ? [...ALL_PART_IDS] : [])

  return (
    <section className="overflow-hidden bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.16),transparent_28%),radial-gradient(circle_at_bottom_right,rgba(249,115,22,0.14),transparent_32%),linear-gradient(180deg,#020617_0%,#0b1220_100%)] text-white">
      <div className="relative pt-24 pb-16 md:pt-28">
        <div className="absolute inset-0 -z-10 bg-[linear-gradient(to_right,rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:96px_96px] opacity-20" />
        <div className="container mx-auto px-4">
          <div className="mb-8 flex flex-wrap items-center gap-3">
            <Badge className="border-cyan-400/30 bg-cyan-400/10 text-cyan-100">Premium configurator</Badge>
            <span className="text-sm text-white/65">Built for a flagship feel, not a basic shop page.</span>
          </div>

          <div className="grid gap-8 lg:grid-cols-[1.02fr_0.98fr] lg:items-start">
            <div className="space-y-8">
              <div className="space-y-5">
                <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-cyan-100 backdrop-blur">
                  <Sparkles className="h-4 w-4" />
                  HelmX order studio
                </div>
                <h1 className="max-w-3xl text-5xl font-black leading-[0.95] tracking-tight md:text-7xl">
                  Configure a smart helmet that feels like a concept piece.
                </h1>
                <p className="max-w-2xl text-lg leading-relaxed text-white/70 md:text-xl">
                  Live 3D preview on the right, build controls on the left, and a quote that updates as you add or remove hardware parts.
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <Card className="border-white/10 bg-white/5 p-5 backdrop-blur-xl">
                  <div className="flex items-center gap-3 text-white/75">
                    <Shield className="h-5 w-5 text-cyan-300" />
                    <span className="text-sm">Core systems</span>
                  </div>
                  <div className="mt-3 text-3xl font-bold">Helmet kit</div>
                  <div className="mt-1 text-sm text-white/55">Shell, compute, power, and essential safety parts</div>
                </Card>
                <Card className="border-white/10 bg-white/5 p-5 backdrop-blur-xl">
                  <div className="flex items-center gap-3 text-white/75">
                    <Gauge className="h-5 w-5 text-orange-300" />
                    <span className="text-sm">Live quote</span>
                  </div>
                  <div className="mt-3 text-3xl font-bold">{formatMoney(total)}</div>
                  <div className="mt-1 text-sm text-white/55">Updates instantly as you customize</div>
                </Card>
                <Card className="border-white/10 bg-white/5 p-5 backdrop-blur-xl">
                  <div className="flex items-center gap-3 text-white/75">
                    <Package className="h-5 w-5 text-emerald-300" />
                    <span className="text-sm">Build status</span>
                  </div>
                  <div className="mt-3 text-3xl font-bold">Built to order</div>
                  <div className="mt-1 text-sm text-white/55">Parts can be added or removed before checkout</div>
                </Card>
              </div>

              <Card className="border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm uppercase tracking-[0.25em] text-white/45">Build controls</p>
                    <h2 className="mt-2 text-2xl font-bold">Add or remove hardware parts</h2>
                  </div>
                  <Badge className="border-white/10 bg-white/10 text-white">{formatMoney(total)}</Badge>
                </div>

                <div className="mt-6 space-y-6">
                  <button
                    type="button"
                    onClick={toggleAll}
                    aria-pressed={allSelected}
                    className="flex items-center gap-3 rounded-lg border border-white/15 bg-white/5 px-4 py-3 text-left transition hover:bg-white/10"
                  >
                    <span
                      className={`flex h-5 w-5 items-center justify-center rounded-full border ${allSelected ? "border-cyan-300 bg-cyan-300 text-slate-950" : "border-white/25 bg-transparent"}`}
                    >
                      {allSelected && <Check className="h-3.5 w-3.5" />}
                    </span>
                    <span className="text-sm font-medium text-white">{allSelected ? "Deselect all parts" : "Select all parts"}</span>
                  </button>

                  {PART_GROUPS.map((group) => (
                    <div key={group.id}>
                      <h3 className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-white/45">{group.label}</h3>
                      <div className="grid grid-cols-2 gap-3">
                        {PARTS.filter((part) => part.group === group.id).map((part) => {
                          const active = !removedParts.includes(part.id)
                          return (
                            <button
                              key={part.id}
                              type="button"
                              aria-pressed={active}
                              title={part.description}
                              onClick={() => toggleRemovedPart(part.id)}
                              className={`flex flex-col gap-2 rounded-lg border p-2 text-left text-xs transition-colors duration-300 ${
                                active
                                  ? "border-cyan-400/40 bg-cyan-400/10 shadow-[0_0_40px_rgba(34,211,238,0.12)]"
                                  : "border-white/10 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.05]"
                              }`}
                            >
                              <div className="flex items-center gap-2">
                                <span
                                  className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border ${active ? "border-cyan-300 bg-cyan-300 text-slate-950" : "border-white/25 bg-transparent text-transparent"}`}
                                >
                                  <Check className="h-2.5 w-2.5" />
                                </span>
                                <span className="text-xs font-medium">{part.name}</span>
                              </div>
                              <span className="text-xs text-emerald-300">{formatMoney(part.price)}</span>
                            </button>
                          )
                        })}
                      </div>
                    </div>
                  ))}

                  <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-4">
                    <div className="mb-3 flex items-center gap-2 text-white/80">
                      <Package className="h-4 w-4 text-emerald-300" />
                      <span className="text-sm font-medium">Storage options</span>
                      <span className="text-xs text-white/45">(optional)</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      {STORAGE_OPTIONS.map((option) => {
                        const active = selectedStorage === option.id
                        return (
                          <button
                            key={option.id}
                            type="button"
                            aria-pressed={active}
                            onClick={() => setSelectedStorage(active ? null : option.id)}
                            className={`rounded-lg border px-2 py-2 text-left text-xs transition ${
                              active
                                ? "border-cyan-400/40 bg-cyan-400/10 text-cyan-100"
                                : "border-white/10 bg-white/[0.03] text-white/70 hover:border-white/20 hover:bg-white/[0.05]"
                            }`}
                          >
                            <span className="block text-xs font-medium leading-tight">{option.name}</span>
                            <span className="mt-1 block text-xs text-emerald-300">{formatMoney(option.price)}</span>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            <div className="space-y-6 lg:sticky lg:top-24">
              <HelmetScene />

              <Card className="border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm uppercase tracking-[0.25em] text-white/45">Order summary</p>
                    <h3 className="mt-2 text-2xl font-bold">Your build estimate</h3>
                  </div>
                  <Badge className="border-white/10 bg-white/10 text-white">
                    {activeParts.length}/{PARTS.length} parts
                  </Badge>
                </div>

                <div className="mt-6 space-y-3">
                  {activeParts.map((part) => (
                    <div key={part.id} className="flex items-center justify-between gap-4 text-sm text-white/75">
                      <span>{part.name}</span>
                      <span>{formatMoney(part.price)}</span>
                    </div>
                  ))}
                  {storage && (
                    <div className="flex items-center justify-between gap-4 text-sm text-white/75">
                      <span>{storage.name} Storage</span>
                      <span>{formatMoney(storage.price)}</span>
                    </div>
                  )}
                  {total === 0 && <p className="text-sm text-white/55">No parts selected yet.</p>}
                  <div className="border-t border-white/10 pt-4">
                    <div className="flex items-center justify-between text-lg font-semibold">
                      <span>Estimated total</span>
                      <span>{formatMoney(total)}</span>
                    </div>
                    <p className="mt-2 text-sm text-white/55">Enter your email to proceed with payment</p>
                  </div>
                </div>

                <div className="mt-4 space-y-3">
                  <label htmlFor="checkout-email" className="sr-only">
                    Email
                  </label>
                  <input
                    id="checkout-email"
                    type="email"
                    autoComplete="email"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    className="w-full rounded-lg border border-white/15 bg-white/5 px-4 py-2 text-white placeholder-white/40 transition focus:border-cyan-400 focus:outline-none"
                  />
                  <StripeCheckoutButton
                    email={email}
                    partIds={partIds}
                    storageId={selectedStorage}
                    disabled={total === 0}
                  />
                </div>

                <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                  <Button asChild variant="outline" className="border-white/15 bg-transparent text-white hover:bg-white/5 hover:text-white">
                    <Link href="/">Back to home</Link>
                  </Button>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
