import { Log } from "@/util/log"
import { WorkerRegistry } from "./registry"
import { FileSyncInput, BatchSyncInput, RemoteExecInput, RemoteExecResult } from "./types"
import { File } from "@/file"
import { Instance } from "@/project/instance"
import path from "path"
import fs from "fs"

const log = Log.create({ service: "worker-sync" })

export namespace WorkerSync {
  // Sync a batch of files to a remote worker
  export async function syncFiles(input: BatchSyncInput): Promise<{
    success: boolean
    syncedCount: number
    errors: string[]
  }> {
    const worker = await WorkerRegistry.get(input.workerId)
    if (!worker) {
      return { success: false, syncedCount: 0, errors: ["Worker not found"] }
    }

    const errors: string[] = []
    let syncedCount = 0

    try {
      const response = await fetch(`${worker.url}/worker/sync`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(worker.password
            ? { Authorization: `Bearer ${worker.password}` }
            : {}),
        },
        body: JSON.stringify({
          directory: input.directory ?? worker.workDirectory,
          files: input.files.map((f) => ({
            path: f.path,
            content: f.content,
            encoding: f.encoding,
            mode: f.mode,
          })),
        }),
        signal: AbortSignal.timeout(30000),
      })

      if (!response.ok) {
        const text = await response.text()
        return {
          success: false,
          syncedCount: 0,
          errors: [`Sync failed: ${response.status} - ${text}`],
        }
      }

      const result = (await response.json()) as { synced: number; errors?: string[] }
      syncedCount = result.synced
      if (result.errors) {
        errors.push(...result.errors)
      }
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e)
      log.error("sync failed", { workerId: input.workerId, error: message })
      errors.push(message)
    }

    return { success: errors.length === 0, syncedCount, errors }
  }

  // Sync a local directory to remote worker
  export async function syncDirectory(
    workerId: string,
    localDirectory: string,
    remoteDirectory?: string,
    options?: {
      exclude?: string[]
      include?: string[]
    },
  ): Promise<{ success: boolean; syncedCount: number; errors: string[] }> {
    const worker = await WorkerRegistry.get(workerId)
    if (!worker) {
      return { success: false, syncedCount: 0, errors: ["Worker not found"] }
    }

    const files: FileSyncInput[] = []
    const exclude = options?.exclude ?? ["node_modules", ".git", "dist", "build", "*.log"]
    const include = options?.include

    // Walk directory and collect files
    const walkDir = (dir: string, baseDir: string) => {
      const entries = fs.readdirSync(dir, { withFileTypes: true })

      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name)
        const relativePath = path.relative(baseDir, fullPath)

        // Check exclude patterns
        if (exclude.some((pattern) => matchPattern(entry.name, pattern))) {
          continue
        }

        if (entry.isDirectory()) {
          walkDir(fullPath, baseDir)
        } else if (entry.isFile()) {
          // Check include patterns if specified
          if (include && !include.some((pattern) => matchPattern(entry.name, pattern))) {
            continue
          }

          try {
            const content = fs.readFileSync(fullPath, "utf-8")
            files.push({
              path: relativePath,
              content: Buffer.from(content).toString("base64"),
              encoding: "base64",
              mode: "create",
            })
          } catch (e) {
            log.warn("failed to read file", { path: fullPath, error: String(e) })
          }
        }
      }
    }

    try {
      walkDir(localDirectory, localDirectory)
    } catch (e) {
      return {
        success: false,
        syncedCount: 0,
        errors: [`Failed to read local directory: ${e instanceof Error ? e.message : String(e)}`],
      }
    }

    if (files.length === 0) {
      return { success: true, syncedCount: 0, errors: [] }
    }

    return syncFiles({
      workerId,
      files,
      directory: remoteDirectory ?? worker.workDirectory,
    })
  }

  // Execute a command on remote worker
  export async function execute(input: RemoteExecInput): Promise<RemoteExecResult> {
    const worker = await WorkerRegistry.get(input.workerId)
    if (!worker) {
      return {
        success: false,
        exitCode: -1,
        stdout: "",
        stderr: "Worker not found",
        duration: 0,
      }
    }

    const startTime = Date.now()

    try {
      const response = await fetch(`${worker.url}/worker/exec`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(worker.password
            ? { Authorization: `Bearer ${worker.password}` }
            : {}),
        },
        body: JSON.stringify({
          command: input.command,
          args: input.args ?? [],
          cwd: input.cwd ?? worker.workDirectory,
          env: input.env ?? {},
          timeout: input.timeout,
        }),
        signal: AbortSignal.timeout((input.timeout ?? 60000) + 5000),
      })

      const duration = Date.now() - startTime

      if (!response.ok) {
        const text = await response.text()
        return {
          success: false,
          exitCode: response.status,
          stdout: "",
          stderr: text,
          duration,
        }
      }

      const result = (await response.json()) as RemoteExecResult
      return { ...result, duration }
    } catch (e) {
      const duration = Date.now() - startTime
      const message = e instanceof Error ? e.message : String(e)
      log.error("exec failed", { workerId: input.workerId, error: message })
      return {
        success: false,
        exitCode: -1,
        stdout: "",
        stderr: message,
        duration,
      }
    }
  }

  // Convenience: compile and run on worker
  export async function compileAndRun(
    workerId: string,
    options: {
      compileCommand: string
      runCommand: string
      cwd?: string
    },
  ): Promise<{
    compile: RemoteExecResult
    run?: RemoteExecResult
  }> {
    const compileResult = await execute({
      workerId,
      command: options.compileCommand,
      cwd: options.cwd,
    })

    if (!compileResult.success) {
      return { compile: compileResult }
    }

    const runResult = await execute({
      workerId,
      command: options.runCommand,
      cwd: options.cwd,
    })

    return { compile: compileResult, run: runResult }
  }
}

// Simple pattern matching helper
function matchPattern(name: string, pattern: string): boolean {
  if (pattern.startsWith("*.")) {
    const ext = pattern.slice(1)
    return name.endsWith(ext)
  }
  if (pattern.endsWith(".*")) {
    const prefix = pattern.slice(0, -2)
    return name.startsWith(prefix)
  }
  if (pattern.includes("*")) {
    const regex = new RegExp("^" + pattern.replace(/\*/g, ".*") + "$")
    return regex.test(name)
  }
  return name === pattern
}