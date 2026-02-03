import { Hono } from "hono"
import { describeRoute, validator, resolver } from "hono-openapi"
import z from "zod"
import { Session } from "../../session"
import { SessionPrompt } from "../../session/prompt"
import { Command } from "../../command"
import { Provider } from "../../provider/provider"
import { Log } from "../../util/log"
import { errors } from "../error"

const log = Log.create({ service: "remote" })

// Store for WebSocket connections
const connections = new Map<string, WebSocket>()

// Schema for remote command execution
const RemoteCommandSchema = z.object({
  type: z.enum(["command", "prompt", "shell", "status"]),
  sessionID: z.string().optional(),
  command: z.string().optional(),
  message: z.string().optional(),
  arguments: z.string().optional(),
  agent: z.string().optional(),
  model: z.string().optional(),
  variant: z.string().optional(),
  directory: z.string().optional(),
  files: z
    .array(
      z.object({
        path: z.string(),
        content: z.string().optional(),
      }),
    )
    .optional(),
})

// Schema for command response
const CommandResponseSchema = z.object({
  success: z.boolean(),
  data: z.any().optional(),
  error: z.string().optional(),
  sessionID: z.string().optional(),
  messageID: z.string().optional(),
})

export const RemoteRoutes = () => {
  const app = new Hono()

  // Health check endpoint
  app.get(
    "/health",
    describeRoute({
      summary: "Remote API health check",
      description: "Check if the remote API is running",
      operationId: "remote.health",
      responses: {
        200: {
          description: "API is healthy",
          content: {
            "application/json": {
              schema: resolver(
                z.object({
                  status: z.string(),
                  version: z.string(),
                }),
              ),
            },
          },
        },
      },
    }),
    async (c) => {
      return c.json({
        status: "ok",
        version: "1.0.0",
      })
    },
  )

  // Execute command endpoint
  app.post(
    "/execute",
    describeRoute({
      summary: "Execute remote command",
      description: "Execute a command, prompt, or shell command remotely",
      operationId: "remote.execute",
      responses: {
        200: {
          description: "Command executed",
          content: {
            "application/json": {
              schema: resolver(CommandResponseSchema),
            },
          },
        },
        ...errors(400, 404, 500),
      },
    }),
    validator("json", RemoteCommandSchema),
    async (c) => {
      try {
        const input = c.req.valid("json")
        log.info("execute", { type: input.type, command: input.command })

        let sessionID = input.sessionID
        let result: any = {}

        switch (input.type) {
          case "command": {
            if (!input.command) {
              return c.json({ success: false, error: "Command is required for type 'command'" }, 400)
            }

            // Check if command exists
            const cmdExists = await Command.get(input.command)
            if (!cmdExists) {
              return c.json({ success: false, error: `Command "${input.command}" not found` }, 404)
            }

            // Create session if not provided
            if (!sessionID) {
              const session = await Session.create({
                title: `Remote: ${input.command}`,
              })
              sessionID = session.id
            }

            const msg = await SessionPrompt.command({
              sessionID,
              command: input.command,
              arguments: input.arguments || "",
              agent: input.agent,
              model: input.model ? Provider.parseModel(input.model) : undefined,
              variant: input.variant,
            })

            result = {
              success: true,
              sessionID,
              messageID: msg.info.id,
              data: msg,
            }
            break
          }

          case "prompt": {
            if (!input.message) {
              return c.json({ success: false, error: "Message is required for type 'prompt'" }, 400)
            }

            // Create session if not provided
            if (!sessionID) {
              const session = await Session.create({
                title: input.message.slice(0, 50),
              })
              sessionID = session.id
            }

            const parts: any[] = [{ type: "text", text: input.message }]

            // Add file attachments if provided
            if (input.files) {
              for (const file of input.files) {
                parts.push({
                  type: "file",
                  url: `file://${file.path}`,
                  filename: file.path.split("/").pop(),
                  mime: "text/plain",
                })
              }
            }

            const msg = await SessionPrompt.prompt({
              sessionID,
              parts,
              agent: input.agent,
              model: input.model ? Provider.parseModel(input.model) : undefined,
              variant: input.variant,
            })

            result = {
              success: true,
              sessionID,
              messageID: msg.info.id,
              data: msg,
            }
            break
          }

          case "shell": {
            if (!input.command) {
              return c.json({ success: false, error: "Command is required for type 'shell'" }, 400)
            }

            // Create session if not provided
            if (!sessionID) {
              const session = await Session.create({
                title: `Shell: ${input.command.slice(0, 50)}`,
              })
              sessionID = session.id
            }

            const msg = await SessionPrompt.shell({
              sessionID,
              command: input.command,
              agent: input.agent,
              model: input.model ? Provider.parseModel(input.model) : undefined,
            })

            result = {
              success: true,
              sessionID,
              messageID: msg.info.id,
              data: msg,
            }
            break
          }

          case "status": {
            if (!sessionID) {
              const sessions: any[] = []
              for await (const s of Session.list()) {
                sessions.push({
                  id: s.id,
                  title: s.title,
                  directory: s.directory,
                  time: s.time,
                })
              }
              result = {
                success: true,
                data: { sessions, count: sessions.length },
              }
            } else {
              const session = await Session.get(sessionID)
              const messages = await Session.messages({ sessionID })
              result = {
                success: true,
                sessionID,
                data: {
                  session,
                  messageCount: messages.length,
                },
              }
            }
            break
          }

          default:
            return c.json({ success: false, error: `Unknown type: ${input.type}` }, 400)
        }

        return c.json(result)
      } catch (error) {
        log.error("execute error", { error })
        return c.json(
          {
            success: false,
            error: error instanceof Error ? error.message : String(error),
          },
          500,
        )
      }
    },
  )

  // List available commands
  app.get(
    "/commands",
    describeRoute({
      summary: "List available commands",
      description: "Get a list of all available opencode commands",
      operationId: "remote.commands",
      responses: {
        200: {
          description: "List of commands",
          content: {
            "application/json": {
              schema: resolver(
                z.object({
                  success: z.boolean(),
                  data: z.array(
                    z.object({
                      name: z.string(),
                      description: z.string(),
                    }),
                  ),
                }),
              ),
            },
          },
        },
      },
    }),
    async (c) => {
      try {
        const commands = await Command.list()
        return c.json({
          success: true,
          data: commands.map((cmd) => ({
            name: cmd.name,
            description: cmd.description || "",
          })),
        })
      } catch (error) {
        log.error("commands error", { error })
        return c.json(
          {
            success: false,
            error: error instanceof Error ? error.message : String(error),
          },
          500,
        )
      }
    },
  )

  return app
}
