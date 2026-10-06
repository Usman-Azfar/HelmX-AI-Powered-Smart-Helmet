import type { ReactNode } from "react"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"

export default function BuyLayout({ children }: { children: ReactNode }) {
  return (
    <main className="min-h-screen">
      <Header />
      {children}
      <Footer />
    </main>
  )
}