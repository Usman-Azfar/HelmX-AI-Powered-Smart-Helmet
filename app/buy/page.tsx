import type { Metadata } from "next"
import { BuyPage } from "@/components/buy-page"

export const metadata: Metadata = {
  title: "Buy HelmX | Premium Smart Helmet Configurator",
  description:
    "Configure your HelmX smart helmet with a live 3D product preview, modular hardware options, and instant pricing estimates.",
}

export default function BuyRoute() {
  return <BuyPage />
}