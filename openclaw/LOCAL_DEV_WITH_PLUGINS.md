# 使用本地开发版本运行自定义插件

## 问题说明

你添加了 `extensions/qqbot` 自定义插件，但是：

1. **全局安装的 `openclaw`** (通过 `npm install -g openclaw`) 不包含本地的 extensions
2. **本地开发版本** (通过 `node openclaw.mjs`) 可以访问所有插件

## 解决方案

### 方案 1：使用本地开发版本（推荐）

在项目根目录运行：

```cmd
# 进入项目目录
cd D:\WorkStation\digitalworker\openclaw

# 使用本地开发版本运行
node openclaw.mjs onboard
```

或者使用提供的启动脚本：

```cmd
openclaw-dev.cmd onboard
```

### 方案 2：将本地版本链接到全局

```cmd
# 进入项目目录
cd D:\WorkStation\digitalworker\openclaw

# 全局链接本地版本
npm link

# 现在可以在任何地方使用 openclaw 命令，它会使用本地版本
openclaw onboard
```

### 方案 3：发布你的插件（高级）

如果你想让插件在全局安装时可用，需要：

1. 将插件发布为独立的 npm 包
2. 或者将插件合并到 OpenClaw 主仓库的 PR 中

## 配置插件

使用本地开发版本后，需要启用插件：

### 方式 1：通过命令行启用

```cmd
node openclaw.mjs plugins enable qqbot
```

### 方式 2：编辑配置文件

编辑 `~/.openclaw/openclaw.json`：

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

## 验证插件已加载

```cmd
# 列出所有插件
node openclaw.mjs plugins list

# 查看 qqbot 插件状态
node openclaw.mjs plugins list | findstr qqbot
```

## 日常使用建议

### 开发模式

如果正在开发 qqbot 插件，建议：

1. **使用本地开发版本**：
   ```cmd
   cd D:\WorkStation\digitalworker\openclaw
   node openclaw.mjs gateway start
   ```

2. **启用热重载**：
   - 修改插件代码后，重启 gateway

3. **查看日志**：
   ```cmd
   node openclaw.mjs logs --follow
   ```

### 生产模式

如果要部署到生产：

1. **构建项目**：
   ```cmd
   pnpm build
   npm pack
   ```

2. **全局安装**：
   ```cmd
   npm install -g openclaw-<version>.tgz
   ```

   **注意**：这样安装的版本仍然不包含本地的 extensions/qqbot

## 插件开发注意事项

### package.json 配置

确保插件的 `package.json` 正确配置：

```json
{
  "name": "qqbot",
  "main": "index.ts",  // 指向 TypeScript 源文件，而不是 dist
  "openclaw": {
    "extensions": ["./index.ts"]
  }
}
```

### 目录结构

```
extensions/qqbot/
├── package.json
├── index.ts              # 插件入口
├── openclaw.plugin.json  # 插件清单
└── src/                  # 源代码
```

## 常见问题

### Q: 为什么全局安装的 openclaw 找不到我的插件？

A: 全局安装的 npm 包不包含项目源码中的 extensions/ 目录。只有发布到 npm 的插件才能被全局安装的版本使用。

### Q: 如何让我的插件可以全局使用？

A: 有几种方式：
1. 将插件发布为独立的 npm 包
2. 将插件提交到 OpenClaw 主仓库
3. 使用 `npm link` 链接本地版本

### Q: 本地版本和全局版本有什么区别？

A:
- **本地版本**：从源码运行 (`node openclaw.mjs`)，包含所有本地插件
- **全局版本**：通过 `npm install -g` 安装，只包含已发布的插件

### Q: 我应该使用哪个版本？

A:
- **开发插件时**：使用本地开发版本
- **日常使用**：可以使用全局版本（如果没有自定义插件）
- **生产环境**：建议使用本地构建的版本

## 快速命令参考

```cmd
# 进入项目目录
cd D:\WorkStation\digitalworker\openclaw

# 重新构建
pnpm build

# 启动 gateway
node openclaw.mjs gateway start

# 查看插件列表
node openclaw.mjs plugins list

# 启用插件
node openclaw.mjs plugins enable qqbot

# 运行向导
node openclaw.mjs onboard

# 查看日志
node openclaw.mjs logs --follow

# 停止 gateway
node openclaw.mjs gateway stop
```

---

**推荐**: 在开发自定义插件时，始终使用 `node openclaw.mjs` 而不是全局安装的 `openclaw` 命令。
