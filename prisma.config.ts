import "dotenv/config"
import { defineConfig } from "prisma/config"

export default defineConfig({
  schema: "prisma/schema.prisma",
  datasource: {
    // POSTGRES_URL is what Vercel's Postgres integrations provide.
    url: process.env.DATABASE_URL || process.env.POSTGRES_URL || "",
  },
})