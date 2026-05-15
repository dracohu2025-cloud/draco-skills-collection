#!/usr/bin/env python3
"""
Generate TTS audio clips for each scene and measure exact durations.
Requires: volc-tts command in PATH, VOLCENGINE_TTS_* env vars set.
Usage:
    python3 tts_measure.py --input plan.md --outdir ./audio --voice female
"""
import argparse, json, os, re, subprocess, sys
from pathlib import Path

def run_volc_tts(text: str, output: str, voice: str = "female") -> bool:
    cmd = ["volc-tts", "--text", text, "--voice", voice, "--output", output]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0 and "code=3000" in r.stdout

def measure_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True
    )
    return float(r.stdout.strip()) if r.returncode == 0 else 0.0

def extract_voiceover_table(plan_md: str) -> list[dict]:
    """Parse plan.md for voiceover table rows."""
    rows = []
    # Look for markdown table after 'Voiceover Script' or similar
    in_table = False
    with open(plan_md) as f:
        for line in f:
            if "|" in line and ("Scene" in line or "场景" in line):
                in_table = True
            if in_table and line.strip().startswith("|") and "---" not in line:
                cells = [c.strip() for c in line.strip("|\n").split("|")]
                if len(cells) >= 3 and cells[0] not in ("Scene", "场景", "S"):
                    rows.append({"scene": cells[0], "text": cells[1], "est_chars": cells[2] if len(cells)>2 else ""})
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="plan.md path")
    parser.add_argument("--outdir", default="./audio", help="audio output directory")
    parser.add_argument("--voice", default="female", choices=["female", "male"])
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows = extract_voiceover_table(args.input)
    if not rows:
        print("No voiceover table found in plan.md. Falling back to manual mode.")
        sys.exit(1)

    manifest = []
    for i, row in enumerate(rows, 1):
        fname = outdir / f"s{i:02d}.mp3"
        ok = run_volc_tts(row["text"], str(fname), args.voice)
        if not ok:
            print(f"FAIL: scene {i} TTS failed")
            continue
        dur = measure_duration(str(fname))
        manifest.append({"scene": i, "file": str(fname), "duration": dur, "text": row["text"]})
        print(f"s{i:02d}.mp3: {dur:.3f}s  |  {row['text'][:40]}...")

    manifest_path = outdir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\nManifest written to {manifest_path}")
    print(f"Total audio duration: {sum(m['duration'] for m in manifest):.3f}s")

if __name__ == "__main__":
    main()
