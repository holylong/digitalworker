# OpenCode 工作空间功能

## 概述

OpenCode 现在支持**默认工作空间**和**自动项目创建**功能，避免在服务器启动目录下直接创建文件，保持目录整洁。

## 功能特性

### 1. 默认工作空间

- **位置**: `~/opencode-workspace/` (可通过环境变量自定义)
- **自动创建**: 工作空间目录会在首次使用时自动创建
- **项目隔离**: 每个项目都有独立的子目录

### 2. 智能项目命名

根据你的请求自动生成项目名称：

| 关键词 | 项目名示例 |
|--------|-----------|
| "创建一个 REST API" | `api-1738529123` |
| "写一个爬虫" | `scraper-1738529123` |
| "开发一个网站" | `web-app-1738529123` |
| "做一个博客" | `blog-1738529123` |
| "构建命令行工具" | `cli-tool-1738529123` |
| 其他 | `你的请求前几个词-timestamp` |

### 3. 项目目录结构

```
~/opencode-workspace/
├── api-1738529123/           # 自动创建的 API 项目
│   ├── src/
│   ├── package.json
│   └── README.md
├── blog-1738529245/          # 博客项目
│   ├── posts/
│   └── index.html
└── scraper-1738529367/       # 爬虫项目
    ├── src/
    └── requirements.txt
```

## 使用方法

### Web 客户端使用

1. **连接服务器**
   ```
   打开 http://localhost:8080
   点击"连接"按钮
   ```

2. **配置工作空间选项**
   - ✅ **自动创建项目** (默认启用): 自动为新请求创建项目目录
   - 📝 **项目名称**: 可选，留空则自动生成

3. **发送请求**
   ```
   你: 创建一个用户注册的 REST API
   ```

   系统会自动：
   - 创建项目目录: `~/opencode-workspace/api-1738529123/`
   - 在该目录下生成所有文件
   - 使用该目录作为工作目录

### API 使用

```bash
# 自动创建项目
curl -X POST http://localhost:4096/remote/execute \
  -H "Content-Type: application/json" \
  -d '{
    "type": "prompt",
    "message": "创建一个 REST API",
    "autoCreateProject": true
  }'

# 指定项目名称
curl -X POST http://localhost:4096/remote/execute \
  -H "Content-Type: application/json" \
  -d '{
    "type": "prompt",
    "message": "创建一个博客系统",
    "autoCreateProject": true,
    "projectName": "my-blog"
  }'

# 指定工作目录（传统方式）
curl -X POST http://localhost:4096/remote/execute \
  -H "Content-Type: application/json" \
  -d '{
    "type": "prompt",
    "message": "添加用户认证",
    "directory": "/path/to/existing/project"
  }'
```

## 配置选项

### 环境变量

```bash
# 自定义工作空间根目录
export OPENCODE_WORKSPACE_ROOT=/path/to/workspace

# 启动服务器
./dist/opencode-linux-x64/bin/opencode remote --port 4096
```

### Web 客户端设置

在 Web 客户端界面中：

1. **自动创建项目** (复选框)
   - ✅ 启用: 每个新请求自动创建项目目录
   - ❌ 禁用: 在当前目录或指定目录工作

2. **项目名称** (文本框)
   - 留空: 自动根据请求内容生成
   - 填写: 使用自定义名称

## 响应格式

成功创建项目后，API 返回：

```json
{
  "success": true,
  "sessionID": "session-id",
  "messageID": "message-id",
  "workspace": "/home/user/opencode-workspace",
  "projectDir": "/home/user/opencode-workspace/api-1738529123",
  "data": { ... }
}
```

## 智能命名规则

### 关键词映射

| 中文 | 英文 | 项目名 |
|------|------|--------|
| 接口 | API | `api-*` |
| 爬虫 | Scraper | `scraper-*` |
| 网站 | Website | `website-*` |
| 博客 | Blog | `blog-*` |
| 命令行 | CLI | `cli-tool-*` |
| 工具 | Tool | `tool-*` |
| 游戏 | Game | `game-*` |
| 插件 | Plugin | `plugin-*` |

### 默认规则

如果没有匹配到关键词：
1. 提取请求的前 3 个词
2. 转换为小写
3. 用连字符连接
4. 添加时间戳

例如：
- "帮我写一个 Python 脚本" → `python-1738529123`
- "创建电商网站" → `创建-电商-网站-1738529123`

## 示例场景

### 场景 1: 创建新项目

```
你: 创建一个 Express REST API

系统:
✓ 已连接到服务器
✓ 工作空间: /home/user/opencode-workspace
📁 项目目录: /home/user/opencode-workspace/api-1738529123

🤖 好的，我来帮你创建 Express REST API...
   [使用工具: Write]
   创建: api-1738529123/package.json
   创建: api-1738529123/src/app.ts
   ...
```

### 场景 2: 继续项目

```
# 方式1: 继续会话（自动使用相同项目目录）
你: 添加用户认证功能

# 方式2: 指定现有项目
你: 在 api-1738529123 项目中添加日志功能
```

### 场景 3: 自定义项目名

```
# Web 客户端
勾选"自动创建项目"
输入项目名: "my-awesome-app"
发送: "创建一个待办事项应用"

结果: ~/opencode-workspace/my-awesome-app/
```

## 最佳实践

1. **启用自动创建项目**
   - 保持服务器目录整洁
   - 每个项目独立管理
   - 便于清理和归档

2. **使用有意义的项目名**
   - 描述性的名称更容易识别
   - 例如: `user-auth-service` 而不是 `project-123`

3. **定期清理**
   ```bash
   # 查看所有项目
   ls -la ~/opencode-workspace/

   # 删除不需要的项目
   rm -rf ~/opencode-workspace/old-project-123
   ```

4. **版本控制**
   ```bash
   cd ~/opencode-workspace/my-project
   git init
   git add .
   git commit -m "Initial commit by OpenCode"
   ```

## 故障排除

### 问题: 项目目录未创建

**检查**:
```bash
ls -la ~/opencode-workspace/
```

**解决**:
- 确保 `autoCreateProject` 设置为 `true`
- 检查目录权限

### 问题: 项目名称不符合预期

**解决**:
- 使用自定义项目名
- 检查请求中的关键词是否正确

### 问题: 文件仍在服务器目录创建

**检查**:
- 是否禁用了"自动创建项目"
- 是否在之前的会话中（会话保持原有的目录）

## 高级用法

### 批量创建项目

```javascript
// 使用测试客户端
const client = new OpenCodeRemoteClient({
    baseUrl: 'http://localhost:4096'
});

const projects = [
    { name: 'user-service', prompt: '创建用户服务 API' },
    { name: 'order-service', prompt: '创建订单服务 API' },
    { name: 'payment-service', prompt: '创建支付服务 API' }
];

for (const project of projects) {
    await client.sendPrompt({
        message: project.prompt,
        projectName: project.name,
        autoCreateProject: true
    });
}
```

### 集成到工作流

```bash
#!/bin/bash
# 创建新项目的快捷脚本

PROJECT_NAME=$1
PROMPT=$2

curl -X POST http://localhost:4096/remote/execute \
  -H "Content-Type: application/json" \
  -d "{
    \"type\": \"prompt\",
    \"message\": \"$PROMPT\",
    \"autoCreateProject\": true,
    \"projectName\": \"$PROJECT_NAME\"
  }"

echo "项目已创建: ~/opencode-workspace/$PROJECT_NAME"
cd ~/opencode-workspace/$PROJECT_NAME
```

## 总结

✅ **优点**:
- 保持服务器目录整洁
- 项目自动隔离
- 智能命名，易于管理
- 支持自定义配置

🎯 **推荐**:
- 默认启用"自动创建项目"
- 使用有意义的项目名称
- 定期清理不需要的项目
