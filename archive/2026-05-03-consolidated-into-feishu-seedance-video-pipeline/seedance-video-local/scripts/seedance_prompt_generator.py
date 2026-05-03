#!/usr/bin/env python3
"""Seedance 2.0 prompt generator.

Methodology source (from the referenced post):
subject > action > camera > style > constraints

This module turns a raw video requirement into a structured prompt package
that is safer for Seedance-style generation.
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any

METHOD = "subject > action > camera > style > constraints"
PROFILE_CHOICES = ("strict", "stable", "cinematic")

CAMERA_MAP = [
    ("第一视角", "first-person POV"),
    ("推近", "slow dolly-in"),
    ("拉近", "slow dolly-in"),
    ("拉远", "dolly-out"),
    ("推拉", "dolly zoom"),
    ("平移", "pan"),
    ("跟拍", "tracking shot"),
    ("跟随", "tracking shot"),
    ("环绕", "orbit"),
    ("360", "360 orbit"),
    ("手持", "handheld"),
    ("稳拍", "gimbal"),
    ("航拍", "aerial drone shot"),
    ("固定", "locked-off"),
    ("特写", "close-up framing"),
    ("慢动作", "slow motion"),
    ("push-in", "slow dolly-in"),
    ("dolly in", "slow dolly-in"),
    ("dolly out", "dolly-out"),
    ("orbit", "orbit"),
    ("tracking", "tracking shot"),
    ("handheld", "handheld"),
    ("gimbal", "gimbal"),
    ("locked", "locked-off"),
    ("static wide", "static wide"),
    ("tripod", "locked tripod"),
    ("steadicam", "steadicam walk"),
    ("whip pan", "whip pan"),
    ("crane", "crane up/down"),
    ("rack focus", "rack focus"),
]

STYLE_MAP = [
    ("golden hour", "golden hour lighting"),
    ("日落", "golden hour lighting"),
    ("逆光", "backlit silhouette"),
    ("边缘光", "dramatic rim light"),
    ("雾", "volumetric fog"),
    ("电影感", "cinematic film tone, 35mm"),
    ("35mm", "cinematic film tone, 35mm"),
    ("16mm", "16mm film, handheld camera"),
    ("teal and orange", "teal and orange grade"),
    ("bleach bypass", "bleach bypass grade"),
    ("暖色", "warm amber-tinted grade"),
    ("crushed blacks", "crushed blacks"),
    ("粉彩", "pastel color grade"),
    ("chiaroscuro", "chiaroscuro high-contrast lighting"),
    ("rim light", "dramatic rim light"),
    ("soft key", "soft key from 45 degrees"),
    ("overcast", "even overcast diffused light"),
    ("anamorphic", "anamorphic lens flare"),
    ("纪实", "documentary-style handheld framing"),
    ("商业广告", "clean commercial product lighting"),
    ("产品广告", "clean commercial product lighting"),
]

DEFAULT_CONSTRAINTS = [
    "avoid jitter",
    "avoid bent limbs",
    "avoid identity drift",
    "avoid temporal flicker",
    "no distortion",
    "no stretching",
    "maintain face consistency",
    "sharp clarity",
    "natural colors",
    "stable picture",
    "no blur",
    "no ghosting",
    "no flickering",
]

PROFILE_DEFAULT_CONSTRAINTS: dict[str, list[str]] = {
    "strict": DEFAULT_CONSTRAINTS
    + [
        "preserve subject identity across all shots",
        "consistent anatomy and limb geometry",
        "camera motion should be physically plausible",
    ],
    "stable": DEFAULT_CONSTRAINTS,
    "cinematic": [
        "avoid temporal flicker",
        "maintain face consistency",
        "no distortion",
    ],
}

BAD_WORD_RULES = [
    (r"\blots of movement\b", "one primary movement only", "replaced 'lots of movement' with one specific movement"),
    (r"\bepic\b", "high-contrast cinematic composition", "replace emotional adjective with visual instruction"),
    (r"\bamazing\b", "high-detail visual composition", "replace emotional adjective with visual instruction"),
    (r"\bbeautiful\b", "balanced composition with clean lighting", "replace emotional adjective with visual instruction"),
    (r"\bstunning\b", "high-detail cinematic framing", "replace emotional adjective with visual instruction"),
    (r"\bfast\b", "single fast element, keep all other elements steady", "replaced risky 'fast' with controlled speed instruction"),
    (r"\bglow\b", "steady intensity diffuse light", "replaced flicker-prone keyword 'glow'"),
    (r"\bglimmer\b", "steady intensity diffuse light", "replaced flicker-prone keyword 'glimmer'"),
    (r"\bglints\b", "steady intensity diffuse light", "replaced flicker-prone keyword 'glints'"),
]

BAD_WORD_RULES_BY_PROFILE: dict[str, list[tuple[str, str, str]]] = {
    "strict": BAD_WORD_RULES,
    "stable": BAD_WORD_RULES,
    "cinematic": [
        BAD_WORD_RULES[0],
        BAD_WORD_RULES[5],
    ],
}

SECTION_ALIASES: dict[str, list[str]] = {
    "subject": ["core subject", "subject", "主体", "主角", "角色", "character", "characters"],
    "environment": ["environment", "scene", "场景", "环境", "image reference"],
    "time_state": ["time state", "time-state", "时间状态", "时间"],
    "main_action": ["main action", "action", "主要动作", "动作", "行为"],
    "action_sequence": ["action sequence", "sequence", "timeline", "时间线", "动作序列"],
    "time_resume": ["time resume moment", "resume moment", "时间恢复", "恢复时刻"],
    "camera": ["cinematography", "camera behavior", "camera settings", "camera", "镜头", "运镜", "摄影"],
    "style": ["visual style", "film style", "style", "color grade", "lighting", "风格", "光线", "色调", "cinematic setup"],
    "quality": ["quality & rendering", "quality", "rendering", "画质", "渲染"],
    "constraints": ["constraints", "约束", "限制"],
    "duration": ["duration", "时长"],
}


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen = set()
    out: list[str] = []
    for it in items:
        k = it.strip().lower()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(it.strip())
    return out


def split_clauses(text: str) -> list[str]:
    parts = [x.strip() for x in re.split(r"[。.!?！？;；\n]+", text) if x.strip()]
    return parts


def _normalize_heading_key(key: str) -> str:
    k = key.strip().lower()
    k = re.sub(r"\s+", " ", k)
    return k


def _canonical_section_key(raw_key: str) -> str | None:
    key = _normalize_heading_key(raw_key).strip("[]【】")
    key = key.replace("：", ":")
    for canonical, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            a = _normalize_heading_key(alias)
            if key == a or key.startswith(f"{a} ") or a in key:
                return canonical
    return None


def extract_sections(text: str) -> dict[str, str]:
    """Extract structured sections from heading-style prompts.

    Supports forms like:
    - Core Subject:
    - [CINEMATIC SETUP]
    - 【风格】
    """
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        m_cn = re.match(r"^【(?P<key>[^】]{1,20})】\s*(?P<tail>.*)$", line)
        if m_cn:
            canonical = _canonical_section_key(m_cn.group("key") or "")
            if canonical:
                current = canonical
                tail = (m_cn.group("tail") or "").strip()
                if tail:
                    sections.setdefault(current, []).append(tail)
                continue
            current = None
            continue

        # avoid treating timeline tags like [00:00-00:04] as section headings
        if re.match(r"^\[?\d{1,2}:\d{2}\s*(?:-|–|—|~|到|至)\s*\d{1,2}:\d{2}\]?", line):
            if current == "action_sequence":
                sections.setdefault(current, []).append(line)
            continue

        m = re.match(
            r"^(?:\[|【)?\s*(?P<key>[A-Za-z][A-Za-z0-9\s&\-—_/]{1,80}|[\u4e00-\u9fff]{1,12})\s*(?:\]|】)?\s*(?:[:：]\s*(?P<tail>.*))?$",
            line,
        )
        if m:
            key = m.group("key") or ""
            canonical = _canonical_section_key(key)
            if canonical:
                current = canonical
                tail = (m.group("tail") or "").strip()
                if tail:
                    sections.setdefault(current, []).append(tail)
                continue

            # heading-like but not recognized: break attachment to previous section
            if re.match(r"^(?:\[|【).*(?:\]|】)$", line) or m.group("tail") is not None:
                current = None
                continue

        if current:
            sections.setdefault(current, []).append(line)

    return {k: " ".join(v).strip() for k, v in sections.items() if v}


def repair_vague_words(text: str, profile: str = "stable") -> tuple[str, list[str]]:
    if profile not in PROFILE_CHOICES:
        raise ValueError(f"未知 profile: {profile}")

    fixed = text
    notes: list[str] = []

    for pat, repl, note in BAD_WORD_RULES_BY_PROFILE[profile]:
        if re.search(pat, fixed, flags=re.I):
            fixed = re.sub(pat, repl, fixed, flags=re.I)
            notes.append(note)

    if (
        profile in {"strict", "stable"}
        and re.search(r"\bcinematic\b", fixed, flags=re.I)
        and "35mm" not in fixed.lower()
    ):
        fixed = re.sub(r"\bcinematic\b", "cinematic film tone, 35mm", fixed, flags=re.I)
        notes.append("expanded 'cinematic' to explicit film anchor")

    return fixed, notes


def _parse_time_to_seconds(token: str) -> float:
    t = token.strip()
    if ":" in t:
        mm, ss = t.split(":", 1)
        return float(mm) * 60 + float(ss)
    return float(t)


def parse_timecoded_shots(text: str) -> list[dict[str, Any]]:
    # 支持：2-4 秒：... / [0-4s]: ... / [00:00-00:04] 镜头1：...
    pattern = re.compile(
        r"(?:\[|\()?\s*(?P<start>\d{1,2}:\d{1,2}(?:\.\d+)?|\d{1,2}(?:\.\d+)?)\s*(?:-|–|—|~|到|至)\s*(?P<end>\d{1,2}:\d{1,2}(?:\.\d+)?|\d{1,2}(?:\.\d+)?)\s*(?:s|秒)?\s*(?:\]|\))?"
        r"\s*(?:(?P<label>[^\n:：]{0,40})[：:])?\s*(?P<body>.*?)"
        r"(?=(?:\[|\()?\s*(?:\d{1,2}:\d{1,2}(?:\.\d+)?|\d{1,2}(?:\.\d+)?)\s*(?:-|–|—|~|到|至)\s*(?:\d{1,2}:\d{1,2}(?:\.\d+)?|\d{1,2}(?:\.\d+)?)\s*(?:s|秒)?\s*(?:\]|\))?\s*(?:[^\n:：]{0,40}[：:])?|$)",
        flags=re.I | re.S,
    )

    shots: list[dict[str, Any]] = []
    for m in pattern.finditer(text):
        start = _parse_time_to_seconds(m.group("start"))
        end = _parse_time_to_seconds(m.group("end"))
        body = re.sub(r"\s+", " ", m.group("body")).strip(" ，,。;；")
        label = re.sub(r"\s+", " ", (m.group("label") or "")).strip(" ，,。;；")
        if label and body:
            body = f"{label}: {body}"
        elif label:
            body = label
        if end <= start or not body:
            continue
        shots.append({"start": start, "end": end, "text": body})
    return shots


def extract_marked_field(text: str, aliases: list[str]) -> str | None:
    for line in text.splitlines():
        for key in aliases:
            m = re.match(rf"\s*{re.escape(key)}\s*[：:]\s*(.+)\s*$", line, flags=re.I)
            if m:
                return m.group(1).strip()
    return None


def detect_keywords(text: str, mapping: list[tuple[str, str]]) -> list[str]:
    out: list[str] = []
    low = text.lower()
    for needle, token in mapping:
        if needle.lower() in low:
            out.append(token)
    return dedupe_keep_order(out)


def normalize_camera_directive(camera: str, profile: str = "stable") -> str:
    """Reduce camera conflicts by profile: strict/stable keeps one, cinematic keeps up to two."""
    parts = [x.strip() for x in re.split(r"[,，;；]+", camera) if x.strip()]
    if not parts:
        return "locked-off"

    normalized = [re.sub(r"\bfast\b", "slow controlled", p, flags=re.I) for p in parts]
    if profile == "cinematic":
        return ", ".join(dedupe_keep_order(normalized)[:2])

    return normalized[0]


def guess_subject(text: str, shots: list[dict[str, Any]], sections: dict[str, str] | None = None) -> str:
    sections = sections or {}
    if sections.get("subject"):
        return sections["subject"]
    if sections.get("environment"):
        env_clause = split_clauses(sections["environment"])
        if env_clause:
            return env_clause[0]

    marked = extract_marked_field(text, ["主体", "主角", "subject"])
    if marked:
        return marked

    # 去掉时间分镜段，避免 subject 被整段分镜污染
    text_wo_shots = re.sub(
        r"(?:\[|\()?\s*\d{1,2}(?::\d{1,2})?\s*(?:-|–|—|~|到|至)\s*\d{1,2}(?::\d{1,2})?\s*(?:s|秒)?\s*(?:\]|\))?\s*(?:[^\n:：]{0,40}[：:])?.*?"
        r"(?=(?:\[|\()?\s*\d{1,2}(?::\d{1,2})?\s*(?:-|–|—|~|到|至)\s*\d{1,2}(?::\d{1,2})?\s*(?:s|秒)?\s*(?:\]|\))?\s*(?:[^\n:：]{0,40}[：:])?|$)",
        " ",
        text,
        flags=re.S,
    )

    clauses = split_clauses(text_wo_shots)
    first = ""
    for c in clauses:
        if re.match(r"^(?:\[|【).*(?:\]|】)$", c):
            continue
        first = c
        break

    first = re.sub(r"\s+", " ", first).strip(" ，,;；:：")
    if len(first) > 120:
        first = first[:120].rstrip(" ，,")
    return first or "single primary subject matching user requirement"


def guess_action(text: str, shots: list[dict[str, Any]], sections: dict[str, str] | None = None) -> str:
    sections = sections or {}
    marked = extract_marked_field(text, ["动作", "action", "行为"])
    if marked:
        return marked

    action_parts: list[str] = []
    for key in ["main_action", "action_sequence", "time_resume", "time_state"]:
        if sections.get(key):
            action_parts.append(sections[key])
    if action_parts:
        return " ".join(action_parts)

    if shots:
        return " ; ".join(s["text"] for s in shots)

    clauses = split_clauses(text)
    if len(clauses) >= 2:
        return "；".join(clauses[1:])
    return clauses[0] if clauses else "one primary movement only"


def guess_camera(
    text: str,
    shots: list[dict[str, Any]],
    sections: dict[str, str] | None = None,
    profile: str = "stable",
) -> str:
    sections = sections or {}
    if sections.get("camera"):
        return sections["camera"]

    marked = extract_marked_field(text, ["镜头", "camera", "运镜"])
    if marked:
        return marked
    merged = text + "\n" + "\n".join(s["text"] for s in shots)
    cams = detect_keywords(merged, CAMERA_MAP)
    if not cams:
        cams = ["locked-off", "slow gentle movement"]
    if shots:
        return ", ".join(cams)
    return normalize_camera_directive(", ".join(cams), profile=profile)


def guess_style(text: str, shots: list[dict[str, Any]], sections: dict[str, str] | None = None) -> str:
    sections = sections or {}
    style_parts = [sections[k] for k in ["style"] if sections.get(k)]
    if style_parts:
        return " ".join(style_parts)

    marked = extract_marked_field(text, ["风格", "style", "光线", "lighting"])
    if marked:
        return marked
    merged = text + "\n" + "\n".join(s["text"] for s in shots)
    styles = detect_keywords(merged, STYLE_MAP)
    if not styles:
        styles = ["clean commercial product lighting", "natural color grade"]
    return ", ".join(styles)


def build_constraints(
    text: str,
    *,
    include_default_constraints: bool = True,
    extra_constraints: list[str] | None = None,
    sections: dict[str, str] | None = None,
    profile: str = "stable",
) -> str:
    sections = sections or {}
    marked = extract_marked_field(text, ["约束", "constraints", "限制"])
    out: list[str] = []
    if include_default_constraints:
        out.extend(PROFILE_DEFAULT_CONSTRAINTS[profile])
    if marked:
        out.extend([x.strip() for x in re.split(r"[,，;；]", marked) if x.strip()])
    if sections.get("constraints"):
        out.extend([x.strip() for x in re.split(r"[,，;；]", sections["constraints"]) if x.strip()])
    if sections.get("quality"):
        out.extend([sections["quality"]])
    if extra_constraints:
        out.extend(extra_constraints)
    return ", ".join(dedupe_keep_order(out))


def build_timeline_prompt(
    shots: list[dict[str, Any]],
    *,
    subject: str,
    fallback_camera: str,
    fallback_style: str,
) -> list[str]:
    lines: list[str] = []
    for s in shots:
        local_cam = detect_keywords(s["text"], CAMERA_MAP)
        local_style = detect_keywords(s["text"], STYLE_MAP)
        cam = ", ".join(local_cam) if local_cam else fallback_camera
        sty = ", ".join(local_style) if local_style else fallback_style
        lines.append(f"[{s['start']}-{s['end']}s]: {subject}; {s['text']}; {cam}; {sty}")
    return lines


def generate_structured_prompt(
    brief: str,
    *,
    include_default_constraints: bool = True,
    extra_constraints: list[str] | None = None,
    profile: str = "stable",
) -> dict[str, Any]:
    if profile not in PROFILE_CHOICES:
        raise ValueError(f"未知 profile: {profile}，可选: {', '.join(PROFILE_CHOICES)}")

    cleaned, notes = repair_vague_words(brief.strip(), profile=profile)
    sections = extract_sections(cleaned)
    shots = parse_timecoded_shots(cleaned)

    subject = guess_subject(cleaned, shots, sections)
    action = guess_action(cleaned, shots, sections)
    camera = guess_camera(cleaned, shots, sections, profile=profile)
    style = guess_style(cleaned, shots, sections)
    constraints = build_constraints(
        cleaned,
        include_default_constraints=include_default_constraints,
        extra_constraints=extra_constraints,
        sections=sections,
        profile=profile,
    )

    if sections.get("environment"):
        action = f"Environment: {sections['environment']}. {action}" if action else f"Environment: {sections['environment']}"

    layers = {
        "subject": subject,
        "action": action,
        "camera": camera,
        "style": style,
        "constraints": constraints,
    }

    timeline_lines: list[str] = []
    if shots:
        timeline_lines = build_timeline_prompt(
            shots,
            subject=subject,
            fallback_camera=camera,
            fallback_style=style,
        )
        final_prompt = (
            f"Global subject: {subject}. "
            f"Global action intent: {action}. "
            + " ".join(timeline_lines)
            + f" Global camera: {camera}. Global style: {style}. Global constraints: {constraints}."
        )
    else:
        final_prompt = (
            f"Subject: {subject}. "
            f"Action: {action}. "
            f"Camera: {camera}. "
            f"Style: {style}. "
            f"Constraints: {constraints}."
        )

    return {
        "method": METHOD,
        "profile": profile,
        "rewrite_notes": notes,
        "layers": layers,
        "timeline": shots,
        "sections": sections,
        "final_prompt": final_prompt,
    }


def _read_brief(args: argparse.Namespace) -> str:
    if args.brief:
        return args.brief
    if args.brief_file:
        with open(args.brief_file, "r", encoding="utf-8") as f:
            return f.read()
    raise ValueError("必须提供 --brief 或 --brief-file")


def main() -> int:
    p = argparse.ArgumentParser(description="Seedance structured prompt generator")
    p.add_argument("--brief", help="自然语言视频需求")
    p.add_argument("--brief-file", help="从文件读取需求")
    p.add_argument("--extra-constraint", action="append", default=[], help="追加约束，可重复")
    p.add_argument("--no-default-constraints", action="store_true", help="不注入默认约束")
    p.add_argument(
        "--profile",
        default="stable",
        choices=list(PROFILE_CHOICES),
        help="提示词风格档位：strict(最稳) / stable(平衡) / cinematic(风格优先)",
    )
    p.add_argument("--json", action="store_true", help="输出 JSON")

    args = p.parse_args()

    try:
        brief = _read_brief(args)
        result = generate_structured_prompt(
            brief,
            include_default_constraints=not args.no_default_constraints,
            extra_constraints=args.extra_constraint,
            profile=args.profile,
        )

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        print(f"Method: {result['method']}")
        print(f"Profile: {result['profile']}")
        print("\n[Layers]")
        for k, v in result["layers"].items():
            print(f"- {k}: {v}")

        if result["rewrite_notes"]:
            print("\n[Rewrite notes]")
            for n in result["rewrite_notes"]:
                print(f"- {n}")

        if result["timeline"]:
            print("\n[Timeline]")
            for x in result["timeline"]:
                print(f"- {x['start']}-{x['end']}s: {x['text']}")

        print("\n[Final Prompt]")
        print(result["final_prompt"])
        return 0
    except Exception as ex:
        print(f"ERROR: {ex}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
