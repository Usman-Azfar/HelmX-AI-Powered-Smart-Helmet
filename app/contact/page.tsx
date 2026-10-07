/**
 * File: contact/page.tsx
 * Purpose: Contact us page with contact form and company information
 * Author: GitHub Copilot
 */

import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { ContactForm } from "@/components/contact-form"
import DotField from "@/components/dot-field"
import { Mail, Phone, MapPin } from "lucide-react"

export const metadata = {
  title: "Contact Us | HelmX",
  description: "Get in touch with the HelmX team. We'd love to hear from you!",
}

export default function ContactPage() {
  return (
    <main className="min-h-screen flex flex-col">
      <Header />
      <div className="relative flex-1">
        <div className="absolute inset-0 pointer-events-none">
        <DotField
          dotRadius={1.5}
          dotSpacing={14}
          bulgeStrength={67}
          glowRadius={160}
          sparkle={false}
          waveAmplitude={0}
          cursorRadius={500}
          cursorForce={0.1}
          bulgeOnly
          gradientFrom="rgba(168, 85, 247, 0.8)"
          gradientTo="rgba(180, 151, 207, 0.6)"
          glowColor="#120F17"
        />
        </div>
        <div className="relative z-10 pt-24 pb-16">
        <div className="container mx-auto px-4">
          {/* Page Header */}
          <div className="mb-16 text-center">
            <h1 className="bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-4xl font-bold text-transparent sm:text-5xl">
              Get in Touch
            </h1>
            <p className="mt-4 text-lg text-muted-foreground">
              Have questions or feedback? We&apos;d love to hear from you. Send us a message and we&apos;ll respond as soon as possible.
            </p>
          </div>

          {/* Main Content */}
          <div className="grid gap-12 lg:grid-cols-3">
            {/* Contact Form */}
            <div className="lg:col-span-2">
              <div className="rounded-lg border border-border/50 bg-background/50 p-8 backdrop-blur-sm">
                <ContactForm />
              </div>
            </div>

            {/* Contact Information */}
            <div className="space-y-8">
              <div>
                <h2 className="text-xl font-semibold">Contact Information</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  Reach out to us through any of these channels
                </p>
              </div>

              {/* Email */}
              <div className="space-y-2 rounded-lg border border-border/50 bg-background/50 p-4 backdrop-blur-sm">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Mail className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Email</p>
                    <a
                      href="mailto:bcsf22m512@pucit.edu.pk"
                      className="text-foreground hover:text-primary transition-colors"
                    >
                      bcsf22m512@pucit.edu.pk
                    </a>
                  </div>
                </div>
              </div>

              {/* Phone */}
              <div className="space-y-2 rounded-lg border border-border/50 bg-background/50 p-4 backdrop-blur-sm">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Phone className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Phone</p>
                    <a
                      href="tel:+923000000000"
                      className="text-foreground hover:text-primary transition-colors"
                    >
                      0300 0000000
                    </a>
                  </div>
                </div>
              </div>

              {/* Location */}
              <div className="space-y-2 rounded-lg border border-border/50 bg-background/50 p-4 backdrop-blur-sm">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <MapPin className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Location</p>
                    <p className="text-foreground">
                      PUCIT, University of the Punjab<br />
                      Lahore, Pakistan
                    </p>
                  </div>
                </div>
              </div>

              {/* Response Time */}
              <div className="rounded-lg border border-primary/50 bg-primary/5 p-4">
                <p className="text-sm text-foreground">
                  <span className="font-semibold">Response Time:</span> We typically respond within 24 hours during business days.
                </p>
              </div>
            </div>
          </div>
        </div>
        </div>
      </div>
      <Footer />
    </main>
  )
}
