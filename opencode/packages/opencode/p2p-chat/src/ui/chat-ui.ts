import { intro, outro, text, select, confirm } from "@clack/prompts"
import { type ChatMessage } from "../network/chat.js"

export class ChatUI {
  private username: string
  private messages: ChatMessage[] = []
  private isRunning = false
  private peersCallback?: () => Promise<void>
  private sendMessageCallback?: () => Promise<void>

  constructor(username: string) {
    this.username = username
  }

  async start(): Promise<void> {
    intro("🌐 欢迎使用局域网P2P聊天工具")

    const name = await text({
      message: "请输入你的用户名:",
      placeholder: this.username,
      validate: (value) => {
        if (!value || value.trim().length === 0) {
          return "用户名不能为空"
        }
        if (value.length > 20) {
          return "用户名不能超过20个字符"
        }
        return undefined
      },
    })

    if (typeof name === "symbol") return Promise.resolve()

    this.username = name.toString().trim()
    console.log(`👋 你好，${this.username}！`)

    this.isRunning = true
    await this.showMainMenu()
  }

  private async showMainMenu(): Promise<void> {
    while (this.isRunning) {
      const action = await select({
        message: "请选择操作:",
        options: [
          { value: "peers", label: "👥 查看在线用户" },
          { value: "chat", label: "💬 发送消息" },
          { value: "messages", label: "📜 查看消息历史" },
          { value: "exit", label: "🚪 退出" },
        ],
      })

      if (typeof action === "symbol") break

      switch (action) {
        case "peers":
          if (this.peersCallback) {
            await this.peersCallback()
          } else {
            console.log("正在加载在线用户...")
            await this.pause()
          }
          break
        case "chat":
          if (this.sendMessageCallback) {
            await this.sendMessageCallback()
          } else {
            console.log("发送功能暂未实现")
            await this.pause()
          }
          break
        case "messages":
          await this.showMessages()
          break
        case "exit":
          await this.exit()
          break
      }
    }
  }

  private async showMessages(): Promise<void> {
    console.log("\n📜 消息历史:")

    if (this.messages.length === 0) {
      console.log("暂无消息")
    } else {
      this.messages.forEach((msg, index) => {
        const time = new Date(msg.timestamp).toLocaleTimeString()
        const sender = msg.from === this.username ? `你` : msg.from

        console.log(`${index + 1}. [${time}] ${sender}: ${msg.content}`)
      })
    }

    console.log("")
    await this.pause()
  }

  private async exit(): Promise<void> {
    const confirmed = await confirm({
      message: "确定要退出吗？",
    })

    if (confirmed) {
      this.isRunning = false
      outro("👋 再见！")
    }
  }

  private async pause(): Promise<void> {
    await text({
      message: "按回车键继续...",
      placeholder: "",
    })
  }

  addMessage(message: ChatMessage): void {
    this.messages.push(message)

    // 实时显示新消息
    if (this.isRunning) {
      const time = new Date(message.timestamp).toLocaleTimeString()
      const sender = message.from === this.username ? `你` : message.from

      console.log(`\n💬 [${time}] ${sender}: ${message.content}\n`)
    }
  }

  getUsername(): string {
    return this.username
  }

  setPeersCallback(callback: () => Promise<void>): void {
    this.peersCallback = callback
  }

  setSendMessageCallback(callback: () => Promise<void>): void {
    this.sendMessageCallback = callback
  }
}
