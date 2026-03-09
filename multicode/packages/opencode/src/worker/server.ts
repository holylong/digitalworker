import { Hono } from "hono"
import { describeRoute, validator, resolver } from "hono-openapi"
import z from "zod"
import { lazy } from "@/util/lazy"
import os from "os"
import { $ } from "bun"
import { Log } from "@/util/log"

const log = Log.create({ service: "worker-server" })

// Detect available compilers/tools
async function detectCapabilities(): Promise<string[]> {
  const capabilities: string[] = []

  const tools = [
    { name: "go", test: "go version" },
    { name: "rust", test: "rustc --version" },
    { name: "node", test: "node --version" },
    { name: "python", test: "python --version" },
    { name: "python3", test: "python3 --version" },
    { name: "java", test: "java -version" },
    { name: "dotnet", test: "dotnet --version" },
    { name: "gcc", test: "gcc --version" },
    { name: "clang", test: "clang --version" },
    { name: "make", test: "make --version" },
    { name: "cmake", test: "cmake --version" },
    { name: "docker", test: "docker --version" },
    { name: "git", test: "git --version" },
    { name: "bun", test: "bun --version" },
  ]

  for (const tool of tools) {
    try {
      const result = $`${tool.test}`.quiet()
      const exitCode = await result.nothrow()
      if (exitCode.exitCode === 0) {
        capabilities.push(tool.name)
      }
    } catch {
      // Tool not available
    }
  }

  return capabilities
}

export const WorkerRoutes = lazy(async () => {
  const capabilities = await detectCapabilities()

  return new Hono()
    .get(
      "/status",
      describeRoute({
        summary: "Get worker status",
        description: "Returns the current status and capabilities of this worker node",
        operationId: "worker.status",
        responses: {
          200: {
            description: "Worker status",
            content: {
              "application/json": {
                schema: resolver(
                  z.object({
                    platform: z.enum(["linux", "windows", "darwin", "unknown"]),
                    arch: z.enum(["x64", "arm64", "ia32", "unknown"]),
                    hostname: z.string(),
                    workDirectory: z.string(),
                    capabilities: z.array(z.string()),
                    version: z.string(),
                  }),
                ),
              },
            },
          },
        },
      }),
      async (c) => {
        const platform = (() => {
          switch (process.platform) {
            case "linux":
              return "linux"
            case "win32":
              return "windows"
            case "darwin":
              return "darwin"
            default:
              return "unknown"
          }
        })()

        const arch = (() => {
          switch (process.arch) {
            case "x64":
              return "x64"
            case "arm64":
              return "arm64"
            case "ia32":
              return "ia32"
            default:
              return "unknown"
          }
        })()

        return c.json({
          platform,
          arch,
          hostname: os.hostname(),
          workDirectory: process.cwd(),
          capabilities,
          version: "1.0.0",
        })
      },
    )
    .post(
      "/sync",
      describeRoute({
        summary: "Sync files to worker",
        description: "Receive and write files to the worker's working directory",
        operationId: "worker.sync",
        responses: {
          200: {
            description: "Sync result",
            content: {
              "application/json": {
                schema: resolver(
                  z.object({
                    synced: z.number(),
                    errors: z.array(z.string()).optional(),
                  }),
                ),
              },
            },
          },
        },
      }),
      validator(
        "json",
        z.object({
          directory: z.string().optional(),
          files: z.array(
            z.object({
              path: z.string(),
              content: z.string().optional(),
              encoding: z.enum(["utf-8", "base64"]).optional(),
              mode: z.enum(["create", "update", "delete"]).optional(),
            }),
          ),
        }),
      ),
      async (c) => {
        const { directory, files } = c.req.valid("json")
        const baseDir = directory ?? process.cwd()
        const errors: string[] = []
        let synced = 0

        for (const file of files) {
          try {
            const filePath = `${baseDir}/${file.path}`

            if (file.mode === "delete") {
              await Bun.file(filePath).exists() && (await Bun.write(filePath, ""))
              const fs = await import("fs")
              fs.unlinkSync(filePath)
              synced++
              continue
            }

            // Ensure directory exists
            const dir = filePath.substring(0, filePath.lastIndexOf("/"))
            await $`mkdir -p ${dir}`.quiet()

            // Write file
            let content: string | Buffer = file.content ?? ""
            if (file.encoding === "base64" && file.content) {
              content = Buffer.from(file.content, "base64")
            }

            await Bun.write(filePath, content)
            synced++

            log.debug("synced file", { path: file.path })
          } catch (e) {
            const message = e instanceof Error ? e.message : String(e)
            errors.push(`${file.path}: ${message}`)
            log.error("failed to sync file", { path: file.path, error: message })
          }
        }

        return c.json({ synced, errors: errors.length > 0 ? errors : undefined })
      },
    )
    .post(
      "/exec",
      describeRoute({
        summary: "Execute command on worker",
        description: "Run a command on the worker and return the result",
        operationId: "worker.exec",
        responses: {
          200: {
            description: "Execution result",
            content: {
              "application/json": {
                schema: resolver(
                  z.object({
                    success: z.boolean(),
                    exitCode: z.number(),
                    stdout: z.string(),
                    stderr: z.string(),
                    duration: z.number(),
                  }),
                ),
              },
            },
          },
        },
      }),
      validator(
        "json",
        z.object({
          command: z.string(),
          args: z.array(z.string()).optional(),
          cwd: z.string().optional(),
          env: z.record(z.string(), z.string()).optional(),
          timeout: z.number().optional(),
        }),
      ),
      async (c) => {
        const { command, args, cwd, env, timeout } = c.req.valid("json")
        const startTime = Date.now()

        try {
          const fullCommand = args && args.length > 0 ? `${command} ${args.join(" ")}` : command

          const result = await $`${fullCommand}`
            .cwd(cwd ?? process.cwd())
            .env({ ...process.env, ...env })
            .timeout(timeout ?? 60000)
            .nothrow()

          const duration = Date.now() - startTime

          return c.json({
            success: result.exitCode === 0,
            exitCode: result.exitCode,
            stdout: result.stdout.toString(),
            stderr: result.stderr.toString(),
            duration,
          })
        } catch (e) {
          const duration = Date.now() - startTime
          const message = e instanceof Error ? e.message : String(e)

          return c.json({
            success: false,
            exitCode: -1,
            stdout: "",
            stderr: message,
            duration,
          })
        }
      },
    )
    .post(
      "/exec/stream",
      describeRoute({
        summary: "Execute command with streaming output",
        description: "Run a command and stream stdout/stderr back in real-time",
        operationId: "worker.exec.stream",
        responses: {
          200: {
            description: "Streaming result",
            content: {
              "application/json": {
                schema: resolver(z.object({})),
              },
            },
          },
        },
      }),
      validator(
        "json",
        z.object({
          command: z.string(),
          args: z.array(z.string()).optional(),
          cwd: z.string().optional(),
          env: z.record(z.string(), z.string()).optional(),
        }),
      ),
      async (c) => {
        // For now, use regular exec
        // TODO: Implement WebSocket streaming
        const { command, args, cwd, env } = c.req.valid("json")
        const startTime = Date.now()

        try {
          const fullCommand = args && args.length > 0 ? `${command} ${args.join(" ")}` : command

          const result = await $`${fullCommand}`
            .cwd(cwd ?? process.cwd())
            .env({ ...process.env, ...env })
            .timeout(120000)
            .nothrow()

          const duration = Date.now() - startTime

          return c.json({
            success: result.exitCode === 0,
            exitCode: result.exitCode,
            stdout: result.stdout.toString(),
            stderr: result.stderr.toString(),
            duration,
          })
        } catch (e) {
          const duration = Date.now() - startTime
          const message = e instanceof Error ? e.message : String(e)

          return c.json({
            success: false,
            exitCode: -1,
            stdout: "",
            stderr: message,
            duration,
          })
        }
      },
    )
})