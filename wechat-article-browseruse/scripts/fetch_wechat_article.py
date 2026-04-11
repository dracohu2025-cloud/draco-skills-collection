#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_PROXY_COUNTRY = os.getenv("BROWSER_USE_PROXY_COUNTRY", "hk")
DEFAULT_TIMEOUT_SECONDS = max(30, min(int(os.getenv("BROWSER_USE_TIMEOUT", "240")), 240))
DEFAULT_WAIT_MS = max(0, int(os.getenv("BROWSER_USE_WAIT_MS", "8000")))
WECHAT_URL_RE = re.compile(r"^https?://mp\.weixin\.qq\.com/s/", re.I)
BOLD_JOIN_RE = re.compile(r"\*\*([^*]+)\*\*\*\*([^*]+)\*\*")

NOISE_SELECTORS = [
    "script",
    "style",
    "svg",
    "iframe",
    "form",
    "button",
    ".js_uneditable",
    ".wx_profile_card_inner",
    ".original_primary_card_tips",
    ".weui-desktop-mass-appmsg__comment",
]


def _progress(message: str) -> None:
    print(f"[wechat-article-browseruse] {message}", file=sys.stderr, flush=True)



def _clean_text(text: str) -> str:
    text = (text or "").replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()



def _resolve_api_key() -> str:
    api_key = os.getenv("BROWSER_USE_API_KEY") or os.getenv("BROWSERUSE_API_KEY")
    if api_key:
        return api_key.strip()
    raise SystemExit(
        "Missing BrowserUse API key. Set BROWSER_USE_API_KEY or BROWSERUSE_API_KEY before running this skill."
    )



def _load_runtime_deps():
    try:
        from browser_use_sdk.v3 import AsyncBrowserUse
        from playwright.async_api import async_playwright
        from bs4 import BeautifulSoup
        from markdownify import markdownify as markdownify_fn
    except ImportError as exc:
        raise SystemExit(
            "Missing Python dependencies. Install them with: "
            "python -m pip install browser-use-sdk playwright beautifulsoup4 markdownify"
        ) from exc
    return AsyncBrowserUse, async_playwright, BeautifulSoup, markdownify_fn



def _prepare_html(html: str, include_images: bool = True) -> str:
    _, _, BeautifulSoup, _ = _load_runtime_deps()
    soup = BeautifulSoup(html or "", "html.parser")

    for selector in NOISE_SELECTORS:
        for node in soup.select(selector):
            node.decompose()

    for img in list(soup.find_all("img")):
        src = (img.get("data-src") or img.get("data-backsrc") or img.get("src") or "").strip()
        alt = _clean_text(img.get("alt") or img.get("data-alt") or "")
        if not include_images or not src or src.startswith("data:") or "res.wx.qq.com/op_res/" in src:
            img.decompose()
            continue
        img["src"] = src
        if alt:
            img["alt"] = alt
        elif img.has_attr("alt"):
            del img["alt"]

    return str(soup)



def _cleanup_markdown(text: str) -> str:
    cleaned = (text or "").replace("\r\n", "\n").replace("\xa0", " ")
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    while True:
        updated = BOLD_JOIN_RE.sub(lambda m: f"**{m.group(1)}{m.group(2)}**", cleaned)
        if updated == cleaned:
            break
        cleaned = updated
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()



def _normalize_images(images: list[dict], article_url: str) -> list[dict]:
    cleaned: list[dict] = []
    seen: set[str] = set()
    for item in images or []:
        src = _clean_text(item.get("src") or item.get("data_src") or "")
        alt = _clean_text(item.get("alt") or "")
        if not src or src.startswith("data:") or src == article_url or src in seen:
            continue
        if "res.wx.qq.com/op_res/" in src:
            continue
        seen.add(src)
        cleaned.append({"src": src, "alt": alt})
    return cleaned



def _html_to_markdown(html: str) -> str:
    _, _, _, markdownify_fn = _load_runtime_deps()
    markdown = markdownify_fn(html or "", heading_style="ATX", strip_document=None)
    return _cleanup_markdown(markdown)



def _text_to_markdown(text: str) -> str:
    lines = [_clean_text(line) for line in (text or "").splitlines()]
    parts = [line for line in lines if line]
    return _cleanup_markdown("\n\n".join(parts))



def _to_markdown(meta: dict) -> str:
    title = _clean_text(meta.get("title") or "") or "Untitled"
    parts = [f"# {title}"]
    info = []
    if _clean_text(meta.get("author") or ""):
        info.append(f"作者：{_clean_text(meta['author'])}")
    if _clean_text(meta.get("published_at") or ""):
        info.append(f"发布时间：{_clean_text(meta['published_at'])}")
    if info:
        parts.extend(["", "_" + " · ".join(info) + "_"])
    content = _cleanup_markdown(meta.get("content_markdown") or "")
    if content:
        parts.extend(["", content])
    return "\n".join(parts).rstrip() + "\n"



def _validate_url(url: str) -> None:
    if not WECHAT_URL_RE.search(url):
        raise SystemExit("Expected a WeChat article URL like https://mp.weixin.qq.com/s/...")


async def _extract_article_payload(url: str, *, proxy_country: str, timeout_seconds: int, wait_ms: int) -> dict:
    AsyncBrowserUse, async_playwright, _, _ = _load_runtime_deps()
    api_key = _resolve_api_key()
    client = AsyncBrowserUse(api_key=api_key)
    browser = None
    remote = None
    try:
        _progress(f"Starting BrowserUse browser (proxy={proxy_country or 'default'})")
        create_kwargs = {"timeout": max(30, min(int(timeout_seconds), 240))}
        if proxy_country:
            create_kwargs["proxy_country_code"] = proxy_country.lower()
        browser = await client.browsers.create(**create_kwargs)

        async with async_playwright() as p:
            remote = await p.chromium.connect_over_cdp(browser.cdp_url)
            context = remote.contexts[0] if remote.contexts else await remote.new_context()
            page = context.pages[0] if context.pages else await context.new_page()
            page.set_default_timeout(max(30000, timeout_seconds * 1000))

            _progress("Opening WeChat article")
            await page.goto(url, wait_until="commit", timeout=max(30000, timeout_seconds * 1000))
            await page.wait_for_selector("#js_content, #img-content", timeout=max(30000, timeout_seconds * 1000))
            if wait_ms:
                _progress(f"Waiting {wait_ms}ms for lazy content")
                await page.wait_for_timeout(wait_ms)

            payload = await page.evaluate(
                """() => {
                    const root = document.querySelector('#js_content') || document.querySelector('#img-content');
                    const title = document.querySelector('#activity-name')?.innerText
                      || document.querySelector('h1')?.innerText
                      || document.title
                      || '';
                    const author = document.querySelector('#js_name')?.innerText
                      || document.querySelector('.wx_tap_link.js_wx_tap_highlight.nickname')?.innerText
                      || document.querySelector('.account_nickname_inner')?.innerText
                      || '';
                    const publishedAt = document.querySelector('#publish_time')?.innerText
                      || document.querySelector('.publish_time')?.innerText
                      || '';
                    const images = root
                      ? Array.from(root.querySelectorAll('img')).map((img) => ({
                          src: img.getAttribute('data-src') || img.getAttribute('data-backsrc') || img.getAttribute('src') || '',
                          alt: img.getAttribute('alt') || img.getAttribute('data-alt') || '',
                        }))
                      : [];
                    return {
                      title,
                      author,
                      published_at: publishedAt,
                      html: root?.innerHTML || '',
                      text: root?.innerText || '',
                      images,
                    };
                }"""
            )
            return payload
    finally:
        if remote is not None:
            try:
                await remote.close()
            except Exception:
                pass
        if browser is not None:
            try:
                await client.browsers.stop(str(browser.id))
            except Exception:
                pass



def fetch_article(
    url: str,
    *,
    include_images: bool = False,
    proxy_country: str = DEFAULT_PROXY_COUNTRY,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    wait_ms: int = DEFAULT_WAIT_MS,
) -> dict:
    _validate_url(url)
    payload = asyncio.run(
        _extract_article_payload(
            url,
            proxy_country=proxy_country,
            timeout_seconds=timeout_seconds,
            wait_ms=wait_ms,
        )
    )
    images = _normalize_images(payload.get("images") or [], article_url=url)
    html = _prepare_html(payload.get("html") or "", include_images=include_images)
    content_markdown = _html_to_markdown(html) if html.strip() else ""
    if not content_markdown:
        content_markdown = _text_to_markdown(payload.get("text") or "")

    meta = {
        "url": url,
        "title": _clean_text(payload.get("title") or ""),
        "author": _clean_text(payload.get("author") or ""),
        "published_at": _clean_text(payload.get("published_at") or ""),
        "content_markdown": content_markdown,
        "images": images if include_images else [],
        "source": "browseruse_cdp_html",
    }
    meta["content_markdown"] = _to_markdown(meta)
    return meta



def main() -> int:
    parser = argparse.ArgumentParser(description="Extract WeChat public account article content via BrowserUse cloud browser")
    parser.add_argument("url", help="WeChat article URL (mp.weixin.qq.com/s/...)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--include-images", action="store_true", default=False)
    parser.add_argument("--save", default=None, help="Optional output file")
    parser.add_argument("--proxy-country", default=DEFAULT_PROXY_COUNTRY, help="BrowserUse proxy country code (default: hk)")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="Browser session timeout, max 240")
    parser.add_argument("--wait-ms", type=int, default=DEFAULT_WAIT_MS, help="Extra wait time for lazy-loaded article content")
    args = parser.parse_args()

    result = fetch_article(
        args.url,
        include_images=args.include_images,
        proxy_country=args.proxy_country,
        timeout_seconds=args.timeout_seconds,
        wait_ms=args.wait_ms,
    )
    rendered = result["content_markdown"] if args.format == "markdown" else json.dumps(result, ensure_ascii=False, indent=2)

    if args.save:
        out = Path(args.save).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered)
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
