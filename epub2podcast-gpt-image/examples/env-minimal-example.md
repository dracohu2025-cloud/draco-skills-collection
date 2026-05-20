# Minimal `.env` Example

下面是一个最小配置思路，用于说明第一次运行时通常至少需要哪些变量。

> 注意：这里是说明模板，不包含任何真实密钥。

```env
# Text generation
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_TEXT=google/gemini-3-flash-preview

# Volcengine TTS
VOLCENGINE_ACCESS_TOKEN=your_volcengine_access_token
VOLCENGINE_APP_ID=your_volcengine_app_id
VOLCENGINE_VOICE_ID_MALE=zh_male_dayi_saturn_bigtts
VOLCENGINE_VOICE_ID_FEMALE=zh_female_mizai_saturn_bigtts
VOLCENGINE_RESOURCE_ID=seed-tts-2.0

# Optional overrides
PPT_HTML_MODEL=google/gemini-3-flash-preview
TTS_MODEL=gemini-2.5-flash-preview-tts
```

如果你只想先跑通一遍主流程，优先确保这些变量可用：

- `OPENROUTER_API_KEY`
- `VOLCENGINE_ACCESS_TOKEN`
- `VOLCENGINE_APP_ID`
- `VOLCENGINE_VOICE_ID_MALE`
- `VOLCENGINE_VOICE_ID_FEMALE`
