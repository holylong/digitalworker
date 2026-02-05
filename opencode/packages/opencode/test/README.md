# OpenCode Web Client 启动和管理指南

## 🚀 快速启动

### 方式一：交互式启动（推荐）

```bash
cd /home/skyer/WorkStation/digitalworker/opencode/packages/opencode/test
./start-all.sh
```

脚本会：
1. ✅ 检查服务是否已在运行
2. ✅ 启动 OpenCode 服务器（端口 4096）
3. ✅ 启动 Web 客户端服务器（端口 8080）
4. ✅ 自动打开浏览器
5. ✅ 显示访问地址和配置信息

### 交互式命令

启动后，你可以输入以下命令：

- **Enter** - 刷新状态，查看服务运行情况
- **logs** - 查看最近的日志（最近 20 行）
- **stop** - 停止所有服务
- **bg** - 切换到后台运行（脚本退出但服务继续运行）

## 📊 日志管理

### 方式一：使用日志查看脚本（推荐）

```bash
./logs.sh
```

提供以下选项：
1. OpenCode 服务器日志（实时）
2. Web 服务器日志（实时）
3. 所有日志（分屏）
4. OpenCode 最近 50 行
5. Web 服务器最近 50 行
6. OpenCode 完整日志
7. Web 服务器完整日志

### 方式二：直接查看日志

```bash
# 实时查看 OpenCode 日志
tail -f /tmp/opencode-remote.log

# 实时查看 Web 服务器日志
tail -f /tmp/web-client.log

# 查看最近 50 行
tail -50 /tmp/opencode-remote.log
```

## 🛑 停止服务

### 方式一：使用停止脚本（推荐）

```bash
./stop-all.sh
```

### 方式二：手动停止

```bash
# 停止 OpenCode 服务器（端口 4096）
lsof -ti :4096 | xargs kill -9

# 停止 Web 服务器（端口 8080）
lsof -ti :8080 | xargs kill -9
```

## 📝 日志文件位置

| 服务 | 日志文件 |
|------|---------|
| OpenCode 服务器 | `/tmp/opencode-remote.log` |
| Web 服务器 | `/tmp/web-client.log` |

## 🔧 问题排查

### 问题 1: 端口已被占用

**症状**: 启动失败，提示端口已被占用

**解决**:
```bash
# 查看占用端口的进程
lsof -i :4096  # OpenCode
lsof -i :8080  # Web 服务器

# 停止进程
./stop-all.sh

# 或强制停止
lsof -ti :4096 | xargs kill -9
lsof -ti :8080 | xargs kill -9
```

### 问题 2: 服务启动失败

**症状**: 脚本运行但服务无法访问

**排查步骤**:
```bash
# 1. 检查服务是否在运行
ps aux | grep opencode
ps aux | grep python.*8080

# 2. 查看日志
./logs.sh

# 3. 检查端口是否正常监听
netstat -tuln | grep -E '4096|8080'
# 或
ss -tuln | grep -E '4096|8080'

# 4. 测试 API 连接
curl http://localhost:4096/remote/health
```

### 问题 3: 页面无法连接服务器

**症状**: Web 页面打开，但无法连接到 OpenCode 服务器

**解决**:
1. 检查服务器是否在运行
   ```bash
   curl http://localhost:4096/remote/health
   ```

2. 检查页面中的服务器地址配置
   - 本地访问: `http://localhost:4096`
   - 网络访问: `http://你的IP:4096`

3. 检查防火墙
   ```bash
   # 查看防火墙状态
   sudo ufw status

   # 如果需要开放端口
   sudo ufw allow 4096
   sudo ufw allow 8080
   ```

## 🌐 网络访问

### 本地访问

```
Web 客户端: http://localhost:8080
API 服务器: http://localhost:4096
```

### 局域网访问

1. 获取本机 IP:
   ```bash
   hostname -I
   ```

2. 从其他设备访问:
   ```
   Web 客户端: http://你的IP:8080
   API 服务器: http://你的IP:4096
   ```

## 🔒 安全建议

如果要在公网访问，建议设置密码：

```bash
# 设置密码
export OPENCODE_PASSWORD=your_secure_password

# 启动服务
./start-all.sh
```

然后在 Web 客户端中配置：
- 用户名: `opencode`
- 密码: `your_secure_password`

## 📋 常用命令

```bash
# 启动所有服务
./start-all.sh

# 查看服务状态
ps aux | grep -E "opencode|python.*8080"

# 查看日志
./logs.sh

# 停止所有服务
./stop-all.sh

# 重启服务
./stop-all.sh && sleep 2 && ./start-all.sh
```

## 💡 提示

1. **服务自动检测**: 脚本会检测服务是否已运行，避免重复启动
2. **后台运行**: 输入 `bg` 可以让脚本退出但服务继续运行
3. **日志查看**: 使用 `./logs.sh` 可以方便地查看和管理日志
4. **浏览器自动打开**: 脚本会尝试自动打开浏览器
5. **IP 地址**: 脚本会自动显示本机 IP，方便从其他设备访问

## 🎯 使用流程

1. **启动服务**:
   ```bash
   cd /home/skyer/WorkStation/digitalworker/opencode/packages/opencode/test
   ./start-all.sh
   ```

2. **打开浏览器**:
   - 脚本会自动打开浏览器
   - 或手动访问: `http://localhost:8080`

3. **配置连接**:
   - 服务器地址: `http://localhost:4096`
   - 用户名: `opencode`
   - 密码: (可选)

4. **开始对话**:
   - 点击"连接"按钮
   - 输入消息，开始使用

5. **查看日志**（如需要）:
   ```bash
   ./logs.sh
   ```

6. **停止服务**:
   ```bash
   ./stop-all.sh
   ```
