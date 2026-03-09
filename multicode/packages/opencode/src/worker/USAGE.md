# OpenCode 分布式 Worker 系统

本文档介绍如何使用 OpenCode 的分布式编译和执行系统，实现跨平台开发。

## 架构概览

```
┌────────────────────────────────────────────────────────────────┐
│                     Linux (Master)                              │
│                                                                 │
│  AI: 写代码 ──▶ 本地保存 ──▶ Sync Engine ──▶ 推送到 Worker      │
│                                    │                            │
│                                    ▼                            │
│                           收集编译/测试结果                      │
└────────────────────────────────────────────────────────────────┘
                                     │
                                     │ HTTP/WS
                                     ▼
┌────────────────────────────────────────────────────────────────┐
│                    Windows/macOS (Worker)                       │
│                                                                 │
│  Worker Server (:4097)                                         │
│  - 接收文件变更                                                  │
│  - 执行编译命令                                                  │
│  - 返回结果                                                      │
└────────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 在 Windows 机器上安装

将编译好的 Windows 版本复制到 Windows 机器：

```bash
# Windows 可执行文件位置
/home/skyer/WorkStation/digitalworker/multicode/packages/opencode/dist/opencode-windows-x64/bin/opencode.exe
```

### 2. 启动 Worker（在 Windows 上）

```powershell
# 在 Windows PowerShell 中运行
.\opencode.exe worker --port 4097 --hostname 0.0.0.0 --directory C:\workspace
```

输出示例：
```
Worker node listening on http://0.0.0.0:4097
Working directory: C:\workspace

Available endpoints:
  GET  /worker/status  - Get worker status and capabilities
  POST /worker/sync    - Sync files to worker
  POST /worker/exec    - Execute command on worker

Press Ctrl+C to stop
```

### 3. 添加 Worker 节点（在 Linux 上）

```bash
opencode node add \
  --name windows \
  --url http://<windows-ip>:4097 \
  --directory C:\workspace
```

### 4. 测试和使用

```bash
# 列出节点
opencode node list

# 测试连接
opencode node test --id wn_xxx

# 同步当前项目并编译
opencode node sync --id wn_xxx --local-dir .
opencode node exec --id wn_xxx --command "go build -o app.exe"
```

## CLI 命令详解

### `opencode worker`

启动一个 worker 节点，监听来自 master 的命令。

```bash
opencode worker [options]

选项:
  --port        监听端口 (默认: 4097)
  --hostname    监听地址 (默认: 127.0.0.1，建议设为 0.0.0.0)
  --directory   工作目录
```

**示例：**

```bash
# Linux
opencode worker --port 4097 --hostname 0.0.0.0 --directory /home/user/workspace

# Windows
opencode worker --port 4097 --hostname 0.0.0.0 --directory C:\workspace
```

### `opencode node`

管理远程 worker 节点。

#### `node list` - 列出所有节点

```bash
opencode node list
```

输出示例：
```
Worker Nodes:

  ● windows (wn_abc123)
    URL: http://192.168.1.100:4097
    Platform: windows/x64
    Directory: C:\workspace
    Status: online
    Capabilities: go, node, python
    Last ping: 5s ago

  ○ macos (wn_def456)
    URL: http://192.168.1.101:4097
    Platform: darwin/arm64
    Directory: /Users/user/workspace
    Status: offline
```

#### `node add` - 添加节点

```bash
opencode node add --name <名称> --url <URL> --directory <目录> [--password <密码>]
```

**参数：**
- `--name`: 节点名称（必填）
- `--url`: 节点 URL，如 `http://192.168.1.100:4097`（必填）
- `--directory`: 远程工作目录（必填）
- `--password`: 可选的认证密码

**示例：**

```bash
opencode node add \
  --name windows-build \
  --url http://192.168.1.100:4097 \
  --directory C:\workspace
```

#### `node remove` - 删除节点

```bash
opencode node remove --id <节点ID>
```

#### `node test` - 测试连接

```bash
opencode node test --id <节点ID>
```

输出示例：
```
Testing connection to worker wn_abc123...
✓ Connection successful
  Platform: windows/x64
  Hostname: DESKTOP-ABC
  Capabilities: go, rust, node, python
```

#### `node sync` - 同步文件

```bash
opencode node sync --id <节点ID> --local-dir <本地目录> [--remote-dir <远程目录>]
```

**参数：**
- `--id`: 节点 ID（必填）
- `--local-dir`: 本地要同步的目录（必填）
- `--remote-dir`: 远程目标目录（可选，默认使用节点配置的目录）

**示例：**

```bash
# 同步当前项目到 Windows
opencode node sync --id wn_xxx --local-dir ./myproject

# 同步到指定远程目录
opencode node sync --id wn_xxx --local-dir . --remote-dir C:\test\myapp
```

#### `node exec` - 执行命令

```bash
opencode node exec --id <节点ID> --command <命令> [--directory <工作目录>]
```

**示例：**

```bash
# 编译 Go 程序
opencode node exec --id wn_xxx --command "go build -o app.exe main.go"

# 运行测试
opencode node exec --id wn_xxx --command "go test ./..."

# 运行程序
opencode node exec --id wn_xxx --command "./app.exe --client 192.168.1.50:8080"
```

## AI 工具使用

AI Agent 可以使用 `worker` 工具进行跨平台开发。工具支持以下操作：

### 列出可用节点

```
action: "list"
```

### 同步文件

```
action: "sync"
workerId: "wn_xxx"
files: [{path: "main.go", content: "..."}]  // 可选，不指定则同步整个项目
```

### 执行命令

```
action: "exec"
workerId: "wn_xxx"
command: "go build -o app.exe"
args: []  // 可选
timeout: 60000  // 可选，毫秒
```

### 编译并运行

```
action: "compile-run"
workerId: "wn_xxx"
compileCommand: "go build -o chat.exe"
runCommand: "./chat.exe --client linux-ip:8080"
```

## 实际使用场景

### 场景：开发 P2P 聊天程序

1. **在 Linux 上用 AI 写代码**

   AI 在本地开发，代码保存在项目目录中。

2. **同步代码到 Windows**

   ```
   AI: 我把代码同步到 Windows 上编译测试
   → worker tool: action="sync", workerId="wn_xxx"
   ```

3. **在 Windows 上编译**

   ```
   → worker tool: action="exec", command="go build -o chat.exe"
   ```

4. **处理编译错误**

   如果编译失败，AI 会看到错误信息：

   ```
   Error: ./main.go:42: undefined: someFunc
   ```

   AI 修改代码后重新同步和编译。

5. **运行测试**

   ```
   # Linux 上运行服务端
   ./chat --server :8080

   # Windows 上运行客户端（通过 worker）
   opencode node exec --id wn_xxx --command "./chat.exe --client 192.168.1.50:8080"
   ```

6. **验证通信**

   两台机器的程序互相发送消息，验证 P2P 通信功能。

## API 端点

Worker 节点暴露以下 HTTP 端点：

| 端点 | 方法 | 描述 |
|------|------|------|
| `/worker/status` | GET | 获取 worker 状态和能力 |
| `/worker/sync` | POST | 同步文件到 worker |
| `/worker/exec` | POST | 在 worker 上执行命令 |
| `/worker/exec/stream` | POST | 执行命令并流式返回输出 |

### `/worker/status`

**响应示例：**

```json
{
  "platform": "windows",
  "arch": "x64",
  "hostname": "DESKTOP-ABC",
  "workDirectory": "C:\\workspace",
  "capabilities": ["go", "rust", "node", "python", "gcc"],
  "version": "1.0.0"
}
```

### `/worker/sync`

**请求体：**

```json
{
  "directory": "C:\\workspace\\myproject",
  "files": [
    {
      "path": "main.go",
      "content": "cGFja2FnZSBtYWlu...",
      "encoding": "base64",
      "mode": "create"
    }
  ]
}
```

**响应：**

```json
{
  "synced": 5,
  "errors": []
}
```

### `/worker/exec`

**请求体：**

```json
{
  "command": "go",
  "args": ["build", "-o", "app.exe"],
  "cwd": "C:\\workspace\\myproject",
  "env": {},
  "timeout": 60000
}
```

**响应：**

```json
{
  "success": true,
  "exitCode": 0,
  "stdout": "",
  "stderr": "",
  "duration": 1234
}
```

## 文件结构

新增的文件：

```
packages/opencode/src/worker/
├── index.ts          # 模块入口
├── types.ts          # 类型定义
├── worker.sql.ts     # 数据库 schema
├── registry.ts       # 节点管理
├── sync.ts           # 文件同步和远程执行
├── server.ts         # Worker HTTP 服务
└── README.md         # 文档

packages/opencode/src/cli/cmd/
├── worker.ts         # opencode worker 命令
└── node.ts           # opencode node 命令

packages/opencode/src/tool/
└── worker.ts         # AI 工具

packages/opencode/migration/
└── 20260306120000_add_worker_tables/
    └── migration.sql # 数据库迁移
```

## 注意事项

1. **网络配置**
   - 确保 worker 节点的端口（默认 4097）可以从 master 访问
   - Windows 防火墙可能需要允许该端口的入站连接

2. **路径格式**
   - Windows 使用反斜杠 `\` 或正斜杠 `/`
   - 建议 CLI 命令中使用正斜杠以保持跨平台兼容

3. **安全性**
   - 使用 `--password` 参数设置认证密码
   - 生产环境建议使用 HTTPS 和更强的认证机制

4. **文件排除**
   - 默认排除 `node_modules`, `.git`, `dist`, `build`, `*.log`
   - 可以通过 API 参数自定义排除规则

## 故障排查

### Worker 无法连接

```bash
# 检查 worker 是否运行
curl http://<worker-ip>:4097/worker/status

# 检查防火墙
# Windows
netsh advfirewall firewall add rule name="OpenCode Worker" dir=in action=allow protocol=tcp localport=4097

# Linux
sudo ufw allow 4097/tcp
```

### 编译失败

```bash
# 检查 worker 上的编译工具
opencode node test --id wn_xxx

# 手动测试命令
opencode node exec --id wn_xxx --command "go version"
```

### 文件同步问题

```bash
# 查看详细错误
opencode node sync --id wn_xxx --local-dir . 2>&1
```