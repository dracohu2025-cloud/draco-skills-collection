#!/usr/bin/env python3
"""
vocabulary-video-pipeline 项目级统一入口脚本。
运行完整流水线：diagnose → TTS/beats → Director signoff → render → upload → report。
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def find_project_root() -> Path:
    """从脚本位置推断项目根目录。"""
    return Path(__file__).parent.parent.resolve()


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    print(f"\n▶ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=check)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a vocabulary video end-to-end.")
    parser.add_argument("--word", required=True, help="Target English word")
    parser.add_argument("--skip-render", action="store_true", help="Skip video rendering")
    parser.add_argument("--skip-upload", action="store_true", help="Skip Feishu upload")
    parser.add_argument("--skip-director", action="store_true", help="Skip Director validation (not recommended)")
    parser.add_argument("--feishu-folder", default="F4p3ffzHylDtQUdrvA0c8wWXngf", help="Feishu drive folder token")
    parser.add_argument("--draft-only", action="store_true", help="Stop after generating draft")
    parser.add_argument("--audio-only", action="store_true", help="Stop after generating audio/beats")
    args = parser.parse_args()

    word = args.word.lower().strip()
    project_root = find_project_root()
    print(f"Using project root: {project_root}")

    draft_path = project_root / "data" / f"{word}-draft.json"
    draft_beats_path = project_root / "data" / f"{word}-draft-with-beats.json"
    render_output = project_root / "renders" / f"{word}-word-video.mp4"

    # 1. Diagnose
    if not draft_path.exists():
        print(f"\n[1/6] Diagnosing word: {word}")
        run(["npm", "run", "diagnose:word", "--", "--word", word], cwd=project_root)
    else:
        print(f"\n[1/6] Draft already exists: {draft_path}")

    if args.draft_only:
        print(f"\nDraft ready at: {draft_path}")
        return 0

    # 2. Generate audio & beats
    if not draft_beats_path.exists():
        print(f"\n[2/6] Generating TTS and beats for: {word}")
        run(["python3", "scripts/generate_audio_beats.py", "--input", str(draft_path)], cwd=project_root)
    else:
        print(f"\n[2/6] Beats config already exists: {draft_beats_path}")

    if args.audio_only:
        print(f"\nAudio/beats ready at: {draft_beats_path}")
        return 0

    # 3. Director validation (SIGNOFF gate)
    if not args.skip_director:
        print(f"\n[3/6] Running Director validation")
        result = run(
            ["python3", "scripts/director_validate.py", "--input", str(draft_beats_path)],
            cwd=project_root,
            check=False,
        )
        if result.returncode != 0:
            print("\n❌ Director signoff failed. Aborting pipeline.", file=sys.stderr)
            return 1
    else:
        print("\n[3/6] Director validation skipped")

    # 4. Render
    if not args.skip_render:
        print(f"\n[4/6] Rendering video for: {word}")
        run(
            [
                "npx", "remotion", "render", "src/index.ts", "WordVideo", str(render_output),
                "--props", str(draft_beats_path),
            ],
            cwd=project_root,
        )
    else:
        print("\n[4/6] Rendering skipped")

    if not render_output.exists() and not args.skip_render:
        print(f"Error: expected render output not found: {render_output}", file=sys.stderr)
        return 1

    # 5. Upload
    if not args.skip_upload and render_output.exists():
        print(f"\n[5/6] Uploading to Feishu drive")
        run(
            [
                "lark-cli", "drive", "+upload",
                "--folder-token", args.feishu_folder,
                "--file", str(render_output),
            ],
            cwd=project_root,
        )
    else:
        print("\n[5/6] Upload skipped")

    # 6. Cost report
    print(f"\n[6/6] TTS cost report")
    run(["python3", "scripts/tts_cost_report.py"], cwd=project_root)

    print(f"\n✅ Done! Output: {render_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
