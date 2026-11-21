import { neon } from "@neondatabase/serverless";
import { drizzle } from "drizzle-orm/neon-http";
import * as schema from "./schema";

const url = process.env.DATABASE_URL;
if (!url) {
  // Next collects route handlers at build time; we only need the URL at runtime,
  // so surface a clear message rather than crashing the build.
  console.warn("DATABASE_URL is not set — web will fail at runtime.");
}

// `sql` for raw tagged-template queries; `db` for Drizzle query builder.
export const sql = neon(url ?? "postgres://invalid");
export const db = drizzle(sql, { schema });

export { schema };
