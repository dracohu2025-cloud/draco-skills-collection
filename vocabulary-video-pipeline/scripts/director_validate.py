#!/usr/bin/env python3
"""
Director 校验模块
责任：确保 TTS 脚本与视觉内容匹配，检查音频不被截断，强制词源场景存在。
未通过 Director signoff 的 draft 不得进入渲染。
"""
import argparse
import json
import sys
from pathlib import Path

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None

TAIL_PADDING = 40
FPS = 30


def collect_errors(config: dict, project_root: Path) -> list[str]:
    errors = []
    scenes = config.get("scenes", [])
    word = config.get("word", "unknown")
    audio_prefix = config.get("audioPrefix", "")
    public_dir = project_root / "public"

    # 1. 强制词源场景
    scene_types = [s["type"] for s in scenes]
    if "origin-chain" not in scene_types:
        errors.append("缺少强制场景: origin-chain (每个单词必须有词源解释)")

    for idx, scene in enumerate(scenes, start=1):
        stype = scene.get("type", "")
        props = scene.get("props", {})
        beats = scene.get("beats", [])
        bcount = len(beats)

        # 2. Beats 数量校验
        expected = None
        if stype == "hero-word":
            expected = (1, None)  # 至少1个
        elif stype == "origin-chain":
            nodes = props.get("nodes", [])
            expected = (len(nodes), len(nodes)) if nodes else (1, 1)
        elif stype == "meaning-compare":
            expected = (2, None)
        elif stype == "full-screen-mood":
            lines = props.get("lines", props.get("moodLines", []))
            line_count = len(lines) if isinstance(lines, list) else 0
            expected = (line_count + 1, line_count + 1)
        elif stype == "quote-page":
            expected = (4, 4)
        elif stype == "answer-cards":
            cards = props.get("cards", [])
            expected = (len(cards) + 1, len(cards) + 1) if cards else (2, 2)
        elif stype == "ending-summary":
            points = props.get("points", [])
            expected = (len(points) + 2, len(points) + 2)
        elif stype == "emoji-storyboard":
            expected = (1, None)
        elif stype == "profile-story":
            story_lines = props.get("storyLines", [])
            expected = (len(story_lines) + 1, len(story_lines) + 1) if story_lines else (1, None)
        elif stype == "timeline-page":
            events = props.get("events", [])
            expected = (len(events), len(events)) if events else (1, None)

        if expected:
            min_b, max_b = expected
            if bcount < min_b:
                errors.append(f"Scene {idx} ({stype}): beats 数量不足。实际 {bcount}，要求至少 {min_b}")
            if max_b is not None and bcount > max_b:
                errors.append(f"Scene {idx} ({stype}): beats 数量过多。实际 {bcount}，要求恰好 {max_b}")

        # 3. 关键词匹配校验（ending-summary / answer-cards / origin-chain）
        if stype == "ending-summary" and bcount >= 2:
            points = props.get("points", [])
            # formula + points + closing
            for i, pt in enumerate(points):
                beat_idx = 1 + i
                if beat_idx < bcount:
                    beat_text = beats[beat_idx]["text"]
                    if pt["text"] not in beat_text:
                        errors.append(f"Scene {idx} ({stype}): 第 {beat_idx+1} 个 beat 不含 point 关键词 '{pt['text']}'")

        if stype == "answer-cards" and bcount >= 2:
            cards = props.get("cards", [])
            for i, card in enumerate(cards):
                beat_idx = 1 + i
                if beat_idx < bcount:
                    beat_text = beats[beat_idx]["text"]
                    if card["headline"] not in beat_text:
                        errors.append(f"Scene {idx} ({stype}): 第 {beat_idx+1} 个 beat 不含 card headline '{card['headline']}'")

        if stype == "origin-chain" and bcount >= 1:
            nodes = props.get("nodes", [])
            for i, node in enumerate(nodes):
                if i < bcount:
                    beat_text = beats[i]["text"]
                    if node["label"] not in beat_text:
                        errors.append(f"Scene {idx} ({stype}): 第 {i+1} 个 beat 不含 node label '{node['label']}'")

        # 4. 音频时长校验（对应 -with-beats 配置）
        if audio_prefix and AudioSegment is not None:
            audio_path = public_dir / audio_prefix / f"scene{idx}.mp3"
            if audio_path.exists():
                audio = AudioSegment.from_file(audio_path)
                audio_frames = int(len(audio) / 1000 * FPS)
                last_end = beats[-1]["endFrame"] if beats else 0
                required = last_end + TAIL_PADDING
                if audio_frames < last_end:
                    errors.append(
                        f"Scene {idx} ({stype}): 音频时长({audio_frames}帧) < 最后一个 beat 结束({last_end}帧)，"
                        f"TTS 会被截断"
                    )
                elif audio_frames < required:
                    errors.append(
                        f"Scene {idx} ({stype}): 音频时长({audio_frames}帧) < 建议时长({required}帧, "
                        f"含{TAIL_PADDING}帧尾部余量)，可能存在截断风险"
                    )
            else:
                # 只有生成了 beats 但还没合成音频时可以忽略
                if bcount > 0:
                    errors.append(f"Scene {idx} ({stype}): 缺少音频文件 {audio_path}")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Director 校验脚本")
    parser.add_argument("--input", required=True, help="-with-beats JSON 路径")
    args = parser.parse_args()

    config_path = Path(args.input)
    if not config_path.exists():
        print(f"[DIRECTOR ERROR] 配置文件不存在: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    project_root = config_path.parent.parent.resolve()
    errors = collect_errors(config, project_root)

    word = config.get("word", "unknown")
    print(f"\n{'='*60}")
    print(f"[DIRECTOR] 审查报告: {word}")
    print(f"{'='*60}")

    if errors:
        print(f"\n❌ 未通过校验，共 {len(errors)} 项问题:")
        for e in errors:
            print(f"  • {e}")
        print(f"\n❌ DIRECTOR SIGNOFF: REJECTED")
        sys.exit(1)
    else:
        print("\n✅ 所有校验通过！")
        print("\n✅ DIRECTOR SIGNOFF: APPROVED")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
