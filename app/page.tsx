/**
 * File: page.tsx
 * Purpose: Main homepage component that renders all sections of the landing page.
 *          Composes header, hero, features, tech stack, why HelmX, app download, and footer sections.
 * Author: Hamza Ahmad
 */
import { Header } from "@/components/header"
import { Hero } from "@/components/hero"
import { Features } from "@/components/features"
import { TechStack } from "@/components/tech-stack"
import { WhyHelmX } from "@/components/why-helmx"
import { AppDownload } from "@/components/app-download"
import { Footer } from "@/components/footer"

export default function HomePage() {
  return (
    <main className="min-h-screen">
      <Header />
      <Hero />
      <Features />
      <TechStack />
      <WhyHelmX />
      <AppDownload />
      <Footer />
    </main>
  )
}
