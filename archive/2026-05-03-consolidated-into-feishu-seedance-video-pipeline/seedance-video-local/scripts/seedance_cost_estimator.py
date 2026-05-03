#!/usr/bin/env python3
"""Seedance video token/cost estimator.

公式（来自官方示意图）：
tokens = (width * height * fps * duration) / 1024 * count
cost_cny = tokens / 1000 * price_per_1k_cny
"""

from __future__ import annotations


def _parse_resolution(resolution: str) -> int:
    s = str(resolution).strip().lower()
    if s.endswith("p"):
        s = s[:-1]
    value = int(s)
    if value <= 0:
        raise ValueError("resolution 必须为正整数，如 480p/720p")
    return value


def _parse_ratio(ratio: str) -> tuple[int, int]:
    s = str(ratio).strip()
    if ":" not in s:
        raise ValueError("ratio 必须形如 16:9")
    a, b = s.split(":", 1)
    w = int(a)
    h = int(b)
    if w <= 0 or h <= 0:
        raise ValueError("ratio 分子分母必须 > 0")
    return w, h


def _to_even(x: int) -> int:
    return x if x % 2 == 0 else x + 1


def estimate_dimensions(resolution: str, ratio: str) -> tuple[int, int]:
    """从 resolution + ratio 估算宽高。

    规则：
    - 横屏/方屏（ratio>=1）：height=resolution, width=height*ratio
    - 竖屏（ratio<1）：width=resolution, height=width/ratio
    - 输出调整为偶数像素
    """
    base = _parse_resolution(resolution)
    rw, rh = _parse_ratio(ratio)
    r = rw / rh

    if r >= 1:
        h = base
        w = round(h * r)
    else:
        w = base
        h = round(w / r)

    return _to_even(int(w)), _to_even(int(h))


def estimate_tokens(width: int, height: int, fps: float, duration: float, count: float) -> float:
    return (float(width) * float(height) * float(fps) * float(duration)) / 1024.0 * float(count)


def estimate_cost_cny(tokens: float, price_per_1k: float = 0.046) -> float:
    return float(tokens) / 1000.0 * float(price_per_1k)


def estimate_from_video_params(
    *,
    resolution: str,
    ratio: str,
    duration: float,
    fps: float = 24,
    count: float = 1,
    price_per_1k: float = 0.046,
    width: int | None = None,
    height: int | None = None,
) -> dict:
    if width is None or height is None:
        width2, height2 = estimate_dimensions(resolution, ratio)
        width = width or width2
        height = height or height2

    tokens = estimate_tokens(width, height, fps, duration, count)
    cost = estimate_cost_cny(tokens, price_per_1k)
    return {
        "width": int(width),
        "height": int(height),
        "fps": float(fps),
        "duration": float(duration),
        "count": float(count),
        "tokens": float(tokens),
        "price_per_1k_cny": float(price_per_1k),
        "estimated_cost_cny": float(cost),
        "formula": "tokens=(width*height*fps*duration)/1024*count; cost=tokens/1000*price_per_1k",
        "note": "智能比例/智能时长下为估算值，实际以最终生成结果为准",
    }
