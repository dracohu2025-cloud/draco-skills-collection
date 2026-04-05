from __future__ import annotations

import json
import mimetypes
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
            self.token_cache = TokenCache(Path.home() / ".cache/wechat-draft-publisher/access_token.json")

    def get_access_token(self, *, now: int | None = None) -> str:
        cached = self.token_cache.load(now=now)
        if cached:
            return cached
        payload = self.transport.request(
            method="GET",
            url="https://api.weixin.qq.com/cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": self.appid,
                "secret": self.appsecret,
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


def _download_lark_image(token: str, output_dir: Path) -> Path:
    """Download image from Lark document using lark-cli."""
    import subprocess
    import json
    import os
    
    # lark-cli requires relative paths, so we need to change to the output directory
    output_filename = f"lark_img_{token[:16]}.jpg"
    output_path = output_dir / output_filename
    
    # Change to output directory and use relative path
    original_cwd = os.getcwd()
    try:
        os.chdir(output_dir)
        
        # Use lark-cli docs +media-download command with relative path
        result = subprocess.run(
            ["lark-cli", "docs", "+media-download", 
             "--token", token,
             "--output", output_filename,
             "--overwrite"],
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to download Lark image: {result.stderr}")
        
        # Parse the output to verify success
        try:
            response = json.loads(result.stdout)
            if not response.get("ok"):
                raise RuntimeError(f"Lark download error: {response}")
        except json.JSONDecodeError:
            # If output is not JSON, check if file was created
            if not output_path.exists():
                raise RuntimeError(f"Image download failed: {result.stdout}")
    finally:
        os.chdir(original_cwd)
    
    return output_path


def rewrite_html_images(*, html: str, article_dir: Path, client, access_token: str | None = None) -> str:
    import re

    pattern = re.compile(r'(<img\b[^>]*?src=")([^"]+)("[^>]*>)')

    def replacer(match):
        prefix, src, suffix = match.groups()
        if src.startswith("http://") or src.startswith("https://"):
            return match.group(0)
        
        # Handle Lark image URLs
        if src.startswith("lark-image://"):
            token = src.replace("lark-image://", "")
            try:
                image_path = _download_lark_image(token, article_dir)
                if access_token is None:
                    uploaded = client.upload_content_image(str(image_path))
                else:
                    uploaded = client.upload_content_image(str(image_path), access_token)
                return f"{prefix}{uploaded}{suffix}"
            except Exception as e:
                # If download fails, return the original and log warning
                print(f"Warning: Failed to download Lark image {token}: {e}")
                return match.group(0)
        
        # Handle local image paths
        image_path = (article_dir / src).resolve()
        if access_token is None:
            uploaded = client.upload_content_image(str(image_path))
        else:
            uploaded = client.upload_content_image(str(image_path), access_token)
        return f"{prefix}{uploaded}{suffix}"

    return pattern.sub(replacer, html)


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
