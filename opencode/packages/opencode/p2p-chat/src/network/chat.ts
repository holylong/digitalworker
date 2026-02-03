import net from "node:net"
import { MessageSchema, type Message, CHAT_PORT } from "../types.js"

export interface ChatMessage {
  from: string
  content: string
  timestamp: number
}

export class ChatServer {
  private server: net.Server
  private port: number
  private onMessageCallback?: (message: ChatMessage) => void

  constructor(port: number = CHAT_PORT) {
    this.port = port
    this.server = net.createServer()
    this.setupServer()
  }

  private setupServer(): void {
    this.server.on("connection", (socket) => {
      console.log("📱 新的TCP连接:", socket.remoteAddress, socket.remotePort)

      let buffer = ""

      socket.on("data", (data) => {
        buffer += data.toString()

        // 处理完整的消息行
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          if (line.trim()) {
            this.handleMessage(line.trim())
          }
        }
      })

      socket.on("error", (error) => {
        console.error("TCP连接错误:", error.message)
      })

      socket.on("close", () => {
        console.log("📱 TCP连接关闭:", socket.remoteAddress, socket.remotePort)
      })
    })

    this.server.on("error", (error) => {
      console.error("服务器错误:", error.message)
    })
  }

  private handleMessage(line: string): void {
    try {
      const message = MessageSchema.parse(JSON.parse(line))

      if (message.type === "chat" && this.onMessageCallback) {
        const chatMessage: ChatMessage = {
          from: message.username,
          content: message.data?.content || "",
          timestamp: message.timestamp,
        }

        this.onMessageCallback(chatMessage)
      }
    } catch (error) {
      console.error("消息解析错误:", error)
    }
  }

  async start(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.server.listen(this.port, () => {
        console.log(`💬 聊天服务器启动在端口 ${this.port}`)
        resolve()
      })

      this.server.on("error", reject)
    })
  }

  onMessage(callback: (message: ChatMessage) => void): void {
    this.onMessageCallback = callback
  }

  stop(): void {
    this.server.close(() => {
      console.log("💬 聊天服务器已关闭")
    })
  }
}

export class ChatClient {
  private socket?: net.Socket

  constructor() {}

  async connect(address: string, port: number): Promise<void> {
    return new Promise((resolve, reject) => {
      this.socket = net.createConnection(port, address, () => {
        console.log(`🔗 已连接到 ${address}:${port}`)
        resolve()
      })

      this.socket.on("error", reject)
    })
  }

  sendMessage(username: string, content: string): void {
    if (!this.socket || this.socket.destroyed) {
      throw new Error("未连接到服务器")
    }

    const message: Message = {
      type: "chat",
      username,
      port: 0,
      timestamp: Date.now(),
      data: { content },
    }

    const messageStr = JSON.stringify(message) + "\n"
    this.socket.write(messageStr)
  }

  disconnect(): void {
    if (this.socket && !this.socket.destroyed) {
      this.socket.end()
    }
  }

  isConnected(): boolean {
    return this.socket !== undefined && !this.socket.destroyed
  }
}
