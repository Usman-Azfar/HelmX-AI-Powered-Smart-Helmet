/**
 * File: features.tsx
 * Purpose: Features section component displaying HelmX safety features with scroll-triggered animations.
 *          Uses IntersectionObserver API for progressive card reveal animations and staggered visibility effects.
 * Author: Hamza Ahmad
 */
'use client'

import * as React from 'react'
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Shield, Eye, Navigation, Camera, Mic, Music, Cloud, Zap, CheckCircle } from "lucide-react"
import { useEffect, useRef, useState } from "react"

const features = [
  {
    icon: Shield,
    title: "Crash Detection",
    description:
      "AI-powered accelerometers and gyroscopes detect crashes accurately. Automatically sends GPS location and alerts to emergency contacts through the cloud.",
    color: "from-red-500 to-orange-500",
    features: ["Real-time Detection", "GPS Tracking", "Emergency Alerts", "Cloud Sync"],
    stats: { value: "99.5%", label: "Accuracy" },
  },
  {
    icon: Eye,
    title: "Drowsiness Detection",
    description:
      "Computer vision monitors eye closure and head position in real time. Alerts the rider instantly through audio and visual signals when fatigue is detected.",
    color: "from-blue-500 to-cyan-500",
    features: ["Eye Tracking", "Head Position", "Audio Alerts", "Visual Warnings"],
    stats: { value: "<1s", label: "Response Time" },
  },
  {
    icon: Navigation,
    title: "Smart Navigation",
    description:
      "AI-enhanced routing with traffic avoidance, weather insights, and ride suggestions. Helps riders stay aware without distraction.",
    color: "from-green-500 to-emerald-500",
    features: ["Traffic Updates", "Weather Alerts", "Route Optimization", "Voice Guidance"],
    stats: { value: "360°", label: "Awareness" },
  },
  {
    icon: Camera,
    title: "Dual Cameras",
    description:
      "Front & rear cameras record rides continuously or capture images on demand. Perfect for evidence, vlogging, traffic monitoring, or situational awareness.",
    color: "from-purple-500 to-pink-500",
    features: ["1080p Recording", "Night Vision", "Loop Recording", "Image Capture"],
    stats: { value: "2x", label: "Cameras" },
  },
  {
    icon: Mic,
    title: "Voice Assistant",
    description:
      "Hands-free voice assistant for calls and navigation. Supports both online and offline commands with adaptive noise handling.",
    color: "from-yellow-500 to-orange-500",
    features: ["Voice Commands", "Call Handling", "Offline Mode", "Noise Handling"],
    stats: { value: "100%", label: "Hands-Free" },
  },
  {
    icon: Music,
    title: "Entertainment System",
    description:
      "Built-in speakers for music and media playback, controlled by voice so riders can enjoy their ride without taking their hands off the bars.",
    color: "from-pink-500 to-rose-500",
    features: ["Music Playback", "Media Control", "Built-in Speakers", "Voice-Controlled"],
    stats: { value: "2", label: "Speakers" },
  },
  {
    icon: Cloud,
    title: "Environmental Monitoring",
    description:
      "Real-time readings of air quality, temperature, humidity, allergens, and weather. Generates smart recommendations for safer and healthier rides.",
    color: "from-indigo-500 to-purple-500",
    features: ["Air Quality", "Temperature", "Humidity", "Weather Data"],
    stats: { value: "Real-time", label: "Monitoring" },
  },
]

const stats = [
  { value: "99%", label: "Uptime Reliability" },
  { value: "AI", label: "Powered Technology" },
  { value: "24/7", label: "Protection & Monitoring" },
  { value: "Real-Time", label: "Cloud Analytics" },
]

export function Features() {
  const [visibleCards, setVisibleCards] = useState<number[]>([])
  const [statsVisible, setStatsVisible] = useState(false)
  const cardRefs = useRef<(HTMLDivElement | null)[]>([])
  const statsRef = useRef<HTMLDivElement | null>(null)

  /**
   * Sets up IntersectionObserver instances for each feature card and stats section.
   * Implements staggered animation delays based on card index for progressive reveal effect.
   * Uses Set to prevent duplicate entries in visibleCards array.
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
              }, index * 100)
            }
          })
        },
        { threshold: 0.1 },
      )

      observer.observe(card)
      return observer
    })

    const statsObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setStatsVisible(true)
          }
        })
      },
      { threshold: 0.2 },
    )

    if (statsRef.current) {
      statsObserver.observe(statsRef.current)
    }

    return () => {
      observers.forEach((observer) => observer?.disconnect())
      statsObserver.disconnect()
    }
  }, [])

  return (
    <section id="features" className="relative py-20 md:py-32">
      <div className="absolute inset-0 -z-10 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px]"></div>

      <div className="container mx-auto px-4">
        <div className="mb-16 text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-1.5 text-sm text-primary">
            <Zap className="h-3 w-3" />
            Seven Essential Features
          </div>
          <h2 className="mb-4 text-balance text-4xl font-bold md:text-5xl">
            Next-Generation{" "}
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Safety Features
            </span>
          </h2>
          <p className="mx-auto max-w-2xl text-pretty text-lg leading-relaxed text-muted-foreground">
            Advanced AI and IoT technologies working together to create the most comprehensive motorcycle safety system
            ever designed
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => (
            <Card
              key={index}
              ref={(el) => {
                cardRefs.current[index] = el
              }}
              className={`group relative overflow-hidden border-border/40 bg-card p-6 transition-all duration-500 ${
                index === features.length - 1 && features.length % 3 === 1 ? "lg:col-start-2" : ""
              } ${
                index === features.length - 1 && features.length % 2 === 1 ? "sm:col-span-2 sm:mx-auto sm:w-[calc(50%-0.75rem)] lg:col-span-1 lg:w-auto" : ""
              } ${
                visibleCards.includes(index) ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
              } hover:border-primary/50 hover:shadow-2xl hover:shadow-primary/20 hover:-translate-y-2`}
            >
              <div className="pointer-events-none absolute inset-0 -z-10 opacity-0 transition-opacity duration-500 group-hover:opacity-100">
                <div className={`h-full w-full bg-gradient-to-br ${feature.color} opacity-5`}></div>
              </div>

              <div className="relative">
                <div className="mb-6 flex items-center justify-between">
                  <div
                    className={`inline-flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br ${feature.color} text-white shadow-lg transition-all duration-300 group-hover:scale-110 group-hover:shadow-2xl group-hover:shadow-primary/30`}
                  >
                    {feature.icon && <feature.icon className="h-7 w-7" />}
                  </div>
                  <Badge
                    variant="outline"
                    className="border-primary/50 bg-primary/10 text-primary transition-all duration-300 group-hover:scale-110 group-hover:border-primary"
                  >
                    <span className="font-bold">{feature.stats.value}</span>
                    <span className="ml-1 text-xs">{feature.stats.label}</span>
                  </Badge>
                </div>

                <h3 className="mb-3 text-2xl font-bold transition-colors group-hover:text-primary">{feature.title}</h3>
                <p className="mb-4 text-sm leading-relaxed text-muted-foreground">{feature.description}</p>

                <div className="mb-4 space-y-2">
                  {feature.features.map((item, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-2 text-xs transition-all duration-300 group-hover:translate-x-1"
                    >
                      <CheckCircle className="h-4 w-4 text-primary transition-all duration-300 group-hover:scale-125" />
                      <span className="text-muted-foreground">{item}</span>
                    </div>
                  ))}
                </div>

                <div className="relative mt-4 h-1 w-full overflow-hidden rounded-full bg-primary/10">
                  <div
                    className={`absolute inset-0 bg-gradient-to-r ${feature.color} transition-transform duration-700 group-hover:translate-x-0 -translate-x-full`}
                  ></div>
                </div>
              </div>
            </Card>
          ))}
        </div>

        <div ref={statsRef} className="mt-20">
          <h3 className="mb-8 text-center text-2xl font-bold md:text-3xl">Why HelmX Stands Out</h3>
          <div className="mx-auto grid max-w-4xl grid-cols-2 gap-4 md:flex md:flex-row md:justify-center md:gap-6">
            {stats.map((stat, index) => (
              <div
                key={index}
                className={`rounded-xl border border-border/40 bg-card/50 p-6 text-center transition-all duration-500 hover:border-primary/50 hover:bg-card/80 hover:shadow-lg ${
                  statsVisible ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"
                }`}
                style={{ transitionDelay: `${index * 100}ms` }}
              >
                <div className="text-2xl font-bold text-primary md:text-3xl">{stat.value}</div>
                <div className="mt-1 text-xs text-muted-foreground md:text-sm">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
