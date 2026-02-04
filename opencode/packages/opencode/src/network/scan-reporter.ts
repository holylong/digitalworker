import { type DeviceInfo } from "./network-scanner.js"

export class ScanReporter {
  private devices: DeviceInfo[]
  private scanTime: number

  constructor(devices: DeviceInfo[], scanTime: number) {
    this.devices = devices
    this.scanTime = scanTime
  }

  generateTextReport(): string {
    const onlineDevices = this.devices.filter((d) => d.up)
    const offlineDevices = this.devices.filter((d) => !d.up)

    let report = "局域网扫描报告\n"
    report += "=".repeat(50) + "\n\n"
    report += `扫描时间: ${new Date().toLocaleString()}\n`
    report += `扫描用时: ${this.scanTime} 秒\n\n`

    report += "统计信息\n"
    report += "-".repeat(30) + "\n"
    report += `总计IP数量: ${this.devices.length}\n`
    report += `在线设备: ${onlineDevices.length}\n`
    report += `离线设备: ${offlineDevices.length}\n`
    report += `在线率: ${((onlineDevices.length / this.devices.length) * 100).toFixed(1)}%\n\n`

    if (onlineDevices.length > 0) {
      report += "在线设备详情\n"
      report += "-".repeat(30) + "\n"

      onlineDevices.forEach((device, index) => {
        report += `${index + 1}. ${device.ip}\n`
        if (device.hostname) report += `   主机名: ${device.hostname}\n`
        if (device.mac) report += `   MAC地址: ${device.mac}\n`
        if (device.responseTime) report += `   响应时间: ${device.responseTime}ms\n`
        if (device.openPorts.length > 0) {
          report += `   开放端口: ${device.openPorts.join(", ")}\n`
        }
        report += "\n"
      })
    }

    return report
  }

  generateCSV(): string {
    let csv = "IP地址,主机名,MAC地址,响应时间(ms),开放端口,状态\n"

    this.devices.forEach((device) => {
      const status = device.up ? "在线" : "离线"
      const hostname = device.hostname || "未知"
      const mac = device.mac || "未知"
      const responseTime = device.responseTime?.toString() || ""
      const openPorts = device.openPorts.length > 0 ? device.openPorts.join(";") : ""

      csv += `${device.ip},"${hostname}","${mac}",${responseTime},"${openPorts}",${status}\n`
    })

    return csv
  }

  generateMarkdown(): string {
    const onlineDevices = this.devices.filter((d) => d.up)
    const offlineDevices = this.devices.filter((d) => !d.up)

    let markdown = "# 局域网扫描报告\n\n"
    markdown += `**扫描时间**: ${new Date().toLocaleString()}\n\n`
    markdown += `**扫描用时**: ${this.scanTime} 秒\n\n`

    markdown += "## 📊 统计信息\n\n"
    markdown += "| 指标 | 数量 |\n"
    markdown += "|------|------|\n"
    markdown += `| 总计IP数量 | ${this.devices.length} |\n`
    markdown += `| 在线设备 | ${onlineDevices.length} |\n`
    markdown += `| 离线设备 | ${offlineDevices.length} |\n`
    markdown += `| 在线率 | ${((onlineDevices.length / this.devices.length) * 100).toFixed(1)}% |\n\n`

    if (onlineDevices.length > 0) {
      markdown += "## 🖥️ 在线设备详情\n\n"
      markdown += "| # | IP地址 | 主机名 | MAC地址 | 响应时间 | 开放端口 |\n"
      markdown += "|---|--------|--------|----------|----------|----------|\n"

      onlineDevices.forEach((device, index) => {
        const hostname = device.hostname || "未知"
        const mac = device.mac || "未知"
        const responseTime = device.responseTime ? `${device.responseTime}ms` : "-"
        const openPorts = device.openPorts.length > 0 ? device.openPorts.join(", ") : "-"

        markdown += `| ${index + 1} | ${device.ip} | ${hostname} | ${mac} | ${responseTime} | ${openPorts} |\n`
      })
    }

    markdown += "\n## 📝 说明\n\n"
    markdown += "- 本报告由局域网扫描器自动生成\n"
    markdown += `- 扫描包含端口检测、主机名解析和MAC地址查询\n`
    markdown += `- 响应时间基于UDP ping测试\n`

    return markdown
  }

  generateHTML(): string {
    const onlineDevices = this.devices.filter((d) => d.up)
    const offlineDevices = this.devices.filter((d) => !d.up)

    return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>局域网扫描报告</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }
        h2 { color: #666; margin-top: 30px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: #f8f9fa; padding: 20px; border-radius: 6px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #007bff; }
        .stat-label { color: #666; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: 600; }
        .status-online { color: #28a745; font-weight: bold; }
        .status-offline { color: #dc3545; }
        .ports { font-family: monospace; background: #f8f9fa; padding: 2px 6px; border-radius: 3px; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 局域网扫描报告</h1>
        <p><strong>扫描时间:</strong> ${new Date().toLocaleString()}</p>
        <p><strong>扫描用时:</strong> ${this.scanTime} 秒</p>

        <h2>📊 统计信息</h2>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">${this.devices.length}</div>
                <div class="stat-label">总计IP数量</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${onlineDevices.length}</div>
                <div class="stat-label">在线设备</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${offlineDevices.length}</div>
                <div class="stat-label">离线设备</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${((onlineDevices.length / this.devices.length) * 100).toFixed(1)}%</div>
                <div class="stat-label">在线率</div>
            </div>
        </div>

        <h2>🖥️ 设备详情</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>IP地址</th>
                    <th>主机名</th>
                    <th>MAC地址</th>
                    <th>响应时间</th>
                    <th>开放端口</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>
                ${this.devices
                  .map(
                    (device, index) => `
                    <tr>
                        <td>${index + 1}</td>
                        <td><code>${device.ip}</code></td>
                        <td>${device.hostname || "未知"}</td>
                        <td><code>${device.mac || "未知"}</code></td>
                        <td>${device.responseTime ? `${device.responseTime}ms` : "-"}</td>
                        <td>${
                          device.openPorts.length > 0
                            ? device.openPorts.map((p: number) => `<span class="ports">${p}</span>`).join(" ")
                            : "-"
                        }</td>
                        <td><span class="status-${device.up ? "online" : "offline"}">
                            ${device.up ? "在线" : "离线"}
                        </span></td>
                    </tr>
                `,
                  )
                  .join("")}
            </tbody>
        </table>

        <div class="footer">
            <p>📝 本报告由局域网扫描器自动生成</p>
        </div>
    </div>
</body>
</html>
    `.trim()
  }

  async saveReports(basePath: string): Promise<void> {
    const { writeFileSync } = await import("node:fs")
    const { join } = await import("node:path")

    try {
      writeFileSync(join(basePath, "network-scan.txt"), this.generateTextReport())
      writeFileSync(join(basePath, "network-scan.csv"), this.generateCSV())
      writeFileSync(join(basePath, "network-scan.md"), this.generateMarkdown())
      writeFileSync(join(basePath, "network-scan.html"), this.generateHTML())

      console.log("📄 报告已生成:")
      console.log(`   📝 network-scan.txt`)
      console.log(`   📊 network-scan.csv`)
      console.log(`   📄 network-scan.md`)
      console.log(`   🌐 network-scan.html`)
    } catch (error) {
      console.error("❌ 保存报告失败:", error)
    }
  }
}
