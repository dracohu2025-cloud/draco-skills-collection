# Manim + Volcengine TTS Video Pipeline

A production-ready pipeline for creating Manim mathematical explainer videos with synchronized Chinese voiceover. Inspired by 3Blue1Brown, optimized for Chinese TTS integration.

## What It Does

```
PLAN → TTS → CODE → DRAFT → PRODUCTION → STITCH → MUX → DELIVER
```

Transforms a mathematical concept into a narrated explainer video with frame-perfect audio-visual synchronization.

## Quick Start

### 1. Plan Your Video

```bash
cp templates/plan.md my-project/plan.md
# Fill in your narrative, voiceover script, and color palette
```

### 2. Generate TTS Audio

```bash
python3 scripts/tts_measure.py --input my-project/plan.md --outdir ./audio --voice female
# Outputs: audio/s01.mp3 ~ sNN.mp3 + manifest.json with exact durations
```

### 3. Write Manim Code

```bash
cp templates/script.py my-project/script.py
# Fill in template placeholders, set run_time/wait to match audio durations
```

### 4. Draft Render (480p15, fast)

```bash
manim -ql my-project/script.py S1_Title S2_...
# Verify timing with ffprobe
```

### 5. Production Render (1080p60)

```bash
manim -qh my-project/script.py S1_Title S2_...
```

### 6. Stitch & Mux

```bash
python3 scripts/stitch_mux.py --scenes 7 --quality 1080p60 --out final.mp4
```

### 7. Deliver

```bash
cp final.mp4 /var/www/hermes.aigc.green/media/my-video.mp4
lark-cli drive +upload --file ./final.mp4 --name "My Video.mp4"
```

## Example: Taylor Expansion of Sine

See the showcase video that demonstrates this pipeline end-to-end:
- **Topic**: Why `sin(x) ≈ x - x³/6 + x⁵/120 - ...`
- **Duration**: ~48s (adult) / ~59s (kids)
- **Resolution**: 1920×1080 @ 60fps
- **TTS**: Volcengine female Chinese voice

## Directory Structure

```
.
├── SKILL.md                 # Full skill documentation
├── README.md                # This file
├── scripts/
│   ├── tts_measure.py       # Generate TTS + measure durations
│   └── stitch_mux.py        # Stitch scenes + mux audio
└── templates/
    ├── plan.md              # Plan template
    └── script.py            # Manim script template
```

## Requirements

- Python 3.10+, Manim Community v0.20+
- ffmpeg
- Volcengine TTS CLI (`volc-tts`)
- lark-cli (for Feishu upload)
- Web server directory (for HTTPS links)

## License

MIT
