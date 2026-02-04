#!/usr/bin/env bun
import { NetworkScanner, type ScanOptions } from "../src/network/network-scanner.js"

export class ScanTool {
  private scanner: NetworkScanner

  constructor(options: Partial<ScanOptions> = {}) {
    this.scanner = new NetworkScanner(options)
  }

  async quickScan(): Promise<void> {
    console.log("🚀 快速扫描模式")
    const startTime = Date.now()

    const devices = await this.scanner.scan()
    const scanTime = (Date.now() - startTime) / 1000

    const onlineDevices = devices.filter((d) => d.up)

    console.log(`\n✅ 快速扫描完成！用时 ${scanTime} 秒`)
    console.log(`🖥️  发现 ${onlineDevices.length} 个在线设备:`)

    onlineDevices.forEach((device, index) => {
      console.log(`${index + 1}. ${device.ip}${device.hostname ? ` (${device.hostname})` : ""}`)
    })
  }

  async fullScan(): Promise<void> {
    console.log("🔍 全面扫描模式")
    const startTime = Date.now()

    const fullScanner = new NetworkScanner({
      timeout: 3000,
      maxConcurrent: 20,
      ports: [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3389, 5432, 3306, 6379, 8080, 3000, 9000, 27017],
      deepScan: true,
    })

    const devices = await fullScanner.scan()
    const scanTime = (Date.now() - startTime) / 1000

    const stats = fullScanner.getDeviceCount()
    const onlineDevices = devices.filter((d) => d.up)

    console.log(`\n✅ 全面扫描完成！用时 ${scanTime} 秒`)
    console.log(`📊 扫描统计: 总计${stats.total}个IP，在线${stats.online}个，离线${stats.offline}个`)

    console.log("\n🔍 详细设备信息:")
    console.log("=".repeat(60))

    onlineDevices.forEach((device, index) => {
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

  async monitorNetwork(intervalMinutes = 5): Promise<void> {
    console.log(`👁️  网络监控模式 - 每 ${intervalMinutes} 分钟扫描一次`)

    const scan = async () => {
      console.log(`\n🕐 ${new Date().toLocaleTimeString()} - 开始扫描...`)
      const devices = await this.scanner.scan()
      const onlineCount = devices.filter((d) => d.up).length

      console.log(`📊 当前在线设备: ${onlineCount} 个`)

      if (onlineCount === 0) {
        console.log("⚠️  警告: 未发现任何在线设备!")
      }
    }

    await scan()
    setInterval(scan, intervalMinutes * 60 * 1000)
  }

  async findSpecificDevice(ipPattern: string): Promise<void> {
    console.log(`🎯 搜索设备: ${ipPattern}`)

    const devices = await this.scanner.scan()
    const matchedDevices = devices.filter((d) => d.up && d.ip.includes(ipPattern))

    if (matchedDevices.length > 0) {
      console.log(`✅ 找到 ${matchedDevices.length} 个匹配的设备:`)
      matchedDevices.forEach((device, index) => {
        console.log(`${index + 1}. ${device.ip}`)
        if (device.hostname) console.log(`   🏷️  ${device.hostname}`)
        if (device.mac) console.log(`   🔗 MAC: ${device.mac}`)
      })
    } else {
      console.log(`❌ 未找到包含 "${ipPattern}" 的在线设备`)
    }
  }
}

async function main() {
  const command = process.argv[2]
  const tool = new ScanTool()

  switch (command) {
    case "quick":
      await tool.quickScan()
      break
    case "full":
      await tool.fullScan()
      break
    case "monitor":
      const interval = parseInt(process.argv[3]) || 5
      await tool.monitorNetwork(interval)
      break
    case "find":
      const pattern = process.argv[3]
      if (!pattern) {
        console.error("❌ 请提供要搜索的IP模式")
        process.exit(1)
      }
      await tool.findSpecificDevice(pattern)
      break
    default:
      console.log("🌐 局域网扫描工具")
      console.log("")
      console.log("用法:")
      console.log("  network-tool quick          - 快速扫描")
      console.log("  network-tool full           - 全面扫描")
      console.log("  network-tool monitor [分钟]  - 持续监控")
      console.log("  network-tool find [IP模式]   - 查找特定设备")
      console.log("")
      console.log("示例:")
      console.log("  network-tool quick")
      console.log("  network-tool find 192.168")
      console.log("  network-tool monitor 10")
      break
  }
}

if (import.meta.main) {
  main()
}
