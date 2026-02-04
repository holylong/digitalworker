# DigitalWorker 项目集合

本目录包含四个主要项目，每个项目都有其独特的功能和应用场景。

---

## 1. OpenClaw - 个人AI助手平台

**目录**: `openclaw/`

**技术栈**: Node.js, TypeScript, React

**项目简介**:
OpenClaw 是一个运行在个人设备上的 AI 助手平台，支持多种消息平台和语音交互。

**核心功能**:
- 多渠道消息支持：WhatsApp、Telegram、Slack、Discord、Google Chat、Signal、iMessage、Microsoft Teams、WebChat
- 扩展渠道支持：BlueBubbles、Matrix、Zalo
- 语音交互：支持 macOS、iOS、Android 平台的语音功能
- Canvas 渲染：交互式 UI 界面
- 本地运行：快速、始终在线的 AI 助手
- 多 AI 模型支持：Anthropic Claude、OpenAI GPT

**项目结构**:
- `clawdbot` 和 `moltbot` 包
- 扩展系统
- 技能框架
- 完善的文档系统
- Docker 支持
- macOS 应用打包

**构建系统**: 使用 pnpm workspaces、TypeScript

---

## 2. OpenCode - AI代码助手

**目录**: `opencode/`

**技术栈**: Bun, TypeScript, React

**项目简介**:
开源的 AI 编码助手，帮助开发者更高效地编写代码。

**核心功能**:
- AI 驱动的代码生成和补全
- 多平台支持：Web、桌面、控制台
- 开发工作流集成
- 可扩展的插件架构

**项目结构** (Monorepo):
- `app` - 主应用程序
- `console` - 控制台界面
- `desktop` - 桌面应用
- `web` - Web 界面
- `sdk` - 软件开发工具包
- `slack` - Slack 集成
- `enterprise` - 企业级功能
- `ui` - 共享 UI 组件
- 其他支持包

**国际化**: 支持 14 种语言，包括英语、中文（简/繁）、韩语、德语、西班牙语、法语、日语、俄语、阿拉伯语等

---

## 3. Voice Control Server - ESP32语音控制服务器

**目录**: `voicectl_server/`

**技术栈**: Python, AsyncIO, Flask, WebSocket

**项目简介**:
专为 ESP32 设备设计的语音控制和聊天服务器，提供实时语音通信和控制功能。

**核心功能**:
- WebSocket 服务器：实时通信
- HTTP 服务器：API 端点
- 音频处理管道：集成 VAD（语音活动检测）
- ASR（自动语音识别）功能
- 音频流和录音
- YAML 配置管理
- 性能测试工具

**架构设计**:
- 客户端层：ESP32 和 Web 客户端
- 网络服务层：WebSocket 和 HTTP 服务器
- 核心处理层：连接管理、消息路由、音频处理

**附加组件**:
- 自动重启脚本
- Docker 配置
- 性能测试工具

---

## 4. Email Server - 邮件管理API服务器

**目录**: `email_server/`

**技术栈**: Python, Flask, SQLite, SMTP

**项目简介**:
简单的邮件服务器，提供 API 功能用于管理联系人并发送邮件。

**核心功能**:
- REST API 邮件操作
- SQLite 数据库：联系人管理
- SMTP 集成：邮件发送
- 联系人管理：姓名、职位、邮件跟踪
- 基于环境变量的配置
- 测试工具

**项目结构**:
- Flask 应用程序
- 数据库初始化
- 联系人管理
- 邮件发送功能

---

## 项目关系图

```
DigitalWorker/
├── openclaw/          # AI助手平台 (消息/语音)
├── opencode/          # AI代码助手 (开发工具)
├── voicectl_server/   # 语音控制服务 (ESP32)
└── email_server/      # 邮件管理服务 (API)
```

---

## 技术特点

所有项目都具有以下特点：
- ✅ 结构良好的代码组织
- ✅ 完善的文档和配置文件
- ✅ 现代化的开发实践
- ✅ 容器化支持（Docker）
- ✅ 多语言支持
- ✅ API 设计友好

---

## 应用领域

- **AI/ML**: OpenClaw、OpenCode
- **消息平台**: OpenClaw
- **语音处理**: Voice Control Server、OpenClaw
- **Web 开发**: 所有项目
- **嵌入式系统**: Voice Control Server (ESP32)
- **邮件服务**: Email Server
