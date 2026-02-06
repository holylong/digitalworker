# OpenClaw 使用指南 - 全局版本 vs 本地版本

## 问题说明

你有两个版本的 OpenClaw：
1. **全局安装版本**: `npm install -g openclaw` → `openclaw` 命令
2. **本地开发版本**: 源码目录 → `node openclaw.mjs`

只有**本地开发版本**才能访问你的 qqbot 插件。

## 解决方案

### 方案 A：使用全局版本（推荐日常使用）

**配置文件**：`~/.openclaw/openclaw.json`（当前状态，无插件配置）

```cmd
# 正常使用
openclaw onboard
openclaw gateway start
openclaw agent --message "hello"
```

**优点**：简单，可以在任何目录使用
**缺点**：无法使用 qqbot 插件

---

### 方案 B：使用本地版本（开发 qqbot 时）

**配置文件**：`~/.openclaw/openclaw.json`（需要添加插件配置）

**步骤**：

1. **进入项目目录**：
   ```cmd
   cd D:\WorkStation\digitalworker\openclaw
   ```

2. **临时启用插件配置**：
   ```cmd
   # 将以下内容添加到 ~/.openclaw/openclaw.json 的末尾
   node -e "const fs=require('fs');const p='C:\\Users\\CPC0057\\.openclaw\\openclaw.json';const c=JSON.parse(fs.readFileSync(p,'utf8'));c.plugins={enabled:true,allow:['qqbot'],entries:{qqbot:{enabled:true}}};fs.writeFileSync(p,JSON.stringify(c,null,2));"
   ```

3. **使用本地版本**：
   ```cmd
   node openclaw.mjs onboard
   node openclaw.mjs gateway start
   ```

4. **使用完成后禁用插件**（如果要切换回全局版本）：
   ```cmd
   node -e "const fs=require('fs');const p='C:\\Users\\CPC0057\\.openclaw\\openclaw.json';const c=JSON.parse(fs.readFileSync(p,'utf8'));delete c.plugins;fs.writeFileSync(p,JSON.stringify(c,null,2));"
   ```

---

### 方案 C：创建专门的配置文件（推荐）

创建两个配置文件，根据需要切换：

**文件 1**: `~/.openclaw/openclaw.json`（全局版本使用）
```json
{
  "meta": { ... },
  "wizard": { ... },
  "auth": { ... },
  "agents": { ... },
  "messages": { ... },
  "commands": { ... },
  "gateway": { ... }
  // 注意：没有 plugins 字段
}
```

**文件 2**: `~/.openclaw/openclaw-with-qqbot.json`（本地版本使用）
```json
{
  "meta": { ... },
  "wizard": { ... },
  "auth": { ... },
  "agents": { ... },
  "messages": { ... },
  "commands": { ... },
  "gateway": { ... },
  "plugins": {
    "enabled": true,
    "allow": ["qqbot"],
    "entries": {
      "qqbot": { "enabled": true }
    }
  }
}
```

**切换脚本**: `switch-config.cmd`
```cmd
@echo off
if "%1"=="global" (
    copy "%USERPROFILE%\.openclaw\openclaw.json" "%USERPROFILE%\.openclaw\openclaw.json.tmp" >nul
    copy "%USERPROFILE%\.openclaw\openclaw.json" "%USERPROFILE%\.openclaw\openclaw-with-qqbot.json" >nul
    copy "%USERPROFILE%\.openclaw\openclaw.json.tmp" "%USERPROFILE%\.openclaw\openclaw.json" >nul
    echo Switched to global config (no qqbot)
) else if "%1"="qqbot" (
    copy "%USERPROFILE%\.openclaw\openclaw.json" "%USERPROFILE%\.openclaw\openclaw-without-qqbot.json" >nul
    copy "%USERPROFILE%\.openclaw\openclaw-with-qqbot.json" "%USERPROFILE%\.openclaw\openclaw.json" >nul
    echo Switched to qqbot config
) else (
    echo Usage: switch-config [global^|qqbot]
)
```

---

### 方案 D：使用环境变量（最简单）

创建一个批处理文件来启动带插件的版本：

**文件**: `run-with-qqbot.cmd`
```cmd
@echo off
set OPENCLAW_CONFIG=%USERPROFILE%\.openclaw\openclaw-qqbot.json
node openclaw.mjs %*
```

但这需要修改 OpenClaw 源码来支持 `OPENCLAW_CONFIG` 环境变量。

---

## 推荐使用方式

### 日常使用（无 qqbot）
```cmd
openclaw onboard
openclaw gateway start
```

### 开发 qqbot 时
```cmd
cd D:\WorkStation\digitalworker\openclaw

# 启用插件
node -e "const fs=require('fs');const p='C:\\Users\\CPC0057\\.openclaw\\openclaw.json';const c=JSON.parse(fs.readFileSync(p,'utf8'));c.plugins={enabled:true,allow:['qqbot'],entries:{qqbot:{enabled:true}}};fs.writeFileSync(p,JSON.stringify(c,null,2));"

# 使用本地版本
node openclaw.mjs gateway start

# 使用完后禁用
node -e "const fs=require('fs');const p='C:\\Users\\CPC0057\\.openclaw\\openclaw.json';const c=JSON.parse(fs.readFileSync(p,'utf8'));delete c.plugins;fs.writeFileSync(p,JSON.stringify(c,null,2));"
```

---

## 当前状态

你的配置文件现在是**全局版本配置**（无插件），可以正常使用：

```cmd
openclaw onboard
```

如果需要使用 qqbot，按照上面的步骤切换到本地版本即可。
