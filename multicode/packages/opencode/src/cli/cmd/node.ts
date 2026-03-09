import { cmd } from "./cmd"
import { WorkerRegistry } from "../../worker/registry"
import { WorkerSync } from "../../worker/sync"
import { UI } from "../ui"

export const NodeCommand = cmd({
  command: "node <action>",
  describe: "Manage remote worker nodes",
  builder: (yargs) =>
    yargs
      .positional("action", {
        type: "string",
        choices: ["list", "add", "remove", "test", "sync", "exec"],
        demandOption: true,
      })
      .option("name", {
        type: "string",
        describe: "Worker node name",
      })
      .option("url", {
        type: "string",
        describe: "Worker node URL (e.g., http://192.168.1.100:4097)",
      })
      .option("directory", {
        type: "string",
        describe: "Working directory on the worker",
      })
      .option("id", {
        type: "string",
        describe: "Worker node ID",
      })
      .option("command", {
        type: "string",
        describe: "Command to execute on worker",
      })
      .option("local-dir", {
        type: "string",
        describe: "Local directory to sync",
      })
      .option("remote-dir", {
        type: "string",
        describe: "Remote directory to sync to",
      })
      .option("password", {
        type: "string",
        describe: "Worker password (optional)",
      }),
  handler: async (args) => {
    const action = args.action as string

    switch (action) {
      case "list": {
        const workers = await WorkerRegistry.list()
        if (workers.length === 0) {
          console.log("No worker nodes configured.")
          console.log("")
          console.log("Add a worker node with: opencode node add --name <name> --url <url> --directory <dir>")
          return
        }

        console.log("Worker Nodes:")
        console.log("")
        for (const worker of workers) {
          const statusIcon =
            worker.status === "online" ? "\x1b[32m●\x1b[0m" : "\x1b[31m●\x1b[0m"
          console.log(`  ${statusIcon} ${worker.name} (${worker.id})`)
          console.log(`    URL: ${worker.url}`)
          console.log(`    Platform: ${worker.platform}/${worker.arch}`)
          console.log(`    Directory: ${worker.workDirectory}`)
          console.log(`    Capabilities: ${worker.capabilities.join(", ") || "none detected"}`)
          if (worker.lastPing) {
            const ago = Math.floor((Date.now() - worker.lastPing) / 1000)
            console.log(`    Last ping: ${ago}s ago`)
          }
          console.log("")
        }
        break
      }

      case "add": {
        if (!args.name || !args.url || !args.directory) {
          console.error("Error: --name, --url, and --directory are required")
          console.log("")
          console.log("Usage: opencode node add --name <name> --url <url> --directory <dir>")
          console.log("")
          console.log("Example:")
          console.log("  opencode node add --name windows-build --url http://192.168.1.100:4097 --directory C:\\workspace")
          return
        }

        console.log(`Adding worker node "${args.name}"...`)
        const worker = await WorkerRegistry.add({
          name: args.name,
          url: args.url,
          workDirectory: args.directory,
          password: args.password,
        })

        if (worker.status === "online") {
          console.log(`\x1b[32m✓\x1b[0m Worker node added successfully`)
          console.log(`  Platform: ${worker.platform}/${worker.arch}`)
          console.log(`  Capabilities: ${worker.capabilities.join(", ") || "none detected"}`)
        } else {
          console.log(`\x1b[33m!\x1b[0m Worker node added but connection failed`)
          console.log("  The worker may be offline. Start it with: opencode worker")
        }
        break
      }

      case "remove": {
        const id = args.id
        if (!id) {
          console.error("Error: --id is required")
          console.log("Usage: opencode node remove --id <worker-id>")
          console.log("List workers with: opencode node list")
          return
        }

        const removed = await WorkerRegistry.remove(id)
        if (removed) {
          console.log(`\x1b[32m✓\x1b[0m Worker node removed`)
        } else {
          console.error(`\x1b[31m✗\x1b[0m Worker node not found`)
        }
        break
      }

      case "test": {
        const id = args.id
        if (!id) {
          console.error("Error: --id is required")
          console.log("Usage: opencode node test --id <worker-id>")
          return
        }

        console.log(`Testing connection to worker ${id}...`)
        try {
          const status = await WorkerRegistry.test(id)
          console.log(`\x1b[32m✓\x1b[0m Connection successful`)
          console.log(`  Platform: ${status.platform}/${status.arch}`)
          console.log(`  Hostname: ${status.hostname}`)
          console.log(`  Capabilities: ${status.capabilities.join(", ") || "none detected"}`)
        } catch (e) {
          console.error(`\x1b[31m✗\x1b[0m Connection failed: ${e instanceof Error ? e.message : String(e)}`)
        }
        break
      }

      case "sync": {
        const id = args.id
        const localDir = args["local-dir"]
        const remoteDir = args["remote-dir"]

        if (!id || !localDir) {
          console.error("Error: --id and --local-dir are required")
          console.log("")
          console.log("Usage: opencode node sync --id <worker-id> --local-dir <dir> [--remote-dir <dir>]")
          console.log("")
          console.log("Example:")
          console.log("  opencode node sync --id wrk_xxx --local-dir ./myproject")
          return
        }

        console.log(`Syncing ${localDir} to worker ${id}...`)
        const result = await WorkerSync.syncDirectory(id, localDir, remoteDir)

        if (result.success) {
          console.log(`\x1b[32m✓\x1b[0m Synced ${result.syncedCount} files`)
        } else {
          console.error(`\x1b[31m✗\x1b[0m Sync failed`)
          for (const error of result.errors) {
            console.error(`  ${error}`)
          }
        }
        break
      }

      case "exec": {
        const id = args.id
        const command = args.command

        if (!id || !command) {
          console.error("Error: --id and --command are required")
          console.log("")
          console.log("Usage: opencode node exec --id <worker-id> --command <command>")
          console.log("")
          console.log("Example:")
          console.log("  opencode node exec --id wrk_xxx --command 'go build -o app main.go'")
          return
        }

        console.log(`Executing command on worker ${id}...`)
        console.log(`  $ ${command}`)
        console.log("")

        const result = await WorkerSync.execute({
          workerId: id,
          command,
          cwd: args.directory,
        })

        if (result.stdout) {
          console.log(result.stdout)
        }
        if (result.stderr) {
          console.error(result.stderr)
        }

        console.log("")
        if (result.success) {
          console.log(`\x1b[32m✓\x1b[0m Command completed (exit code: ${result.exitCode}, ${result.duration}ms)`)
        } else {
          console.error(`\x1b[31m✗\x1b[0m Command failed (exit code: ${result.exitCode})`)
        }
        break
      }

      default:
        console.error(`Unknown action: ${action}`)
        console.log("Available actions: list, add, remove, test, sync, exec")
    }
  },
})