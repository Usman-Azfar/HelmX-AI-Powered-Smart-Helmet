/**
 * File: layout.tsx
 * Purpose: Root layout component that wraps all pages with global styles, fonts, and metadata.
 *          Configures Next.js metadata and provides the base HTML structure for the application.
 * Author: Hamza Ahmad
 */
import type React from "react"
import type { Metadata, Viewport } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { Toaster } from "@/components/ui/toaster"
import { SITE_URL } from "@/lib/site"
import "./globals.css"

const geistSans = Geist({ subsets: ["latin"], variable: "--font-geist-sans" })
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono" })

const description =
  "HelmX is an AI-powered smart helmet designed to make riding safer, smarter, and more connected through crash detection, drowsiness alerts, and smart navigation."

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "HelmX – AI Powered Smart Helmet | Redefining Motorcycle Safety",
    template: "%s | HelmX",
  },
  description,
  applicationName: "HelmX",
  keywords: ["smart helmet", "motorcycle safety", "crash detection", "drowsiness detection", "Raspberry Pi", "HelmX"],
  openGraph: {
    type: "website",
    siteName: "HelmX",
    url: "/",
    title: "HelmX – AI Powered Smart Helmet",
    description,
    images: [{ url: "/futuristic-ai-smart-motorcycle-helmet-with-hud-dis.jpg", width: 1024, height: 1024, alt: "HelmX smart helmet" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "HelmX – AI Powered Smart Helmet",
    description,
    images: ["/futuristic-ai-smart-motorcycle-helmet-with-hud-dis.jpg"],
  },
}

export const viewport: Viewport = {
  themeColor: "#0a0a0a",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`dark ${geistSans.variable} ${geistMono.variable}`}>
      <body className="font-sans antialiased">
        {children}
        <Toaster />
        <Analytics />
      </body>
    </html>
  )
}
