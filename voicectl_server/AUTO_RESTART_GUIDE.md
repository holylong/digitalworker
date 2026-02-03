# 服务器自动重启使用指南

本指南提供了两种自动重启方案，当app.py崩溃时自动重启服务。

## 方案对比

| 方案 | 优点 | 缺点 | 推荐场景 |
|------|------|------|----------|
| **Shell脚本监控** | 简单易用，无需root权限 | 需要保持终端运行 | 开发测试环境 |
| **Systemd服务** | 开机自启，更稳定，日志管理完善 | 需要root权限安装 | 生产环境 |

---

## 方案一：Shell脚本监控（推荐用于开发）

### 快速开始

```bash
# 1. 启动服务器（带自动重启）
./run_with_auto_restart.sh
```

### 工作原理

1. 脚本会自动启动app.py
2. 每5秒检查一次进程是否存活
3. 如果检测到进程停止，等待3秒后自动重启
4. 具有重启频率保护：如果1分钟内重启超过5次，会暂停60秒避免无限循环

### 输出示例

```
[INFO] 2025-01-19 14:00:00 - ===== voicectl_server 自动重启监控启动 =====
[INFO] 2025-01-19 14:00:00 - 监控脚本 PID: 12345
[INFO] 2025-01-19 14:00:00 - voicectl_server 已启动，PID: 12346
[INFO] 2025-01-19 14:00:00 - 标准输出日志: tmp/server_stdout.log
[INFO] 2025-01-19 14:00:00 - 应用日志: tmp/server.log
[INFO] 2025-01-19 14:00:00 - 按 Ctrl+C 停止监控（应用将继续运行）
...
[WARN] 2025-01-19 14:05:23 - 检测到 voicectl_server 已停止！
[WARN] 2025-01-19 14:05:23 - 这是第 1 次重启
[WARN] 2025-01-19 14:05:23 - 最后的日志输出:
  | Traceback (most recent call last):
  |   File "app.py", line 123, in <module>
  |     ...
[INFO] 2025-01-19 14:05:26 - 正在启动 voicectl_server...
[INFO] 2025-01-19 14:05:26 - voicectl_server 已启动，PID: 12347
```

### 停止监控

按 `Ctrl+C` 停止监控脚本（应用会继续运行）。

如果需要完全停止应用：

```bash
# 查看运行的应用
ps aux | grep "python.*app.py"

# 终止应用
kill <PID>

# 或者使用脚本中的PID文件
kill $(cat tmp/server.pid)
```

### 后台运行

如果想在后台运行监控脚本：

```bash
# 使用nohup后台运行
nohup ./run_with_auto_restart.sh > tmp/monitor.log 2>&1 &

# 查看监控日志
tail -f tmp/monitor.log
```

### 配置选项

编辑 `run_with_auto_restart.sh` 中的配置：

```bash
PYTHON_CMD="python"           # Python命令（可改为python3）
APP_SCRIPT="app.py"            # 应用脚本
START_DELAY=3                  # 重启前等待秒数
MAX_RESTART_PER_MINUTE=5       # 每分钟最多重启次数
```

---

## 方案二：Systemd服务（推荐用于生产）

### 安装步骤

#### 1. 修改服务文件

编辑 `voicectl_server.service`，修改以下内容：

```ini
User=YOUR_USERNAME          # 改成你的用户名
WorkingDirectory=/home/skyer/WorkStation/texo_server/texo_ai/voicectl_server  # 改成项目路径
Environment="PATH=/home/skyer/WorkStation/texo_server/texo_ai/voicectl_server/venv/bin:/usr/local/bin:/usr/bin:/bin"  # 如果用虚拟环境，修改路径
ExecStart=/usr/bin/python3 app.py  # Python路径（用 which python3 查看）
```

#### 2. 安装服务

```bash
# 复制服务文件到systemd目录
sudo cp voicectl_server.service /etc/systemd/system/

# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable voicectl_server.service

# 启动服务
sudo systemctl start voicectl_server.service
```

#### 3. 管理服务

```bash
# 查看服务状态
sudo systemctl status voicectl_server.service

# 停止服务
sudo systemctl stop voicectl_server.service

# 重启服务
sudo systemctl restart voicectl_server.service

# 查看服务日志
sudo journalctl -u voicectl_server.service -f

# 查看最近100行日志
sudo journalctl -u voicectl_server.service -n 100
```

### Systemd优势

✅ **自动重启**：进程崩溃后自动重启
✅ **开机自启**：系统重启后自动启动服务
✅ **日志管理**：集成systemd日志系统
✅ **资源限制**：可以限制CPU、内存使用
✅ **稳定可靠**：不依赖终端会话

### 高级配置

如果需要添加更多配置，可以修改service文件的 `[Service]` 部分：

```ini
[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/voicectl_server

# 环境变量
Environment="PYTHONUNBUFFERED=1"
Environment="LOG_LEVEL=DEBUG"

# 资源限制
MemoryLimit=512M
CPUQuota=50%

# 重启策略
Restart=always           # 总是重启
RestartSec=3             # 重启前等待3秒
StartLimitInterval=60    # 60秒内
StartLimitBurst=5        # 最多重启5次

# 日志
StandardOutput=append:tmp/server_stdout.log
StandardError=append:tmp/server_stderr.log

# 如果使用虚拟环境
ExecStart=/path/to/venv/bin/python app.py
```

---

## 日志查看

### Shell脚本方案

```bash
# 查看应用标准输出
tail -f tmp/server_stdout.log

# 查看应用日志
tail -f tmp/server.log

# 查看监控日志（如果后台运行）
tail -f tmp/monitor.log
```

### Systemd方案

```bash
# 实时查看服务日志
sudo journalctl -u voicectl_server.service -f

# 查看最近100行
sudo journalctl -u voicectl_server.service -n 100 --since "10 minutes ago"

# 查看带时间戳的日志
sudo journalctl -u voicectl_server.service -n 50 --since today
```

---

## 故障排查

### 问题1：服务无法启动

**检查Python路径**：
```bash
which python3
which python
```

**检查文件权限**：
```bash
ls -la app.py
chmod +x app.py  # 如果需要
```

### 问题2：频繁重启

**查看日志找出原因**：
```bash
# Shell方案
tail -50 tmp/server_stdout.log

# Systemd方案
sudo journalctl -u voicectl_server.service -n 50
```

**检查是否有端口冲突**：
```bash
netstat -tulpn | grep 8001
lsof -i :8001
```

### 问题3：自动重启不工作

**Shell方案**：检查监控脚本是否在运行
```bash
ps aux | grep run_with_auto_restart
```

**Systemd方案**：检查服务状态
```bash
sudo systemctl status voicectl_server.service
```

---

## 推荐使用方案

### 开发环境
使用 **Shell脚本监控**：
- 简单快速
- 可以直接看到输出
- 便于调试

### 生产环境
使用 **Systemd服务**：
- 开机自启
- 更稳定可靠
- 日志管理完善
- 可以配合其他监控工具

---

## 快速切换

如果已经在使用Shell脚本，想切换到Systemd：

```bash
# 1. 停止Shell脚本监控（按Ctrl+C）

# 2. 确保应用没有运行
ps aux | grep "python.*app.py"
pkill -f "python.*app.py"

# 3. 安装并启动Systemd服务
sudo systemctl start voicectl_server.service

# 4. 查看状态
sudo systemctl status voicectl_server.service
```

如果从Systemd切换回Shell脚本：

```bash
# 1. 停止Systemd服务
sudo systemctl stop voicectl_server.service
sudo systemctl disable voicectl_server.service

# 2. 启动Shell脚本监控
./run_with_auto_restart.sh
```

---

## 总结

无论使用哪种方案，都能实现app.py崩溃时自动重启：

- ✅ 防止服务中断
- ✅ 提高系统可用性
- ✅ 减少人工干预

根据您的使用场景选择合适的方案即可！
