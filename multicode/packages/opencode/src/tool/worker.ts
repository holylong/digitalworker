import z from "zod"
import { Tool } from "./tool"
import { WorkerRegistry } from "@/worker/registry"
import { WorkerSync } from "@/worker/sync"
import { Instance } from "@/project/instance"
import { Log } from "@/util/log"

const log = Log.create({ service: "worker-tool" })

export const WorkerTool = Tool.define("worker", async () => {
  return {
    description: `Execute commands on remote worker nodes for cross-platform compilation and testing.

This tool allows you to:
1. List available worker nodes with their platforms and capabilities
2. Sync files from the current project to a remote worker
3. Execute commands (like compile, test, run) on remote workers
4. Get results back including stdout, stderr, and exit codes

Use this when you need to:
- Compile code for a different platform (e.g., Windows .exe from Linux)
- Test code on a different operating system
- Run commands in a different environment

Current project directory: ${Instance.directory}`,

    parameters: z.object({
      action: z.enum(["list", "sync", "exec", "compile-run"]).describe("Action to perform"),
      workerId: z.string().optional().describe("Worker node ID (required for sync/exec/compile-run)"),
      files: z
        .array(
          z.object({
            path: z.string().describe("Relative file path"),
            content: z.string().optional().describe("File content (base64 for binary)"),
            encoding: z.enum(["utf-8", "base64"]).optional().default("utf-8"),
          }),
        )
        .optional()
        .describe("Files to sync (for sync action)"),
      command: z.string().optional().describe("Command to execute (for exec action)"),
      args: z.array(z.string()).optional().describe("Command arguments"),
      cwd: z.string().optional().describe("Working directory on worker"),
      compileCommand: z.string().optional().describe("Compile command (for compile-run action)"),
      runCommand: z.string().optional().describe("Run command after compilation (for compile-run action)"),
      timeout: z.number().optional().default(60000).describe("Timeout in milliseconds"),
    }),

    async execute(params, ctx) {
      const {
        action,
        workerId,
        files,
        command,
        args,
        cwd,
        compileCommand,
        runCommand,
        timeout = 60000,
      } = params

      switch (action) {
        case "list": {
          const workers = await WorkerRegistry.list()

          if (workers.length === 0) {
            return {
              title: "No workers configured",
              metadata: { workers: [], count: 0 },
              output: `No worker nodes configured.

To add a worker node, use the CLI:
  opencode node add --name <name> --url <url> --directory <dir>

Example:
  opencode node add --name windows --url http://192.168.1.100:4097 --directory C:\\workspace

Then start the worker on the remote machine:
  opencode worker --port 4097`,
            }
          }

          const lines = workers.map((w) => {
            const status = w.status === "online" ? "online" : "offline"
            return `- ${w.name} (${w.id})
  Platform: ${w.platform}/${w.arch}
  URL: ${w.url}
  Directory: ${w.workDirectory}
  Status: ${status}
  Capabilities: ${w.capabilities.join(", ") || "none detected"}`
          })

          return {
            title: `${workers.length} worker(s) available`,
            metadata: { workers, count: workers.length },
            output: `Available worker nodes:\n\n${lines.join("\n\n")}`,
          }
        }

        case "sync": {
          if (!workerId) {
            return {
              title: "Error: workerId required",
              metadata: { error: "workerId required" },
              output: "Error: workerId is required for sync action. Use 'list' to see available workers.",
            }
          }

          const worker = await WorkerRegistry.get(workerId)
          if (!worker) {
            return {
              title: `Error: worker ${workerId} not found`,
              metadata: { error: "worker not found", workerId },
              output: `Error: Worker node ${workerId} not found. Use action='list' to see available workers.`,
            }
          }

          // If no files specified, sync the entire project directory
          if (!files || files.length === 0) {
            ctx.metadata({ title: `Syncing project to ${worker.name}...` })
            const result = await WorkerSync.syncDirectory(workerId, Instance.directory, undefined, {
              exclude: ["node_modules", ".git", "dist", "build", "*.log", ".opencode"],
            })

            return {
              title: result.success
                ? `Synced ${result.syncedCount} files to ${worker.name}`
                : `Sync failed to ${worker.name}`,
              metadata: { ...result, workerId },
              output: result.success
                ? `Successfully synced ${result.syncedCount} files to ${worker.name} (${worker.platform}/${worker.arch})\nRemote directory: ${worker.workDirectory}`
                : `Sync failed:\n${result.errors.join("\n")}`,
            }
          }

          // Sync specific files
          ctx.metadata({ title: `Syncing ${files.length} file(s) to ${worker.name}...` })
          const result = await WorkerSync.syncFiles({
            workerId,
            files: files.map((f) => ({
              path: f.path,
              content: f.content,
              encoding: f.encoding ?? "utf-8",
              mode: "create" as const,
            })),
          })

          return {
            title: result.success
              ? `Synced ${result.syncedCount} files to ${worker.name}`
              : `Sync failed to ${worker.name}`,
            metadata: { ...result, workerId },
            output: result.success
              ? `Successfully synced ${result.syncedCount} file(s) to ${worker.name}`
              : `Sync failed:\n${result.errors.join("\n")}`,
          }
        }

        case "exec": {
          if (!workerId) {
            return {
              title: "Error: workerId required",
              metadata: { error: "workerId required" },
              output: "Error: workerId is required for exec action. Use 'list' to see available workers.",
            }
          }

          if (!command) {
            return {
              title: "Error: command required",
              metadata: { error: "command required" },
              output: "Error: command is required for exec action.",
            }
          }

          const worker = await WorkerRegistry.get(workerId)
          if (!worker) {
            return {
              title: `Error: worker ${workerId} not found`,
              metadata: { error: "worker not found", workerId },
              output: `Error: Worker node ${workerId} not found. Use action='list' to see available workers.`,
            }
          }

          ctx.metadata({ title: `Running on ${worker.name}: ${command}` })
          log.info("executing on worker", { workerId, command, args })

          const result = await WorkerSync.execute({
            workerId,
            command,
            args,
            cwd: cwd ?? worker.workDirectory,
            timeout,
          })

          const output = [
            `Command: ${command}${args ? " " + args.join(" ") : ""}`,
            `Worker: ${worker.name} (${worker.platform}/${worker.arch})`,
            `Exit code: ${result.exitCode}`,
            `Duration: ${result.duration}ms`,
            "",
            result.stdout && "STDOUT:",
            result.stdout,
            result.stderr && "STDERR:",
            result.stderr,
          ]
            .filter(Boolean)
            .join("\n")

          return {
            title: result.success
              ? `Command succeeded on ${worker.name}`
              : `Command failed on ${worker.name}`,
            metadata: { ...result, workerId, command },
            output,
          }
        }

        case "compile-run": {
          if (!workerId) {
            return {
              title: "Error: workerId required",
              metadata: { error: "workerId required" },
              output: "Error: workerId is required for compile-run action. Use 'list' to see available workers.",
            }
          }

          if (!compileCommand) {
            return {
              title: "Error: compileCommand required",
              metadata: { error: "compileCommand required" },
              output: "Error: compileCommand is required for compile-run action.",
            }
          }

          const worker = await WorkerRegistry.get(workerId)
          if (!worker) {
            return {
              title: `Error: worker ${workerId} not found`,
              metadata: { error: "worker not found", workerId },
              output: `Error: Worker node ${workerId} not found. Use action='list' to see available workers.`,
            }
          }

          // First sync the project
          ctx.metadata({ title: `Syncing to ${worker.name}...` })
          log.info("syncing before compile", { workerId })

          const syncResult = await WorkerSync.syncDirectory(workerId, Instance.directory, undefined, {
            exclude: ["node_modules", ".git", "dist", "build", "*.log", ".opencode"],
          })

          if (!syncResult.success) {
            return {
              title: `Sync failed to ${worker.name}`,
              metadata: { ...syncResult, workerId },
              output: `Sync failed before compilation:\n${syncResult.errors.join("\n")}`,
            }
          }

          // Compile
          ctx.metadata({ title: `Compiling on ${worker.name}...` })
          log.info("compiling on worker", { workerId, compileCommand })

          const compileResult = await WorkerSync.execute({
            workerId,
            command: compileCommand,
            cwd: cwd ?? worker.workDirectory,
            timeout,
          })

          if (!compileResult.success) {
            const output = [
              `Compile command: ${compileCommand}`,
              `Worker: ${worker.name} (${worker.platform}/${worker.arch})`,
              `Exit code: ${compileResult.exitCode}`,
              "",
              "STDOUT:",
              compileResult.stdout,
              "",
              "STDERR:",
              compileResult.stderr,
            ].join("\n")

            return {
              title: `Compilation failed on ${worker.name}`,
              metadata: { compileResult, workerId },
              output,
            }
          }

          // If run command specified, run it
          if (runCommand) {
            ctx.metadata({ title: `Running on ${worker.name}...` })
            log.info("running on worker", { workerId, runCommand })

            const runResult = await WorkerSync.execute({
              workerId,
              command: runCommand,
              cwd: cwd ?? worker.workDirectory,
              timeout,
            })

            const output = [
              `Compile: ${compileCommand} - Success (${compileResult.duration}ms)`,
              `Run: ${runCommand}`,
              `Worker: ${worker.name} (${worker.platform}/${worker.arch})`,
              `Exit code: ${runResult.exitCode}`,
              `Duration: ${runResult.duration}ms`,
              "",
              runResult.stdout && "STDOUT:",
              runResult.stdout,
              runResult.stderr && "STDERR:",
              runResult.stderr,
            ]
              .filter(Boolean)
              .join("\n")

            return {
              title: runResult.success
                ? `Compiled and ran successfully on ${worker.name}`
                : `Compiled OK, run failed on ${worker.name}`,
              metadata: { compileResult, runResult, workerId },
              output,
            }
          }

          // Just compile
          const output = [
            `Compile: ${compileCommand}`,
            `Worker: ${worker.name} (${worker.platform}/${worker.arch})`,
            `Exit code: ${compileResult.exitCode}`,
            `Duration: ${compileResult.duration}ms`,
            "",
            compileResult.stdout && "STDOUT:",
            compileResult.stdout,
            compileResult.stderr && "STDERR:",
            compileResult.stderr,
          ]
            .filter(Boolean)
            .join("\n")

          return {
            title: `Compiled successfully on ${worker.name}`,
            metadata: { compileResult, workerId },
            output,
          }
        }

        default:
          return {
            title: `Unknown action: ${action}`,
            metadata: { error: "unknown action" },
            output: `Unknown action: ${action}. Available actions: list, sync, exec, compile-run`,
          }
      }
    },
  }
})