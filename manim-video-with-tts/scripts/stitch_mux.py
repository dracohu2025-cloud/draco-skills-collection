#!/usr/bin/env python3
"""
Stitch Manim scene clips and mux with TTS narration.
Usage:
    python3 stitch_mux.py --scenes 7 --quality 1080p60 --out final.mp4
"""
import argparse, glob, json, os, subprocess, sys
from pathlib import Path

def ffprobe_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True
    )
    return float(r.stdout.strip()) if r.returncode == 0 else 0.0

def write_concat_list(files, outpath):
    with open(outpath, "w") as f:
        for p in files:
            f.write(f"file '{p}'\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenes", type=int, required=True, help="number of scenes")
    parser.add_argument("--quality", default="1080p60", help="Manim quality folder name")
    parser.add_argument("--scene-prefix", default="S", help="scene class name prefix")
    parser.add_argument("--audio-dir", default="./audio", help="directory containing s01.mp3 ...")
    parser.add_argument("--video-dir", default="./media/videos/script", help="Manim video output root")
    parser.add_argument("--out", default="final.mp4", help="output filename")
    args = parser.parse_args()

    video_dir = Path(args.video_dir) / args.quality
    audio_dir = Path(args.audio_dir)

    video_clips = []
    for i in range(1, args.scenes + 1):
        candidates = [
            video_dir / f"{args.scene_prefix}{i}_*.mp4",
            video_dir / f"S{i}_*.mp4",
        ]
        found = None
        for pattern in candidates:
            matches = sorted(glob.glob(str(pattern)))
            if matches:
                found = matches[0]
                break
        if not found:
            print(f"ERROR: No video clip found for scene {i}")
            sys.exit(1)
        video_clips.append(found)
        print(f"Video {i}: {found} ({ffprobe_duration(found):.3f}s)")

    audio_clips = [str(audio_dir / f"s{i:02d}.mp3") for i in range(1, args.scenes + 1)]
    for a in audio_clips:
        if not os.path.exists(a):
            print(f"ERROR: Audio clip missing: {a}")
            sys.exit(1)

    vlist = "concat_video.txt"
    alist = "concat_audio.txt"
    write_concat_list(video_clips, vlist)
    write_concat_list(audio_clips, alist)

    vout = "video_stitched.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", vlist, "-c", "copy", vout], check=True)
    aout = "audio_stitched.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", alist, "-c", "copy", aout], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", vout, "-i", aout, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", args.out], check=True)

    vdur = ffprobe_duration(vout)
    adur = ffprobe_duration(aout)
    print(f"\nFinal output: {args.out}")
    print(f"Video: {vdur:.3f}s | Audio: {adur:.3f}s | Diff: {abs(vdur - adur):.3f}s")

    for f in [vlist, alist, vout, aout]:
        if os.path.exists(f):
            os.remove(f)

if __name__ == "__main__":
    main()
