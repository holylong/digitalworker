import { cmd } from "./cmd"
import { withNetworkOptions, resolveNetworkOptions } from "../network"
import { Flag } from "../../flag/flag"
import { Server } from "../../server/server"
import { RemoteRoutes } from "../../server/routes/remote"

export const RemoteCommand = cmd({
  command: "remote",
  builder: (yargs) =>
    withNetworkOptions(yargs)
      .option("token", {
        type: "string",
        describe: "authentication token for remote connections",
      })
      .option("allow-origin", {
        type: "string",
        array: true,
        describe: "allowed CORS origins for remote connections",
        default: [] as string[],
      }),
  describe: "start a remote API server for executing commands over network",
  handler: async (args) => {
    if (!Flag.OPENCODE_SERVER_PASSWORD) {
      console.log("Warning: OPENCODE_SERVER_PASSWORD is not set; server is unsecured.")
      console.log("Set OPENCODE_SERVER_PASSWORD environment variable for security.")
    }

    const opts = await resolveNetworkOptions(args)
    const allowOrigins = Array.isArray(args["allow-origin"])
      ? args["allow-origin"]
      : args["allow-origin"]
        ? [args["allow-origin"]]
        : []

    // Merge CORS origins
    const cors = [...opts.cors, ...allowOrigins]

    console.log("\n🚀 OpenCode Remote API Server")
    console.log("=" .repeat(50))
    console.log(`📡 Starting remote API server...`)
    console.log(`🔒 Auth: ${Flag.OPENCODE_SERVER_PASSWORD ? "Enabled" : "Disabled (WARNING!)"}`)
    console.log(`🌐 CORS: ${cors.length > 0 ? cors.join(", ") : "Default origins"}`)

    const server = Server.listen({ ...opts, cors })

    console.log(`\n✅ Server ready!`)
    console.log(`   HTTP: http://${server.hostname}:${server.port}`)
    console.log(`   API Docs: http://${server.hostname}:${server.port}/doc`)
    console.log(`   Remote API: http://${server.hostname}:${server.port}/remote`)
    console.log("\n📋 Available endpoints:")
    console.log("   GET  /remote/health     - Health check")
    console.log("   POST /remote/execute    - Execute commands/prompts")
    console.log("   GET  /remote/commands   - List available commands")
    console.log("   GET  /event             - SSE event stream")
    console.log("\nPress Ctrl+C to stop the server\n")

    await new Promise(() => {})
    await server.stop()
  },
})
