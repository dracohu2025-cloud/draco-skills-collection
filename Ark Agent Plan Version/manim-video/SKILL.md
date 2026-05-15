---
name: manim-video
description: "Production pipeline for mathematical and technical animations using Manim Community Edition. Creates 3Blue1Brown-style explainer videos, algorithm visualizations, equation derivations, architecture diagrams, and data stories. Use when users request: animated explanations, math animations, concept visualizations, algorithm walkthroughs, technical explainers, 3Blue1Brown style videos, or any programmatic animation with geometric/mathematical content."
version: 1.0.0
---

# Manim Video Production Pipeline

## Creative Standard

This is educational cinema. Every frame teaches. Every animation reveals structure.

**Before writing a single line of code**, articulate the narrative arc. What misconception does this correct? What is the "aha moment"? What visual story takes the viewer from confusion to understanding? The user's prompt is a starting point — interpret it with pedagogical ambition.

**Geometry before algebra.** Show the shape first, the equation second. Visual memory encodes faster than symbolic memory. When the viewer sees the geometric pattern before the formula, the equation feels earned.

**First-render excellence is non-negotiable.** The output must be visually clear and aesthetically cohesive without revision rounds. If something looks cluttered, poorly timed, or like "AI-generated slides," it is wrong.

**Opacity layering directs attention.** Never show everything at full brightness. Primary elements at 1.0, contextual elements at 0.4, structural elements (axes, grids) at 0.15. The brain processes visual salience in layers.

**Breathing room.** Every animation needs `self.wait()` after it. The viewer needs time to absorb what just appeared. Never rush from one animation to the next. A 2-second pause after a key reveal is never wasted.

**Cohesive visual language.** All scenes share a color palette, consistent typography sizing, matching animation speeds. A technically correct video where every scene uses random different colors is an aesthetic failure.

## Prerequisites

Run `scripts/setup.sh` to verify all dependencies. Requires: Python 3.10+, Manim Community Edition v0.20+ (`pip install manim`), LaTeX, and ffmpeg. Reference docs tested against Manim CE v0.20.1.

### Proven Ubuntu 24.04 install path

On this Ubuntu 24.04 environment, the following combination was actually validated end-to-end:

```bash
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  pkg-config libcairo2-dev libpango1.0-dev libffi-dev python3-dev \
  libgdk-pixbuf2.0-dev cmake \
  texlive-latex-base texlive-latex-extra texlive-fonts-recommended \
  texlive-science texlive-plain-generic dvisvgm

source .venv/bin/activate  # 或使用你自己的 Python 虚拟环境
python -m pip install manim
```

Notes:
- `ffmpeg` was already present here, but still verify it with `ffmpeg -version`.
- Full `texlive-full` is unnecessary overkill for this path; the package set above was enough to render `Text` + `MathTex` successfully.
- On this machine, Chinese `Text(...)` rendering worked with `font="Noto Sans CJK SC"` and code-like CJK text worked with `font="Noto Sans Mono CJK SC"`. These are good defaults for Chinese explainer videos.
- After install, verify with:

```bash
source .venv/bin/activate  # 或使用你自己的 Python 虚拟环境
manim --version
pdflatex --version
ffmpeg -version
bash ./scripts/setup.sh
```

## Modes

| Mode | Input | Output | Reference |
|------|-------|--------|-----------|
| **Concept explainer** | Topic/concept | Animated explanation with geometric intuition | `references/scene-planning.md` |
| **Equation derivation** | Math expressions | Step-by-step animated proof | `references/equations.md` |
| **Algorithm visualization** | Algorithm description | Step-by-step execution with data structures | `references/graphs-and-data.md` |
| **Data story** | Data/metrics | Animated charts, comparisons, counters | `references/graphs-and-data.md` |
| **Architecture diagram** | System description | Components building up with connections | `references/mobjects.md` |
| **Paper explainer** | Research paper | Key findings and methods animated | `references/scene-planning.md` |
| **Mechanism explainer** | How an engine / renderer / algorithm works | Use one concept per scene with specimen-style comparisons and keyframes | `references/scene-planning.md` |
| **3D visualization** | 3D concept | Rotating surfaces, parametric curves, spatial geometry | `references/camera-and-3d.md` |

## Stack

Single Python script per project. No browser, no Node.js, no GPU required.

| Layer | Tool | Purpose |
|-------|------|---------|
| Core | Manim Community Edition | Scene rendering, animation engine |
| Math | LaTeX (texlive/MiKTeX) | Equation rendering via `MathTex` |
| Video I/O | ffmpeg | Scene stitching, format conversion, audio muxing |
| TTS | ElevenLabs / Qwen3-TTS (optional) | Narration voiceover |

## Pipeline

```
PLAN --> CODE --> RENDER --> STITCH --> AUDIO (optional) --> REVIEW
```

1. **PLAN** — Write `plan.md` with narrative arc, scene list, visual elements, color palette, voiceover script
2. **CODE** — Write `script.py` with one class per scene, each independently renderable
3. **RENDER** — `manim -ql script.py Scene1 Scene2 ...` for draft, `-qh` for production
4. **STITCH** — ffmpeg concat of scene clips into `final.mp4`
5. **AUDIO** (optional) — Add voiceover and/or background music via ffmpeg. See `references/rendering.md`
6. **REVIEW** — Render preview stills, verify against plan, adjust

## Project Structure

```
project-name/
  plan.md                # Narrative arc, scene breakdown
  script.py              # All scenes in one file
  concat.txt             # ffmpeg scene list
  final.mp4              # Stitched output
  media/                 # Auto-generated by Manim
    videos/script/480p15/
```

## Creative Direction

### Color Palettes

| Palette | Background | Primary | Secondary | Accent | Use case |
|---------|-----------|---------|-----------|--------|----------|
| **Classic 3B1B** | `#1C1C1C` | `#58C4DD` (BLUE) | `#83C167` (GREEN) | `#FFFF00` (YELLOW) | General math/CS |
| **Warm academic** | `#2D2B55` | `#FF6B6B` | `#FFD93D` | `#6BCB77` | Approachable |
| **Neon tech** | `#0A0A0A` | `#00F5FF` | `#FF00FF` | `#39FF14` | Systems, architecture |
| **Monochrome** | `#1A1A2E` | `#EAEAEA` | `#888888` | `#FFFFFF` | Minimalist |

### Animation Speed

| Context | run_time | self.wait() after |
|---------|----------|-------------------|
| Title/intro appear | 1.5s | 1.0s |
| Key equation reveal | 2.0s | 2.0s |
| Transform/morph | 1.5s | 1.5s |
| Supporting label | 0.8s | 0.5s |
| FadeOut cleanup | 0.5s | 0.3s |
| "Aha moment" reveal | 2.5s | 3.0s |

### Typography Scale

| Role | Font size | Usage |
|------|-----------|-------|
| Title | 48 | Scene titles, opening text |
| Heading | 36 | Section headers within a scene |
| Body | 30 | Explanatory text |
| Label | 24 | Annotations, axis labels |
| Caption | 20 | Subtitles, fine print |

### Fonts

**Use monospace fonts for all text.** Manim's Pango renderer produces broken kerning with proportional fonts at all sizes. See `references/visual-design.md` for full recommendations.

```python
MONO = "Menlo"  # define once at top of file

Text("Fourier Series", font_size=48, font=MONO, weight=BOLD)  # titles
Text("n=1: sin(x)", font_size=20, font=MONO)                  # labels
MathTex(r"\nabla L")                                            # math (uses LaTeX)
```

On this Ubuntu machine, Chinese text rendered successfully with:

```python
FONT = "Noto Sans CJK SC"
MONO = "Noto Sans Mono CJK SC"
```

Use those for Chinese explainer videos instead of guessing font names.

Minimum `font_size=18` for readability.

### Per-Scene Variation

Never use identical config for all scenes. For each scene:
- **Different dominant color** from the palette
- **Different layout** — don't always center everything
- **Different animation entry** — vary between Write, FadeIn, GrowFromCenter, Create
- **Different visual weight** — some scenes dense, others sparse

## Workflow

### Step 1: Plan (plan.md)

Before any code, write `plan.md`. See `references/scene-planning.md` for the comprehensive template.

### Special pattern: mechanism explainers

When the goal is to explain **how something works** (renderer, algorithm, internal engine, update loop), do **not** cram multiple abstractions into one scene. Use this pattern instead:

0. **Start with the answer** — for zero-background users, open with the one-sentence conclusion first, then unpack layers. Use a pyramid structure: summary -> layer 1 specimen -> layer 2 specimen -> general pipeline -> parameter details.
1. **One concept per scene** — if the viewer must learn `Create`, `shift`, `alpha`, and `renderer`, split them. Do not explain all four at once.
2. **Use a specimen** — one minimal code example or one minimal visual object per scene.
3. **Show keyframes** — frame 1 / 10 / 20 / 30 style comparisons are often clearer than a single moving animation.
4. **Say what changed** — e.g. “the visible path ratio changed” or “the position changed, not the shape”.
5. **Only after the specimen lands, show the general pipeline** — `time -> current state -> redraw -> video`.
6. **Mechanism videos should feel like a guided lab, not a slide deck.**
7. **If there is TTS, align per scene** — do not lay one long narration track over the whole video and hope the scene lengths match. Generate one narration clip per scene, then extend/trim that scene video to the clip duration before final concat.
8. **For the final concrete example, do not collapse everything back into one crowded “all params on one slide” page.** Use a lab sequence instead: (a) state the target animation effect in plain language, (b) show the overall time map, (c) inspect one timestamp at a time, and (d) only then explain dt as the per-frame step inside the current stage.
9. **Never hide important code or formulas behind foreground cards.** Background-code aesthetics are fine only when the code is non-essential. If the viewer must reason from the code or formula, it must remain fully readable or be removed.
10. **When explaining multiple time-related quantities (`t`, `alpha`, `dt`), assign them different jobs explicitly.** A durable novice-safe phrasing is: `t` tells you where you are in the whole animation, `alpha` tells you how far the current step has progressed, and `dt` tells you how much one frame advances the current step.

   - scene A: overall time map (`0s -> 3s`, with phase boundaries and sample timestamps)
   - scene B: inspect one timestamp inside the first phase and compute local `alpha` explicitly
   - scene C: inspect a later timestamp after the phase switch and show what visible property now changes
   - scene D: only then zoom into frame-level `dt` stepping
   This keeps reading order aligned with causal order.
9. **If there is TTS, align per scene** — do not lay one long narration track over the whole video and hope the scene lengths match. Generate one narration clip per scene, then extend/trim that scene video to the clip duration before final concat.
10. **For zero-background viewers, prefer life analogies over engine jargon** — e.g. say “many static pictures played in sequence” before saying “discrete frame sampling” or “state update”. Use the technical phrasing only after the mental model lands.
11. **Split `alpha` and `dt` into separate scenes unless the audience is already technical** — putting both on one slide makes first-time viewers half-understand both. Teach `alpha = total progress` first, then `dt = time between adjacent frames`.
12. **Do not add code unless it materially helps the visual explanation** — for novice-facing mechanism videos, diagrams, before/after specimens, and labeled frames usually beat code snippets. If code is present in a final example, keep it clearly secondary and never half-covered behind foreground cards.
13. **Enforce layout safety margins explicitly** — keep titles fully above content boxes, keep bottom summary text off the lower edge, and leave enough right-edge space for the last card. If a scene feels crowded, cut text before shrinking everything.
14. **QA with single-frame extracts, not sloppy contact sheets** — inspect the real per-scene frames directly when checking overlap, clipping, or chapter transitions. A badly assembled contact sheet can create fake layout bugs and waste time.
15. **Do not fake progress bars** — if you show `alpha` as a progress bar, the fill must stay inside the track and map cleanly from `0` to the demo value. Decorative overshoot makes the explanation less trustworthy.

This pattern was validated on a Manim explainer task: the first draft was too abstract because it introduced too many concepts at once; the clearer second draft improved comprehension by splitting `Create(circle)` and `shift` into separate specimen scenes and only then summarizing `alpha / dt / renderer`.

### Step 2: Code (script.py)

One class per scene. Every scene is independently renderable.

```python
from manim import *

BG = "#1C1C1C"
PRIMARY = "#58C4DD"
SECONDARY = "#83C167"
ACCENT = "#FFFF00"
MONO = "Menlo"

class Scene1_Introduction(Scene):
    def construct(self):
        self.camera.background_color = BG
        title = Text("Why Does This Work?", font_size=48, color=PRIMARY, weight=BOLD, font=MONO)
        self.add_subcaption("Why does this work?", duration=2)
        self.play(Write(title), run_time=1.5)
        self.wait(1.0)
        self.play(FadeOut(title), run_time=0.5)
```

Key patterns:
- **Subtitles** on every animation: `self.add_subcaption("text", duration=N)` or `subcaption="text"` on `self.play()`
- **Shared color constants** at file top for cross-scene consistency
- **`self.camera.background_color`** set in every scene
- **Clean exits** — FadeOut all mobjects at scene end: `self.play(FadeOut(Group(*self.mobjects)))`

### Step 3: Render

```bash
manim -ql script.py Scene1_Introduction Scene2_CoreConcept  # draft
manim -qh script.py Scene1_Introduction Scene2_CoreConcept  # production
```

### Practical workflow for narrated explainers

When the user expects a **finished explainer video with TTS**, do not start by replying with long text-only teaching. Build the video first.

Use this sequence:

1. **Write the narration first** into `narration.txt`.
2. **Generate TTS immediately** and measure real duration with `ffprobe`.
3. **Adjust scene `wait()` / run_time values to the real narration length** instead of guessing pacing.
4. **Run a smoke render first** (`-ql` or `-qm`) to catch layout/font bugs cheaply.
5. **Only after smoke passes, run the final render**.
6. **Concat scene files, then mux narration audio** into the final MP4.
7. **Verify the result** with `ffprobe` plus a few extracted review frames.

A proven command pattern on this machine:

```bash
# 1) synthesize narration first
python3 /path/to/volcengine_tts.py \
  --input narration.txt \
  --output narration.mp3 \
  --voice female

# 2) measure audio duration
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 narration.mp3

# 3) smoke render
manim -ql script.py Scene1 Scene2 Scene3

# 4) final render
manim -qm script.py Scene1 Scene2 Scene3

# 5) concat + mux
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy video_silent.mp4
ffmpeg -y -i video_silent.mp4 -i narration.mp3 \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest final.mp4

# 6) verify duration / size
ffprobe -v error -show_entries format=duration,size -of default=nw=1:nk=1 final.mp4
```

For review stills, extract 3–4 timestamps and inspect them before delivery.

### Step 4: Stitch

```bash
cat > concat.txt << 'EOF'
file 'media/videos/script/480p15/Scene1_Introduction.mp4'
file 'media/videos/script/480p15/Scene2_CoreConcept.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy final.mp4
```

### Step 5: Review

```bash
manim -ql --format=png -s script.py Scene2_CoreConcept  # preview still
```

## Critical Implementation Notes

### Raw Strings for LaTeX
```python
# WRONG: MathTex("\\frac{1}{2}")
# RIGHT:
MathTex(r"\\frac{1}{2}")
```

### Manim CE v0.20.1 pitfalls actually hit on this machine

#### `NumberLine(..., include_numbers=True, decimal_number_config=...)`
On Manim CE v0.20.1 here, passing `font_size` inside `decimal_number_config` caused:

```text
TypeError: DecimalNumber() got multiple values for keyword argument 'font_size'
```

Safe path:

```python
NumberLine(
    x_range=[0, 1, 0.25],
    include_numbers=True,
    decimal_number_config={"num_decimal_places": 2},
)
```

Do not pass `font_size` there on this version unless you've re-verified the exact code path.

#### `interpolate_color` with hex strings
On this Manim version, `interpolate_color(PRIMARY, SECONDARY, alpha)` failed when `PRIMARY` / `SECONDARY` were plain hex strings, because the helper expected `ManimColor` objects.

Safe path:

```python
color=interpolate_color(ManimColor(PRIMARY), ManimColor(SECONDARY), alpha)
```

#### Chinese text font defaults
For Chinese explainer videos on this Ubuntu machine, these worked cleanly:

```python
FONT = "Noto Sans CJK SC"
MONO = "Noto Sans Mono CJK SC"
```

### buff >= 0.5 for Edge Text
```python
label.to_edge(DOWN, buff=0.5)  # never < 0.5
```

### FadeOut Before Replacing Text
```python
self.play(ReplacementTransform(note1, note2))  # not Write(note2) on top
```

### Never Animate Non-Added Mobjects
```python
self.play(Create(circle))  # must add first
self.play(circle.animate.set_color(RED))  # then animate
```

## Performance Targets

| Quality | Resolution | FPS | Speed |
|---------|-----------|-----|-------|
| `-ql` (draft) | 854x480 | 15 | 5-15s/scene |
| `-qm` (medium) | 1280x720 | 30 | 15-60s/scene |
| `-qh` (production) | 1920x1080 | 60 | 30-120s/scene |

Always iterate at `-ql`. Only render `-qh` for final output.

## Frame-by-frame teaching / debugging mode

Use this when the user says the explanation is still too abstract, or when you need to prove what Manim is doing on specific frames instead of hand-waving.

### Best minimal specimen

For teaching, reduce the script to **one animation only**. Example:

```python
from manim import *

config.pixel_width = 1280
config.pixel_height = 720
config.frame_rate = 30

class FrameByFrameCreate(Scene):
    def construct(self):
        circle = Circle()
        self.play(Create(circle), run_time=1, rate_func=linear)
```

Why this works:
- `run_time=1` at `30fps` gives a clean mental model: roughly 30 sampled animation frames
- `rate_func=linear` avoids easing confusion when teaching `alpha`
- one mobject, one animation, no scene clutter

### Extract concrete frames

Render at 30fps, then pull specific video frames with ffmpeg. Good teaching checkpoints:
- frame 1 (`n=0`) → start state
- frame 10 (`n=9`) → early progress
- frame 20 (`n=19`) → middle/late progress
- frame 30 (`n=29`) → almost complete, but often not yet exactly final

```bash
manim -qm script.py FrameByFrameCreate
ffmpeg -y -i media/videos/script/720p30/FrameByFrameCreate.mp4 \
  -vf "select='eq(n,0)+eq(n,9)+eq(n,19)+eq(n,29)'" \
  -vsync 0 review/frame-%02d.png
```

Then label them into a 2x2 contact sheet for discussion.

### Critical teaching point: why “frame 30” may still not be fully complete

In Manim CE 0.20.1, the scene loop renders sampled times first, then calls `animation.finish()` afterwards.

Relevant source behavior:
- `Scene.update_to_time()` computes `alpha = t / animation.run_time`
- sampled frame `n=29` at `30fps` for a `1s` animation corresponds to `t = 29/30 = 0.9667`, not `1.0`
- after the render loop, `Animation.finish()` calls `self.interpolate(1)`

So if you extract video frame 30 by index, the circle may still have a tiny gap. That is expected. The fully final object state is forced after sampling via `finish()`.

### How to explain it clearly

Avoid saying “the next frame predicts the future” or “pixels are gradually painted on top forever”.

Say this instead:
1. Manim samples a time `t`
2. computes the current animation state for that `t`
3. redraws the whole frame from that state
4. writes the frame into the video

For `Create(circle)`, the concrete explanation is:
- frame 1: visible arc length ≈ 0%
- frame 10: visible arc length ≈ 30%
- frame 20: visible arc length ≈ 63%
- frame 30: visible arc length ≈ 96.7%

That makes the mechanism tangible.

## References

| File | Contents |
|------|----------|
| `references/animations.md` | Core animations, rate functions, composition, `.animate` syntax, timing patterns |
| `references/mobjects.md` | Text, shapes, VGroup/Group, positioning, styling, custom mobjects |
| `references/visual-design.md` | 12 design principles, opacity layering, layout templates, color palettes |
| `references/equations.md` | LaTeX in Manim, TransformMatchingTex, derivation patterns |
| `references/graphs-and-data.md` | Axes, plotting, BarChart, animated data, algorithm visualization |
| `references/camera-and-3d.md` | MovingCameraScene, ThreeDScene, 3D surfaces, camera control |
| `references/scene-planning.md` | Narrative arcs, layout templates, scene transitions, planning template |
| `references/rendering.md` | CLI reference, quality presets, ffmpeg, voiceover workflow, GIF export |
| `references/troubleshooting.md` | LaTeX errors, animation errors, common mistakes, debugging |
| `references/animation-design-thinking.md` | When to animate vs show static, decomposition, pacing, narration sync |
| `references/updaters-and-trackers.md` | ValueTracker, add_updater, always_redraw, time-based updaters, patterns |
| `references/paper-explainer.md` | Turning research papers into animations — workflow, templates, domain patterns |
| `references/decorations.md` | SurroundingRectangle, Brace, arrows, DashedLine, Angle, annotation lifecycle |
| `references/production-quality.md` | Pre-code, pre-render, post-render checklists, spatial layout, color, tempo |
