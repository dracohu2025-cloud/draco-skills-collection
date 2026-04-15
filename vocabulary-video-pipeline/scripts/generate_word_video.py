#!/usr/bin/env python3
"""
vocabulary-video-pipeline skill orchestrator.
Runs the full pipeline: diagnose -> TTS/beats -> render -> upload -> report.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def find_project_root() -> Path:
    env = os.environ.get("VOCAB_VIDEO_PROJECT_ROOT", "").strip()
    if env:
        return Path(env)
    candidates = [
        Path("/home/ubuntu/projects/vocabulary-video-pipeline"),
        Path("/home/ubuntu/projects/remotion-remotion-explainer"),
    ]
    for c in candidates:
        if (c / "package.json").exists() and (c / "scripts" / "diagnose_word.py").exists():
            return c
    raise FileNotFoundError(
        "Could not find vocabulary-video-pipeline project. "
        "Please set VOCAB_VIDEO_PROJECT_ROOT or clone the repo."
    )


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    print(f"\n▶ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=check)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a vocabulary video end-to-end.")
    parser.add_argument("--word", required=True, help="Target English word")
    parser.add_argument("--project-root", help="Override project root path")
    parser.add_argument("--skip-render", action="store_true", help="Skip video rendering")
    parser.add_argument("--skip-upload", action="store_true", help="Skip Feishu upload")
    parser.add_argument("--feishu-folder", default="F4p3ffzHylDtQUdrvA0c8wWXngf", help="Feishu drive folder token")
    parser.add_argument("--draft-only", action="store_true", help="Stop after generating draft")
    parser.add_argument("--audio-only", action="store_true", help="Stop after generating audio/beats")
    args = parser.parse_args()

    word = args.word.lower().strip()
    project_root = Path(args.project_root) if args.project_root else find_project_root()
    print(f"Using project root: {project_root}")

    draft_path = project_root / "data" / f"{word}-draft.json"
    draft_beats_path = project_root / "data" / f"{word}-draft-with-beats.json"
    render_output = project_root / "renders" / f"{word}-word-video.mp4"

    # 1. Diagnose
    if not draft_path.exists():
        print(f"\n[1/5] Diagnosing word: {word}")
        run(["npm", "run", "diagnose:word", "--", "--word", word], cwd=project_root)
    else:
        print(f"\n[1/5] Draft already exists: {draft_path}")

    if args.draft_only:
        print(f"\nDraft ready at: {draft_path}")
        return 0

    # 2. Generate audio & beats
    if not draft_beats_path.exists():
        print(f"\n[2/5] Generating TTS and beats for: {word}")
        run(["python3", "scripts/generate_audio_beats.py", "--input", str(draft_path)], cwd=project_root)
    else:
        print(f"\n[2/5] Beats config already exists: {draft_beats_path}")

    if args.audio_only:
        print(f"\nAudio/beats ready at: {draft_beats_path}")
        return 0

    # 3. Render
    if not args.skip_render:
        print(f"\n[3/5] Rendering video for: {word}")
        run(
            [
                "npx", "remotion", "render", "WordVideo", str(render_output),
                "--props", str(draft_beats_path),
            ],
            cwd=project_root,
        )
    else:
        print("\n[3/5] Rendering skipped")

    if not render_output.exists() and not args.skip_render:
        print(f"Error: expected render output not found: {render_output}", file=sys.stderr)
        return 1

    # 4. Upload
    if not args.skip_upload and render_output.exists():
        print(f"\n[4/5] Uploading to Feishu drive")
        run(
            [
                "lark-cli", "drive", "+upload",
                "--folder-token", args.feishu_folder,
                "--file", str(render_output),
            ],
            cwd=project_root,
        )
    else:
        print("\n[4/5] Upload skipped")

    # 5. Cost report
    print(f"\n[5/5] TTS cost report")
    run(["python3", "scripts/tts_cost_report.py"], cwd=project_root)

    print(f"\n✅ Done! Output: {render_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
