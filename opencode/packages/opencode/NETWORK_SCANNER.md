# 局域网扫描器

一个强大的局域网设备扫描工具，可以快速发现网络中的所有在线设备并收集详细信息。

## 功能特性

- 🔍 **快速扫描**: 迅速发现局域网中的所有在线设备
- 🖥️ **设备信息收集**: 获取IP地址、MAC地址、主机名等详细信息
- 🔓 **端口扫描**: 检测常用端口的开放状态
- 📊 **多种报告格式**: 支持文本、CSV、Markdown、HTML等多种输出格式
- ⚡ **并发扫描**: 高效的并发扫描机制，提高扫描速度
- 🎯 **灵活配置**: 支持自定义超时、并发数、扫描端口等参数

## 安装与使用

### 基本用法

```bash
# 快速扫描
bun run bin/network-tool.ts quick

# 全面扫描（包含详细信息）
bun run bin/network-tool.ts full

# 持续监控模式
bun run bin/network-tool.ts monitor 5

# 搜索特定设备
bun run bin/network-tool.ts find 192.168

# 生成完整报告
bun run bin/lan-scanner.ts
```

### 编程接口

```typescript
import { NetworkScanner } from "./src/network/network-scanner.js"
import { ScanReporter } from "./src/network/scan-reporter.js"

// 创建扫描器实例
const scanner = new NetworkScanner({
  timeout: 2000,
  maxConcurrent: 30,
  ports: [22, 80, 443, 3389, 8080],
  deepScan: true,
})

// 执行扫描
const devices = await scanner.scan()

// 生成报告
const reporter = new ScanReporter(devices, scanTime)
await reporter.saveReports("./")
```

## 扫描选项

- `network`: 网络范围（如 "192.168.1.0/24"），默认自动检测
- `timeout`: 连接超时时间（毫秒），默认3000ms
- `maxConcurrent`: 最大并发数，默认50
- `ports`: 要扫描的端口列表
- `deepScan`: 是否执行深度扫描（主机名、MAC地址等）

## 输出格式

扫描器支持多种输出格式：

- **JSON**: 结构化数据，便于程序处理
- **文本**: 简洁的文本报告，适合控制台查看
- **CSV**: 表格数据，便于Excel等工具处理
- **Markdown**: 文档格式，便于README等文档使用
- **HTML**: 网页格式，可视化展示

## 技术实现

- 使用UDP ping检测设备在线状态
- 并发扫描提高效率
- 支持ARP表查询获取MAC地址
- DNS反向解析获取主机名
- TCP连接测试端口开放状态

## 注意事项

- 需要管理员/root权限才能获取完整的ARP信息
- 某些设备可能配置了防火墙，影响扫描结果
- 大型网络扫描可能需要较长时间
- 请确保在合法授权的网络环境中使用

## 示例输出

```
🌐 局域网扫描报告
==================================================
扫描时间: 2024-01-01 12:00:00
扫描用时: 2.3 秒

统计信息
------------------------------
总计IP数量: 254
在线设备: 12
离线设备: 242
在线率: 4.7%

在线设备详情
------------------------------
1. 192.168.1.1
   主机名: router.local
   MAC地址: aa:bb:cc:dd:ee:ff
   响应时间: 5ms
   开放端口: 80, 443, 22

2. 192.168.1.100
   主机名: desktop-pc
   MAC地址: 11:22:33:44:55:66
   响应时间: 12ms
   开放端口: 22, 80, 443
```
