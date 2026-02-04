import { exec } from "node:child_process"
import { promisify } from "node:util"
import { createSocket } from "node:dgram"
import { createConnection } from "node:net"
import { z } from "zod"

const execAsync = promisify(exec)

export const DeviceInfoSchema = z.object({
  ip: z.string(),
  mac: z.string().optional(),
  hostname: z.string().optional(),
  vendor: z.string().optional(),
  openPorts: z.array(z.number()).default([]),
  responseTime: z.number().optional(),
  os: z.string().optional(),
  up: z.boolean(),
})

export type DeviceInfo = z.infer<typeof DeviceInfoSchema>

export const ScanOptionsSchema = z.object({
  network: z.string().optional(),
  timeout: z.number().default(3000),
  maxConcurrent: z.number().default(50),
  ports: z.array(z.number()).default([22, 80, 443, 3389, 8080]),
  deepScan: z.boolean().default(false),
})

export type ScanOptions = z.infer<typeof ScanOptionsSchema>

export class NetworkScanner {
  private options: ScanOptions
  private devices = new Map<string, DeviceInfo>()
  private activePings = 0

  constructor(options: Partial<ScanOptions> = {}) {
    this.options = ScanOptionsSchema.parse(options)
  }

  async scan(): Promise<DeviceInfo[]> {
    console.log("🔍 开始扫描局域网设备...")

    const network = this.options.network || (await this.getLocalNetwork())
    console.log(`📡 扫描网络范围: ${network}`)

    const ips = this.generateIPRange(network)
    console.log(`🎯 需要扫描 ${ips.length} 个IP地址`)

    await this.pingSweep(ips)

    if (this.options.deepScan) {
      console.log("🔍 开始深度扫描...")
      await this.deepScan()
    }

    return Array.from(this.devices.values()).sort((a, b) => a.ip.localeCompare(b.ip))
  }

  private async getLocalNetwork(): Promise<string> {
    try {
      const { stdout } = await execAsync("ip route get 1.1.1.1 | awk '{print $7}'")
      const localIP = stdout.trim()
      const parts = localIP.split(".")
      parts[3] = "0/24"
      return parts.join(".")
    } catch {
      return "192.168.1.0/24"
    }
  }

  private generateIPRange(network: string): string[] {
    const [base, mask] = network.split("/")
    const parts = base.split(".")

    if (mask === "24") {
      const ips = []
      for (let i = 1; i < 255; i++) {
        ips.push(`${parts[0]}.${parts[1]}.${parts[2]}.${i}`)
      }
      return ips
    }

    throw new Error("目前只支持 /24 网络掩码")
  }

  private async pingSweep(ips: string[]): Promise<void> {
    const batches = this.chunkArray(ips, this.options.maxConcurrent)

    for (const batch of batches) {
      await Promise.all(batch.map((ip) => this.pingHost(ip)))
    }
  }

  private async pingHost(ip: string): Promise<void> {
    return new Promise((resolve) => {
      const socket = createSocket("udp4")
      const startTime = Date.now()

      socket.on("error", () => {
        socket.close()
        resolve()
      })

      socket.on("message", () => {
        const responseTime = Date.now() - startTime

        this.devices.set(ip, {
          ip,
          up: true,
          responseTime,
          openPorts: [],
        })

        socket.close()
        resolve()
      })

      setTimeout(() => {
        socket.close()
        resolve()
      }, this.options.timeout)

      socket.send("", 0, 0, 7, ip)
    })
  }

  private async deepScan(): Promise<void> {
    const onlineDevices = Array.from(this.devices.values()).filter((d) => d.up)

    await Promise.all([
      this.getHostnameInfo(onlineDevices),
      this.getMACAddresses(onlineDevices),
      this.portScan(onlineDevices),
    ])
  }

  private async getHostnameInfo(devices: DeviceInfo[]): Promise<void> {
    await Promise.all(devices.map((device) => this.getHostname(device)))
  }

  private async getHostname(device: DeviceInfo): Promise<void> {
    try {
      const { stdout } = await execAsync(`nslookup ${device.ip}`)
      const match = stdout.match(/name = (.+)/i)
      if (match) {
        device.hostname = match[1].trim()
      }
    } catch {
      // 忽略nslookup错误
    }
  }

  private async getMACAddresses(devices: DeviceInfo[]): Promise<void> {
    try {
      const { stdout } = await execAsync("arp -a")

      for (const device of devices) {
        const match = stdout.match(new RegExp(`\\(${device.ip}\\) at ([\\da-fA-F:]+)`))
        if (match) {
          device.mac = match[1]
        }
      }
    } catch {
      // 忽略arp错误
    }
  }

  private async portScan(devices: DeviceInfo[]): Promise<void> {
    await Promise.all(devices.map((device) => this.scanDevicePorts(device)))
  }

  private async scanDevicePorts(device: DeviceInfo): Promise<void> {
    const openPorts: number[] = []

    for (const port of this.options.ports) {
      const isOpen = await this.checkPort(device.ip, port)
      if (isOpen) {
        openPorts.push(port)
      }
    }

    device.openPorts = openPorts
  }

  private async checkPort(ip: string, port: number): Promise<boolean> {
    return new Promise((resolve) => {
      const socket = createConnection({ host: ip, port })

      socket.on("connect", () => {
        socket.destroy()
        resolve(true)
      })

      socket.on("error", () => {
        resolve(false)
      })

      setTimeout(() => {
        socket.destroy()
        resolve(false)
      }, 1000)
    })
  }

  private chunkArray<T>(array: T[], size: number): T[][] {
    const chunks: T[][] = []
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size))
    }
    return chunks
  }

  getResults(): DeviceInfo[] {
    return Array.from(this.devices.values())
  }

  getOnlineDevices(): DeviceInfo[] {
    return Array.from(this.devices.values()).filter((d) => d.up)
  }

  getDeviceCount(): { total: number; online: number; offline: number } {
    const total = this.devices.size
    const online = this.getOnlineDevices().length
    const offline = total - online

    return { total, online, offline }
  }
}
