import { sqliteTable, text, integer, index } from "drizzle-orm/sqlite-core"
import { Timestamps } from "@/storage/schema.sql"

export const WorkerNodeTable = sqliteTable(
  "worker_node",
  {
    id: text().primaryKey(),
    name: text().notNull(),
    url: text().notNull(),
    platform: text().notNull(), // "linux" | "windows" | "darwin"
    arch: text().notNull(), // "x64" | "arm64" | etc
    work_directory: text().notNull(), // remote working directory
    status: text().notNull().default("offline"), // "online" | "offline" | "busy"
    last_ping: integer(),
    capabilities: text({ mode: "json" }).$type<string[]>(), // ["go", "rust", "node", "python", etc]
    password: text(), // optional auth password
    ...Timestamps,
  },
  (table) => [index("worker_node_status_idx").on(table.status)],
)

export const SyncSessionTable = sqliteTable(
  "sync_session",
  {
    id: text().primaryKey(),
    worker_id: text()
      .notNull()
      .references(() => WorkerNodeTable.id, { onDelete: "cascade" }),
    directory: text().notNull(), // local directory being synced
    remote_directory: text().notNull(), // remote working directory
    status: text().notNull().default("active"), // "active" | "paused" | "stopped"
    last_sync: integer(),
    files_synced: integer().default(0),
    ...Timestamps,
  },
  (table) => [index("sync_session_worker_idx").on(table.worker_id)],
)