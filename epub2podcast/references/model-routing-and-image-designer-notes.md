# Model routing and image_designer notes

Session learning from GPT-Image-2 visual-mode prototyping and model migration.

## Default text/PPT model

Use OpenRouter model ID:

```text
deepseek/deepseek-v4-flash
```

Local CLI shorthand:

```text
deepseek-v4-flash
```

Legacy `gemini-3-flash` configs may be accepted only as a compatibility alias, but should resolve to `deepseek/deepseek-v4-flash` in optimized local runs.

## Responsibility split

Do not describe EPUB parsing as LLM reading.

| Layer | Responsibility |
|---|---|
| EPUB/PDF/MOBI parser | Extract book text, chapters, metadata, cover; no semantic creation |
| `scriptService.generateScript(...)` | LLM reads extracted book content and writes 18-22 dual-host TTS segments |
| TTS provider | Synthesizes segment text only; no content design |
| `image_designer` | LLM reads each script segment and creates visual strategy + GPT-Image-2 prompt |
| `image_generate` / GPT-Image-2 | Generates full visual page from prompt |
| QA/retry | Checks exact Chinese text, topical binding, visual quality; retries with forbidden wrong text when needed |

## image_designer should be LLM-driven

The GPT-Image-2 prompt should not be a fixed template with blind string interpolation. It should be produced by an LLM-driven `image_designer` module that receives:

- book title and optional style bible
- segment index / total segments
- segment text
- speaker
- estimated duration
- neighboring context when useful

It outputs a structured frame spec and final image prompt:

```json
{
  "segmentIndex": 4,
  "strategy": "knowledge-comic",
  "title": "...",
  "requiredText": ["..."],
  "visualHook": "...",
  "prompt": "..."
}
```

## Prompt QA rule

For Chinese text in GPT-Image-2 outputs:

1. Prompt must include `Include ONLY these exact Simplified Chinese texts`.
2. QA must compare generated visible text against `requiredText`.
3. If the model writes plausible-but-wrong text, retry with explicit `forbidden wrong text` lines.
4. Do not batch-integrate a visual style until 3-5 representative samples pass QA.

## Operational note

When changing default models, update all three surfaces together:

1. runtime code (`localPipeline.ts`, `worker.ts`, server defaults)
2. built output via `npm run build`
3. skill docs/examples so future runs do not silently use stale model IDs
