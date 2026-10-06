/**
 * File: layout.tsx
 * Purpose: Root layout component that wraps all pages with global styles, fonts, and metadata.
 *          Configures Next.js metadata and provides the base HTML structure for the application.
 * Author: Hamza Ahmad
 */
import type React from "react"
import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { Toaster } from "@/components/ui/toaster"
import "./globals.css"

const geistSans = Geist({ subsets: ["latin"], variable: "--font-geist-sans" })
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono" })

export const metadata: Metadata = {
  title: "HelmX – AI Powered Smart Helmet | Redefining Motorcycle Safety",
  description:
    "HelmX is an AI-powered smart helmet designed to make riding safer, smarter, and more connected through crash detection, drowsiness alerts, and smart navigation.",
  generator: "v0.app",
  icons: {
    icon: "/favicon.svg",
    apple: "/favicon.svg",
  },
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
