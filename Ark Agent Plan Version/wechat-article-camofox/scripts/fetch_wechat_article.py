#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

CAMOFOX_PORT = os.getenv("CAMOFOX_PORT", "9377")
CAMOFOX_BASE = f"http://127.0.0.1:{CAMOFOX_PORT}"
CAMOFOX_REPO_URL = os.getenv("CAMOFOX_BROWSER_GIT_URL", "https://github.com/jo-inc/camofox-browser.git")
CAMOFOX_REPO = Path(os.getenv("CAMOFOX_BROWSER_REPO", str(Path.home() / ".hermes" / "camofox-browser"))).expanduser()
CAMOFOX_LOG_DIR = Path(os.getenv("CAMOFOX_LOG_DIR", str(Path.home() / ".hermes" / "logs"))).expanduser()
CAMOFOX_LOG_FILE = CAMOFOX_LOG_DIR / "camofox-browser.log"
CAMOFOX_PID_FILE = CAMOFOX_LOG_DIR / "camofox-browser.pid"
CAMOFOX_INSTALL_TIMEOUT = int(os.getenv("CAMOFOX_INSTALL_TIMEOUT", "1800"))
CAMOFOX_HEALTH_WAIT_SECONDS = int(os.getenv("CAMOFOX_HEALTH_WAIT_SECONDS", "120"))
DATE_RE = re.compile(r"\d{4}年\d{1,2}月\d{1,2}日(?:\s+\d{1,2}:\d{2})?")
STOP_MARKERS = [
    "预览时标签不可点",
    "微信扫一扫 关注该公众号",
    "继续滑动看下一个",
    "轻触阅读原文",
    "当前内容可能存在未经审核",
    "写留言",
    "暂无留言",
    "已无更多数据",
    "选择留言身份",
    "选择互动身份",
    "确认提交投诉",
    "发消息",
    "微信扫一扫可打开此内容",
    "篇原创内容 公众号",
]

SKIP_SUBSTRINGS = [
    "Your browser does not support video tags",
    "观看更多",
    "继续观看",
    "分享视频",
    "倍速播放中",
    "切换到横屏模式",
    "退出全屏",
    "全屏",
    "关闭",
    "更多",
    "已关注",
    "关注",
    "赞",
    "推荐",
    "收藏",
    "视频详情",
    "写下你的评论",
    "轻点两下打开表情键盘",
    "轻点两下选择图片",
    "知道了",
    "取消",
    "允许",
]


def _http(method: str, path: str, payload=None, timeout: int = 60):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(CAMOFOX_BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    return json.loads(body)


def _progress(message: str) -> None:
    print(f"[wechat-article-camofox] {message}", file=sys.stderr, flush=True)



def _require_command(command: str) -> None:
    if shutil.which(command):
        return
    hints = {
        "git": "请先安装 git，再重新运行此 skill。",
        "npm": "请先安装 Node.js 18+（需自带 npm），再重新运行此 skill。",
    }
    raise SystemExit(f"Missing required command '{command}'. {hints.get(command, '')}".strip())



def _install_camofox_repo(repo_path: Path | None = None) -> Path:
    repo = (repo_path or CAMOFOX_REPO).expanduser()
    _require_command("git")
    _require_command("npm")
    repo.parent.mkdir(parents=True, exist_ok=True)

    if not (repo / "server.js").exists():
        _progress(f"Installing camofox-browser: cloning repo into {repo}")
        subprocess.run(
            ["git", "clone", "--depth", "1", CAMOFOX_REPO_URL, str(repo)],
            check=True,
            timeout=CAMOFOX_INSTALL_TIMEOUT,
        )
    else:
        _progress(f"Installing camofox-browser: reusing existing repo at {repo}")

    if not (repo / "package.json").exists():
        raise SystemExit(f"camofox-browser install looks incomplete at {repo}")

    if not (repo / "node_modules").exists():
        _progress("Installing camofox-browser: running npm install (first run may take a while)")
        subprocess.run(["npm", "install"], cwd=repo, check=True, timeout=CAMOFOX_INSTALL_TIMEOUT)
    else:
        _progress("Installing camofox-browser: npm dependencies already present")

    return repo



def _start_camofox_server(repo_path: Path | None = None) -> None:
    repo = (repo_path or CAMOFOX_REPO).expanduser()
    start_script = shutil.which("camofox-browser-start")
    env = os.environ.copy()
    env.setdefault("CAMOFOX_BROWSER_REPO", str(repo))
    env.setdefault("CAMOFOX_PORT", str(CAMOFOX_PORT))

    if start_script:
        _progress(f"Starting camofox-browser via helper script on :{CAMOFOX_PORT}")
        subprocess.run([start_script], check=True, timeout=CAMOFOX_HEALTH_WAIT_SECONDS, env=env)
        return

    _require_command("npm")
    if not (repo / "server.js").exists():
        raise SystemExit(f"camofox-browser repo not found at {repo}")

    _progress(f"Starting camofox-browser via npm start on :{CAMOFOX_PORT}")
    CAMOFOX_LOG_DIR.mkdir(parents=True, exist_ok=True)
    with CAMOFOX_LOG_FILE.open("ab") as log_fp:
        proc = subprocess.Popen(
            ["npm", "start"],
            cwd=repo,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=env,
        )
    CAMOFOX_PID_FILE.write_text(str(proc.pid))



def _ensure_camofox() -> None:
    _progress(f"Checking camofox-browser health on :{CAMOFOX_PORT}")
    try:
        _http("GET", "/health", timeout=10)
        _progress("camofox-browser is healthy")
        return
    except Exception:
        _progress("camofox-browser is not healthy yet; bootstrapping now")

    _progress("Installing camofox-browser dependencies")
    repo = _install_camofox_repo()
    _progress("Starting camofox-browser service")
    _start_camofox_server(repo)

    _progress("Waiting for camofox-browser health check to pass")
    deadline = time.time() + CAMOFOX_HEALTH_WAIT_SECONDS
    while time.time() < deadline:
        try:
            _http("GET", "/health", timeout=10)
            _progress("camofox-browser is healthy")
            return
        except Exception:
            time.sleep(1)

    raise SystemExit(
        f"camofox-browser did not become healthy in time. Check {CAMOFOX_LOG_FILE} for details."
    )


def _clean_text(text: str) -> str:
    text = text.replace('\\"', '"').strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\\+$", "", text)
    return text.strip()


def _extract_quoted(line: str) -> str:
    m = re.search(r'"(.*?)"', line)
    return _clean_text(m.group(1)) if m else ""


def _line_depth(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _image_block(item: dict, index: int) -> str:
    src = (item.get('src') or '').strip()
    alt = (item.get('alt') or '').strip()
    if not src:
        return ''
    return f"![{alt or f'image-{index}'}]({src})"


def _normalize_list_text(text: str) -> str:
    text = _clean_text(text)
    text = re.sub(r'^[•·▪◦‣∙●○■□◆◇\-–—]+\s*', '', text)
    return text.strip()


def _apply_prefix(text: str, prefix: str) -> str:
    if not prefix:
        return text
    return '\n'.join(f"{prefix}{line}" if line else prefix.rstrip() for line in text.splitlines())


def _inline_fragment(stripped: str, *, inline: bool) -> str:
    if stripped.startswith('- paragraph:'):
        return stripped.split(':', 1)[1].strip()
    if stripped.startswith('- text:'):
        return stripped.split(':', 1)[1].strip()
    if stripped.startswith('- strong:'):
        text = stripped.split(':', 1)[1].strip()
        return f"**{text}**" if inline and text else text
    if stripped.startswith('- emphasis:'):
        text = stripped.split(':', 1)[1].strip()
        return f"*{text}*" if inline and text else text
    if stripped.startswith('- code:'):
        text = stripped.split(':', 1)[1].strip()
        return f"`{text}`" if inline and text else text
    if stripped.startswith('- link '):
        return _extract_quoted(stripped)
    if stripped.startswith('- listitem:'):
        return stripped.split(':', 1)[1].strip()
    return ''


def _render_inline(entries: list[tuple[int, str]], start: int, end: int, *, list_item: bool = False) -> str:
    fragments: list[str] = []
    for idx in range(start, end):
        _, stripped = entries[idx]
        fragment = _inline_fragment(stripped, inline=idx != start or list_item)
        if not fragment:
            continue
        if list_item:
            fragment = _normalize_list_text(fragment)
            if not fragment:
                continue
        fragments.append(fragment)
    return _clean_text(''.join(fragments))


def _render_images(entries: list[tuple[int, str]], start: int, end: int, image_list: list[dict], image_index: int) -> tuple[list[str], int]:
    blocks: list[str] = []
    for _, stripped in entries[start:end]:
        if not stripped.startswith('- img'):
            continue
        if image_index >= len(image_list):
            break
        img_md = _image_block(image_list[image_index], image_index + 1)
        image_index += 1
        if img_md:
            blocks.append(img_md)
            blocks.append('')
    return blocks, image_index


def _parse_entries(
    entries: list[tuple[int, str]],
    start: int,
    end: int,
    parent_depth: int,
    meta: dict,
    image_list: list[dict],
    image_index: int,
    state: dict,
    *,
    prefix: str = '',
) -> tuple[list[str], int]:
    blocks: list[str] = []
    i = start
    while i < end:
        depth, stripped = entries[i]
        if depth < parent_depth:
            break
        if depth > parent_depth:
            i += 1
            continue

        child_end = i + 1
        while child_end < end and entries[child_end][0] > depth:
            child_end += 1

        if depth > 0 and ('/url:' in stripped or stripped.startswith('- option') or stripped.startswith('- navigation')):
            i = child_end
            continue

        if stripped.startswith('- heading '):
            heading = _extract_quoted(stripped)
            if heading:
                if not meta['title']:
                    meta['title'] = heading
                else:
                    level_match = re.search(r'\[level=(\d+)\]', stripped)
                    level = int(level_match.group(1)) if level_match else 2
                    blocks.append(_apply_prefix(f"{'#' * min(level, 6)} {heading}", prefix))
                    state['started'] = True
            i = child_end
            continue

        if stripped.startswith('- list:'):
            child_depth = entries[i + 1][0] if i + 1 < child_end else depth + 2
            child_blocks, image_index = _parse_entries(
                entries, i + 1, child_end, child_depth, meta, image_list, image_index, state, prefix=prefix
            )
            blocks.extend(child_blocks)
            i = child_end
            continue

        if stripped.startswith('- blockquote'):
            child_depth = entries[i + 1][0] if i + 1 < child_end else depth + 2
            child_blocks, image_index = _parse_entries(
                entries, i + 1, child_end, child_depth, meta, image_list, image_index, state, prefix=prefix + '> '
            )
            blocks.extend(child_blocks)
            i = child_end
            continue

        if stripped.startswith('- figure'):
            image_blocks, image_index = _render_images(entries, i + 1, child_end, image_list, image_index)
            for block in image_blocks:
                blocks.append(_apply_prefix(block, prefix) if block else block)
            if image_blocks:
                state['started'] = True
            i = child_end
            continue

        if stripped.startswith('- link '):
            link_text = _extract_quoted(stripped)
            if link_text:
                if not meta['author'] and not state['started'] and not DATE_RE.search(link_text):
                    meta['author'] = link_text
                elif any(token in link_text for token in STOP_MARKERS):
                    state['stop'] = True
                    break
                elif not any(token in link_text for token in SKIP_SUBSTRINGS) and not link_text.startswith('#') and not link_text.startswith('javascript:'):
                    blocks.append(_apply_prefix(link_text, prefix))
                    state['started'] = True
            i = child_end
            continue

        if stripped.startswith('- separator'):
            blocks.append(_apply_prefix('---', prefix))
            state['started'] = True
            i = child_end
            continue

        if stripped.startswith('- img'):
            image_blocks, image_index = _render_images(entries, i, child_end, image_list, image_index)
            for block in image_blocks:
                blocks.append(_apply_prefix(block, prefix) if block else block)
            if image_blocks:
                state['started'] = True
            i = child_end
            continue

        if stripped.startswith('- button'):
            i = child_end
            continue

        list_item = stripped.startswith('- listitem')
        text = _render_inline(entries, i, child_end, list_item=list_item)
        plain_text = re.sub(r'[*`_]+', '', text)

        if stripped.startswith('- emphasis:') and not meta['published_at'] and DATE_RE.search(plain_text):
            meta['published_at'] = DATE_RE.search(plain_text).group(0)
            i = child_end
            continue

        if any(marker in plain_text for marker in STOP_MARKERS):
            state['stop'] = True
            break
        if any(skip in plain_text for skip in SKIP_SUBSTRINGS):
            i = child_end
            continue

        if stripped.startswith('- code:') and text and not list_item and child_end == i + 1:
            text = f"``` {plain_text} ```"
        elif list_item:
            text = _normalize_list_text(text)
            if text:
                text = f"- {text}"

        if text and plain_text not in {'Original', '原创', '-'}:
            if not (plain_text.startswith('#') and len(plain_text) < 32):
                if not (plain_text.startswith('"') and 'debugging' in plain_text):
                    blocks.append(_apply_prefix(text, prefix))
                    state['started'] = True

        image_blocks, image_index = _render_images(entries, i + 1, child_end, image_list, image_index)
        for block in image_blocks:
            blocks.append(_apply_prefix(block, prefix) if block else block)
        if image_blocks:
            state['started'] = True

        i = child_end

    return blocks, image_index


def _parse_snapshot(snapshot: str, images: list[dict] | None = None) -> tuple[dict, list[str]]:
    meta = {"title": "", "author": "", "published_at": ""}
    blocks: list[str] = []
    image_list = list(images or [])
    image_index = 0
    if image_list and (image_list[0].get('alt') or '').strip() == 'cover_image':
        cover = _image_block(image_list[0], 1)
        if cover:
            blocks.append(cover)
            blocks.append('')
        image_index = 1

    entries = []
    for raw in snapshot.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        if not stripped.startswith('-'):
            continue
        entries.append((_line_depth(line), stripped))

    state = {'started': False, 'stop': False}
    parsed_blocks, image_index = _parse_entries(entries, 0, len(entries), 0, meta, image_list, image_index, state)
    blocks.extend(parsed_blocks)

    cleaned_blocks: list[str] = []
    prev_blank = False
    for block in blocks:
        b = block.strip()
        if not b:
            if not prev_blank and cleaned_blocks:
                cleaned_blocks.append("")
            prev_blank = True
            continue
        prev_blank = False
        cleaned_blocks.append(b)

    while cleaned_blocks and not cleaned_blocks[-1].strip():
        cleaned_blocks.pop()

    return meta, cleaned_blocks


def _fetch_snapshot(user_id: str, tab_id: str) -> str:
    offset = 0
    pieces = []
    seen = set()
    while True:
        query = urllib.parse.urlencode({"userId": user_id, "offset": offset} if offset else {"userId": user_id})
        data = _http("GET", f"/tabs/{tab_id}/snapshot?{query}", timeout=120)
        chunk = data.get("snapshot", "")
        if chunk and chunk not in seen:
            pieces.append(chunk)
            seen.add(chunk)
        if not data.get("hasMore") or not data.get("nextOffset"):
            break
        offset = int(data["nextOffset"])
    return "\n".join(pieces)


def _normalize_images(images: list[dict], article_url: str) -> list[dict]:
    cleaned = []
    seen = set()
    for item in images or []:
        src = str(item.get('src') or '').strip()
        alt = str(item.get('alt') or '').strip()
        if not src or src in seen:
            continue
        seen.add(src)
        if src.startswith('data:'):
            continue
        if src == article_url:
            continue
        if 'res.wx.qq.com/op_res/' in src:
            continue
        if alt in {'跳转二维码', '划线引导图'}:
            continue
        cleaned.append({
            'src': src,
            'alt': alt,
            'width': item.get('width'),
            'height': item.get('height'),
        })
    return cleaned


def _fetch_images(user_id: str, tab_id: str, article_url: str) -> list[dict]:
    query = urllib.parse.urlencode({"userId": user_id, "limit": 50})
    try:
        data = _http("GET", f"/tabs/{tab_id}/images?{query}", timeout=120)
    except Exception:
        return []
    raw = []
    if isinstance(data, list):
        raw = data
    elif isinstance(data, dict) and isinstance(data.get("images"), list):
        raw = data["images"]
    return _normalize_images(raw, article_url)


def _to_markdown(meta: dict, blocks: list[str]) -> str:
    parts = []
    title = meta.get("title") or "Untitled"
    parts.append(f"# {title}")
    info = []
    if meta.get("author"):
        info.append(f"作者：{meta['author']}")
    if meta.get("published_at"):
        info.append(f"发布时间：{meta['published_at']}")
    if info:
        parts.append("")
        parts.append("_" + " · ".join(info) + "_")
    if blocks:
        parts.append("")
        for idx, block in enumerate(blocks):
            if block == "":
                parts.append("")
                continue
            parts.append(block)
            next_block = blocks[idx + 1] if idx + 1 < len(blocks) else ""
            if block.startswith("- "):
                if next_block and not next_block.startswith("- "):
                    parts.append("")
            else:
                parts.append("")
    text = "\n".join(parts)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return text


def fetch_article(url: str, include_images: bool = False) -> dict:
    _ensure_camofox()
    user_id = f"wechat-article-{uuid.uuid4().hex[:8]}"
    session_key = "extract"
    tab_id = None
    try:
        created = _http("POST", "/tabs", {"userId": user_id, "sessionKey": session_key, "url": url}, timeout=120)
        tab_id = created["tabId"]
        snapshot = _fetch_snapshot(user_id, tab_id)
        images = _fetch_images(user_id, tab_id, url) if include_images else []
        meta, blocks = _parse_snapshot(snapshot, images if include_images else None)
        markdown = _to_markdown(meta, blocks)
        return {
            "url": url,
            "title": meta.get("title") or "",
            "author": meta.get("author") or "",
            "published_at": meta.get("published_at") or "",
            "content_markdown": markdown,
            "images": images if include_images else [],
            "source": "camofox_snapshot",
        }
    finally:
        try:
            if tab_id:
                _http("DELETE", f"/tabs/{tab_id}?userId={urllib.parse.quote(user_id)}", timeout=30)
        except Exception:
            pass
        try:
            _http("DELETE", f"/sessions/{urllib.parse.quote(user_id)}", timeout=30)
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract WeChat public account article content via camofox-browser")
    parser.add_argument("url", help="WeChat article URL (mp.weixin.qq.com/s/...)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--include-images", action="store_true", default=False)
    parser.add_argument("--save", default=None, help="Optional output file")
    args = parser.parse_args()

    result = fetch_article(args.url, include_images=args.include_images)
    rendered = result["content_markdown"] if args.format == "markdown" else json.dumps(result, ensure_ascii=False, indent=2)

    if args.save:
        out = Path(args.save).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered)
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
