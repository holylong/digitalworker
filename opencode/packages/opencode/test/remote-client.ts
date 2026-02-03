#!/usr/bin/env bun
/**
 * OpenCode Remote API Test Client
 *
 * This is a test client for the OpenCode Remote API.
 * It can be used to send commands and prompts to a running OpenCode remote server.
 */

interface RemoteCommandInput {
  type: "command" | "prompt" | "shell" | "status"
  sessionID?: string
  command?: string
  message?: string
  arguments?: string
  agent?: string
  model?: string
  variant?: string
  directory?: string
  files?: Array<{ path: string; content?: string }>
}

interface CommandResponse {
  success: boolean
  data?: any
  error?: string
  sessionID?: string
  messageID?: string
}

class OpenCodeRemoteClient {
  private baseUrl: string
  private username?: string
  private password?: string

  constructor(options: { baseUrl: string; username?: string; password?: string }) {
    this.baseUrl = options.baseUrl.replace(/\/$/, "")
    this.username = options.username
    this.password = options.password
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    }

    if (this.username && this.password) {
      const auth = Buffer.from(`${this.username}:${this.password}`).toString("base64")
      headers["Authorization"] = `Basic ${auth}`
    }

    return headers
  }

  /**
   * Check if the remote server is healthy
   */
  async healthCheck(): Promise<{ status: string; version: string }> {
    const response = await fetch(`${this.baseUrl}/remote/health`, {
      headers: this.getHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`)
    }
    return response.json()
  }

  /**
   * List all available commands
   */
  async listCommands(): Promise<Array<{ name: string; description: string }>> {
    const response = await fetch(`${this.baseUrl}/remote/commands`, {
      headers: this.getHeaders(),
    })
    if (!response.ok) {
      throw new Error(`List commands failed: ${response.status}`)
    }
    const result = await response.json()
    return result.data
  }

  /**
   * Execute a remote command
   */
  async execute(input: RemoteCommandInput): Promise<CommandResponse> {
    const response = await fetch(`${this.baseUrl}/remote/execute`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(input),
    })
    if (!response.ok) {
      throw new Error(`Execute failed: ${response.status} - ${await response.text()}`)
    }
    return response.json()
  }

  /**
   * Execute a command
   */
  async runCommand(options: {
    command: string
    arguments?: string
    sessionID?: string
    agent?: string
    model?: string
  }): Promise<CommandResponse> {
    return this.execute({
      type: "command",
      command: options.command,
      arguments: options.arguments,
      sessionID: options.sessionID,
      agent: options.agent,
      model: options.model,
    })
  }

  /**
   * Send a prompt
   */
  async sendPrompt(options: {
    message: string
    sessionID?: string
    agent?: string
    model?: string
    files?: Array<{ path: string; content?: string }>
  }): Promise<CommandResponse> {
    return this.execute({
      type: "prompt",
      message: options.message,
      sessionID: options.sessionID,
      agent: options.agent,
      model: options.model,
      files: options.files,
    })
  }

  /**
   * Run a shell command
   */
  async runShell(options: {
    command: string
    sessionID?: string
    agent?: string
    model?: string
  }): Promise<CommandResponse> {
    return this.execute({
      type: "shell",
      command: options.command,
      sessionID: options.sessionID,
      agent: options.agent,
      model: options.model,
    })
  }

  /**
   * Get status (sessions or session details)
   */
  async getStatus(sessionID?: string): Promise<CommandResponse> {
    return this.execute({
      type: "status",
      sessionID,
    })
  }
}

// CLI Interface
async function main() {
  const args = process.argv.slice(2)

  if (args.length === 0) {
    printUsage()
    process.exit(1)
  }

  const command = args[0]
  const baseUrl = process.env.OPENCODE_REMOTE_URL || "http://localhost:4096"
  const username = process.env.OPENCODE_REMOTE_USERNAME || "opencode"
  const password = process.env.OPENCODE_REMOTE_PASSWORD

  const client = new OpenCodeRemoteClient({ baseUrl, username, password })

  try {
    switch (command) {
      case "health":
      case "ping": {
        const health = await client.healthCheck()
        console.log(JSON.stringify(health, null, 2))
        break
      }

      case "list":
      case "commands": {
        const commands = await client.listCommands()
        console.log("\n📋 Available commands:")
        console.log("=" .repeat(50))
        commands.forEach((cmd) => {
          console.log(`  ${cmd.name.padEnd(20)} - ${cmd.description}`)
        })
        console.log()
        break
      }

      case "run": {
        const cmdName = args[1]
        if (!cmdName) {
          console.error("Error: Command name is required")
          console.log("Usage: remote-client run <command> [arguments]")
          process.exit(1)
        }
        const cmdArgs = args.slice(2).join(" ")
        const result = await client.runCommand({
          command: cmdName,
          arguments: cmdArgs || undefined,
        })
        printResult(result)
        break
      }

      case "prompt": {
        const message = args.slice(1).join(" ")
        if (!message) {
          console.error("Error: Message is required")
          console.log("Usage: remote-client prompt <message>")
          process.exit(1)
        }
        console.log(`\n📝 Sending prompt: ${message}`)
        const result = await client.sendPrompt({ message })
        printResult(result)
        break
      }

      case "shell": {
        const shellCmd = args.slice(1).join(" ")
        if (!shellCmd) {
          console.error("Error: Shell command is required")
          console.log("Usage: remote-client shell <command>")
          process.exit(1)
        }
        console.log(`\n🐚 Running shell: ${shellCmd}`)
        const result = await client.runShell({ command: shellCmd })
        printResult(result)
        break
      }

      case "status":
      case "info": {
        const sessionID = args[1]
        const result = await client.getStatus(sessionID)
        printResult(result)
        break
      }

      case "watch":
      case "events": {
        console.log(`\n📡 Connecting to event stream: ${baseUrl}/event`)
        console.log("Press Ctrl+C to stop\n")

        const headers: Record<string, string> = {}
        if (username && password) {
          const auth = Buffer.from(`${username}:${password}`).toString("base64")
          headers["Authorization"] = `Basic ${auth}`
        }

        const response = await fetch(`${baseUrl}/event`, { headers })
        if (!response.ok) {
          throw new Error(`Failed to connect: ${response.status}`)
        }

        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error("No response body")
        }

        const decoder = new TextDecoder()
        let buffer = ""

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split("\n")
          buffer = lines.pop() || ""

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6)
              try {
                const event = JSON.parse(data)
                console.log(`[${event.type}]`, JSON.stringify(event.properties || {}).slice(0, 200))
              } catch {
                console.log(line)
              }
            }
          }
        }
        break
      }

      default:
        console.error(`Unknown command: ${command}`)
        printUsage()
        process.exit(1)
    }
  } catch (error) {
    console.error(`Error: ${error instanceof Error ? error.message : String(error)}`)
    process.exit(1)
  }
}

function printUsage() {
  console.log(`
OpenCode Remote API Test Client
================================

Usage: remote-client <command> [arguments...]

Commands:
  health, ping           Check if the remote server is running
  list, commands         List all available commands
  run <cmd> [args]       Execute an opencode command
  prompt <message>       Send a prompt to the AI
  shell <command>        Run a shell command
  status, info [id]      Get status of all sessions or a specific session
  watch, events          Watch event stream (SSE)

Environment Variables:
  OPENCODE_REMOTE_URL    Remote server URL (default: http://localhost:4096)
  OPENCODE_REMOTE_USERNAME  Auth username (default: opencode)
  OPENCODE_REMOTE_PASSWORD  Auth password (default: none)

Examples:
  remote-client health
  remote-client list
  remote-client run commit "Fix bug in user login"
  remote-client prompt "Create a new REST API endpoint"
  remote-client shell "ls -la"
  remote-client status
  remote-client watch
`)
}

function printResult(result: CommandResponse) {
  console.log("\n" + "=".repeat(50))
  console.log(`${result.success ? "✅" : "❌"} ${result.success ? "Success" : "Failed"}`)
  console.log("=".repeat(50))

  if (result.sessionID) {
    console.log(`Session ID: ${result.sessionID}`)
  }
  if (result.messageID) {
    console.log(`Message ID: ${result.messageID}`)
  }
  if (result.error) {
    console.log(`Error: ${result.error}`)
  }
  if (result.data) {
    console.log("\nResponse:")
    console.log(JSON.stringify(result.data, null, 2))
  }
  console.log()
}

// Run if called directly
if (import.meta.main) {
  main()
}

export { OpenCodeRemoteClient, type RemoteCommandInput, type CommandResponse }
