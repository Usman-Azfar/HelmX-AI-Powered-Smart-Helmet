/**
 * File: logo.tsx
 * Purpose: Shared HelmX brand lockup (helmet mark + gradient wordmark) so the logo
 *          looks identical everywhere it appears.
 */
import Image from "next/image"
import { cn } from "@/lib/utils"

export function Logo({ className, priority = false }: { className?: string; priority?: boolean }) {
  return (
    <span className={cn("flex items-center gap-2", className)}>
      <Image src="/logo-mark.png" alt="HelmX Logo" width={40} height={40} priority={priority} className="h-10 w-10" />
      <span className="bg-gradient-to-r from-[#3F51B5] via-[#0288D1] to-[#448AFF] bg-clip-text text-xl font-bold text-transparent">
        HelmX
      </span>
    </span>
  )
}
