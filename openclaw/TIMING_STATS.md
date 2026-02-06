# 响应时间统计功能

## 功能概述

为 OpenClaw 添加了详细的响应时间统计功能，帮助分析每次 Agent 回复的性能瓶颈。

## 添加的时间统计

### 1. 用户可见的统计信息

在每次 Agent 回复后，会显示以下统计信息：

```
⏱️  Duration: 15.234s | 📦 Model: anthropic/claude-sonnet-4-5-20250514 | 📊 Tokens: 12,456 (819.2 t/s)
```

**包含的信息：**
- **Duration**: 总响应时间（自动格式化为 ms/s/min）
- **Model**: 使用的模型（provider/model）
- **Tokens**: Token 使用情况和吞吐量
  - 总 token 数
  - 每秒 token 数（tokens/second）
  - 缓存命中（如果有）

### 2. 开发者调试日志

在 debug 模式下，会记录详细的时间标记：

```
[agent/embedded] [TIMING] init: +5ms
[agent/embedded] [TIMING] session_ready: +234ms
[agent/embedded] [TIMING] prompt_start: +512ms
[agent/embedded] [TIMING] prompt_complete: +12,456ms
[agent/embedded] [TIMING] complete: +15,234ms
```

**时间标记说明：**
- `init`: 初始化阶段
- `session_ready`: 会话准备完成
- `prompt_start`: 开始发送提示词到 API
- `prompt_complete`: API 返回完成
- `complete`: 整个请求处理完成

## 修改的文件

### 1. `src/commands/agent/delivery.ts`

**添加的功能：**
- `formatDuration()`: 格式化时间显示（ms/s/min）
- `formatTimingStats()`: 生成时间统计信息

**修改内容：**
- 导入 `shouldLogVerbose` 用于控制显示
- 在输出 payload 后显示统计信息
- 即使没有回复也显示时间统计（在 verbose 模式下）

### 2. `src/agents/pi-embedded-runner/run/attempt.ts`

**添加的功能：**
- 时间跟踪变量 (`timingStart`, `timingMarkers`)
- `logTiming()`: 记录时间标记的辅助函数

**修改内容：**
- 在关键阶段添加时间标记：
  - 初始化完成
  - 会话准备完成
  - 提示词发送开始
  - 提示词完成
  - 整个流程完成
- 所有时间标记通过 debug 日志输出

## 使用方法

### 正常使用

默认情况下，时间统计会显示在每次 Agent 回复后：

```cmd
node openclaw.mjs agent --agent main --message "你好"
```

输出示例：
```
你好！有什么我可以帮助你的吗？

⏱️  Duration: 3.456s | 📦 Model: anthropic/claude-sonnet-4-5-20250514 | 📊 Tokens: 856 (247.6 t/s)
```

### 开发调试模式

启用 verbose 模式查看详细的时间标记：

```cmd
OPENCLAW_VERBOSE=1 node openclaw.mjs agent --agent main --message "测试"
```

### 分析性能瓶颈

通过时间标记可以识别瓶颈：

1. **init 时间长** → 工作空间加载或文件系统问题
2. **session_ready 时间长** → 会话恢复或历史记录加载问题
3. **prompt_start 到 prompt_complete** → API 响应时间（网络或模型处理）
4. **prompt_complete 到 complete** → 响应后处理时间

## 性能优化建议

根据时间统计，可以针对性优化：

### 如果 init 阶段慢
- 检查工作空间大小
- 考虑使用 SSD
- 清理不必要的文件

### 如果 session_ready 阶段慢
- 减少历史记录长度
- 使用 context pruning
- 考虑使用 cache-ttl 模式

### 如果 API 调用慢（prompt_start 到 prompt_complete）
- 检查网络连接
- 考虑使用更快的模型
- 启用缓存（如果适用）
- 检查 API provider 状态

### 如果响应处理慢（prompt_complete 到 complete）
- 检查是否有大量工具调用
- 优化工具执行效率
- 减少不必要的后处理

## 示例输出

### 快速响应（< 1s）
```
⏱️  Duration: 567ms | 📦 Model: anthropic/claude-sonnet-4-5-20250514 | 📊 Tokens: 234 (412.7 t/s)
```

### 中等响应（1-10s）
```
⏱️  Duration: 5.234s | 📦 Model: anthropic/claude-sonnet-4-5-20250514 | 📊 Tokens: 4,521 (863.7 t/s)
```

### 慢响应（> 10s）
```
⏱️  Duration: 23.456s | 📦 Model: anthropic/claude-opus-4-5-20250514 | 📊 Tokens: 15,234 (649.2 t/s)
```

### 带缓存的响应
```
⏱️  Duration: 1.234s | 📦 Model: anthropic/claude-sonnet-4-5-20250514 | 📊 Tokens: 8,456 (6,853.0 t/s, cache: 4096)
```

## 配置选项

### 禁用时间显示

如果不需要时间统计，可以通过环境变量控制：

```cmd
# 只在 verbose 模式显示
OPENCLAW_VERBOSE=0 node openclaw.mjs agent --agent main --message "test"
```

### JSON 模式

在 JSON 模式下，时间信息包含在 meta 字段中：

```cmd
node openclaw.mjs agent --agent main --message "test" --json
```

输出：
```json
{
  "payloads": [...],
  "meta": {
    "durationMs": 5678,
    "agentMeta": {
      "sessionId": "...",
      "provider": "anthropic",
      "model": "claude-sonnet-4-5-20250514",
      "usage": {
        "input": 1234,
        "output": 567,
        "total": 1801
      }
    }
  }
}
```

## 实现细节

### 时间格式化

```typescript
function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  const seconds = Math.floor(ms / 1000);
  const milliseconds = ms % 1000;
  if (seconds < 60) {
    return `${seconds}.${milliseconds.toString().padStart(3, '0')}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}
```

### Token 吞吐量计算

```typescript
const tokensPerSec = (totalTokens / (durationMs / 1000)).toFixed(1);
```

### 缓存处理

缓存读取和写入会被单独显示：
```
(cache: R:4096)  - 只读取缓存
(cache: W:512)   - 只写入缓存
(cache: R:2048 W:1024) - 读写都有
```

## 故障排除

### 时间统计不显示

**原因**: 可能在非交互模式或某些通道下

**解决**: 使用 `OPENCLAW_VERBOSE=1` 启用详细日志

### Token 数量为 0 或不显示

**原因**:
1. 某些 provider 不返回 token 使用情况
2. CLI 模式下可能不统计

**解决**: 这是正常的，不同 provider 有不同的行为

### 时间明显比预期长

**检查步骤**:
1. 启用 verbose 模式查看详细时间标记
2. 检查网络连接
3. 查看日志中的 `[TIMING]` 标记找出瓶颈阶段
4. 根据瓶颈阶段进行针对性优化

## 相关文件

- `src/commands/agent/delivery.ts` - 用户可见的时间统计
- `src/agents/pi-embedded-runner/run/attempt.ts` - 开发者调试时间标记
- `src/agents/pi-embedded-runner/types.ts` - 类型定义

## 未来改进

可能的增强功能：
1. [ ] 添加历史响应时间图表
2. [ ] 按模型/通道分组统计
3. [ ] 告警机制（超过阈值时警告）
4. [ ] 导出时间统计数据
5. [ ] 与性能监控工具集成

---

**添加日期**: 2026-02-06
**版本**: 2026.1.30+
**状态**: ✅ 已实现并测试
