#!/usr/bin/env bun

// 测试脚本 - 启动服务器并测试 API
import { spawn } from "child_process"

// 启动服务器
console.log("🚀 启动 REST API 服务器...")
const serverProcess = spawn("bun", ["run", "simple-api.ts"], {
  stdio: ["pipe", "pipe", "pipe"],
})

let port: string | null = null

// 监听服务器输出获取端口
serverProcess.stdout.on("data", (data) => {
  const output = data.toString()
  console.log(output.trim())

  // 提取端口号
  const match = output.match(/正在监听 http:\/\/localhost:(\d+)/)
  if (match && !port) {
    port = match[1]
    setTimeout(() => {
      if (port) testAPI(port)
    }, 1000) // 等待服务器完全启动
  }
})

serverProcess.stderr.on("data", (data) => {
  console.error("服务器错误:", data.toString())
})

async function testAPI(port: string) {
  console.log(`\n🧪 测试 API (端口: ${port})\n`)

  const baseUrl = `http://localhost:${port}`

  try {
    // 测试 1: 获取 API 信息
    console.log("1. GET /")
    const response1 = await fetch(`${baseUrl}/`)
    const data1 = await response1.json()
    console.log("   响应:", JSON.stringify(data1, null, 2))
    console.log("")

    // 测试 2: 获取所有用户
    console.log("2. GET /users")
    const response2 = await fetch(`${baseUrl}/users`)
    const data2 = await response2.json()
    console.log("   响应:", JSON.stringify(data2, null, 2))
    console.log("")

    // 测试 3: 创建用户
    console.log("3. POST /users")
    const response3 = await fetch(`${baseUrl}/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "王五", email: "wangwu@example.com" }),
    })
    const data3 = await response3.json()
    console.log("   响应:", JSON.stringify(data3, null, 2))
    console.log("")

    // 测试 4: 获取单个用户
    if (data3.id) {
      console.log(`4. GET /users/${data3.id}`)
      const response4 = await fetch(`${baseUrl}/users/${data3.id}`)
      const data4 = await response4.json()
      console.log("   响应:", JSON.stringify(data4, null, 2))
      console.log("")
    }

    // 测试 5: 更新用户
    if (data3.id) {
      console.log(`5. PUT /users/${data3.id}`)
      const response5 = await fetch(`${baseUrl}/users/${data3.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "王五更新" }),
      })
      const data5 = await response5.json()
      console.log("   响应:", JSON.stringify(data5, null, 2))
      console.log("")
    }

    // 测试 6: 删除用户
    if (data3.id) {
      console.log(`6. DELETE /users/${data3.id}`)
      const response6 = await fetch(`${baseUrl}/users/${data3.id}`, {
        method: "DELETE",
      })
      const data6 = await response6.json()
      console.log("   响应:", JSON.stringify(data6, null, 2))
      console.log("")
    }

    console.log("✅ 所有测试完成!")
  } catch (error) {
    console.error("❌ 测试失败:", error instanceof Error ? error.message : String(error))
  }

  // 关闭服务器
  setTimeout(() => {
    console.log("\n🛑 关闭服务器...")
    serverProcess.kill()
    process.exit(0)
  }, 1000)
}

// 超时处理
setTimeout(() => {
  console.log("❌ 服务器启动超时")
  serverProcess.kill()
  process.exit(1)
}, 10000)
