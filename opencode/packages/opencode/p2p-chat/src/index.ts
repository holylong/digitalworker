import { PeerDiscovery } from "./discovery/peer-discovery.js"
import { ChatServer, ChatClient, type ChatMessage } from "./network/chat.js"
import { ChatUI } from "./ui/chat-ui.js"
import { CHAT_PORT } from "./types.js"

export class P2PChat {
  private discovery: PeerDiscovery
  private server: ChatServer
  private ui: ChatUI
  private clients = new Map<string, ChatClient>()

  constructor(username: string) {
    this.discovery = new PeerDiscovery(username, CHAT_PORT)
    this.server = new ChatServer(CHAT_PORT)
    this.ui = new ChatUI(username)

    this.setupCallbacks()
  }

  private setupCallbacks(): void {
    // 设置消息接收回调
    this.server.onMessage((message: ChatMessage) => {
      this.ui.addMessage(message)
    })

    // 设置UI回调
    this.ui.setPeersCallback(async () => {
      const peers = this.discovery.getPeers()
      console.log("\n👥 在线用户:")

      if (peers.length === 0) {
        console.log("暂无其他在线用户")
      } else {
        peers.forEach((peer, index) => {
          console.log(`${index + 1}. ${peer.username} (${peer.address}:${peer.port})`)
        })
      }

      console.log("")
    })

    this.ui.setSendMessageCallback(async () => {
      const peers = this.discovery.getPeers()

      if (peers.length === 0) {
        console.log("没有在线用户可发送消息")
        return
      }

      // 选择接收者
      const { text } = await import("@clack/prompts")
      const recipientIndex = await text({
        message: "请输入接收者编号:",
        validate: (value) => {
          const num = parseInt(value || "0")
          if (isNaN(num) || num < 1 || num > peers.length) {
            return `请输入1-${peers.length}之间的数字`
          }
          return undefined
        },
      })

      if (typeof recipientIndex === "symbol") return Promise.resolve()

      const recipient = peers[parseInt(recipientIndex.toString() || "0") - 1]

      const message = await text({
        message: `发送消息给 ${recipient.username}:`,
        validate: (value) => {
          if (!value || value.trim().length === 0) {
            return "消息内容不能为空"
          }
          return undefined
        },
      })

      if (typeof message === "symbol") return

      await this.sendToPeer(recipient, message.toString())
    })
  }

  private async sendToPeer(peer: any, content: string): Promise<void> {
    try {
      const clientKey = `${peer.address}:${peer.port}`
      let client = this.clients.get(clientKey)

      if (!client || !client.isConnected()) {
        client = new ChatClient()
        await client.connect(peer.address, peer.port)
        this.clients.set(clientKey, client)
      }

      client.sendMessage(this.ui.getUsername(), content)
      console.log(`✅ 消息已发送给 ${peer.username}`)
    } catch (error) {
      console.error(`❌ 发送消息失败:`, error)
    }
  }

  async start(): Promise<void> {
    try {
      console.log("🚀 正在启动P2P聊天工具...")

      // 启动聊天服务器
      await this.server.start()

      // 启动peer发现
      await this.discovery.start()

      // 启动UI
      await this.ui.start()
    } catch (error) {
      console.error("启动失败:", error)
    }
  }

  async stop(): Promise<void> {
    console.log("🛑 正在停止P2P聊天工具...")

    // 断开所有客户端连接
    for (const client of this.clients.values()) {
      client.disconnect()
    }

    // 停止服务
    this.server.stop()
    this.discovery.stop()

    console.log("✅ P2P聊天工具已停止")
  }
}

// 程序入口
async function main(): Promise<void> {
  const args = process.argv.slice(2)
  const username = args[0] || `User_${Math.random().toString(36).substr(2, 6)}`

  const chat = new P2PChat(username)

  // 处理程序退出
  process.on("SIGINT", async () => {
    console.log("\n收到退出信号...")
    await chat.stop()
    process.exit(0)
  })

  process.on("SIGTERM", async () => {
    console.log("\n收到终止信号...")
    await chat.stop()
    process.exit(0)
  })

  await chat.start()
}

// 只有直接运行此文件时才执行main
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error)
}
