/**
 * File: app-download.tsx
 * Purpose: App download section with animated content reveal and staggered feature list animations.
 *          Uses IntersectionObserver for scroll-triggered visibility and progressive content animation.
 * Author: Hamza Ahmad
 */
"use client"

import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Download, Smartphone, Star, Users, TrendingUp } from "lucide-react"
import { useEffect, useState } from "react"

export function AppDownload() {
  const [isVisible, setIsVisible] = useState(false)

  /**
   * Observes the download section for scroll-triggered animation.
   * Triggers visibility state when section enters viewport.
   */
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true)
          }
        })
      },
      { threshold: 0.2 },
    )

    const section = document.getElementById("download")
    if (section) observer.observe(section)

    return () => observer.disconnect()
  }, [])

  return (
    <section id="download" className="py-20 md:py-32">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-6xl overflow-hidden rounded-2xl border border-border/40 bg-gradient-to-br from-primary/10 via-accent/5 to-background shadow-2xl">
          <div className="grid gap-8 p-8 md:grid-cols-2 md:items-center md:p-12">
            <div
              className={`transition-all duration-700 ${isVisible ? "translate-x-0 opacity-100" : "-translate-x-8 opacity-0"}`}
            >
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-sm text-primary transition-all hover:scale-105 hover:shadow-lg hover:shadow-primary/20">
                <Smartphone className="h-4 w-4 animate-pulse" />
                Coming Soon
              </div>

              <h2 className="mb-4 text-balance text-4xl font-bold md:text-5xl">
                Download Our{" "}
                <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                  Mobile App
                </span>
              </h2>

              <p className="mb-6 text-pretty text-lg leading-relaxed text-muted-foreground">
                Get the HelmX companion app to unlock the full potential of your smart helmet. Monitor your rides, view
                analytics, and manage all your safety features from your phone.
              </p>

              <div className="mb-8 space-y-3">
                {[
                  { icon: Star, text: "Real-time ride monitoring" },
                  { icon: TrendingUp, text: "Detailed analytics & insights" },
                  { icon: Users, text: "Emergency contact management" },
                ].map((feature, index) => (
                  <div
                    key={index}
                    className={`flex items-center gap-3 transition-all duration-500 ${
                      isVisible ? "translate-x-0 opacity-100" : "-translate-x-4 opacity-0"
                    } hover:translate-x-2`}
                    style={{ transitionDelay: `${(index + 2) * 100}ms` }}
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary transition-all hover:scale-110 hover:bg-primary hover:text-primary-foreground">
                      {feature.icon && <feature.icon className="h-4 w-4" />}
                    </div>
                    <span className="text-sm text-foreground">{feature.text}</span>
                  </div>
                ))}
              </div>

              <Button size="lg" disabled aria-disabled="true" className="bg-primary disabled:opacity-80">
                <Download className="mr-2 inline h-5 w-5" />
                Coming soon on Play Store
              </Button>
            </div>

            <div
              className={`relative flex items-center justify-center transition-all duration-700 delay-300 ${isVisible ? "translate-x-0 opacity-100" : "translate-x-8 opacity-0"}`}
            >
              <div className="relative">
                <Image
                  src="/smartphone-mockup-showing-helmet-app-dashboard.jpg"
                  alt="HelmX Mobile App"
                  width={1122}
                  height={1402}
                  sizes="400px"
                  className="relative h-[500px] w-auto rounded-3xl shadow-2xl"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
