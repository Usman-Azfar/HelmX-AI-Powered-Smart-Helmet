/**
 * File: footer.tsx
 * Purpose: Footer component with navigation links, company information, and hover animations.
 *          Implements interactive link hover effects with underline animations.
 * Author: Hamza Ahmad
 */
import Image from "next/image"
import Link from "next/link"

const productLinks = [
  { label: "Features", href: "/#features" },
  { label: "Technology", href: "/#technology" },
  { label: "Download App", href: "/#download" },
]

const aboutLinks = [
  { label: "Why HelmX", href: "/#why-helmx" },
  { label: "Buy HelmX", href: "/buy" },
  { label: "Contact", href: "/contact" },
]

function FooterLink({ label, href }: { label: string; href: string }) {
  return (
    <Link href={href} className="group relative inline-block transition-all duration-300 hover:translate-x-1 hover:text-primary">
      {label}
      <span className="absolute -bottom-1 left-0 h-0.5 w-0 bg-primary transition-all duration-300 group-hover:w-full" />
    </Link>
  )
}

export function Footer() {
  return (
    <footer className="border-t border-border/40 bg-card py-12">
      <div className="container mx-auto px-4">
        <div className="grid gap-8 md:grid-cols-4">
          <div className="md:col-span-2">
            <div className="mb-4 flex items-center gap-2 transition-transform hover:scale-105">
              <div className="relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-lg bg-gradient-to-br from-primary to-accent shadow-lg">
                <Image
                  src="/futuristic-motorcycle-helmet-icon-minimal.jpg"
                  alt="HelmX Logo"
                  width={36}
                  height={36}
                  className="h-full w-full object-cover"
                />
              </div>
              <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-xl font-bold text-transparent">
                HelmX
              </span>
            </div>
            <p className="mb-4 max-w-md text-sm leading-relaxed text-muted-foreground">
              AI-powered smart helmet designed to make riding safer, smarter, and more connected. A collaboration of BS
              CS students from the University of the Punjab.
            </p>
            <p className="text-sm text-muted-foreground">© {new Date().getFullYear()} HelmX. The future of safe riding starts now.</p>
          </div>

          <div>
            <h3 className="mb-4 text-sm font-semibold">Product</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              {productLinks.map(({ label, href }) => (
                <li key={label}>
                  <FooterLink label={label} href={href} />
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="mb-4 text-sm font-semibold">About</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              {aboutLinks.map(({ label, href }) => (
                <li key={label}>
                  <FooterLink label={label} href={href} />
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-8 border-t border-border/40 pt-8 text-center text-sm text-muted-foreground">
          <p className="transition-all hover:text-primary hover:scale-105">Built with AI, designed for safety. Powered by innovation.</p>
        </div>
      </div>
    </footer>
  )
}
