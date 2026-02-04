#!/usr/bin/env bun
import { NetworkScanner } from "../src/network/network-scanner.js"
import { writeFileSync } from "node:fs"
import { join } from "node:path"

async function main() {
  console.log("🌐 局域网设备扫描器")
  console.log("=".repeat(40))

  const scanner = new NetworkScanner({
    timeout: 2000,
    maxConcurrent: 30,
    ports: [22, 80, 443, 3389, 8080, 3000, 5432, 3306, 6379],
    deepScan: true,
  })

  try {
    const startTime = Date.now()
    const devices = await scanner.scan()
    const scanTime = (Date.now() - startTime) / 1000

    console.log(`\n✅ 扫描完成！用时 ${scanTime} 秒`)
    console.log("=".repeat(40))

    const stats = scanner.getDeviceCount()
    console.log(`📊 统计信息:`)
    console.log(`   总计: ${stats.total} 个IP`)
    console.log(`   在线: ${stats.online} 个设备`)
    console.log(`   离线: ${stats.offline} 个设备`)

    if (stats.online > 0) {
      console.log("\n🖥️  在线设备列表:")
      console.log("-".repeat(40))

      devices
        .filter((d) => d.up)
        .forEach((device, index) => {
          console.log(`${index + 1}. ${device.ip}`)
          if (device.hostname) console.log(`   🏷️  主机名: ${device.hostname}`)
          if (device.mac) console.log(`   🔗 MAC地址: ${device.mac}`)
          if (device.responseTime) console.log(`   ⚡ 响应时间: ${device.responseTime}ms`)
          if (device.openPorts.length > 0) {
            console.log(`   🔓 开放端口: ${device.openPorts.join(", ")}`)
          }
          console.log()
        })
    }

    const report = {
      scanTime: new Date().toISOString(),
      scanDuration: scanTime,
      stats,
      devices: devices,
    }

    const reportPath = join(process.cwd(), "network-scan-report.json")
    writeFileSync(reportPath, JSON.stringify(report, null, 2))
    console.log(`📄 详细报告已保存至: ${reportPath}`)
  } catch (error) {
    console.error("❌ 扫描过程中出现错误:", error)
    process.exit(1)
  }
}

if (import.meta.main) {
  main()
}
