# Ollama 配置修复记录

**日期**: 2026-02-28
**问题**: 配置本地 Ollama 模型时报错

## 问题描述

在 `openclaw.json` 中配置 Ollama 本地模型时，遇到以下错误：

```
Invalid config at C:\Users\CPC0057\.openclaw\openclaw.json:
- models.providers.ollama.api: Invalid input
```

后续又遇到：
```
No API provider registered for api: undefined
```

以及：
```
400 think value "low" is not supported for this model
```

## 解决方案

### 1. 移除错误的 api 字段值

**错误配置**:
```json
{
  "models": {
    "providers": {
      "ollama": {
        "api": "ollama",  // 错误！
        "apiKey": "ollama-local",
        "baseUrl": "http://10.184.60.127:11434/v1",
        ...
      }
    }
  }
}
```

**正确配置**:
```json
{
  "models": {
    "providers": {
      "ollama": {
        "api": "openai-completions",  // 正确值
        "apiKey": "ollama-local",
        "baseUrl": "http://10.184.60.127:11434/v1",
        ...
      }
    }
  }
}
```

### 2. 修改默认模型

将 `agents.defaults.model.primary` 从 `zai/glm-4.7` 改为 `ollama/qwen3.5:27b`：

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/qwen3.5:27b"
      }
    }
  }
}
```

### 3. 修正 reasoning 设置

qwen3.5 不是推理模型，需要将 `reasoning` 设置为 `false`：

```json
{
  "models": {
    "providers": {
      "ollama": {
        "models": [
          {
            "id": "qwen3.5:27b",
            "name": "qwen3.5:27b",
            "reasoning": false,  // 非推理模型应设为 false
            "input": ["text"],
            "contextWindow": 262144,
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            }
          }
        ]
      }
    }
  }
}
```

## 最终配置示例

```json
{
  "models": {
    "providers": {
      "ollama": {
        "api": "openai-completions",
        "apiKey": "ollama-local",
        "baseUrl": "http://10.184.60.127:11434/v1",
        "models": [
          {
            "id": "qwen3.5:27b",
            "name": "qwen3.5:27b",
            "reasoning": false,
            "input": ["text"],
            "contextWindow": 262144,
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            }
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/qwen3.5:27b"
      }
    }
  }
}
```

## 参考文档

- `/docs/providers/ollama.md` - Ollama 配置详细说明
- `/docs/concepts/model-providers.md` - 模型提供商概览

## 注意事项

1. **api 字段**: Ollama 需要使用 `openai-completions` 作为 api 值
2. **reasoning 字段**: 只有像 deepseek-r1 这类推理模型才应设为 `true`
3. **input 字段**: 确认模型是否真的支持图像输入再添加 `"image"`
4. **本地 vs 远程**: 如果 Ollama 在本地运行，可以使用自动检测模式，无需配置 `models.providers.ollama`
