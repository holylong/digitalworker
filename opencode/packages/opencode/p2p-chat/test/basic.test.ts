#!/usr/bin/env bun
// 测试P2P聊天工具的基本功能

import { PeerDiscovery } from "../src/discovery/peer-discovery.js"
import { ChatServer, ChatClient } from "../src/network/chat.js"
import { CHAT_PORT, BROADCAST_PORT } from "../src/types.js"

async function testDiscovery() {
  console.log("🧪 测试UDP发现机制...")

  const discovery1 = new PeerDiscovery("User1", 30002)
  const discovery2 = new PeerDiscovery("User2", 30003)

  try {
    await discovery1.start()
    console.log("✅ User1 发现服务启动成功")

    await discovery2.start()
    console.log("✅ User2 发现服务启动成功")

    // 等待一段时间让发现机制工作
    await new Promise((resolve) => setTimeout(resolve, 2000))

    const peers1 = discovery1.getPeers()
    const peers2 = discovery2.getPeers()

    console.log(`📊 User1 发现的peers: ${peers1.length}`)
    console.log(`📊 User2 发现的peers: ${peers2.length}`)

    discovery1.stop()
    discovery2.stop()

    console.log("✅ 发现机制测试完成")
  } catch (error) {
    console.error("❌ 发现机制测试失败:", error)
  }
}

async function testChatServer() {
  console.log("🧪 测试聊天服务器...")

  const server = new ChatServer(30004)
  const client = new ChatClient()

  try {
    await server.start()
    console.log("✅ 聊天服务器启动成功")

    let messageReceived = false

    server.onMessage((message) => {
      console.log(`📨 收到消息: ${message.from}: ${message.content}`)
      messageReceived = true
    })

    await client.connect("127.0.0.1", 30004)
    console.log("✅ 客户端连接成功")

    client.sendMessage("TestUser", "Hello, P2P Chat!")
    console.log("✅ 消息发送成功")

    // 等待消息处理
    await new Promise((resolve) => setTimeout(resolve, 1000))

    if (messageReceived) {
      console.log("✅ 聊天功能测试成功")
    } else {
      console.log("❌ 消息未收到")
    }

    client.disconnect()
    server.stop()
  } catch (error) {
    console.error("❌ 聊天功能测试失败:", error)
  }
}

async function main() {
  console.log("🚀 开始P2P聊天工具功能测试\n")

  await testDiscovery()
  console.log("")

  await testChatServer()
  console.log("")

  console.log("✅ 所有测试完成")
}

main().catch(console.error)
