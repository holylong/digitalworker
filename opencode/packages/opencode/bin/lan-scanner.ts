#!/usr/bin/env bun
import { ScanTool } from "./network-tool.js"
import { ScanReporter } from "../src/network/scan-reporter.js"
import { writeFileSync } from "node:fs"
import { join } from "node:path"

async function main() {
  console.log("🌐 局域网设备扫描器 - 完整版")
  console.log("=".repeat(50))

  const scanner = new ScanTool({
    timeout: 2000,
    maxConcurrent: 30,
    ports: [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3389, 5432, 3306, 6379, 8080, 3000, 9000, 27017],
    deepScan: true,
  })

  try {
    const startTime = Date.now()

    console.log("🔍 开始扫描局域网设备...")
    const devices = await scanner.scanner.scan()
    const scanTime = (Date.now() - startTime) / 1000

    console.log(`✅ 扫描完成！用时 ${scanTime} 秒`)

    const onlineDevices = devices.filter((d) => d.up)
    const stats = scanner.scanner.getDeviceCount()

    console.log("\n📊 扫描统计:")
    console.log(`   总计IP: ${stats.total}`)
    console.log(`   在线设备: ${stats.online}`)
    console.log(`   离线设备: ${stats.offline}`)
    console.log(`   在线率: ${((stats.online / stats.total) * 100).toFixed(1)}%`)

    if (onlineDevices.length > 0) {
      console.log("\n🖥️ 在线设备概览:")
      onlineDevices.slice(0, 10).forEach((device, index) => {
        console.log(`   ${index + 1}. ${device.ip}${device.hostname ? ` (${device.hostname})` : ""}`)
      })

      if (onlineDevices.length > 10) {
        console.log(`   ... 还有 ${onlineDevices.length - 10} 个设备`)
      }
    }

    console.log("\n📄 生成详细报告...")
    const reporter = new ScanReporter(devices, scanTime)
    await reporter.saveReports(process.cwd())

    const jsonReport = {
      scanInfo: {
        timestamp: new Date().toISOString(),
        scanDuration: scanTime,
        network: "自动检测",
        options: "深度扫描模式",
      },
      statistics: stats,
      devices: devices,
    }

    const jsonPath = join(process.cwd(), "network-scan-report.json")
    writeFileSync(jsonPath, JSON.stringify(jsonReport, null, 2))
    console.log(`📋 JSON数据报告: ${jsonPath}`)

    console.log("\n🎉 扫描完成！所有报告已保存到当前目录。")
  } catch (error) {
    console.error("❌ 扫描过程中出现错误:", error)
    process.exit(1)
  }
}

if (import.meta.main) {
  main()
}
