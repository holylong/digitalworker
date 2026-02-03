import dgram from "node:dgram"
import { MessageSchema, type Message, BROADCAST_PORT, CHAT_PORT, BROADCAST_INTERVAL, type Peer } from "../types.js"

export class PeerDiscovery {
  private socket: dgram.Socket
  private peers = new Map<string, Peer>()
  private username: string
  private chatPort: number
  private broadcastInterval?: NodeJS.Timeout

  constructor(username: string, chatPort: number = CHAT_PORT) {
    this.username = username
    this.chatPort = chatPort
    this.socket = dgram.createSocket("udp4")
  }

  async start(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.socket.bind(BROADCAST_PORT, () => {
        this.socket.setBroadcast(true)
        this.setupMessageHandler()
        this.startBroadcasting()
        console.log(`🔍 Peer discovery started on port ${BROADCAST_PORT}`)
        resolve()
      })

      this.socket.on("error", reject)
    })
  }

  private setupMessageHandler(): void {
    this.socket.on("message", (msg, rinfo) => {
      try {
        const message = MessageSchema.parse(JSON.parse(msg.toString()))

        if (message.type === "discovery" && message.username !== this.username) {
          const peerKey = `${rinfo.address}:${message.port}`
          const peer: Peer = {
            username: message.username,
            address: rinfo.address,
            port: message.port,
            lastSeen: Date.now(),
          }

          this.peers.set(peerKey, peer)
          console.log(`👋 发现用户: ${message.username} (${rinfo.address}:${message.port})`)

          // 发送响应消息
          this.sendDiscoveryResponse(rinfo.address, BROADCAST_PORT)
        }
      } catch (error) {
        // 忽略无效消息
      }
    })
  }

  private startBroadcasting(): void {
    this.broadcast()
    this.broadcastInterval = setInterval(() => {
      this.broadcast()
    }, BROADCAST_INTERVAL)
  }

  private broadcast(): void {
    const message: Message = {
      type: "discovery",
      username: this.username,
      port: this.chatPort,
      timestamp: Date.now(),
    }

    const messageBuffer = Buffer.from(JSON.stringify(message))

    this.socket.send(messageBuffer, 0, messageBuffer.length, BROADCAST_PORT, "255.255.255.255", (error) => {
      if (error) {
        console.error("广播发送失败:", error)
      }
    })
  }

  private sendDiscoveryResponse(address: string, port: number): void {
    const message: Message = {
      type: "discovery",
      username: this.username,
      port: this.chatPort,
      timestamp: Date.now(),
    }

    const messageBuffer = Buffer.from(JSON.stringify(message))
    this.socket.send(messageBuffer, 0, messageBuffer.length, port, address)
  }

  getPeers(): Peer[] {
    // 清理过期的peers (30秒未活动)
    const now = Date.now()
    const timeout = 30000

    for (const [key, peer] of this.peers.entries()) {
      if (now - peer.lastSeen > timeout) {
        this.peers.delete(key)
        console.log(`👋 用户离线: ${peer.username}`)
      }
    }

    return Array.from(this.peers.values())
  }

  stop(): void {
    if (this.broadcastInterval) {
      clearInterval(this.broadcastInterval)
    }

    this.socket.close(() => {
      console.log("🔍 Peer discovery stopped")
    })
  }
}
