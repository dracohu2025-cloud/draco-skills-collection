#!/usr/bin/env python3
"""Publish an EPUB2Podcast delivery as a static YouTube handoff page."""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import shutil
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except Exception:  # pragma: no cover
    Image = ImageDraw = ImageFont = ImageFilter = None


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text).strip("-")
    if re.search(r"[\u4e00-\u9fff]", text):
        return "podcast-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    return text[:80] or "podcast"


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text("utf-8"))
    except Exception:
        return default


def fmt_time(seconds: float) -> str:
    s = max(0, int(seconds))
    return f"{s//60:02d}:{s%60:02d}"


def extract_segment_topic(seg: dict[str, Any], idx: int, total: int) -> str:
    """Derive a section label for YouTube timestamps; never paste dialogue lines."""
    visual = seg.get("visualPrompt")
    if isinstance(visual, dict):
        for key in ("title", "subtitle", "keyLine", "visualHook"):
            value = str(visual.get(key) or "").strip()
            if value:
                return value[:28]
    elif isinstance(visual, str):
        for pattern in (r"【标题】([^\n【]+)", r"TITLE[^:：]*[:：]\s*([^\n]+)", r"title[\"']?\s*[:=]\s*[\"']([^\"']+)"):
            m = re.search(pattern, visual, re.I)
            if m and m.group(1).strip():
                return m.group(1).strip()[:28]

    if idx == 0:
        return "开场与核心问题"
    if idx >= max(0, total - 2):
        return "总结与延伸思考"

    text = re.sub(r"\s+", "", str(seg.get("text") or ""))
    text = re.sub(r"^(想象一下|完全正确|没错|这是个好问题|你提到的)[，,。！!]*", "", text)
    # Convert dialogue into a neutral section heading rather than quoting it.
    for marker in ("为什么", "如何", "怎么", "关键", "核心", "转折", "影响"):
        pos = text.find(marker)
        if pos >= 0:
            return text[pos:pos + 18] + ("…" if len(text[pos:]) > 18 else "")
    return f"关键段落 {idx + 1}"


def fallback_marketing(title: str, script: list[dict[str, Any]]) -> dict[str, str]:
    main_title = re.split(r"[:：]", title, 1)[0].strip() or title
    yt_title = f"《{main_title}》深度解读：关键问题、脉络与启发"
    picks = []
    if script:
        target_count = min(8, max(5, len(script)))
        indexes = sorted({round(i * (len(script) - 1) / max(1, target_count - 1)) for i in range(target_count)})
        for i in indexes:
            seg = script[i]
            picks.append(f"{fmt_time(float(seg.get('startTime') or 0))} {extract_segment_topic(seg, i, len(script))}")
    timestamps = "\n".join(picks)
    description = f"""《{title}》视频播客解读。\n\n本期围绕书中的核心问题、关键概念和主要论证展开，梳理内容脉络，也提炼值得继续追问的观点。\n\n你会看到：\n- 全书核心问题与阅读入口\n- 关键概念、人物或事件之间的关系\n- 主要论证如何推进\n- 对现实理解或后续阅读的启发\n\n时间轴：\n{timestamps}\n\n#读书 #视频播客 #知识分享"""
    return {
        "title": yt_title,
        "description": description,
        "thumbnailTitle": main_title[:18],
        "thumbnailPrompt": f"High-CTR YouTube thumbnail for a Chinese book podcast about {title}: cinematic editorial poster, strong focal image, bold accurate Chinese title text, no watermark, no extra text."
    }


def find_first_existing(base: Path, names: list[str]) -> Path | None:
    for name in names:
        p = base / name
        if p.exists() and p.is_file():
            return p
    return None


def find_thumbnail_source(delivery: Path) -> Path | None:
    candidates = [
        "youtube_thumbnail.jpg", "youtube-thumbnail.jpg", "youtube_thumbnail.png",
        "thumbnail.jpg", "thumbnail.png", "gpt_image_slides/000.png",
        "smart_slides/000.png", "contact_sheet_gpt_images.jpg", "assets/cover.jpg",
    ]
    return find_first_existing(delivery, candidates)


def extract_openrouter_image(data: dict[str, Any]) -> tuple[bytes, str]:
    message = (data.get("choices") or [{}])[0].get("message") or {}

    def decode_data_url(value: str) -> tuple[bytes, str] | None:
        if value.startswith("data:image/"):
            m = re.match(r"data:(image/\w+);base64,(.+)", value, re.S)
            if m:
                return base64.b64decode(m.group(2)), m.group(1)
        if re.fullmatch(r"[A-Za-z0-9+/=\s]+", value or "") and len(value) > 1000:
            return base64.b64decode(re.sub(r"\s+", "", value)), "image/png"
        return None

    for item in message.get("images") or []:
        if isinstance(item, str):
            found = decode_data_url(item)
            if found:
                return found
        elif isinstance(item, dict):
            for value in [item.get("b64_json"), item.get("url"), (item.get("image_url") or {}).get("url")]:
                if value:
                    found = decode_data_url(value)
                    if found:
                        return found

    content = message.get("content") or ""
    if isinstance(content, str):
        found = decode_data_url(content)
        if found:
            return found

    raise RuntimeError("OpenRouter returned no image data")


def generate_gpt_image_thumbnail(prompt: str, out: Path, aspect_ratio: str = "16:9") -> bool:
    """Generate thumbnail through the GPT image provider API shape used by source code."""
    api_key = (os.environ.get("GPT_IMAGE_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key or not prompt:
        return False

    base_url = os.environ.get("GPT_IMAGE_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("GPT_IMAGE_MODEL", "gpt-image-2-high")
    body = {
        "model": model,
        "prompt": f"Create a sharp 16:9 YouTube thumbnail. {prompt}",
        "n": 1,
        "size": os.environ.get("GPT_IMAGE_SIZE", "1536x1024"),
        "quality": os.environ.get("GPT_IMAGE_QUALITY", "high"),
        "aspect_ratio": aspect_ratio,
    }
    req = urllib.request.Request(
        f"{base_url}/images/generations",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        item = (data.get("data") or [{}])[0]
        if item.get("b64_json"):
            image_bytes = base64.b64decode(item["b64_json"])
        elif item.get("url"):
            with urllib.request.urlopen(item["url"], timeout=300) as img_resp:
                image_bytes = img_resp.read()
        else:
            raise RuntimeError("GPT image generation returned no image data")
        out.parent.mkdir(parents=True, exist_ok=True)
        if Image is not None:
            tmp = out.with_suffix(".tmp")
            tmp.write_bytes(image_bytes)
            Image.open(tmp).convert("RGB").save(out, quality=94, optimize=True)
            tmp.unlink(missing_ok=True)
        else:
            out.write_bytes(image_bytes)
        print(f"[thumbnail] generated via GPT image model={model}")
        return True
    except (urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError, OSError) as e:
        print(f"[thumbnail] GPT image generation failed; trying OpenRouter/local fallback: {e}")
        return False


def generate_ai_thumbnail(prompt: str, out: Path, aspect_ratio: str = "16:9") -> bool:
    """Generate thumbnail from marketing.thumbnailPrompt via OpenRouter image model."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key or not prompt:
        return False

    model = os.environ.get("OPENROUTER_IMAGE", "google/gemini-3.1-flash-image-preview")
    body = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": (
                f"IMPORTANT: Generate this image in {aspect_ratio} aspect ratio, "
                "as a sharp high-CTR YouTube thumbnail. "
                f"Generate an image based on this description: {prompt}"
            ),
        }],
        "max_tokens": 4096,
        "modalities": ["image", "text"],
        "provider": {"order": ["Vertex AI"]},
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://podcast.aigc.green",
            "X-Title": "EPUB to Podcast",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        image_bytes, mime = extract_openrouter_image(data)
        out.parent.mkdir(parents=True, exist_ok=True)
        if mime != "image/jpeg" and Image is not None:
            tmp = out.with_suffix(".tmp")
            tmp.write_bytes(image_bytes)
            Image.open(tmp).convert("RGB").save(out, quality=94, optimize=True)
            tmp.unlink(missing_ok=True)
        else:
            out.write_bytes(image_bytes)
        print(f"[thumbnail] generated via OpenRouter model={model}")
        return True
    except (urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError, OSError) as e:
        print(f"[thumbnail] AI generation failed; falling back to local thumbnail: {e}")
        return False


def load_font(size: int, bold: bool = False):
    paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def wrap_text(draw, text: str, font, max_width: int, max_lines: int) -> list[str]:
    chars = list(text)
    lines, cur = [], ""
    for ch in chars:
        test = cur + ch
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = ch
            if len(lines) >= max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) == max_lines and len("".join(lines)) < len(text):
        lines[-1] = lines[-1].rstrip("，。？！：；、 ") + "…"
    return lines


def copy_existing_thumbnail(src: Path, out: Path) -> bool:
    """Use a pre-generated YouTube thumbnail exactly as generated; no 16:9 conversion, no blurred side fill."""
    if not src or not src.exists():
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, out)
    return True


def make_thumbnail(src: Path | None, out: Path, title: str) -> None:
    if Image is None:
        if src:
            shutil.copy2(src, out)
            return
        raise RuntimeError("Pillow is required to generate thumbnail")
    W, H = 1280, 720
    if src and src.exists():
        im = Image.open(src).convert("RGB")
        scale = max(W / im.width, H / im.height)
        bg = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        left = (bg.width - W) // 2
        top = (bg.height - H) // 2
        bg = bg.crop((left, top, left + W, top + H)).filter(ImageFilter.GaussianBlur(12))
        # Keep the source image as a blurred cinematic background only.
        # Do not paste the full slide as foreground, because slide text competes with the YouTube title.
        fg = None
    else:
        bg = Image.new("RGB", (W, H), (18, 14, 10))
        fg = None
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((0, 0, W, H), fill=(8, 6, 3, 100))
    od.rectangle((0, 0, int(W * 0.62), H), fill=(9, 8, 6, 190))
    bg = Image.alpha_composite(bg.convert("RGBA"), overlay)
    if fg:
        x = W - fg.width - 46
        y = (H - fg.height) // 2
        shadow = Image.new("RGBA", (fg.width + 24, fg.height + 24), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle((12, 12, fg.width + 12, fg.height + 12), radius=18, fill=(0, 0, 0, 130))
        bg.alpha_composite(shadow, (x - 12, y - 8))
        bg.alpha_composite(fg.convert("RGBA"), (x, y))
    draw = ImageDraw.Draw(bg)
    font_big = load_font(74, True)
    font_mid = load_font(36, True)
    font_small = load_font(28, False)
    draw.text((58, 58), "视频播客", fill=(245, 184, 77), font=font_mid)
    lines = wrap_text(draw, title, font_big, 640, 3)
    yy = 126
    for line in lines:
        draw.text((56, yy), line, fill=(255, 248, 226), font=font_big, stroke_width=2, stroke_fill=(0, 0, 0))
        yy += 88
    draw.line((58, yy + 20, 560, yy + 20), fill=(217, 153, 58), width=4)
    draw.text((58, yy + 52), "阿提拉 · 成吉思汗 · 帖木儿", fill=(238, 221, 185), font=font_small)
    out.parent.mkdir(parents=True, exist_ok=True)
    bg.convert("RGB").save(out, quality=92, optimize=True)


def write_html(out_dir: Path, title: str, marketing: dict[str, str], duration: str, video_name: str, thumb_name: str) -> None:
    safe_title = html.escape(title)
    yt_title = marketing.get("title") or title
    desc = marketing.get("description") or ""
    page = f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
<title>{html.escape(yt_title)}｜YouTube 素材交付</title>
<style>
:root {{ --bg:#0b0a08; --card:#16130e; --ink:#f7efe1; --muted:#b9aa91; --line:#2c2418; --gold:#d99b3d; --gold2:#f4c76c; }}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at 70% 0,#3a2510 0,#0b0a08 40%,#050403 100%);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans CJK SC','PingFang SC',sans-serif;}}
a{{color:inherit}} .wrap{{max-width:1180px;margin:0 auto;padding:42px 22px 64px}} .hero{{display:grid;grid-template-columns:1.1fr .9fr;gap:28px;align-items:end;margin-bottom:28px}}
.kicker{{color:var(--gold2);font-size:14px;letter-spacing:.18em;text-transform:uppercase}} h1{{font-size:clamp(34px,5vw,64px);line-height:1.03;margin:12px 0 18px;letter-spacing:-.04em}} .sub{{color:var(--muted);font-size:18px;line-height:1.7}}
.panel{{background:linear-gradient(180deg,rgba(255,255,255,.055),rgba(255,255,255,.025));border:1px solid var(--line);border-radius:24px;padding:18px;box-shadow:0 20px 80px rgba(0,0,0,.35)}}
video,img{{width:100%;border-radius:18px;background:#000;display:block}} .grid{{display:grid;grid-template-columns:1.15fr .85fr;gap:24px;margin-top:24px}} .stack{{display:grid;gap:18px}}
.card{{background:rgba(22,19,14,.82);border:1px solid var(--line);border-radius:24px;padding:22px}} .card h2{{font-size:21px;margin:0 0 14px}} .meta{{display:flex;gap:10px;flex-wrap:wrap;color:var(--muted);font-size:14px}}
.btns{{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}} .btn{{border:1px solid #5b421f;background:#24180c;color:#ffe6a8;padding:10px 14px;border-radius:999px;text-decoration:none;cursor:pointer;font-weight:700}} .btn.primary{{background:linear-gradient(135deg,#d99b3d,#f4c76c);color:#1a1005;border:0}}
textarea,input{{width:100%;background:#0f0d0a;color:var(--ink);border:1px solid var(--line);border-radius:16px;padding:14px;font:inherit;line-height:1.55}} textarea{{min-height:310px;resize:vertical;white-space:pre-wrap}} input{{font-weight:700}}
.toast{{position:fixed;right:18px;bottom:18px;background:#ffe1a1;color:#1c1207;padding:12px 16px;border-radius:14px;font-weight:800;opacity:0;transform:translateY(10px);transition:.22s}} .toast.show{{opacity:1;transform:none}}
footer{{color:#847762;font-size:13px;margin-top:30px;text-align:center}} @media(max-width:900px){{.hero,.grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class=\"wrap\">
  <section class=\"hero\">
    <div>
      <div class=\"kicker\">Podcast Delivery Kit</div>
      <h1>{safe_title}</h1>
      <p class=\"sub\">视频、YouTube 封面、标题和简介集中交付。下载、复制，一键拿走。少点折腾，像人类。</p>
      <div class=\"meta\"><span>时长：{html.escape(duration)}</span><span>格式：MP4 + 封面图片 + YouTube 文案</span></div>
    </div>
    <div class=\"panel\"><img src=\"assets/{html.escape(thumb_name)}\" alt=\"YouTube thumbnail\"></div>
  </section>
  <div class=\"grid\">
    <div class=\"stack\">
      <div class=\"card\"><h2>最终视频</h2><video controls preload=\"metadata\" poster=\"assets/{html.escape(thumb_name)}\"><source src=\"assets/{html.escape(video_name)}\" type=\"video/mp4\"></video><div class=\"btns\"><a class=\"btn primary\" href=\"assets/{html.escape(video_name)}\" download>下载视频 MP4</a></div></div>
      <div class=\"card\"><h2>YouTube 封面</h2><img src=\"assets/{html.escape(thumb_name)}\" alt=\"YouTube thumbnail\"><div class=\"btns\"><a class=\"btn primary\" href=\"assets/{html.escape(thumb_name)}\" download>下载封面图片</a></div></div>
    </div>
    <div class=\"stack\">
      <div class=\"card\"><h2>YouTube Title</h2><input id=\"yt-title\" value=\"{html.escape(yt_title, quote=True)}\" readonly><div class=\"btns\"><button class=\"btn primary\" data-copy=\"yt-title\">复制 Title</button></div></div>
      <div class=\"card\"><h2>YouTube Description</h2><textarea id=\"yt-description\" readonly>{html.escape(desc)}</textarea><div class=\"btns\"><button class=\"btn primary\" data-copy=\"yt-description\">复制 Description</button><a class=\"btn\" href=\"assets/marketing.json\" download>下载 marketing.json</a></div></div>
    </div>
  </div>
  <footer>Generated by Hermes · {html.escape(datetime.now().strftime('%Y-%m-%d %H:%M'))}</footer>
</div>
<div id=\"toast\" class=\"toast\">已复制</div>
<script>
const toast=document.getElementById('toast');
function flash(t='已复制'){{toast.textContent=t;toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),1200)}}
async function copyText(id){{const el=document.getElementById(id); const text=el.value || el.textContent; try{{await navigator.clipboard.writeText(text); flash();}}catch(e){{el.select(); document.execCommand('copy'); flash();}}}}
document.querySelectorAll('[data-copy]').forEach(b=>b.addEventListener('click',()=>copyText(b.dataset.copy)));
</script>
</body>
</html>"""
    (out_dir / "index.html").write_text(page, "utf-8")


def write_listing(site_root: Path) -> None:
    entries = []
    for child in sorted(site_root.iterdir() if site_root.exists() else [], key=lambda p: p.stat().st_mtime, reverse=True):
        if child.is_dir() and (child / "index.html").exists():
            title = child.name
            m = re.search(r"<h1>(.*?)</h1>", (child / "index.html").read_text("utf-8", errors="ignore"), re.S)
            if m:
                title = re.sub("<.*?>", "", html.unescape(m.group(1)))
            entries.append((child.name, title))
    cards = "\n".join(f'<li><a href="{html.escape(slug)}/">{html.escape(title)}</a></li>' for slug, title in entries)
    (site_root / "index.html").write_text(f"""<!doctype html><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Podcast Delivery Kits</title><style>body{{margin:0;background:#0b0a08;color:#f7efe1;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans CJK SC',sans-serif}}main{{max-width:900px;margin:0 auto;padding:52px 22px}}a{{color:#f4c76c;font-size:22px;text-decoration:none}}li{{margin:18px 0;padding:18px;border:1px solid #2c2418;border-radius:18px;background:#16130e}}h1{{font-size:44px}}</style><main><h1>Podcast Delivery Kits</h1><ul>{cards}</ul></main>""", "utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--delivery-dir", required=True)
    ap.add_argument("--site-root", default="/var/www/hermes.aigc.green/podcasts")
    ap.add_argument("--slug")
    ap.add_argument("--base-url", default="https://hermes.aigc.green/podcasts")
    ap.add_argument("--prefer-feishu-video", action="store_true", help="Use smaller final_podcast_feishu.mp4 when present")
    ap.add_argument("--thumbnail-mode", choices=["auto", "ai", "local"], default="auto", help="auto/ai uses marketing.thumbnailPrompt via GPT image provider, then OpenRouter fallback; local uses PIL fallback only")
    ns = ap.parse_args()

    delivery = Path(ns.delivery_dir).resolve()
    site_root = Path(ns.site_root).resolve()
    if not delivery.exists():
        raise SystemExit(f"delivery dir not found: {delivery}")

    manifest = read_json(delivery / "manifest.json", {})
    title = manifest.get("title") or delivery.name
    script = read_json(delivery / "metadata" / "script.json", [])
    marketing_path = delivery / "metadata" / "marketing.json"
    marketing = read_json(marketing_path, None)
    if not marketing:
        marketing = fallback_marketing(title, script if isinstance(script, list) else [])
        marketing_path.parent.mkdir(parents=True, exist_ok=True)
        marketing_path.write_text(json.dumps(marketing, ensure_ascii=False, indent=2), "utf-8")

    video_names = ["final_podcast_feishu.mp4", "final_podcast.mp4"] if ns.prefer_feishu_video else ["final_podcast.mp4", "final_podcast_feishu.mp4"]
    video = find_first_existing(delivery, video_names)
    if not video:
        raise SystemExit("No final_podcast*.mp4 found")

    slug = ns.slug or slugify(title)
    out_dir = site_root / slug
    assets = out_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    video_name = "final_podcast.mp4"
    shutil.copy2(video, assets / video_name)

    prebuilt = find_first_existing(delivery, ["youtube_thumbnail.jpg", "youtube-thumbnail.jpg", "youtube_thumbnail.png", "thumbnail.jpg", "thumbnail.png"])
    prebuilt_ext = prebuilt.suffix.lower() if prebuilt else ""
    if prebuilt_ext == ".jpeg":
        prebuilt_ext = ".jpg"
    thumb_name = f"youtube-thumbnail{prebuilt_ext if prebuilt_ext in {'.jpg', '.png', '.webp'} else '.jpg'}"
    thumb_path = assets / thumb_name
    generated = False
    if prebuilt and ns.thumbnail_mode in ("auto", "local"):
        generated = copy_existing_thumbnail(prebuilt, thumb_path)
        if generated:
            print(f"[thumbnail] using pre-generated thumbnail as-is: {prebuilt}")
    if not generated and ns.thumbnail_mode in ("auto", "ai"):
        prompt = marketing.get("thumbnailPrompt") or ""
        generated = generate_gpt_image_thumbnail(prompt, thumb_path) or generate_ai_thumbnail(prompt, thumb_path)
        if ns.thumbnail_mode == "ai" and not generated:
            raise SystemExit("AI thumbnail generation failed")
    if not generated:
        make_thumbnail(find_thumbnail_source(delivery), thumb_path, marketing.get("thumbnailTitle") or marketing.get("title") or title)
    shutil.copy2(marketing_path, assets / "marketing.json")

    dur_s = manifest.get("durationSeconds") or manifest.get("totalDuration") or 0
    duration = fmt_time(float(dur_s)) if dur_s else "未知"
    write_html(out_dir, title, marketing, duration, video_name, thumb_name)
    write_listing(site_root)
    print(json.dumps({"url": f"{ns.base_url.rstrip('/')}/{slug}/", "path": str(out_dir), "video": str(assets/video_name), "thumbnail": str(assets/thumb_name)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
