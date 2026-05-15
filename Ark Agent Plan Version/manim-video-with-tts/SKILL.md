---
name: manim-video-with-tts
description: "End-to-end production pipeline for Manim mathematical explainer videos with Volcengine TTS narration. Plan → TTS → Code → Render → Stitch → Deliver. Use when users want: Manim animation + Chinese voiceover, math concept video with synchronized narration, 3Blue1Brown-style explainer with TTS, or any programmatic animation requiring precise audio-visual sync."
version: 1.0.0
---

# Manim + Volcengine TTS Showcase Pipeline

## Trigger Conditions

Use this skill when the user requests:
- Manim animation **with** Chinese voiceover / narration
- Math/tech explainer video where **audio timing must match visuals**
- "用 Manim 做解释视频，并加上中文旁白"
- "确保语音和画面节奏匹配"
- 3Blue1Brown-style video with TTS integration

## Pipeline Overview

```
PLAN → TTS → CODE → DRAFT → PRODUCTION → STITCH → MUX → DELIVER
```

| Step | Tool | Output |
|------|------|--------|
| 1. Plan | Markdown | `plan.md` — narrative arc, scene breakdown, voiceover script, color palette |
| 2. TTS | Volcengine TTS | `audio/s01.mp3` ~ `sNN.mp3` + duration manifest |
| 3. Code | Manim CE | `script.py` — one class per scene, run_times synced to audio |
| 4. Draft | `manim -ql` | 480p15 preview clips for rhythm verification |
| 5. Production | `manim -qh` | 1080p60 final scene clips |
| 6. Stitch | ffmpeg concat | `video_pro.mp4` — seamless scene assembly |
| 7. Mux | ffmpeg | `final.mp4` — video + narration mixed |
| 8. Deliver | lark-cli + web | Feishu Drive link + HTTPS direct link |

## Prerequisites

- Python 3.10+, Manim Community v0.20+
- ffmpeg
- Volcengine TTS credentials (`VOLCENGINE_TTS_ACCESS_TOKEN`, `VOLCENGINE_TTS_APP_ID`, `VOLCENGINE_TTS_VOICE_TYPE_*`)
- lark-cli for Feishu upload
- Web server directory `/var/www/hermes.aigc.green/media/`

## Step 1: Plan

Write `plan.md` **before any code**. Include:

1. **Narrative Arc**: Core question → Aha moment → Emotional curve
2. **Scene Breakdown**: One table row per scene with timing, visuals, animation type
3. **Voiceover Script**: Chinese text per scene, with estimated character count
4. **Color Palette**: Background, target curve, approximation, text, accent, grid
5. **Typography**: Monospace font only (FreeMono/DejaVu Sans Mono), minimum size 18

**Rule**: Scene count = audio segment count. Each scene gets exactly one TTS clip.

## Step 2: Generate TTS & Measure Durations

Generate one MP3 per scene using Volcengine TTS:

```bash
volc-tts --text '第N段旁白' --voice female --output ./audio/s0N.mp3
```

Then measure exact durations:

```bash
for f in audio/*.mp3; do
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  echo "$f: ${dur}s"
done
```

Record these durations — they are the **master clock** for all Manim timing.

## Step 3: Write Manim Code

### Sync Strategy: Audio-Driven Timing

Since Manim does **not** natively support Volcengine TTS, use the manual sync approach:

```python
# In each Scene.construct(), the sum of:
#   all run_time values + all self.wait() values
# must equal the corresponding audio clip duration.
```

### Cross-Scene Continuity

To avoid rebuilding axes/curves every scene (wasting precious audio time):

```python
class S3_NextScene(Scene):
    def construct(self):
        self.camera.background_color = BG
        axes = Axes(...)
        sin_curve = axes.plot(...)
        prev_curve = axes.plot(...)
        
        # Carry over from previous scene — instant, costs 0s
        self.add(axes, sin_curve, prev_curve)
        
        # Only animate NEW elements
        self.play(ReplacementTransform(prev_curve, next_curve), run_time=2.0)
        self.wait(...)
        # ...
```

**Critical**: The last frame of Scene N must match the first frame of Scene N+1 for seamless ffmpeg concatenation. If Scene N fades out an element, Scene N+1 must not `self.add()` it.

### Duration Budgeting Template

For a scene with audio duration `D`:

```
D = Σ(run_times) + Σ(waits)
```

Recommended allocation:
- Title/text appearance: 0.8–1.2s
- Curve drawing/creation: 1.5–2.5s
- Transform/morph: 1.5–2.0s
- Formula writing: 0.8–1.0s
- Indicator/effect: 0.5–0.8s
- FadeOut cleanup: 0.3–0.5s
- Breathing waits: distribute remainder

### Color Constants (High-Contrast Showcase)

```python
BG          = "#0A0A0F"      # deep void black
SIN_COLOR   = "#FF4D4D"      # coral red — target curve
APPROX_COLOR= "#00F5FF"      # electric cyan — approximation
TEXT_COLOR  = "#FFFFFF"      # pure white
ACCENT      = "#FFD93D"      # golden yellow
GRID_COLOR  = "#2A2A3A"      # dim purple-grey
MONO        = "FreeMono"     # or "DejaVu Sans Mono"
```

## Step 4: Draft Render

```bash
manim -ql script.py Scene1 Scene2 Scene3 ...
```

Verify each clip duration matches audio:

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 media/videos/script/480p15/Scene1.mp4
```

If mismatch > 0.1s, adjust `run_time` or `self.wait()` in code and re-render.

## Step 5: Production Render

```bash
manim -qh script.py Scene1 Scene2 Scene3 ...
```

## Step 6: Stitch & Mux

```bash
# Video concat
cat > concat_video.txt << 'EOF'
file 'media/videos/script/1080p60/Scene1.mp4'
file 'media/videos/script/1080p60/Scene2.mp4'
...
EOF
ffmpeg -y -f concat -safe 0 -i concat_video.txt -c copy video_pro.mp4

# Audio concat
cat > concat_audio.txt << 'EOF'
file 'audio/s01.mp3'
file 'audio/s02.mp3'
...
EOF
ffmpeg -y -f concat -safe 0 -i concat_audio.txt -c copy audio_full.mp3

# Mux
ffmpeg -y -i video_pro.mp4 -i audio_full.mp3 -c:v copy -c:a aac -b:a 192k final.mp4
```

## Step 7: Deliver

### Web Server (Primary Link)

```bash
cp final.mp4 /var/www/hermes.aigc.green/media/<filename>.mp4
# URL: https://hermes.aigc.green/media/<filename>.mp4
```

### Feishu Drive (Backup)

```bash
cd <project-dir>
lark-cli drive +upload --file ./final.mp4 --name "<Title>.mp4"
lark-cli drive metas batch_query --data '{"request_docs":[{"doc_token":"<TOKEN>","doc_type":"file"}],"with_url":true}'
```

Extract `url` from response for Feishu direct link.

## Performance Targets

| Stage | Resolution | FPS | Typical Speed |
|-------|-----------|-----|---------------|
| Draft (`-ql`) | 854×480 | 15 | 5–15s/scene |
| Production (`-qh`) | 1920×1080 | 60 | 30–120s/scene |

## Audience Adaptation: Two Dimensions

When adapting a technical explainer, distinguish two **independent** dimensions:
1. **Audience age**: Adult → Kids (cognitive complexity)
2. **Locale**: Global English → China-localized (language & cultural context)

These require separate rewrites. Do not try to make one version serve both purposes.

### Dimension 1: Age Adaptation (Kids vs Adult)

When adapting for younger audiences (elementary/middle school), **do not tweak—rewrite entirely**. The kids version requires new plan, new script, new TTS, and new code.

| Aspect | Technical (Adult) | Kids/Student |
|--------|-------------------|--------------|
| **Narrative hook** | "泰勒展开" / "Taylor Expansion" | "计算器是怎么算出来的？" |
| **Central metaphor** | Mathematical approximation | **Building blocks** (积木) |
| **Character naming** | "目标曲线" / "逼近曲线" | **小红 & 小蓝** (give curves personalities) |
| **Pace** | Tight, efficient | +20-30% duration, longer pauses between concepts |
| **Language** | Technical terms (derivative, order, convergence) | Shape, slope, bend, "pretend", "looks like" |
| **Voice** | Neutral | **Female voice** (perceived as more approachable) |
| **Colors** | High-contrast electric | **Softer, friendlier** palette |

**Kids-Optimized Color Palette**:
```python
BG          = "#0D1117"      # deep void (same)
SIN_COLOR   = "#FF6B6B"      # coral red — warmer, less aggressive
APPROX_COLOR= "#4ECDC4"      # mint cyan — softer than electric
TEXT_COLOR  = "#F0F6FC"      # off-white, easier on eyes
ACCENT      = "#FFE66D"      # golden yellow — magic/block highlights
GRID_COLOR  = "#30363D"      # dim grey
MONO        = "FreeMono"
```

**Kids Script Guidelines**:
- "展开" / "expansion" → "搭积木" (building blocks)
- "阶数" / "order" → "第几块积木" (which block)
- "导数" / "derivative" → "斜率" (slope) or "弯的程度" (how much it bends)
- "收敛" / "convergence" → "越来越像" (more and more alike)
- "假装" (pretend) — the straight line is "pretending" to be the curve
- "骗过眼睛" (fool the eye) — technical accuracy achieved through deception
- "双胞胎" (twins) — when two curves become indistinguishable
- "弯腰" (bend at the waist) — cubic term makes the line "bend"

**Timing Adjustments for Kids**:
```python
# Adult version
self.wait(0.3)  # between phrases

# Kids version  
self.wait(0.5)  # longer breathing room
```
Add **suspense pauses** before reveals: `self.wait(1.0)` before "Here's the secret..."

### Dimension 2: China Localization (中英双语注释)

When the audience is **Chinese students**, apply the **Bilingual Annotation Principle**:

> **Every English mathematical term must appear with its Chinese equivalent on first use.**

This applies to **both narration and on-screen text**.

#### Bilingual Annotation Rules

| Rule | Example | Bad | Good |
|------|---------|-----|------|
| **Narration**: Chinese first, then English in parentheses | sine | "sine" | "正弦（sine）" |
| **Narration**: Read formulas in Chinese, not symbols | y=x | "y equals x" | "y 等于 x（y=x）" |
| **Narration**: Describe operations in Chinese | x³/6 | "x cubed over six" | "x 的立方除以六" |
| **On-screen labels**: 100% Chinese | title | "Math Magic" | "数学的魔法" |
| **On-screen labels**: Chinese with English sub-label | formula label | "good fit!" | "很像！" |
| **Math formulas**: Keep standard notation on screen | y=x | Remove formula | Keep `y=x` on screen, but narration says "y 等于 x" |

**Critical**: The mathematical notation (MathTex) on screen should **never** be removed or translated. The formula `y = x`, `x - x³/6`, etc. must remain in standard mathematical notation. Only the **narration** and **text labels** are localized.

#### China-Localized On-Screen Text Mapping

| English Label | 中文标签 | Notes |
|---------------|---------|-------|
| Math Magic | 数学的魔法 | Title |
| How does a calculator know sine? | 计算器是怎么算出正弦的？ | Hook question |
| 小红 | 小红 | Character name (keep simple) |
| Let's pretend with a straight line! | 用直线来假装！ | Subtitle |
| Add a magic block! | 加一块魔法积木！ | Subtitle |
| good fit! | 很像！ | Region label |
| much better! | 更像了！ | Region label |
| Another block! | 再加一块！ | Subtitle |
| Here's the secret... | 秘密在这里... | Subtitle |
| shape, slope, bend | 形状、斜率、弯曲度 | Concept text |
| Infinite simple blocks | 无限个简单积木 | Closing text |
| building something complex & beautiful | 搭出复杂又美丽的东西 | Closing text |

#### Three-Version Iteration Pattern

In practice, producing a China-localized kids version requires **three iterations**:

| Version | Language | Labels | Audience |
|---------|----------|--------|----------|
| V1: Adult Technical | English terms, English labels | English | Global adult |
| V2: Generic Kids | English terms, mixed labels | English/Chinese | International kids |
| **V3: China-localized Kids** | **Chinese + bilingual annotations** | **100% Chinese** | **Chinese students** |

**Workflow for V3**:
```bash
# 1. Create entirely new plan (do not reuse V1/V2 plan)
cat > plan-kids-cn.md << 'EOF'
## Audience: Chinese Elementary/Early Middle School
## Principle: Bilingual annotation (Chinese first, English in parens)
## Labels: 100% Chinese
## Voice: Female Chinese TTS
EOF

# 2. Write Chinese narration with bilingual annotations
# Example: "你有没有想过，计算器是怎么算出正弦（sine）的？"

# 3. Generate TTS with female voice
volc-tts --text '...' --voice female --output ./audio-kids-cn/s01.mp3

# 4. Create new script file with Chinese labels
# script-kids-cn.py — all Text() objects use Chinese strings

# 5. Render, stitch, deliver separately
```

#### Example: China-Localized Script Evolution

| Scene | V1 Adult (EN) | V2 Kids (Mixed) | **V3 China Kids (CN+EN)** |
|-------|--------------|-----------------|---------------------------|
| S1 | "sin x Maclaurin expansion" | "How does a calculator know sine?" | "你有没有想过，计算器是怎么算出**正弦（sine）**的？" |
| S3 | "First order gives tangent y=x" | "y=x fools the eye!" | "**y 等于 x（y=x）**，居然在中心骗过了眼睛！" |
| S4 | "Introduce cubic correction -x³/6" | "Add a block: x³/6" | "数学家加了一块积木：**减去 x 的立方除以六**" |
| S6 | "Match derivatives at zero" | "Shape and slope match" | "**形状、斜率、弯曲程度**，都和小红一模一样！" |

#### Pitfall: Symbol Reading in Chinese TTS

Chinese TTS cannot naturally read mathematical symbols. **Never** write:
- ❌ `volc-tts --text 'x³/6'` — TTS will say random characters or fail
- ❌ `volc-tts --text 'y=x'` — TTS may read as "y dengyu x" (awkward)

**Always** write the spoken Chinese description:
- ✅ `volc-tts --text '减去 x 的立方除以六'` — natural Chinese
- ✅ `volc-tts --text 'y 等于 x'` — natural Chinese

The **screen** still shows `x - x³/6` and `y=x` via MathTex. The narration describes them in Chinese. This dual-channel approach (visual: standard notation, audio: Chinese description) is the core of bilingual annotation.

### Workflow for Kids Version

```bash
# 1. Save adult plan as baseline
cp plan.md plan-adult.md

# 2. Create entirely new plan
cat > plan-kids.md << 'EOF'
# Math Magic: How Calculators Know Sine
## Audience: Elementary/Early Middle School
## Metaphor: Building Blocks
## Characters: 小红 (target), 小蓝 (building)
EOF

# 3. Generate new TTS with female voice
volc-tts --text '...' --voice female --output ./audio-kids/s01.mp3

# 4. Create new script file (do not reuse adult script)
# script-kids.py with adjusted timings and softer colors

# 5. Render, stitch, deliver separately from adult version
```

## Critical Pitfalls

1. **Font not found**: Always use `FreeMono` or `DejaVu Sans Mono`. `Menlo` is macOS-only.
2. **SurroundingRectangle on point**: `SurroundingRectangle` requires a Mobject, not a coordinate. Use `Rectangle(...).move_to(point)` instead.
3. **Frame quantization at 15fps**: Draft (`-ql`) can have up to ~0.07s timing drift per animation. Production (`-qh`) at 60fps reduces this to ~0.017s.
4. **Audio shorter than video**: If sum(video) > sum(audio), the final clip will have silent tail. Acceptable if < 0.5s. If larger, trim video with ffmpeg or adjust waits.
5. **Scene transition flash**: If Scene N fades out elements that Scene N+1 `self.add()`s, ensure the last frame of N matches the first frame of N+1. Otherwise a "flash" occurs at the stitch point.
6. **Polynomial explosion**: Taylor polynomials diverge outside the convergence radius. Set `y_range` wide enough to show the "shrinking" effect visually, or clip `x_range` to safe bounds.
7. **Kids version feels rushed**: If adapting for kids, **increase all waits by 50%**. Children's processing speed is slower; they need time to connect the metaphor to the math.

## Sync Quality Checklist

- [ ] Each scene's `run_time + wait` sum matches audio duration within 0.1s
- [ ] Production render durations verified with ffprobe
- [ ] No visual flash at scene stitch points
- [ ] Audio concat duration matches video concat duration within 0.5s
- [ ] Final mux outputs without `-shortest` truncation
- [ ] Both Feishu + Web links tested and accessible
