# OpenCode Web Client

一个简单易用的 Web 界面，用于与 OpenCode 远程服务进行交互。

## 功能特性

- 💬 **聊天式界面** - 像使用聊天工具一样与 OpenCode 交互
- 📡 **实时更新** - 通过 SSE 接收实时响应和事件
- 🎨 **美观界面** - 现代化的 UI 设计，支持 Markdown 渲染
- 🛠️ **工具显示** - 显示 AI 使用的工具和输出
- 🔐 **身份验证** - 支持基本身份验证
- ⚡ **快捷操作** - 预设的快捷操作按钮

## 快速开始

### 方法 1: 使用启动脚本（推荐）

```bash
cd /home/skyer/WorkStation/digitalworker/opencode/packages/opencode
./test/start-web-client.sh
```

### 方法 2: 手动启动

1. **启动 OpenCode 远程服务器**

```bash
cd /home/skyer/WorkStation/digitalworker/opencode/packages/opencode

# 基本启动（无密码，不安全）
./dist/opencode-linux-x64/bin/opencode remote --port 4096

# 带密码保护（推荐）
export OPENCODE_SERVER_PASSWORD=your_password
./dist/opencode-linux-x64/bin/opencode remote --port 4096
```

2. **打开 Web 客户端**

在浏览器中打开：
```
file:///home/skyer/WorkStation/digitalworker/opencode/packages/opencode/test/web-client/index.html
```

3. **连接并开始对话**

- 输入服务器地址：`http://localhost:4096`
- 如果设置了密码，输入用户名和密码
- 点击"连接"按钮
- 开始对话！

## 使用说明

### 界面说明

```
┌─────────────────────────────────────────┐
│  🤖 OpenCode Web Client          ● 已连接 │  <- 标题栏
├─────────────────────────────────────────┤
│  [服务器地址] [用户名] [密码] [连接]      │  <- 配置面板
├─────────────────────────────────────────┤
│                                         │
│  🤖 你好！我可以帮你做什么？              │  <- AI 消息
│                                         │
│  👤 帮我创建一个 API    14:30           │  <- 用户消息
│                                         │
│  🤖 好的，我来帮你...                   │
│     [使用工具: Edit]                    │  <- 工具使用
│     [代码输出]                          │
│                                         │
├─────────────────────────────────────────┤
│  [输入消息框...]              [发送]     │  <- 输入区
│  [列出文件] [创建 API] [写测试] [修复]  │  <- 快捷操作
└─────────────────────────────────────────┘
```

### 发送消息

1. 在输入框中输入你的消息
2. 按 `Enter` 发送，或按 `Shift+Enter` 换行
3. AI 的响应会实时显示

### 快捷操作

点击快捷操作按钮可以快速发送常用指令：
- **列出文件** - 列出当前目录的文件
- **创建 API** - 创建一个 REST API
- **写测试** - 编写测试用例
- **修复 Bug** - 修复代码 bug

### 消息类型

1. **用户消息**（右侧，紫色）
   - 你发送的消息

2. **AI 消息**（左侧，白色）
   - OpenCode 的回复
   - 支持 Markdown 格式
   - 代码高亮显示

3. **工具使用**（黄色高亮）
   - 显示 AI 使用的工具
   - 显示工具参数和输出

4. **错误消息**（红色）
   - 显示执行过程中的错误

## 配置选项

### 环境变量

```bash
# 服务器端口
export OPENCODE_PORT=4096

# 服务器密码（强烈推荐）
export OPENCODE_SERVER_PASSWORD=your_secure_password

# 自动连接
export OPENCODE_AUTO_CONNECT=true
```

### 浏览器兼容性

支持所有现代浏览器：
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## 高级用法

### 自定义样式

编辑 `index.html` 中的 `<style>` 部分来自定义界面样式。

### 远程访问

要从其他设备访问：

1. 启动服务器时监听所有接口：
```bash
./dist/opencode-linux-x64/bin/opencode remote --hostname 0.0.0.0 --port 4096
```

2. 在 Web 客户端中输入服务器的 IP 地址：
```
http://192.168.1.100:4096
```

### CORS 配置

如果需要从 Web 服务器访问，配置允许的源：
```bash
./dist/opencode-linux-x64/bin/opencode remote --allow-origin https://yourdomain.com
```

## 故障排除

### 连接失败

1. **检查服务器是否运行**
```bash
curl http://localhost:4096/remote/health
```

2. **检查防火墙设置**
```bash
sudo ufw allow 4096
```

3. **查看服务器日志**
```bash
tail -f /tmp/opencode-remote.log
```

### SSE 事件未接收

SSE（Server-Sent Events）在某些情况下可能不支持基本认证。如果遇到此问题：

1. 不设置密码进行测试
2. 使用反向代理（如 nginx）处理认证

### 响应延迟

- 检查网络连接
- 减少 AI 响应的长度
- 使用更快的模型

## API 参考

Web 客户端使用以下 API 端点：

### GET /remote/health
健康检查

### POST /remote/execute
执行命令
```json
{
  "type": "prompt",
  "message": "你的消息",
  "sessionID": "会话ID（可选）"
}
```

### GET /event
SSE 事件流

## 示例场景

### 1. 创建新功能

```
你: 创建一个用户注册的 REST API
🤖: 好的，我来帮你创建...
   [使用工具: Write]
   [创建用户模型]
   [创建路由]
   [添加验证]
```

### 2. 调试代码

```
你: 帮我找找这个 bug
🤖: 让我看看代码...
   [使用工具: Read]
   [使用工具: Grep]
   找到问题了！在第 42 行...
```

### 3. 代码审查

```
你: 审查一下 src/app.ts
🤖: 正在分析...
   [使用工具: Read]
   发现几个潜在问题：
   1. ...
   2. ...
```

## 安全建议

1. **始终使用密码保护**
```bash
export OPENCODE_SERVER_PASSWORD=strong_password_here
```

2. **使用 HTTPS**（生产环境）
   - 设置反向代理（nginx）
   - 配置 SSL 证书

3. **限制访问来源**
```bash
./dist/opencode-linux-x64/bin/opencode remote --allow-origin https://yourdomain.com
```

4. **定期更新**
   - 更新 OpenCode 到最新版本
   - 更新系统依赖

## 许可证

MIT

## 贡献

欢迎提交问题和 Pull Request！
