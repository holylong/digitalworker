import { cmd } from "./cmd"
import { withNetworkOptions, resolveNetworkOptions } from "../network"
import { WorkerRoutes } from "../../worker/server"
import { Log } from "../../util/log"

const log = Log.create({ service: "worker-cmd" })

export const WorkerCommand = cmd({
  command: "worker",
  describe: "Start a worker node that can receive commands from master",
  builder: (yargs) =>
    withNetworkOptions(yargs).option("directory", {
      type: "string",
      describe: "Working directory for the worker",
      default: process.cwd(),
    }),
  handler: async (args) => {
    const opts = await resolveNetworkOptions(args)
    const directory = args.directory ?? process.cwd()

    const app = await WorkerRoutes()
    const server = Bun.serve({
      hostname: opts.hostname,
      port: opts.port || 4097,
      fetch: app.fetch,
    })

    log.info("worker started", {
      url: `http://${server.hostname}:${server.port}`,
      directory,
    })

    console.log(`Worker node listening on http://${server.hostname}:${server.port}`)
    console.log(`Working directory: ${directory}`)
    console.log("")
    console.log("Available endpoints:")
    console.log("  GET  /worker/status  - Get worker status and capabilities")
    console.log("  POST /worker/sync    - Sync files to worker")
    console.log("  POST /worker/exec    - Execute command on worker")
    console.log("")
    console.log("Press Ctrl+C to stop")

    // Keep running
    await new Promise(() => {})
    await server.stop()
  },
})