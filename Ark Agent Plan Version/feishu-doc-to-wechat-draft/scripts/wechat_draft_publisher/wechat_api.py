from __future__ import annotations

import json
import html as html_lib
import mimetypes
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class WechatAPIError(RuntimeError):
    pass


class Transport(Protocol):
    def request(self, *, method: str, url: str, params=None, data=None, files=None) -> dict: ...


@dataclass(slots=True)
class TokenCache:
    path: Path
    skew_seconds: int = 300

    def load(self, *, now: int | None = None) -> str | None:
        if not self.path.exists():
            return None
        payload = json.loads(self.path.read_text())
        now = int(time.time()) if now is None else now
        if payload.get("expires_at", 0) <= now + self.skew_seconds:
            return None
        return payload.get("access_token")

    def save(self, *, token: str, expires_in: int, now: int | None = None) -> None:
        now = int(time.time()) if now is None else now
        payload = {
            "access_token": token,
            "expires_at": now + int(expires_in),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=False))


class UrllibTransport:
    def request(self, *, method: str, url: str, params=None, data=None, files=None) -> dict:
        params = params or {}
        if params:
            url = f"{url}?{urlencode(params)}"

        headers = {}
        body = None

        if files:
            body, content_type = _encode_multipart(data or {}, files)
            headers["Content-Type"] = content_type
        elif data is not None:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"

        request = Request(url=url, data=body, method=method.upper(), headers=headers)
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
        payload = json.loads(raw)
        _raise_if_wechat_error(payload)
        return payload


@dataclass(slots=True)
class WechatClient:
    appid: str
    appsecret: str
    transport: Transport | None = None
    token_cache: TokenCache | None = None

    def __post_init__(self) -> None:
        if self.transport is None:
            self.transport = UrllibTransport()
        if self.token_cache is None:
            safe_appid = (self.appid or "default").strip() or "default"
            self.token_cache = TokenCache(Path.home() / ".cache/wechat-draft-publisher" / f"access_token_{safe_appid}.json")

    def get_access_token(self, *, now: int | None = None) -> str:
        payload = self.transport.request(
            method="POST",
            url="https://api.weixin.qq.com/cgi-bin/stable_token",
            data={
                "grant_type": "client_credential",
                "appid": self.appid,
                "secret": self.appsecret,
                "force_refresh": True,
            },
        )
        token = payload["access_token"]
        self.token_cache.save(token=token, expires_in=payload.get("expires_in", 7200), now=now)
        return token

    def upload_content_image(self, path: str, access_token: str) -> str:
        payload = self.transport.request(
            method="POST",
            url="https://api.weixin.qq.com/cgi-bin/media/uploadimg",
            params={"access_token": access_token},
            files={"media": _prepare_file_tuple(path)},
        )
        return payload["url"]

    def upload_cover_image(self, path: str, access_token: str) -> str:
        payload = self.transport.request(
            method="POST",
            url="https://api.weixin.qq.com/cgi-bin/material/add_material",
            params={"access_token": access_token, "type": "image"},
            files={"media": _prepare_file_tuple(path)},
        )
        return payload["media_id"]

    def upload_video_material(self, path: str, access_token: str, *, title: str, introduction: str) -> str:
        payload = self.transport.request(
            method="POST",
            url="https://api.weixin.qq.com/cgi-bin/material/add_material",
            params={"access_token": access_token, "type": "video"},
            data={"description": json.dumps({"title": title, "introduction": introduction}, ensure_ascii=False)},
            files={"media": _prepare_file_tuple(path)},
        )
        return payload["media_id"]

    def add_draft(self, payload: dict, access_token: str) -> str:
        response = self.transport.request(
            method="POST",
            url="https://api.weixin.qq.com/cgi-bin/draft/add",
            params={"access_token": access_token},
            data=payload,
        )
        return response["media_id"]


def _get_feishu_access_token() -> str:
    """Get Feishu tenant_access_token using app credentials."""
    import os
    import json
    from urllib.request import Request, urlopen
    
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")
    
    if not app_id or not app_secret:
        raise RuntimeError("FEISHU_APP_ID and FEISHU_APP_SECRET environment variables are required")
    
    request = Request(
        url="https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=json.dumps({"app_id": app_id, "app_secret": app_secret}).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )
    
    with urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
    
    if result.get("code") != 0:
        raise RuntimeError(f"Feishu auth error: {result}")
    
    return result["tenant_access_token"]


def _download_lark_media(token: str, output_dir: Path, filename: str | None = None) -> Path:
    """Download media/file token from Lark docs to a local path."""
    safe_filename = _safe_local_filename(filename or f"lark_media_{token[:16]}.bin")
    output_path = output_dir / safe_filename

    original_cwd = Path.cwd()
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        os.chdir(output_dir)
        result = subprocess.run(
            [
                "lark-cli",
                "docs",
                "+media-download",
                "--token",
                token,
                "--output",
                f"./{safe_filename}",
                "--overwrite",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "failed to download Lark media")
        payload = json.loads(result.stdout)
        if not payload.get("ok"):
            raise RuntimeError(f"Lark media download error: {payload}")
    finally:
        os.chdir(original_cwd)

    return output_path


def _download_lark_image(token: str, output_dir: Path) -> Path:
    """Download image from Lark document using lark-cli."""
    return _download_lark_media(token, output_dir, filename=f"lark_img_{token[:16]}.jpg")


def _extract_video_poster(video_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    poster_path = output_dir / f"{video_path.stem}-cover.jpg"
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            "thumbnail,scale='min(1280,iw)':-2",
            "-frames:v",
            "1",
            str(poster_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not poster_path.exists():
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "failed to extract video poster")
    return poster_path


def rewrite_html_images(*, html: str, article_dir: Path, client, access_token: str | None = None) -> str:
    rewritten_html, _ = rewrite_html_assets(
        html=html,
        article_dir=article_dir,
        client=client,
        access_token=access_token,
        source_url=None,
    )
    return rewritten_html


def rewrite_html_assets(*, html: str, article_dir: Path, client, access_token: str, source_url: str | None = None) -> tuple[str, list[dict]]:
    image_pattern = re.compile(r'(<img\b[^>]*?src=")([^"]+)("[^>]*>)')
    video_pattern = re.compile(r'<figure class="md-video-card"(?P<attrs>[^>]*)>.*?</figure>', re.S)
    video_materials: list[dict] = []

    def replace_image(match):
        prefix, src, suffix = match.groups()
        if src.startswith("http://") or src.startswith("https://"):
            return match.group(0)

        if src.startswith("lark-image://"):
            token = src.replace("lark-image://", "")
            try:
                image_path = _download_lark_image(token, article_dir)
                image_path = _ensure_wechat_supported_image(image_path)
                uploaded = client.upload_content_image(str(image_path), access_token)
                return f"{prefix}{uploaded}{suffix}"
            except Exception as e:
                raise RuntimeError(f"Failed to sync Lark image {token}; aborting draft publish to avoid missing images") from e

        image_path = _ensure_wechat_supported_image((article_dir / src).resolve())
        uploaded = client.upload_content_image(str(image_path), access_token)
        return f"{prefix}{uploaded}{suffix}"

    def replace_video(match):
        attrs = match.group('attrs')
        token_match = re.search(r'data-video-token="([^"]+)"', attrs)
        name_match = re.search(r'data-video-name="([^"]+)"', attrs)
        if not token_match or not name_match:
            return match.group(0)

        token = html_lib.unescape(token_match.group(1))
        name = html_lib.unescape(name_match.group(1))
        introduction = f"来自飞书文档同步的视频素材：{name}"
        title = Path(name).stem[:64] or "Feishu video"

        try:
            video_path = _download_lark_media(token, article_dir, filename=name)
            media_id = client.upload_video_material(str(video_path), access_token, title=title, introduction=introduction)
            poster_path = _extract_video_poster(video_path, article_dir)
            cover_url = client.upload_content_image(str(poster_path), access_token)
        except Exception as e:
            print(f"Warning: Failed to sync Lark video {token}: {e}")
            return _render_failed_video_card(name)

        video_materials.append(
            {
                "token": token,
                "name": name,
                "media_id": media_id,
                "cover_url": cover_url,
                "source_url": source_url,
            }
        )
        return _render_synced_video_card(name=name, cover_url=cover_url)

    html = image_pattern.sub(replace_image, html)
    html = video_pattern.sub(replace_video, html)
    return html, video_materials


def _safe_local_filename(name: str) -> str:
    sanitized = re.sub(r'[^0-9A-Za-z._-]+', '-', name).strip('-')
    return sanitized or 'lark-media.bin'


def _ensure_wechat_supported_image(path: Path) -> Path:
    """Convert formats unsupported by WeChat image upload, especially Lark-downloaded WebP."""
    try:
        from PIL import Image
    except Exception:
        return path

    try:
        image = Image.open(path)
        fmt = (image.format or "").upper()
    except Exception:
        return path

    if fmt in {"JPEG", "JPG", "PNG", "GIF", "BMP"}:
        return path

    converted = path.with_suffix(".wechat.jpg")
    if image.mode in {"RGBA", "LA"}:
        bg = Image.new("RGB", image.size, (255, 255, 255))
        bg.paste(image, mask=image.getchannel("A"))
        image = bg
    else:
        image = image.convert("RGB")
    converted.parent.mkdir(parents=True, exist_ok=True)
    image.save(converted, "JPEG", quality=92)
    return converted


def _render_synced_video_card(*, name: str, cover_url: str) -> str:
    safe_name = html_lib.escape(name)
    return (
        '<figure class="md-video-card md-video-card-synced" '
        'style="margin: 1.5em 8px; border-radius: 12px; overflow: hidden; border: 1px solid rgba(15,23,42,.08); background: #fff; box-shadow: 0 8px 24px rgba(15,23,42,.06);">'
        f'<img class="md-img" style="display: block; width: 100%; max-width: 100%; border-radius: 0; box-shadow: none;" src="{cover_url}" alt="{safe_name}" />'
        '<figcaption class="md-video-card-caption" style="padding: 12px 14px; color: #24292f; font-size: .95em; line-height: 1.7; text-align: left;">'
        f'<strong style="display:block; color:#24292f;">视频：{safe_name}</strong>'
        '<span style="color:#6b7280;">已同步到公众号视频素材库；公众号正文暂不支持内嵌播放。</span>'
        '</figcaption>'
        '</figure>'
    )


def _render_failed_video_card(name: str) -> str:
    safe_name = html_lib.escape(name)
    return (
        '<figure class="md-video-card md-video-card-fallback" '
        'style="margin: 1.5em 8px; border-radius: 12px; overflow: hidden; border: 1px solid rgba(15,23,42,.08); background: #fff7ed;">'
        '<section class="md-video-card-poster" style="display:flex; align-items:center; justify-content:center; min-height: 120px; background: linear-gradient(135deg, rgba(250,81,81,.92), rgba(15,76,129,.92)); color:#fff; font-size:40px;">▶</section>'
        '<figcaption class="md-video-card-caption" style="padding: 12px 14px; color: #24292f; font-size: .95em; line-height: 1.7; text-align: left;">'
        f'<strong style="display:block; color:#24292f;">视频：{safe_name}</strong>'
        '<span style="color:#9a3412;">视频素材同步失败，正文暂以占位卡片保留。</span>'
        '</figcaption>'
        '</figure>'
    )


def _prepare_file_tuple(path: str) -> tuple[str, bytes, str]:
    file_path = Path(path)
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    return file_path.name, file_path.read_bytes(), content_type


def _encode_multipart(fields: dict, files: dict) -> tuple[bytes, str]:
    boundary = f"----HermesWechatDraftBoundary{int(time.time() * 1000)}"
    chunks: list[bytes] = []

    for key, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )

    for key, (filename, content, content_type) in files.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'
                    f"Content-Type: {content_type}\r\n\r\n"
                ).encode(),
                content,
                b"\r\n",
            ]
        )

    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _raise_if_wechat_error(payload: dict) -> None:
    errcode = payload.get("errcode", 0)
    if errcode not in (0, None):
        raise WechatAPIError(f"WeChat API error {errcode}: {payload.get('errmsg', '')}")
