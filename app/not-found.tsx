import Link from "next/link"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { Button } from "@/components/ui/button"

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col">
      <Header />
      <section className="container mx-auto flex flex-1 flex-col items-center justify-center px-4 py-32 text-center">
        <p className="mb-2 text-sm font-semibold uppercase tracking-widest text-primary">404</p>
        <h1 className="mb-4 text-4xl font-bold md:text-5xl">This road doesn&apos;t exist</h1>
        <p className="mb-8 max-w-md text-muted-foreground">
          The page you&apos;re looking for has moved or never existed. Head back home or configure your own HelmX.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Button asChild>
            <Link href="/">Back to home</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/buy">Build your helmet</Link>
          </Button>
        </div>
      </section>
      <Footer />
    </main>
  )
}
