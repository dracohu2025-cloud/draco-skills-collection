# OpenRouter script generation pitfalls

Session finding from E2E test with 《草原帝国：阿提拉、成吉思汗与帖木儿》.

## Context

The optimized local pipeline parsed the EPUB successfully:

- 26 chapters
- ~439k source characters/words reported by parser
- cover extraction worked
- local asset server worked

The run failed before TTS/image generation, inside script generation validation.

## Pitfall 1: model returns object-wrapped JSON

DeepSeek via OpenRouter may obey JSON mode but return an object wrapper instead of a top-level array, e.g.

```json
{
  "script": [
    { "speaker": "Male", "text": "...", "visualPrompt": null }
  ]
}
```

Old behavior accepted only a top-level JSON array and failed with:

```text
Invalid script: expected array with 10+ segments, got object
```

Durable fix pattern:

- Keep top-level array support.
- Also unwrap common keys: `script`, `segments`, `podcastScript`, `podcast_script`.
- If wrapper exists but value is not an array, fail loudly.
- Add a regression test for response normalization.

## Pitfall 2: DeepSeek may over-segment while meeting length/quality goals

In this session DeepSeek repeatedly generated 24-26 segments. The strict gate required max 22 segments, so all attempts failed even though dialogue density and estimated duration were acceptable:

```text
segments=24, chars=4506, estDuration=901.2s
segment count 24 > maximum 22
```

Practical gate recommendation:

- Keep strict minimums for spoken length and estimated duration.
- For Chinese smart-podcast mode, allow minor segment overshoot, e.g. up to 24, when total chars and duration pass.
- Reject extreme over-segmentation or many very short segments.
- Prefer a regression test that 24 healthy Chinese segments pass, but short/noisy 24-segment output still fails.

## Pitfall 3: model aliases can rot

`--text-model gemini-3-pro` mapped to `google/gemini-3-pro-preview`, which returned:

```text
No endpoints found for google/gemini-3-pro-preview
```

Do not hard-code trust in legacy model aliases. Before switching models to unblock E2E, verify the provider endpoint still exists, or use the project’s configured default.

## E2E operating note

For long runs, start the command in the background with completion notification and poll/log periodically. This matches the user's preference: avoid long silent runs.
