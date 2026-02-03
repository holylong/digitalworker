# OpenCode Remote API

OpenCode Remote API 允许你通过网络远程执行 OpenCode 命令和操作。

## 功能特性

- **RESTful API**: 通过 HTTP POST 请求执行命令
- **多种命令类型**: 支持 command、prompt、shell、status 操作
- **会话管理**: 创建和继续现有会话
- **事件流**: 通过 SSE 订阅实时事件
- **身份验证**: 支持基本身份验证

## 启动远程服务器

```bash
# 基本启动（默认 localhost:4096）
opencode remote

# 指定端口
opencode remote --port 8080

# 监听所有接口
opencode remote --hostname 0.0.0.0

# 启用密码保护
export OPENCODE_SERVER_PASSWORD=your_password
opencode remote

# 指定允许的 CORS 源
opencode remote --allow-origin https://example.com --allow-origin https://app.example.com
```

## API 端点

### 1. 健康检查

```bash
GET /remote/health
```

响应示例：
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### 2. 列出可用命令

```bash
GET /remote/commands
```

### 3. 执行命令

```bash
POST /remote/execute
Content-Type: application/json

{
  "type": "command|prompt|shell|status",
  "sessionID": "optional-session-id",
  "command": "command-name",        // for type=command
  "arguments": "command args",      // for type=command
  "message": "your message",        // for type=prompt
  "agent": "agent-name",            // optional
  "model": "provider/model",        // optional
  "variant": "high|max|minimal",    // optional
  "files": [                        // optional file attachments
    {"path": "/path/to/file"}
  ]
}
```

## 使用示例

### 使用 curl

```bash
# 健康检查
curl http://localhost:4096/remote/health

# 列出命令
curl http://localhost:4096/remote/commands

# 发送提示（带密码）
curl -u opencode:password \
  -X POST http://localhost:4096/remote/execute \
  -H "Content-Type: application/json" \
  -d '{"type":"prompt","message":"Create a REST API"}'

# 执行命令
curl -u opencode:password \
  -X POST http://localhost:4096/remote/execute \
  -H "Content-Type: application/json" \
  -d '{"type":"command","command":"commit","arguments":"Fix bug"}'

# 运行 shell 命令
curl -u opencode:password \
  -X POST http://localhost:4096/remote/execute \
  -H "Content-Type: application/json" \
  -d '{"type":"shell","command":"ls -la"}'

# 获取会话状态
curl -u opencode:password \
  -X POST http://localhost:4096/remote/execute \
  -H "Content-Type: application/json" \
  -d '{"type":"status"}'
```

### 使用测试客户端

```bash
# 设置环境变量（可选）
export OPENCODE_REMOTE_URL=http://localhost:4096
export OPENCODE_REMOTE_PASSWORD=your_password

# 健康检查
bun test/remote-client.ts health

# 列出命令
bun test/remote-client.ts list

# 执行命令
bun test/remote-client.ts run commit "Fix bug in login"

# 发送提示
bun test/remote-client.ts prompt "Create a new REST API endpoint"

# 运行 shell 命令
bun test/remote-client.ts shell "ls -la"

# 获取状态
bun test/remote-client.ts status

# 监听事件流
bun test/remote-client.ts watch
```

### 使用 JavaScript/TypeScript

```typescript
import { OpenCodeRemoteClient } from './test/remote-client'

const client = new OpenCodeRemoteClient({
  baseUrl: 'http://localhost:4096',
  username: 'opencode',
  password: 'your-password'
})

// 健康检查
await client.healthCheck()

// 执行命令
const result = await client.runCommand({
  command: 'commit',
  arguments: 'Add new feature'
})

// 发送提示
const response = await client.sendPrompt({
  message: 'Create a REST API',
  model: 'anthropic/claude-sonnet-4-5'
})

// 运行 shell 命令
const shellResult = await client.runShell({
  command: 'npm test'
})
```

### 使用 Python

```python
import requests
import json

server_url = "http://localhost:4096"
auth = ("opencode", "your_password")

# 发送提示
response = requests.post(
    f"{server_url}/remote/execute",
    auth=auth,
    json={
        "type": "prompt",
        "message": "Create a REST API"
    }
)
print(response.json())

# 执行命令
response = requests.post(
    f"{server_url}/remote/execute",
    auth=auth,
    json={
        "type": "command",
        "command": "commit",
        "arguments": "Fix bug"
    }
)
print(response.json())
```

## 命令类型

### 1. Command（命令）

执行 OpenCode 命令（如 commit、test、build 等）

```json
{
  "type": "command",
  "command": "commit",
  "arguments": "Optional commit message",
  "sessionID": "optional-existing-session"
}
```

### 2. Prompt（提示）

向 AI 发送消息

```json
{
  "type": "prompt",
  "message": "Your message here",
  "agent": "optional-agent-name",
  "model": "anthropic/claude-sonnet-4-5",
  "sessionID": "optional-existing-session"
}
```

### 3. Shell（Shell 命令）

执行 shell 命令

```json
{
  "type": "shell",
  "command": "ls -la",
  "sessionID": "optional-existing-session"
}
```

### 4. Status（状态）

获取会话信息

```json
{
  "type": "status",
  "sessionID": "optional-session-id"
}
```

如果不提供 sessionID，将返回所有会话列表。

## 响应格式

成功响应：
```json
{
  "success": true,
  "sessionID": "session-id",
  "messageID": "message-id",
  "data": { ... }
}
```

错误响应：
```json
{
  "success": false,
  "error": "Error message"
}
```

## 安全建议

1. **始终在生产环境使用密码**：
   ```bash
   export OPENCODE_SERVER_PASSWORD=strong_password_here
   ```

2. **限制 CORS 源**：
   ```bash
   opencode remote --allow-origin https://yourdomain.com
   ```

3. **使用反向代理**：在生产环境中，建议使用 nginx 或其他反向代理来处理 TLS/SSL

4. **防火墙规则**：限制对 4096 端口的访问

## 事件流（SSE）

你可以订阅服务器发送事件（SSE）来获取实时更新：

```bash
curl -N -H "Accept: text/event-stream" http://localhost:4096/event
```

或者使用测试客户端：
```bash
bun test/remote-client.ts watch
```

## 测试

运行自动化测试脚本：
```bash
./test/test-remote.sh
```

这会运行一系列测试来验证 API 功能。

## 故障排除

1. **连接被拒绝**：确保服务器正在运行
   ```bash
   # 检查服务器状态
   curl http://localhost:4096/remote/health
   ```

2. **认证失败**：检查用户名和密码
   ```bash
   curl -u username:password http://localhost:4096/remote/health
   ```

3. **CORS 错误**：添加你的域名到允许列表
   ```bash
   opencode remote --allow-origin https://yourdomain.com
   ```

## 高级用法

### 指定工作目录

通过 `x-opencode-directory` header 或查询参数指定：

```bash
curl -H "x-opencode-directory: /path/to/project" \
  http://localhost:4096/remote/execute
```

### 继续现有会话

```bash
curl -X POST http://localhost:4096/remote/execute \
  -H "Content-Type: application/json" \
  -d '{
    "type": "prompt",
    "message": "Continue with the previous task",
    "sessionID": "existing-session-id"
  }'
```
