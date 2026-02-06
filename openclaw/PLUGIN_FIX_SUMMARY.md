# 插件加载问题修复总结

## 问题描述

```
Invalid config at C:\Users\CPC0057\.openclaw\openclaw.json:
- plugins.entries.qqbot: plugin not found: qqbot
- plugins.allow: plugin not found: qqbot
```

## 根本原因

1. **全局安装的 `openclaw` vs 本地开发版本**
   - 全局安装：`npm install -g openclaw` → 不包含本地 `extensions/` 目录
   - 本地开发：`node openclaw.mjs` → 可以访问所有本地插件

2. **插件 package.json 配置错误**
   - `main` 字段指向 `dist/index.js`，但没有编译输出
   - 应该指向 `index.ts`

## 修复内容

### 1. 修改 qqbot package.json

**文件**: `extensions/qqbot/package.json`

```diff
{
  "main": "dist/index.js",  // ❌ 错误
+ "main": "index.ts",       // ✅ 正确
}
```

### 2. 使用本地开发版本

**不要使用**：
```cmd
openclaw onboard  # ❌ 全局版本，找不到本地插件
```

**改用**：
```cmd
cd D:\WorkStation\digitalworker\openclaw
node openclaw.mjs onboard  # ✅ 本地版本，可以访问所有插件
```

或者使用提供的脚本：
```cmd
openclaw-dev.cmd onboard
```

### 3. 配置文件更新

**文件**: `~/.openclaw/openclaw.json`

```json
{
  "plugins": {
    "enabled": true,
    "allow": ["qqbot"],
    "entries": {
      "qqbot": {
        "enabled": true
      }
    }
  }
}
```

## 验证结果

**命令**：
```cmd
node openclaw.mjs plugins list | grep qqbot
```

**输出**：
```
│ QQ Bot       │ qqbot    │ loaded   │ ...  │ 1.3.0 │
```

## 快速使用指南

### 日常命令

```cmd
# 进入项目目录
cd D:\WorkStation\digitalworker\openclaw

# 启动 gateway
node openclaw.mjs gateway start

# 运行向导
node openclaw.mjs onboard

# 查看插件
node openclaw.mjs plugins list

# 查看日志
node openclaw.mjs logs --follow

# 停止服务
node openclaw.mjs gateway stop
```

### 创建快捷脚本（可选）

**文件**: `openclaw-dev.cmd`
```cmd
@echo off
set "OPENCLAW_ROOT=%~dp0"
node "%OPENCLAW_ROOT%openclaw.mjs" %*
```

使用：
```cmd
openclaw-dev.cmd onboard
```

## 核心要点

| 要点 | 说明 |
|------|------|
| **使用本地版本** | `node openclaw.mjs` 而不是 `openclaw` |
| **工作目录** | 始终在项目根目录运行 |
| **插件配置** | 在 `~/.openclaw/openclaw.json` 中启用 |
| **package.json** | `main` 字段指向源文件而不是编译输出 |

## 相关文件

- `LOCAL_DEV_WITH_PLUGINS.md` - 详细的本地开发指南
- `extensions/qqbot/package.json` - 插件配置（已修复）
- `~/.openclaw/openclaw.json` - 用户配置（已更新）
- `openclaw-dev.cmd` - 快捷启动脚本

## 常见问题

### Q: 为什么不使用全局安装的 openclaw？

A: 全局安装的版本不包含 `extensions/` 目录中的自定义插件。只有已发布到 npm 的插件才会被包含。

### Q: 可以让插件在全局版本中可用吗？

A: 有几种方式：
1. 将插件发布为独立的 npm 包
2. 使用 `npm link` 链接本地版本
3. 将插件提交到 OpenClaw 主仓库

### Q: 修改插件后需要重新构建吗？

A: 使用 `node openclaw.mjs` 运行时不需要，它直接加载 TypeScript 源文件。但如果你修改了 `package.json`，需要重启 gateway。

---

**状态**: ✅ 已修复
**验证**: qqbot 插件已加载
**下一步**: 使用 `node openclaw.mjs onboard` 配置 QQ Bot 通道
