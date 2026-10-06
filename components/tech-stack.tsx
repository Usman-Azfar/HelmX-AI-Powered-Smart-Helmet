/**
 * File: tech-stack.tsx
 * Purpose: Technology stack section displaying technologies used in HelmX with hover interactions.
 *          Implements IntersectionObserver for scroll animations and complex hover state management.
 * Author: Hamza Ahmad
 */
"use client"

import { Badge } from "@/components/ui/badge"
import { Cpu, Cloud, Smartphone, Zap } from "lucide-react"
import { useEffect, useRef, useState } from "react"

const technologies = [
  {
    category: "AI & Vision",
    items: ["TensorFlow Lite", "OpenCV", "CNN Models"],
    icon: Cpu,
    color: "from-purple-500 to-pink-500",
  },
  {
    category: "Backend",
    items: ["AWS IoT Core", "Node.js", "Twilio", "MongoDB"],
    icon: Cloud,
    color: "from-blue-500 to-cyan-500",
  },
  {
    category: "Frontend",
    items: ["React.js", "Kotlin Android App"],
    icon: Smartphone,
    color: "from-green-500 to-emerald-500",
  },
  {
    category: "Hardware",
    items: ["IMU Sensors", "Dual Cameras", "GPS", "Edge Processor"],
    icon: Zap,
    color: "from-orange-500 to-red-500",
  },
]

export function TechStack() {
  const [visibleCards, setVisibleCards] = useState<number[]>([])
  const [hoveredCard, setHoveredCard] = useState<number | null>(null)
  const cardRefs = useRef<(HTMLDivElement | null)[]>([])

  /**
   * Creates IntersectionObserver for each technology card with staggered animation delays.
   * Alternates animation direction (up/down) based on card index for visual variety.
   */
  useEffect(() => {
    const observers = cardRefs.current.map((card, index) => {
      if (!card) return null

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              setTimeout(() => {
                setVisibleCards((prev) => [...new Set([...prev, index])])
              }, index * 150)
            }
          })
        },
        { threshold: 0.2 },
      )

      observer.observe(card)
      return observer
    })

    return () => {
      observers.forEach((observer) => observer?.disconnect())
    }
  }, [])

  return (
    <section id="technology" className="relative py-20 md:py-32">
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute top-0 left-1/3 h-96 w-96 rounded-full bg-primary/10 blur-3xl animate-pulse-slow"></div>
        <div className="absolute bottom-0 right-1/3 h-96 w-96 rounded-full bg-accent/10 blur-3xl animate-pulse-slow"></div>
      </div>

      <div className="container mx-auto px-4">
        <div className="mb-16 text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-1.5 text-sm text-primary transition-all hover:scale-105 hover:shadow-lg hover:shadow-primary/20">
            <Zap className="h-3 w-3 animate-pulse" />
            Cutting-Edge Technologies
          </div>
          <h2 className="mb-4 text-balance text-4xl font-bold md:text-5xl">
            Powered by{" "}
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Industry Leaders
            </span>
          </h2>
          <p className="mx-auto max-w-2xl text-pretty text-lg leading-relaxed text-muted-foreground">
            Built with cutting-edge technologies and industry-leading platforms to ensure reliability and performance
          </p>
        </div>

        <div className="mx-auto grid max-w-5xl gap-8 md:grid-cols-2">
          {technologies.map((tech, index) => (
            <div
              key={index}
              ref={(el) => {
                cardRefs.current[index] = el
              }}
              onMouseEnter={() => setHoveredCard(index)}
              onMouseLeave={() => setHoveredCard(null)}
              className={`group relative overflow-hidden rounded-xl border border-border/40 bg-card p-8 transition-all duration-700 ${
                visibleCards.includes(index)
                  ? "translate-y-0 opacity-100"
                  : index % 2 === 0
                    ? "-translate-y-8 opacity-0"
                    : "translate-y-8 opacity-0"
              } ${hoveredCard === index ? "scale-105 border-primary/50 shadow-2xl shadow-primary/20" : ""}`}
            >
              <div
                className={`absolute inset-0 bg-gradient-to-br ${tech.color} opacity-0 transition-opacity duration-500 ${
                  hoveredCard === index ? "opacity-10" : ""
                }`}
              ></div>

              <div className="relative mb-6 flex items-center gap-4">
                <div
                  className={`inline-flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br ${tech.color} text-white shadow-lg transition-all duration-500 ${
                    hoveredCard === index ? "scale-110 rotate-12 shadow-2xl" : ""
                  }`}
                >
                  {tech.icon && <tech.icon className="h-7 w-7" />}
                </div>
                <h3 className="text-2xl font-bold transition-colors group-hover:text-primary">{tech.category}</h3>
              </div>

              <div className="relative flex flex-wrap gap-2">
                {tech.items.map((item, itemIndex) => (
                  <Badge
                    key={itemIndex}
                    variant="secondary"
                    className={`bg-muted text-foreground transition-all duration-500 hover:scale-110 hover:bg-primary hover:text-primary-foreground ${
                      hoveredCard === index ? "translate-y-0 opacity-100" : "translate-y-2 opacity-70"
                    }`}
                    style={{ transitionDelay: `${itemIndex * 50}ms` }}
                  >
                    {item}
                  </Badge>
                ))}
              </div>

              <div className="relative mt-6 h-1 w-full overflow-hidden rounded-full bg-border">
                <div
                  className={`h-full bg-gradient-to-r ${tech.color} transition-all duration-1000 ${
                    hoveredCard === index ? "w-full" : "w-0"
                  }`}
                ></div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Technologies", value: "15+" },
            { label: "Cloud Services", value: "AWS" },
            { label: "AI Models", value: "3+" },
            { label: "Platforms", value: "Multi" },
          ].map((stat, index) => (
            <div
              key={index}
              className={`group rounded-xl border border-border/40 bg-card/50 p-6 text-center backdrop-blur-sm transition-all duration-700 hover:scale-105 hover:border-primary/50 hover:bg-card hover:shadow-lg ${
                visibleCards.length > 0 ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"
              }`}
              style={{ transitionDelay: `${(index + 4) * 100}ms` }}
            >
              <div className="mb-2 text-3xl font-bold text-primary transition-transform group-hover:scale-110">
                {stat.value}
              </div>
              <div className="text-sm text-muted-foreground">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
