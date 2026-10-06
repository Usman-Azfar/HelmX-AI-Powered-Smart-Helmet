/**
 * File: why-helmx.tsx
 * Purpose: "Why HelmX" section explaining product benefits with scroll-triggered animations.
 *          Implements progressive content reveal with staggered delays for list items.
 * Author: Hamza Ahmad
 */
"use client"

import Image from "next/image"
import { CheckCircle2 } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import SoftAurora from "@/components/soft-aurora"

const benefits = [
  "Proactive accident prevention",
  "Instant crash response",
  "Smarter, safer navigation",
  "Fully integrated ride analytics",
  "Modern AI-driven riding experience",
  "Cost-effective all-in-one solution",
]

export function WhyHelmX() {
  const [isVisible, setIsVisible] = useState(false)
  const sectionRef = useRef<HTMLElement | null>(null)

  /**
   * Observes the about section for scroll-triggered animation.
   * Triggers visibility state when section enters viewport threshold.
   */
  useEffect(() => {
    const section = sectionRef.current
    if (!section) {
      setIsVisible(true)
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setIsVisible(true)
          observer.disconnect()
        }
      },
      { threshold: 0.2 },
    )

    observer.observe(section)
    return () => observer.disconnect()
  }, [])

  return (
    <section ref={sectionRef} id="why-helmx" className="relative overflow-hidden py-20 md:py-32">
      <div className="pointer-events-none absolute inset-0 opacity-40">
        <SoftAurora
          speed={0.6}
          scale={1.5}
          brightness={1}
          color1="#f7f7f7"
          color2="#e100ff"
          noiseFrequency={2.5}
          noiseAmplitude={1}
          bandHeight={0.5}
          bandSpread={1}
          octaveDecay={0.1}
          layerOffset={0}
          colorSpeed={1}
          enableMouseInteraction
          mouseInfluence={0.25}
        />
      </div>
      <div className="container mx-auto px-4">
        <div className="mx-auto grid max-w-6xl gap-12 md:grid-cols-2 md:items-center">
          <div
            className={`relative z-10 transition-all duration-700 ${isVisible ? "translate-x-0 opacity-100" : "-translate-x-8 opacity-0"}`}
          >
            <h2 className="mb-6 text-balance text-4xl font-bold md:text-5xl">Why HelmX?</h2>
            <p className="mb-8 text-pretty text-lg leading-relaxed text-muted-foreground">
              HelmX stands apart by bringing together seven essential safety and lifestyle features into one
              cost-effective helmet. Unlike existing devices that focus on a single capability, HelmX delivers a
              complete safety ecosystem.
            </p>
            <div className="space-y-3">
              {benefits.map((benefit, index) => (
                <div
                  key={index}
                  className={`flex items-start gap-3 transition-all duration-500 ${
                    isVisible ? "translate-x-0 opacity-100" : "-translate-x-4 opacity-0"
                  } hover:translate-x-2`}
                  style={{ transitionDelay: `${(index + 1) * 100}ms` }}
                >
                  <CheckCircle2 className="mt-1 h-5 w-5 shrink-0 text-primary transition-transform hover:scale-125" />
                  <span className="text-foreground">{benefit}</span>
                </div>
              ))}
            </div>
            <div
              className={`mt-10 rounded-lg border border-primary/20 bg-primary/5 p-6 transition-all duration-700 delay-700 ${
                isVisible ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"
              } hover:border-primary/40 hover:bg-primary/10`}
            >
              <p className="text-balance text-lg font-semibold text-foreground">
                Our mission is simple: To reduce motorcycle fatalities and make every ride smarter, safer, and more
                enjoyable.
              </p>
            </div>
          </div>

          <div
            className={`relative z-10 transition-all duration-700 delay-300 ${isVisible ? "translate-x-0 opacity-100" : "translate-x-8 opacity-0"}`}
          >
            <div className="relative aspect-square overflow-hidden rounded-2xl border border-border/40 bg-muted">
              <Image
                src="/futuristic-ai-smart-motorcycle-helmet-with-hud-dis.jpg"
                alt="HelmX Smart Helmet"
                fill
                sizes="(min-width: 768px) 50vw, 100vw"
                className="object-cover"
              />
            </div>
            <div
              className={`absolute -bottom-6 -right-6 rounded-lg border border-border/40 bg-card p-4 shadow-lg transition-all duration-700 delay-1000 hover:scale-110 hover:shadow-xl ${
                isVisible ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="flex -space-x-2">
                  {[...Array(4)].map((_, i) => (
                    <div
                      key={i}
                      className="h-8 w-8 rounded-full border-2 border-background bg-gradient-to-br from-primary to-accent transition-transform hover:scale-125 hover:z-10"
                    />
                  ))}
                </div>
                <div>
                  <p className="text-sm font-semibold">Project Team</p>
                  <p className="text-xs text-muted-foreground">4 BS CS Students</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
