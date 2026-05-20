# E2E recovery and GPT-Image provider quirks

Session-derived notes from a real EPUB → dual-host podcast → GPT-Image visual video run.

## Trigger

Use this when an `epub2podcast-local-run --visual-mode gpt-image-slide` run partially succeeds: script + TTS + `full_podcast.mp3` exist, but the pipeline stops before GPT image slides, metadata, manifest, or MP4.

## Durable lessons

### 1. Segment count controls GPT-Image cost

In `--image-density segment`, one script segment becomes one visual frame. To keep GPT-Image generation cost, runtime, and QA surface bounded, strict Chinese smart podcast output should be exactly 18 segments.

Preferred gate shape:

- Accept healthy strict Chinese smart podcast output at exactly 18 segments.
- Reject 19+ segments even if total dialogue length and estimated duration are healthy; ask the model to merge/compress instead.
- Reject genuinely fragmented output by ratio, not by a fixed “more than 1 short segment” rule.
- Keep hard minimums for total characters and duration.
- Add regression tests for healthy 18-segment output and over-limit 19-segment output.

### 2. Object-wrapped OpenRouter responses are normal

OpenRouter text models may return any of these shapes:

```json
{ "script": [...] }
{ "segments": [...] }
{ "podcastScript": [...] }
{ "podcast_script": [...] }
```

Normalize these in parsing code; do not rely only on prompt obedience.

### 3. Avoid Gemini fallback paths

If the project has legacy aliases such as `gemini-3-flash` or `gemini-3-pro`, map them to the current approved model (`deepseek/deepseek-v4-flash`) or remove them. A provider/model 404 is not a reason to revive Gemini in this pipeline.

### 4. If GPT image provider env is missing, recover rather than discard work

The in-project `GptImageProvider` expects `GPT_IMAGE_API_KEY` or `OPENAI_API_KEY`. Hermes may still have a working `image_generate` tool backed by GPT-Image-2 even when those env vars are absent.

Recovery path:

1. Keep the partial delivery directory.
2. Verify `full_podcast.mp3` and `audio_segments/*.mp3` exist.
3. Reconstruct `metadata/script.json` from TTS log lines if the run stopped before metadata write:
   - Parse lines like `[TTSService] Synthesizing segment for Male/Female...`.
   - Extract the following request `text` field.
   - Use `ffprobe` on each `audio_segments/NNN.mp3` to compute durations.
   - Accumulate `startTime` and write script segments with `speaker`, `text`, `startTime`, `estimatedDuration`.
4. Redact secrets from `run.log` before preserving or uploading logs.
5. Generate missing visual frames with Hermes `image_generate` using concise segment-bound prompts.
6. Copy/crop frames into `gpt_image_slides/NNN.png`, then compose MP4 from image durations + `full_podcast.mp3`.

### 5. Redact logs aggressively

TTS request payloads can print credentials such as `token`. Before keeping logs as deliverables or debugging artifacts, replace sensitive fields:

```text
"token": "[REDACTED]"
"appid": "[REDACTED]"   # if needed for external sharing
```

### 6. Keep progress visible on long runs

For long EPUB podcast runs, start the command as a background process and poll logs periodically. The user has explicitly complained about long silent `npm run` / pipeline commands feeling stuck.

## Prompt pattern for manual GPT-Image recovery

Use short, exact text. Long quotes reduce text fidelity.

```text
Create a finished 4:3 editorial cinematic podcast visual frame, target 1440x1080.
Book: 《草原帝国》. Segment 1/18.
Style: black-gold Chinese historical fantasy + serious documentary infographic, high-impact, not PPT.
Scene: <segment-specific visual scene>.
Include ONLY these exact Simplified Chinese texts, no extra words:
1. 《草原帝国》
2. <short frame title>
3. <short thesis line>
No English, no watermark, no logo, no random characters.
```

Do not ask GPT-Image to render long transcript excerpts unless exact text fidelity has been tested for that model/settings combination.
