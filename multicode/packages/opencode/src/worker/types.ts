import z from "zod"
import { Identifier } from "@/id/id"

// Worker node info
export const WorkerNodeInfo = z.object({
  id: Identifier.schema("worker"),
  name: z.string(),
  url: z.string(),
  platform: z.enum(["linux", "windows", "darwin", "unknown"]),
  arch: z.enum(["x64", "arm64", "ia32", "unknown"]),
  workDirectory: z.string(),
  status: z.enum(["online", "offline", "busy"]),
  lastPing: z.number().nullable(),
  capabilities: z.array(z.string()),
})
export type WorkerNodeInfo = z.infer<typeof WorkerNodeInfo>

// Create worker input
export const WorkerCreateInput = z.object({
  name: z.string().min(1).max(100),
  url: z.string().url(),
  workDirectory: z.string().min(1),
  password: z.string().optional(),
})
export type WorkerCreateInput = z.infer<typeof WorkerCreateInput>

// File sync input
export const FileSyncInput = z.object({
  path: z.string(),
  content: z.string().optional(), // base64 encoded
  encoding: z.enum(["utf-8", "base64"]).default("utf-8"),
  mode: z.enum(["create", "update", "delete"]).default("create"),
})
export type FileSyncInput = z.infer<typeof FileSyncInput>

// Batch file sync input
export const BatchSyncInput = z.object({
  workerId: z.string(),
  files: z.array(FileSyncInput),
  directory: z.string().optional(), // optional subdirectory
})
export type BatchSyncInput = z.infer<typeof BatchSyncInput>

// Remote execution input
export const RemoteExecInput = z.object({
  workerId: z.string(),
  command: z.string(),
  args: z.array(z.string()).optional(),
  cwd: z.string().optional(),
  env: z.record(z.string(), z.string()).optional(),
  timeout: z.number().optional().default(60000),
})
export type RemoteExecInput = z.infer<typeof RemoteExecInput>

// Remote execution result
export const RemoteExecResult = z.object({
  success: z.boolean(),
  exitCode: z.number(),
  stdout: z.string(),
  stderr: z.string(),
  duration: z.number(), // milliseconds
})
export type RemoteExecResult = z.infer<typeof RemoteExecResult>

// Worker status response from remote worker
export const WorkerStatusResponse = z.object({
  platform: z.enum(["linux", "windows", "darwin", "unknown"]),
  arch: z.enum(["x64", "arm64", "ia32", "unknown"]),
  hostname: z.string(),
  workDirectory: z.string(),
  capabilities: z.array(z.string()),
  version: z.string(),
})
export type WorkerStatusResponse = z.infer<typeof WorkerStatusResponse>

// Sync session info
export const SyncSessionInfo = z.object({
  id: Identifier.schema("sync"),
  workerId: z.string(),
  directory: z.string(),
  remoteDirectory: z.string(),
  status: z.enum(["active", "paused", "stopped"]),
  lastSync: z.number().nullable(),
  filesSynced: z.number(),
})
export type SyncSessionInfo = z.infer<typeof SyncSessionInfo>