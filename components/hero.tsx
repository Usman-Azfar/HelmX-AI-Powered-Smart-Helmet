/**
 * File: hero.tsx
 * Purpose: Hero section component with animated background effects and fade-in animations.
 *          Implements mouse tracking for parallax-like background blur effects.
 * Author: Hamza Ahmad
 */
"use client"

import { Button } from "@/components/ui/button"
import { ArrowRight, Sparkles } from "lucide-react"
import Link from "next/link"
import { useEffect, useRef } from "react"
import LineWaves from "@/components/line-waves"

export function Hero() {
  const parallaxRef = useRef<HTMLDivElement>(null)

  /**
   * Sets up mouse tracking for parallax background effects (the fade-in is pure CSS, see .animate-fade-up).
   * Writes the normalized mouse offset to CSS variables (throttled to one update per frame)
   * instead of React state, so mouse movement never re-renders the hero.
   */
  useEffect(() => {
    let frame = 0
    const handleMouseMove = (e: MouseEvent) => {
      if (frame) return
      frame = requestAnimationFrame(() => {
        frame = 0
        const el = parallaxRef.current
        if (!el) return
        el.style.setProperty("--mx", `${(e.clientX / window.innerWidth - 0.5) * 20}px`)
        el.style.setProperty("--my", `${(e.clientY / window.innerHeight - 0.5) * 20}px`)
      })
    }

    window.addEventListener("mousemove", handleMouseMove, { passive: true })
    return () => {
      window.removeEventListener("mousemove", handleMouseMove)
      cancelAnimationFrame(frame)
    }
  }, [])

  return (
    <section
      id="hero"
      className="relative mt-16 flex min-h-[calc(100svh-4rem)] items-center overflow-hidden py-10 md:py-12"
    >
      <div className="pointer-events-none absolute inset-0 opacity-40">
        <LineWaves
          speed={0.3}
          innerLineCount={32}
          outerLineCount={36}
          warpIntensity={1}
          rotation={-45}
          edgeFadeWidth={0}
          colorCycleSpeed={1}
          brightness={0.2}
          color1="#ffffff"
          color2="#ffffff"
          color3="#ffffff"
          enableMouseInteraction
          mouseInfluence={2}
        />
      </div>
      {/* Darkens the line waves behind the copy so the subtitle stays readable */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_55%_45%_at_center,rgba(0,0,0,0.85)_0%,rgba(0,0,0,0.5)_55%,transparent_100%)]" />
      <div ref={parallaxRef} className="absolute inset-0 -z-10">
        <div className="absolute top-1/4 left-1/4 h-96 w-96 translate-x-[var(--mx,0px)] translate-y-[var(--my,0px)] rounded-full bg-primary/20 blur-3xl transition-transform duration-1000"></div>
        <div className="absolute bottom-1/4 right-1/4 h-96 w-96 translate-x-[calc(var(--mx,0px)*-1)] translate-y-[calc(var(--my,0px)*-1)] rounded-full bg-accent/20 blur-3xl transition-transform duration-1000"></div>
      </div>

      <div className="container relative z-10 mx-auto px-4">
        <div className="mx-auto max-w-4xl text-center">
          <div
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-1.5 text-sm text-primary transition-all duration-700 hover:scale-105 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/20 animate-fade-up"
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-primary"></span>
            </span>
            <Sparkles className="h-3 w-3 animate-pulse" />
            AI Powered Smart Helmet
          </div>

          <h1
            className="mb-6 text-balance text-5xl font-bold tracking-tight [animation-delay:100ms] md:text-7xl animate-fade-up"
          >
            Redefining Motorcycle Safety Through{" "}
            <span className="relative inline-block bg-gradient-to-r from-primary via-accent to-primary bg-[length:200%_auto] bg-clip-text text-transparent animate-shimmer">
              Artificial Intelligence
            </span>
          </h1>

          <p
            className="mb-10 text-pretty text-lg leading-relaxed text-muted-foreground [animation-delay:200ms] md:text-xl animate-fade-up"
          >
            HelmX combines AI, IoT sensors, and cloud computing to create a fully integrated safety ecosystem. Making
            every ride smarter, safer, and more connected.
          </p>

          <div
            className="flex flex-col items-center justify-center gap-4 [animation-delay:300ms] sm:flex-row animate-fade-up"
          >
            <Button
              asChild
              size="lg"
              className="group relative overflow-hidden bg-primary transition-all hover:scale-105 hover:bg-primary/90 hover:shadow-2xl hover:shadow-primary/50"
            >
              <Link href="/buy">
                <span className="relative z-10">Build Your Helmet</span>
                <ArrowRight className="relative z-10 ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                <div className="absolute inset-0 -z-0 bg-gradient-to-r from-transparent via-white/20 to-transparent translate-x-[-100%] transition-transform duration-1000 group-hover:translate-x-[100%]"></div>
              </Link>
            </Button>
            <Button
              asChild
              size="lg"
              variant="outline"
              className="group bg-transparent transition-all hover:scale-105 hover:border-primary hover:bg-primary/5"
            >
              <a href="#features">Explore Features</a>
            </Button>
          </div>

          <div
            className="mt-16 grid grid-cols-2 md:flex md:flex-row items-center justify-center gap-4 md:gap-8 text-sm text-muted-foreground [animation-delay:500ms] animate-fade-up"
          >
            <div className="group flex flex-col items-center gap-1 transition-all hover:scale-110 hover:text-primary rounded-lg border border-border/40 bg-card/50 p-4">
              <span className="text-2xl font-bold text-primary transition-colors group-hover:text-primary">98.5%</span>
              <span className="text-center">AI Accuracy</span>
            </div>
            <div className="group flex flex-col items-center gap-1 transition-all hover:scale-110 hover:text-primary rounded-lg border border-border/40 bg-card/50 p-4">
              <span className="text-2xl font-bold text-primary transition-colors group-hover:text-primary">
                {"<2s"}
              </span>
              <span className="text-center">Response Time</span>
            </div>
            <div className="group flex flex-col items-center gap-1 transition-all hover:scale-110 hover:text-primary rounded-lg border border-border/40 bg-card/50 p-4">
              <span className="text-2xl font-bold text-primary transition-colors group-hover:text-primary">95%</span>
              <span className="text-center">Crash Detection</span>
            </div>
            <div className="group flex flex-col items-center gap-1 transition-all hover:scale-110 hover:text-primary rounded-lg border border-border/40 bg-card/50 p-4">
              <span className="text-2xl font-bold text-primary transition-colors group-hover:text-primary">24/7</span>
              <span className="text-center">Monitoring</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
