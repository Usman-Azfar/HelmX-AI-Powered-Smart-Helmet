/**
 * File: header.tsx
 * Purpose: Fixed navigation header component with logo, navigation links, and status badge.
 *          Provides sticky header with backdrop blur effect and smooth hover animations,
 *          plus a slide-out menu on small screens.
 * Author: Hamza Ahmad
 */
import Image from "next/image"
import Link from "next/link"
import { Menu } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Sheet, SheetClose, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet"

const navLinks = [
  { label: "Features", href: "/#features" },
  { label: "Technology", href: "/#technology" },
  { label: "Buy HelmX", href: "/buy" },
  { label: "About", href: "/#why-helmx" },
  { label: "Contact", href: "/contact" },
  { label: "Download", href: "/#download" },
]

export function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-lg">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/#hero" className="flex items-center gap-2 transition-transform hover:scale-105">
          <div className="relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-lg bg-gradient-to-br from-primary to-accent transition-all hover:shadow-lg hover:shadow-primary/50">
            <Image
              src="/futuristic-motorcycle-helmet-icon-minimal.jpg"
              alt="HelmX Logo"
              width={36}
              height={36}
              priority
              className="h-full w-full object-cover"
            />
          </div>
          <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-xl font-bold text-transparent">
            HelmX
          </span>
        </Link>

        <nav className="hidden items-center gap-6 md:flex">
          {navLinks.map(({ label, href }) => (
            <Link
              key={href}
              href={href}
              className="relative text-sm text-muted-foreground transition-colors hover:text-foreground after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 after:bg-primary after:transition-all after:duration-300 hover:after:w-full"
            >
              {label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <Badge variant="outline" className="border-primary/50 bg-primary/10 text-primary">
            <span className="relative mr-2 flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-primary"></span>
            </span>
            Available Now
          </Badge>

          <Sheet>
            <SheetTrigger
              className="inline-flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-primary/10 hover:text-foreground md:hidden"
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </SheetTrigger>
            <SheetContent side="right" className="w-64">
              <SheetTitle className="px-4 pt-4">Menu</SheetTitle>
              <nav className="flex flex-col gap-1 px-2">
                {navLinks.map(({ label, href }) => (
                  <SheetClose asChild key={href}>
                    <Link
                      href={href}
                      className="rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-primary/10 hover:text-foreground"
                    >
                      {label}
                    </Link>
                  </SheetClose>
                ))}
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  )
}
