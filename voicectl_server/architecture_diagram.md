# 小智ESP32语音聊天服务器架构图

## 整体架构概览

```mermaid
graph TB
    subgraph "客户端层"
        ESP32[ESP32设备<br/>客户端]
        WebClient[Web客户端<br/>测试页面]
    end

    subgraph "网络服务层"
        WS[WebSocket服务器<br/>端口:8000]
        HTTP[HTTP服务器<br/>端口:8003]
    end

    subgraph "核心处理层"
        subgraph "连接管理"
            CH[ConnectionHandler<br/>连接处理器]
            Auth[认证中间件]
        end

        subgraph "消息路由"
            TextRoute[文本消息路由]
            AudioRoute[音频消息路由]
        end

        subgraph "音频处理流水线"
            VAD[语音活动检测<br/>VAD]
            ASR[语音识别<br/>ASR]
            Intent[意图识别]
            LLM[大语言模型<br/>LLM]
            TTS[语音合成<br/>TTS]
        end
    end

    subgraph "功能模块层"
        Memory[记忆模块]
        Tools[工具调用模块]
        Plugins[插件系统]
        MCP[MCP集成]
    end

    subgraph "配置与日志"
        Config[配置管理]
        Logger[日志系统]
    end

    subgraph "外部服务"
        API[配置API服务]
        ExternalASR[外部ASR服务]
        ExternalLLM[外部LLM服务]
        ExternalTTS[外部TTS服务]
    end

    %% 连接关系
    ESP32 --> WS
    WebClient --> WS
    WebClient --> HTTP

    WS --> CH
    HTTP --> CH

    CH --> Auth
    CH --> TextRoute
    CH --> AudioRoute

    AudioRoute --> VAD
    VAD --> ASR
    ASR --> Intent
    Intent --> LLM
    LLM --> TTS
    TTS --> ESP32

    TextRoute --> Intent

    CH --> Memory
    CH --> Tools
    CH --> Plugins
    CH --> MCP

    Config --> CH
    Logger --> CH

    ASR --> ExternalASR
    LLM --> ExternalLLM
    TTS --> ExternalTTS

    API --> Config
```

## 详细组件调用流程

### 1. 启动流程
```mermaid
sequenceDiagram
    participant App as app.py
    participant Config as 配置管理
    participant WS as WebSocket服务器
    participant HTTP as HTTP服务器

    App->>Config: load_config()
    App->>WS: WebSocketServer(config)
    App->>HTTP: SimpleHttpServer(config)
    App->>WS: start()
    App->>HTTP: start()
    App->>App: wait_for_exit()
```

### 2. 连接处理流程
```mermaid
sequenceDiagram
    participant Client as 客户端
    participant WS as WebSocket服务器
    participant CH as ConnectionHandler
    participant Auth as 认证中间件
    participant Modules as 模块初始化

    Client->>WS: WebSocket连接请求
    WS->>CH: 创建ConnectionHandler
    CH->>Auth: 认证验证
    Auth-->>CH: 认证结果
    CH->>Modules: 初始化组件(VAD,ASR,LLM,TTS等)
    CH-->>Client: 连接成功响应

    loop 消息处理
        Client->>CH: 发送消息(文本/音频)
        CH->>CH: 路由消息
    end
```

### 3. 音频处理流程
```mermaid
sequenceDiagram
    participant Client as 客户端
    participant CH as ConnectionHandler
    participant VAD as VAD模块
    participant ASR as ASR模块
    participant Intent as 意图识别
    participant LLM as LLM模块
    participant TTS as TTS模块

    Client->>CH: 发送音频数据
    CH->>VAD: 语音活动检测
    VAD-->>CH: 检测结果

    alt 有语音活动
        CH->>ASR: 语音识别
        ASR-->>CH: 识别文本
        CH->>Intent: 意图分析
        Intent-->>CH: 意图结果

        alt 需要LLM处理
            CH->>LLM: 调用大模型
            LLM-->>CH: 生成回复
            CH->>TTS: 语音合成
            TTS-->>Client: 合成音频
        else 意图直接处理
            CH->>Intent: 执行意图动作
            Intent-->>Client: 响应结果
        end
    else 无语音活动
        CH->>CH: 超时检测
    end
```

### 4. 文本处理流程
```mermaid
sequenceDiagram
    participant Client as 客户端
    participant CH as ConnectionHandler
    participant Intent as 意图识别
    participant LLM as LLM模块
    participant TTS as TTS模块

    Client->>CH: 发送文本消息
    CH->>Intent: 意图分析
    Intent-->>CH: 意图结果

    alt 需要LLM处理
        CH->>LLM: 调用大模型
        LLM-->>CH: 生成回复
        CH->>TTS: 语音合成
        TTS-->>Client: 合成音频
    else 意图直接处理
        CH->>Intent: 执行意图动作
        Intent-->>Client: 响应结果
    end
```

## 核心模块说明

### 1. 主程序 (app.py)
- **功能**: 服务器入口点，启动WebSocket和HTTP服务
- **关键组件**:
  - WebSocketServer: 处理语音聊天连接
  - SimpleHttpServer: 提供OTA和视觉分析接口
  - 配置加载和初始化

### 2. WebSocket服务器 (websocket_server.py)
- **功能**: 管理WebSocket连接，处理客户端连接请求
- **关键特性**:
  - 支持多客户端并发连接
  - 动态配置更新
  - 连接生命周期管理

### 3. 连接处理器 (connection.py)
- **功能**: 处理单个客户端的完整会话生命周期
- **核心组件**:
  - 认证中间件
  - 模块初始化(VAD, ASR, LLM, TTS, Memory, Intent)
  - 消息路由
  - 资源管理

### 4. 音频处理模块
- **VAD (Voice Activity Detection)**: 语音活动检测，识别用户是否在说话
- **ASR (Automatic Speech Recognition)**: 语音转文本，支持多种服务提供商
- **TTS (Text-to-Speech)**: 文本转语音，支持多种服务提供商

### 5. 智能处理模块
- **LLM (Large Language Model)**: 大语言模型，生成智能回复
- **Intent Recognition**: 意图识别，理解用户意图
- **Memory**: 对话记忆管理
- **Tools**: 工具调用系统

### 6. 插件系统
- **位置**: `plugins_func/functions/`
- **功能**: 扩展功能模块，如天气查询、音乐播放等
- **机制**: 自动导入和注册

### 7. 配置管理
- **配置文件**: `config.yaml`
- **功能**: 模块选择、API密钥管理、参数配置
- **特性**: 支持动态配置更新

## 数据流总结

1. **输入流**: 客户端音频/文本 → WebSocket → ConnectionHandler → 路由处理
2. **音频处理流**: VAD检测 → ASR识别 → 意图分析 → LLM处理 → TTS合成
3. **文本处理流**: 意图分析 → LLM处理 → TTS合成
4. **输出流**: TTS音频 → WebSocket → 客户端播放

这个架构设计支持高度模块化，每个组件都可以独立配置和替换，支持多种外部服务集成，具有良好的扩展性和维护性。