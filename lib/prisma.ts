import { PrismaClient } from "@prisma/client"
import { PrismaPg } from "@prisma/adapter-pg"
import { Pool } from "pg"

// Reuse one client/pool per process. In development this also survives hot reloads,
// which would otherwise open a new connection pool on every file change.
const globalForPrisma = globalThis as unknown as {
  prisma?: PrismaClient
  pgPool?: Pool
}

// POSTGRES_URL is the direct connection string Vercel's Postgres integrations provide.
const connectionString = process.env.DATABASE_URL || process.env.POSTGRES_URL

const pgPool = globalForPrisma.pgPool ?? new Pool({ connectionString })

export const prisma = globalForPrisma.prisma ?? new PrismaClient({ adapter: new PrismaPg(pgPool) })

globalForPrisma.pgPool = pgPool
globalForPrisma.prisma = prisma
