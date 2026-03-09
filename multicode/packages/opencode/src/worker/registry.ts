import { eq } from "drizzle-orm"
import { Database } from "@/storage/db"
import { WorkerNodeTable } from "./worker.sql"
import { WorkerNodeInfo, WorkerCreateInput, WorkerStatusResponse } from "./types"
import { Identifier } from "@/id/id"
import { Log } from "@/util/log"
import { NamedError } from "@opencode-ai/util/error"
import z from "zod"

const log = Log.create({ service: "worker" })

export const WorkerNodeError = NamedError.create(
  "WorkerNodeError",
  z.object({
    workerId: z.string(),
    message: z.string(),
  }),
)

export namespace WorkerRegistry {
  // List all worker nodes
  export async function list(): Promise<WorkerNodeInfo[]> {
    const rows = await Database.use((db) =>
      db.select().from(WorkerNodeTable).orderBy(WorkerNodeTable.time_created),
    )

    return rows.map((row) => ({
      id: row.id,
      name: row.name,
      url: row.url,
      platform: row.platform as WorkerNodeInfo["platform"],
      arch: row.arch as WorkerNodeInfo["arch"],
      workDirectory: row.work_directory,
      status: row.status as WorkerNodeInfo["status"],
      lastPing: row.last_ping,
      capabilities: row.capabilities ?? [],
    }))
  }

  // Get a specific worker node
  export async function get(id: string): Promise<WorkerNodeInfo | null> {
    const rows = await Database.use((db) =>
      db.select().from(WorkerNodeTable).where(eq(WorkerNodeTable.id, id)),
    )

    if (rows.length === 0) return null

    const row = rows[0]
    return {
      id: row.id,
      name: row.name,
      url: row.url,
      platform: row.platform as WorkerNodeInfo["platform"],
      arch: row.arch as WorkerNodeInfo["arch"],
      workDirectory: row.work_directory,
      status: row.status as WorkerNodeInfo["status"],
      lastPing: row.last_ping,
      capabilities: row.capabilities ?? [],
    }
  }

  // Add a new worker node
  export async function add(input: WorkerCreateInput): Promise<WorkerNodeInfo> {
    const id = Identifier.generate("worker")
    const now = Date.now()

    // Try to connect and get status
    let status: WorkerNodeInfo["status"] = "offline"
    let platform: WorkerNodeInfo["platform"] = "unknown"
    let arch: WorkerNodeInfo["arch"] = "unknown"
    let capabilities: string[] = []

    try {
      const statusResponse = await pingWorker(input.url, input.password)
      status = "online"
      platform = statusResponse.platform
      arch = statusResponse.arch
      capabilities = statusResponse.capabilities
    } catch (e) {
      log.warn("failed to ping worker on add", {
        url: input.url,
        error: e instanceof Error ? e.message : String(e),
      })
    }

    await Database.use((db) =>
      db.insert(WorkerNodeTable).values({
        id,
        name: input.name,
        url: input.url,
        platform,
        arch,
        work_directory: input.workDirectory,
        status,
        last_ping: status === "online" ? now : null,
        capabilities,
        password: input.password,
        time_created: now,
        time_updated: now,
      }),
    )

    return {
      id,
      name: input.name,
      url: input.url,
      platform,
      arch,
      workDirectory: input.workDirectory,
      status,
      lastPing: status === "online" ? now : null,
      capabilities,
    }
  }

  // Remove a worker node
  export async function remove(id: string): Promise<boolean> {
    const result = await Database.use((db) =>
      db.delete(WorkerNodeTable).where(eq(WorkerNodeTable.id, id)),
    )
    return result.changes > 0
  }

  // Update worker status
  export async function updateStatus(
    id: string,
    status: WorkerNodeInfo["status"],
  ): Promise<void> {
    const now = Date.now()
    await Database.use((db) =>
      db
        .update(WorkerNodeTable)
        .set({
          status,
          last_ping: status === "online" ? now : undefined,
          time_updated: now,
        })
        .where(eq(WorkerNodeTable.id, id)),
    )
  }

  // Test connection to a worker
  export async function test(id: string): Promise<WorkerStatusResponse> {
    const worker = await get(id)
    if (!worker) {
      throw new WorkerNodeError({ workerId: id, message: "Worker not found" })
    }

    const response = await pingWorker(worker.url, undefined)
    await updateStatus(id, "online")
    return response
  }

  // Ping worker endpoint
  export async function pingWorker(
    url: string,
    password?: string,
  ): Promise<WorkerStatusResponse> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    }
    if (password) {
      headers["Authorization"] = `Bearer ${password}`
    }

    const response = await fetch(`${url}/worker/status`, {
      method: "GET",
      headers,
      signal: AbortSignal.timeout(10000),
    })

    if (!response.ok) {
      throw new Error(`Worker returned ${response.status}`)
    }

    const data = await response.json()
    return WorkerStatusResponse.parse(data)
  }

  // Update worker info from remote
  export async function refresh(id: string): Promise<WorkerNodeInfo> {
    const worker = await get(id)
    if (!worker) {
      throw new WorkerNodeError({ workerId: id, message: "Worker not found" })
    }

    const status = await pingWorker(worker.url, undefined)
    const now = Date.now()

    await Database.use((db) =>
      db
        .update(WorkerNodeTable)
        .set({
          platform: status.platform,
          arch: status.arch,
          capabilities: status.capabilities,
          status: "online",
          last_ping: now,
          time_updated: now,
        })
        .where(eq(WorkerNodeTable.id, id)),
    )

    return {
      ...worker,
      platform: status.platform,
      arch: status.arch,
      capabilities: status.capabilities,
      status: "online",
      lastPing: now,
    }
  }
}