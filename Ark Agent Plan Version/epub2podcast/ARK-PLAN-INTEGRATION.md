# Ark Agent Plan 集成指南

## 概述

本版本的 `epub2podcast` 已完全适配 Ark Agent Plan 的火山引擎技术栈，与 Seedream/Seedance 共享同一套认证体系。

---

## 🔑 统一认证配置

### 环境变量

只需配置这两个环境变量，即可同时支持：
- ✅ 火山引擎 TTS（本项目）
- ✅ Seedream 图片生成
- ✅ Seedance 视频生成

```bash
VOLCENGINE_ACCESS_TOKEN=your_token_here
VOLCENGINE_TTS_APP_ID=your_app_id_here
```

### 与其他 Skills 的兼容性

| Skill | 复用的认证 |
|---|---|
| `article-to-wechat-cover` | `VOLCENGINE_ACCESS_TOKEN` → Seedream |
| `feishu-seedance-video-pipeline` | `VOLCENGINE_ACCESS_TOKEN` → Seedance |
| `epub2podcast` | `VOLCENGINE_ACCESS_TOKEN` → 火山 TTS + Seedream |

---

## 🔧 原生工具集成（可选）

### 火山引擎 TTS 工具

如果需要将 TTS 作为 Agent Plan 的原生工具（与 `byted-seedream-image-generate` 类似），可以按以下方式集成：

```typescript
// 工具定义示例：byted-volcengine-tts
{
  name: "byted-volcengine-tts",
  description: "火山引擎 TTS 文本转语音，与 Seedream/Seedance 共享认证",
  parameters: {
    text: "要合成的文本",
    voice: "音色 ID（zh_male_dayi_saturn_bigtts / zh_female_mizai_saturn_bigtts）",
    format: "输出格式（mp3/wav）",
    speed: "语速（0.5-2.0）"
  }
}
```

### Skill 中的调用方式

`epub2podcast` 已内置支持原生工具调用：

```typescript
// 设置环境变量启用原生调用
process.env.AGENT_PLAN_NATIVE_TTS = 'true'

// TTS 服务会自动优先尝试原生工具调用
// 失败时自动 fallback 到直接 API 调用
```

---

## 📦 完整技术栈统一

| 能力 | 服务 | 状态 |
|---|---|---|
| LLM 文本生成 | 豆包大模型 | ✅ 已配置默认 |
| TTS 语音合成 | 火山引擎 TTS | ✅ 已设为默认 |
| 图片生成 | Seedream | ✅ 已配置默认 |
| 视频生成 | Seedance | ✅ 与其他 skill 共享 |

---

## 🚀 快速开始

1. 复制 `.env.example` 为 `.env`
2. 填入你的火山引擎认证信息（与 Seedream/Seedance 相同）
3. 运行：`npm install && npm run build`
4. 测试：`node dist/cli/run.js --epub example.epub`

---

## 📝 注意事项

1. **无需额外 API Key**：TTS 使用与 Seedream/Seedance 相同的火山引擎认证
2. **自动 Fallback**：原生工具调用失败时，自动降级为直接 API 调用
3. **中文优先**：默认音色均为中文播客优化
4. **成本控制**：火山引擎 TTS 成本低于 ElevenLabs/Gemini

---

## 🔗 相关 Skills

- `feishu-seedance-video-pipeline` - 视频产线（同一技术栈）
- `article-to-wechat-cover` - 公众号封面（同一技术栈）
- `vocabulary-video-pipeline` - 单词视频（同一技术栈）
