#!/usr/bin/env python3
"""
TTS + 音频静默检测 beats 生成器
输入：vocab config JSON
输出：每个 scene 的 mp3 + beats JSON（startFrame/endFrame）
"""

import argparse
import base64
import json
import math
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

try:
    from pydub import AudioSegment
    from pydub.silence import detect_nonsilent
except ImportError as e:
    print(f"Missing pydub: {e}", file=sys.stderr)
    sys.exit(1)

DEFAULT_FPS = 30
MIN_SILENCE_LEN = 300  # ms
SILENCE_THRESH = -42   # dBFS
COST_PER_10K_CHARS = 3.0  # 豆包 TTS 2.0 后付费单价：3元/万字符


def choose_voice(voice: str) -> str:
    if voice == "male":
        return os.environ["VOLCENGINE_TTS_VOICE_TYPE_MALE"]
    return os.environ["VOLCENGINE_TTS_VOICE_TYPE_FEMALE"]


def synthesize_volcengine(text: str, voice: str = "female") -> bytes:
    token = os.environ["VOLCENGINE_TTS_ACCESS_TOKEN"]
    payload = {
        "app": {
            "appid": os.environ["VOLCENGINE_TTS_APP_ID"],
            "token": token,
            "cluster": "volcano_tts",
        },
        "user": {"uid": "hermes-volcengine-tts-local"},
        "audio": {
            "voice_type": choose_voice(voice),
            "encoding": "mp3",
            "speed_ratio": 1.0,
            "volume_ratio": 1.0,
            "pitch_ratio": 1.0,
            "language": "zh-CN",
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "operation": "query",
            "with_frontend": 1,
            "frontend_type": "unitTson",
            "resource_id": os.environ["VOLCENGINE_TTS_2_RESOURCE_ID"],
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        "https://openspeech.bytedance.com/api/v1/tts",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer; {token}",
        },
        method="POST",
    )
    with urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8")
    result = json.loads(raw)
    if result.get("code") != 3000 or not result.get("data"):
        raise RuntimeError(f"Volcengine TTS error: {result}")
    return base64.b64decode(result["data"])


def ms_to_frame(ms: int, fps: int) -> int:
    return int(round(ms / 1000 * fps))


def split_beats_by_silence(audio: AudioSegment, beat_texts: list[str], fps: int = DEFAULT_FPS):
    """
    通过静默检测将音频切分为与 beat_texts 数量匹配的段落。
    返回 beats: [{startFrame, endFrame, text}, ...]
    """
    nonsilent = detect_nonsilent(audio, min_silence_len=MIN_SILENCE_LEN, silence_thresh=SILENCE_THRESH)
    target = len(beat_texts)
    total_ms = len(audio)

    print(f"  detected {len(nonsilent)} nonsilent ranges, target beats={target}")

    if not nonsilent:
        segment_ms = total_ms / target
        ranges = [(int(i * segment_ms), int((i + 1) * segment_ms)) for i in range(target)]
    elif len(nonsilent) == target:
        ranges = nonsilent
    elif len(nonsilent) > target:
        ranges = list(nonsilent)
        while len(ranges) > target:
            shortest_idx = min(range(len(ranges)), key=lambda i: ranges[i][1] - ranges[i][0])
            left_dur = ranges[shortest_idx][0] - ranges[shortest_idx - 1][0] if shortest_idx > 0 else math.inf
            right_dur = ranges[shortest_idx + 1][1] - ranges[shortest_idx][0] if shortest_idx < len(ranges) - 1 else math.inf
            if left_dur <= right_dur and shortest_idx > 0:
                ranges[shortest_idx - 1] = (ranges[shortest_idx - 1][0], ranges[shortest_idx][1])
                ranges.pop(shortest_idx)
            elif shortest_idx < len(ranges) - 1:
                ranges[shortest_idx] = (ranges[shortest_idx][0], ranges[shortest_idx + 1][1])
                ranges.pop(shortest_idx + 1)
            else:
                ranges[shortest_idx - 1] = (ranges[shortest_idx - 1][0], ranges[shortest_idx][1])
                ranges.pop(shortest_idx)
    else:
        ranges = list(nonsilent)
        while len(ranges) < target:
            gaps = []
            for i in range(len(ranges) - 1):
                gap = ranges[i + 1][0] - ranges[i][1]
                gaps.append((gap, i))
            if not gaps:
                break
            gaps.sort(reverse=True)
            gap_ms, idx = gaps[0]
            split_at = ranges[idx][1] + gap_ms // 2
            ranges.insert(idx + 1, (split_at, ranges[idx + 1][1]))
            ranges[idx] = (ranges[idx][0], split_at)
        while len(ranges) < target:
            longest_idx = max(range(len(ranges)), key=lambda i: ranges[i][1] - ranges[i][0])
            mid = (ranges[longest_idx][0] + ranges[longest_idx][1]) // 2
            ranges.insert(longest_idx + 1, (mid, ranges[longest_idx][1]))
            ranges[longest_idx] = (ranges[longest_idx][0], mid)

    adjusted = []
    for i, (start, end) in enumerate(ranges):
        start = max(0, start - 50)
        end = min(total_ms, end + 50)
        adjusted.append((start, end))

    beats = []
    for i, (start, end) in enumerate(adjusted):
        text = beat_texts[i] if i < len(beat_texts) else ""
        beats.append({
            "startFrame": ms_to_frame(start, fps),
            "endFrame": ms_to_frame(end, fps),
            "text": text,
        })

    return beats


def process_scene(scene_index: int, scene: dict, audio_prefix: str, fps: int, voice: str, out_dir: Path):
    beats_input = scene.get("beats", [])
    if not beats_input:
        print(f"  Scene {scene_index}: no beats, skip")
        return 0

    texts = [b["text"] for b in beats_input]
    full_text = "。".join(texts) + "。"
    char_count = len(full_text)
    print(f"Scene {scene_index}: synthesizing TTS for {len(texts)} beats, {char_count} chars...")

    audio_bytes = synthesize_volcengine(full_text, voice)
    audio_path = out_dir / f"scene{scene_index}.mp3"
    audio_path.write_bytes(audio_bytes)
    print(f"  saved {audio_path} ({len(audio_bytes)} bytes)")

    audio = AudioSegment.from_mp3(str(audio_path))
    detected_beats = split_beats_by_silence(audio, texts, fps)

    # 确保音频尾部有足够余量，防止 TTS 在视频末尾被截断
    last_end_frame = detected_beats[-1]["endFrame"] if detected_beats else 0
    current_frames = int(len(audio) / 1000 * fps)
    if current_frames < last_end_frame + 40:
        needed_frames = last_end_frame + 40 - current_frames
        needed_ms = math.ceil(needed_frames / fps * 1000)
        padding = AudioSegment.silent(duration=needed_ms)
        audio = audio + padding
        audio.export(audio_path, format="mp3")
        print(f"  appended {needed_ms}ms silence tail to prevent truncation")
    else:
        print(f"  appended 0ms silence tail to prevent truncation")

    beats_path = out_dir / f"scene{scene_index}-beats.json"
    beats_path.write_text(json.dumps(detected_beats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  saved {beats_path}")
    for b in detected_beats:
        print(f"    [{b['startFrame']:4d} - {b['endFrame']:4d}] {b['text']}")

    return char_count


def log_cost(project_root: Path, word: str, total_chars: int, cost: float, scenes_count: int, beats_count: int):
    log_path = project_root / "data" / "tts-cost-log.jsonl"
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "word": word,
        "totalChars": total_chars,
        "costCNY": round(cost, 6),
        "scenesCount": scenes_count,
        "beatsCount": beats_count,
        "unitPrice": f"{COST_PER_10K_CHARS}元/万字符",
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def print_cost_report(word: str, total_chars: int, cost: float, scene_details: list):
    print("\n" + "=" * 50)
    print(f"TTS 成本统计报告 — {word}")
    print("=" * 50)
    for idx, chars in scene_details:
        scene_cost = chars / 10000 * COST_PER_10K_CHARS
        print(f"  Scene {idx}: {chars:4d} 字符 → ¥{scene_cost:.4f}")
    print("-" * 50)
    print(f"  总计: {total_chars} 字符")
    print(f"  单价: {COST_PER_10K_CHARS}元/万字符")
    print(f"  实际 TTS 成本: ¥{cost:.4f}")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="vocab config JSON path")
    parser.add_argument("--public-dir", default="public", help="project public directory")
    parser.add_argument("--voice", choices=["female", "male"], default="female")
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS)
    args = parser.parse_args()

    required_env = [
        "VOLCENGINE_TTS_ACCESS_TOKEN",
        "VOLCENGINE_TTS_APP_ID",
        "VOLCENGINE_TTS_VOICE_TYPE_FEMALE",
        "VOLCENGINE_TTS_VOICE_TYPE_MALE",
        "VOLCENGINE_TTS_2_RESOURCE_ID",
    ]
    missing = [k for k in required_env if not os.getenv(k)]
    if missing:
        print(f"Missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    config_path = Path(args.input)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    audio_prefix = config.get("audioPrefix", "word-audio-v1")
    fps = config.get("fps", args.fps)
    word = config.get("word", config_path.stem)

    project_root = config_path.parent.parent.resolve()
    out_dir = Path(args.public_dir) / audio_prefix
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {out_dir}\n")

    scenes = config.get("scenes", [])
    total_chars = 0
    scene_details = []
    total_beats = 0

    for i, scene in enumerate(scenes, start=1):
        chars = process_scene(i, scene, audio_prefix, fps, args.voice, out_dir)
        total_chars += chars
        scene_details.append((i, chars))
        total_beats += len(scene.get("beats", []))

    for i, scene in enumerate(scenes):
        beats_path = out_dir / f"scene{i+1}-beats.json"
        if beats_path.exists():
            scene["beats"] = json.loads(beats_path.read_text(encoding="utf-8"))

    updated_config_path = config_path.parent / f"{config_path.stem}-with-beats.json"
    updated_config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nUpdated config with beats: {updated_config_path}")

    cost = total_chars / 10000 * COST_PER_10K_CHARS
    print_cost_report(word, total_chars, cost, scene_details)
    log_cost(project_root, word, total_chars, cost, len(scenes), total_beats)
    print(f"成本记录已追加到: {project_root / 'data' / 'tts-cost-log.jsonl'}")


if __name__ == "__main__":
    main()
