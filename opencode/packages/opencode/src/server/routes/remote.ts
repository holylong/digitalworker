import { Hono } from "hono"
import { describeRoute, validator, resolver } from "hono-openapi"
import z from "zod"
import { Session } from "../../session"
import { SessionPrompt } from "../../session/prompt"
import { Command } from "../../command"
import { Provider } from "../../provider/provider"
import { Log } from "../../util/log"
import { errors } from "../error"
import path from "path"
import { mkdirSync, existsSync } from "fs"

const log = Log.create({ service: "remote" })

// 默认工作目录配置
const DEFAULT_WORKSPACE_ROOT = process.env.OPENCODE_WORKSPACE_ROOT ||
                                path.join(process.env.HOME || process.env.HOMEPATH || '.', 'opencode-workspace')

// 项目名称生成器
function generateProjectName(message: string, type: 'command' | 'prompt' | 'shell'): string {
  // 移除特殊字符，只保留 ASCII 字母、数字和连字符
  // 将中文字符翻译或移除
  const cleaned = message
    .toLowerCase()
    // 移除所有非 ASCII 字母数字和空格
    .replace(/[^\x00-\x7F]+/g, ' ')
    // 替换特殊字符为空格
    .replace(/[^\w\s-]/gi, ' ')
    .replace(/\s+/g, '-')
    .trim()
    .substring(0, 50)

  if (!cleaned || cleaned === '-') {
    return `project-${Date.now()}`
  }

  // 根据消息内容智能命名
  const keywords = {
    'api': 'api',
    'rest': 'rest-api',
    'web': 'web-app',
    'blog': 'blog',
    'cli': 'cli-tool',
    'bot': 'bot',
    'scraper': 'scraper',
    'game': 'game',
    'plugin': 'plugin',
    'tool': 'tool',
  }

  // 检查关键词
  for (const [key, value] of Object.entries(keywords)) {
    if (message.toLowerCase().includes(key)) {
      return `${value}-${Date.now()}`
    }
  }

  // 使用清理后的名称
  return `${cleaned}-${Date.now()}`
}

// 确保工作目录存在
function ensureWorkspaceDir(dirPath: string): string {
  try {
    if (!existsSync(dirPath)) {
      mkdirSync(dirPath, { recursive: true })
      log.info("created workspace directory", { path: dirPath })
    }
    return dirPath
  } catch (error) {
    log.error("failed to create workspace directory", { path: dirPath, error })
    throw error
  }
}

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
  projectName: z.string().optional(),
  autoCreateProject: z.boolean().optional().default(false),
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
  workspace: z.string().optional(),
  projectDir: z.string().optional(),
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
                  workspace: z.string(),
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
        workspace: DEFAULT_WORKSPACE_ROOT,
      })
    },
  )

  // Get workspace info endpoint
  app.get(
    "/workspace",
    describeRoute({
      summary: "Get workspace information",
      description: "Get the default workspace directory and configuration",
      operationId: "remote.workspace",
      responses: {
        200: {
          description: "Workspace information",
          content: {
            "application/json": {
              schema: resolver(
                z.object({
                  workspaceRoot: z.string(),
                  exists: z.boolean(),
                }),
              ),
            },
          },
        },
      },
    }),
    async (c) => {
      const exists = existsSync(DEFAULT_WORKSPACE_ROOT)
      return c.json({
        workspaceRoot: DEFAULT_WORKSPACE_ROOT,
        exists,
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
        log.info("execute", { type: input.type, command: input.command, autoCreateProject: input.autoCreateProject })

        let sessionID = input.sessionID
        let result: any = {}
        let projectDir: string | undefined

        // 确定工作目录
        let workingDirectory = input.directory

        // 如果启用自动创建项目且没有指定目录
        if (input.autoCreateProject && !workingDirectory) {
          const projectName = input.projectName ||
                            generateProjectName(input.message || input.command || input.arguments || '', input.type)

          projectDir = path.join(DEFAULT_WORKSPACE_ROOT, projectName)
          workingDirectory = ensureWorkspaceDir(projectDir)

          log.info("auto-created project directory", { projectDir })
        }

        // 设置工作目录 header（用于后续请求）
        if (workingDirectory) {
          c.header("X-OpenCode-Directory", workingDirectory)
        }

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
                directory: workingDirectory,
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
              workspace: DEFAULT_WORKSPACE_ROOT,
              projectDir: projectDir || workingDirectory,
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
                directory: workingDirectory,
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
              workspace: DEFAULT_WORKSPACE_ROOT,
              projectDir: projectDir || workingDirectory,
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
                directory: workingDirectory,
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
              workspace: DEFAULT_WORKSPACE_ROOT,
              projectDir: projectDir || workingDirectory,
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
                workspace: DEFAULT_WORKSPACE_ROOT,
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
                workspace: DEFAULT_WORKSPACE_ROOT,
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
