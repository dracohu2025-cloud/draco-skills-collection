from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

VALID_PROFILES = {"default", "doocs", "classic", "minimal"}
VALID_THEMES = {"default", "grace", "simple"}
VALID_CODE_THEMES = {"dark", "light", "github-dark", "github-dark-dimmed", "github-light", "github", "one-dark", "vitesse-light", "vitesse-dark"}
VALID_HR_STYLES = {"dash", "star", "underscore"}
VALID_HEADING_STYLES = {"solid", "left-bar", "underline", "minimal"}
VALID_HEADING_LEVEL_STYLES = {"default", "color-only", "border-bottom", "border-left", "custom"}
VALID_CAPTION_MODES = {"title-first", "alt-first", "title-only", "alt-only", "hidden"}
VALID_HEADING_LEVELS = {"h1", "h2", "h3", "h4", "h5", "h6"}
VALID_STYLE_KEYS = {
    "profile",
    "theme",
    "primary_color",
    "font_family",
    "font_size",
    "line_height",
    "justify",
    "indent_first_line",
    "code_theme",
    "hr_style",
    "heading_style",
    "heading_styles",
    "mac_code_block",
    "code_line_numbers",
    "caption_mode",
    "footnote_links",
}

COLOR_PRESETS = {
    "classic-blue": "#0F4C81",
    "emerald-green": "#009874",
    "vitality-orange": "#FA5151",
    "lemon-yellow": "#FECE00",
    "lavender-purple": "#92617E",
    "sky-blue": "#55C9EA",
    "rose-gold": "#B76E79",
    "olive-green": "#556B2F",
    "graphite-black": "#333333",
    "mist-gray": "#A9A9A9",
    "sakura-pink": "#FFB7C5",
}

COLOR_PRESET_LABELS = {
    "classic-blue": "经典蓝",
    "emerald-green": "翡翠绿",
    "vitality-orange": "活力橙",
    "lemon-yellow": "柠檬黄",
    "lavender-purple": "薰衣紫",
    "sky-blue": "天空蓝",
    "rose-gold": "玫瑰金",
    "olive-green": "橄榄绿",
    "graphite-black": "石墨黑",
    "mist-gray": "雾烟灰",
    "sakura-pink": "樱花粉",
}

HEADING_STYLE_LABELS = {
    "solid": "默认",
    "left-bar": "左侧竖线",
    "underline": "下划线",
    "minimal": "极简",
}

CAPTION_MODE_LABELS = {
    "title-first": "title 优先",
    "alt-first": "alt 优先",
    "title-only": "只显示 title",
    "alt-only": "只显示 alt",
    "hidden": "不显示",
}

HEADING_LEVEL_LABELS = {
    "h1": "一级标题",
    "h2": "二级标题",
    "h3": "三级标题",
    "h4": "四级标题",
    "h5": "五级标题",
    "h6": "六级标题",
}

HEADING_LEVEL_STYLE_LABELS = {
    "default": "默认",
    "color-only": "主题色文字",
    "border-bottom": "下边框",
    "border-left": "左边框",
    "custom": "自定义",
}

FONT_FAMILY_PRESETS = {
    "sans": "-apple-system-font,BlinkMacSystemFont, Helvetica Neue, PingFang SC, Hiragino Sans GB , Microsoft YaHei UI , Microsoft YaHei ,Arial,sans-serif",
    "serif": "Optima-Regular, Optima, PingFangSC-light, PingFangTC-light, 'PingFang SC', Cambria, Cochin, Georgia, Times, 'Times New Roman', serif",
    "mono": "Menlo, Monaco, 'Courier New', monospace",
}

FONT_FAMILY_LABELS = {
    "sans": "无衬线",
    "serif": "衬线",
    "mono": "等宽",
}

PROFILE_LABEL_ALIASES = {
    "默认": "default",
    "经典": "classic",
    "极简": "minimal",
    "doocs": "doocs",
}

THEME_LABEL_ALIASES = {
    "默认": "default",
    "优雅": "grace",
    "简约": "simple",
}

HR_STYLE_LABEL_ALIASES = {
    "虚线": "dash",
    "星号": "star",
    "短实线": "underscore",
}

FONT_SIZE_ALIASES = {
    "更小": 14,
    "稍小": 15,
    "推荐": 16,
    "稍大": 17,
    "更大": 18,
}

_TOGGLE_TRUE = {True, 1, "1", "true", "True", "yes", "on", "enable", "enabled", "开启", "开", "是"}
_TOGGLE_FALSE = {False, 0, "0", "false", "False", "no", "off", "disable", "disabled", "关闭", "关", "否"}

_STYLE_KEY_ALIASES = {
    "profile": "profile",
    "theme": "theme",
    "primary_color": "primary_color",
    "primarycolor": "primary_color",
    "primary-color": "primary_color",
    "theme_color": "primary_color",
    "themecolor": "primary_color",
    "theme-color": "primary_color",
    "theme_colors": "primary_color",
    "themecolors": "primary_color",
    "custom_theme_color": "primary_color",
    "customthemecolor": "primary_color",
    "主题色": "primary_color",
    "自定义主题色": "primary_color",
    "font": "font_family",
    "font_family": "font_family",
    "fontfamily": "font_family",
    "font-family": "font_family",
    "字体": "font_family",
    "font_size": "font_size",
    "fontsize": "font_size",
    "font-size": "font_size",
    "字号": "font_size",
    "line_height": "line_height",
    "lineheight": "line_height",
    "line-height": "line_height",
    "行高": "line_height",
    "justify": "justify",
    "段落两端对齐": "justify",
    "indent_first_line": "indent_first_line",
    "indentfirstline": "indent_first_line",
    "indent-first-line": "indent_first_line",
    "段落首行缩进": "indent_first_line",
    "code_theme": "code_theme",
    "codetheme": "code_theme",
    "code-theme": "code_theme",
    "代码块主题": "code_theme",
    "hr_style": "hr_style",
    "hrstyle": "hr_style",
    "hr-style": "hr_style",
    "分割线样式": "hr_style",
    "heading_style": "heading_style",
    "headingstyle": "heading_style",
    "heading-style": "heading_style",
    "标题样式": "heading_style",
    "二级标题": "heading_style",
    "heading_styles": "heading_styles",
    "headingstyles": "heading_styles",
    "各级标题样式": "heading_styles",
    "h1-style": "h1_style",
    "h2-style": "h2_style",
    "h3-style": "h3_style",
    "h4-style": "h4_style",
    "h5-style": "h5_style",
    "h6-style": "h6_style",
    "mac_code_block": "mac_code_block",
    "maccodeblock": "mac_code_block",
    "mac-code-block": "mac_code_block",
    "mac 代码块": "mac_code_block",
    "code_line_numbers": "code_line_numbers",
    "codelinenumbers": "code_line_numbers",
    "code-line-numbers": "code_line_numbers",
    "代码块行号": "code_line_numbers",
    "caption_mode": "caption_mode",
    "captionmode": "caption_mode",
    "caption-mode": "caption_mode",
    "图注格式": "caption_mode",
    "footnote_links": "footnote_links",
    "footnotelinks": "footnote_links",
    "footnote-links": "footnote_links",
    "微信外链转底部引用": "footnote_links",
}


def _normalize_style_key(key: str) -> str:
    raw = key.strip()
    lowered = raw.lower().replace(" ", "_")
    compact = lowered.replace("-", "_")
    return _STYLE_KEY_ALIASES.get(raw, _STYLE_KEY_ALIASES.get(lowered, _STYLE_KEY_ALIASES.get(compact, raw)))


def _normalize_toggle(value: Any) -> bool | None:
    if value in _TOGGLE_TRUE:
        return True
    if value in _TOGGLE_FALSE:
        return False
    return None


def _normalize_profile(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return PROFILE_LABEL_ALIASES.get(text, text)


def _normalize_theme(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return THEME_LABEL_ALIASES.get(text, text)


def _normalize_primary_color(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text in COLOR_PRESETS:
        return text
    if text == "活力橘":
        return "vitality-orange"
    for key, label in COLOR_PRESET_LABELS.items():
        if text == label:
            return key
    return text


def _normalize_font_family(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    presets = {
        "sans": "sans",
        "sans-serif": "sans",
        "无衬线": "sans",
        "serif": "serif",
        "衬线": "serif",
        "mono": "mono",
        "monospace": "mono",
        "等宽": "mono",
    }
    preset_key = presets.get(text)
    if preset_key:
        return FONT_FAMILY_PRESETS[preset_key]
    return text


def _normalize_font_size(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if text in FONT_SIZE_ALIASES:
        return FONT_SIZE_ALIASES[text]
    if text.isdigit():
        return int(text)
    return None


def _normalize_line_height(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    try:
        return float(text)
    except ValueError:
        return None


def _normalize_heading_style(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    for key, label in HEADING_STYLE_LABELS.items():
        if text == label:
            return key
    return text.replace("_", "-")


def _normalize_caption_mode(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    for key, label in CAPTION_MODE_LABELS.items():
        if text == label:
            return key
    return text.replace("_", "-")


def _normalize_hr_style(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return HR_STYLE_LABEL_ALIASES.get(text, text.replace("_", "-"))


def _extract_style_mapping(data: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    wrappers = ["style", "styles", "render", "rendering", "config", "values", "wechat_style"]
    for key in wrappers:
        value = data.get(key)
        if isinstance(value, dict):
            merged.update(value)
    merged.update({k: v for k, v in data.items() if k not in wrappers})
    return merged


def _normalize_heading_style_per_level(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    mapping = {
        "默认": "default",
        "default": "default",
        "主题色文字": "color-only",
        "color-only": "color-only",
        "下边框": "border-bottom",
        "border-bottom": "border-bottom",
        "左边框": "border-left",
        "left-bar": "border-left",
        "border-left": "border-left",
        "自定义": "custom",
        "custom": "custom",
    }
    return mapping.get(text, text.replace("_", "-"))


def _normalize_heading_styles(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    normalized: dict[str, str] = {}
    for key, raw in value.items():
        level = str(key).strip().lower()
        if level not in VALID_HEADING_LEVELS:
            continue
        style = _normalize_heading_style_per_level(raw)
        if style and style in VALID_HEADING_LEVEL_STYLES:
            normalized[level] = style
    return normalized or None


def normalize_style_config(data: dict[str, Any]) -> dict[str, Any]:
    source = _extract_style_mapping(data)
    normalized: dict[str, Any] = {}
    heading_styles_map: dict[str, str] = {}
    for key, value in source.items():
        target = _normalize_style_key(str(key))
        if target == "profile":
            normalized[target] = _normalize_profile(value)
        elif target == "theme":
            normalized[target] = _normalize_theme(value)
        elif target == "primary_color":
            normalized[target] = _normalize_primary_color(value)
        elif target == "font_family":
            normalized[target] = _normalize_font_family(value)
        elif target == "font_size":
            normalized[target] = _normalize_font_size(value)
        elif target == "line_height":
            normalized[target] = _normalize_line_height(value)
        elif target in {"justify", "indent_first_line", "mac_code_block", "code_line_numbers", "footnote_links"}:
            toggle = _normalize_toggle(value)
            normalized[target] = value if toggle is None else toggle
        elif target == "heading_style":
            normalized[target] = _normalize_heading_style(value)
        elif target == "heading_styles":
            nested = _normalize_heading_styles(value)
            if nested:
                heading_styles_map.update(nested)
        elif target.startswith("h") and target.endswith("_style") and target[:2] in VALID_HEADING_LEVELS:
            style = _normalize_heading_style(value)
            if style:
                heading_styles_map[target[:2]] = style
        elif target == "caption_mode":
            normalized[target] = _normalize_caption_mode(value)
        elif target == "hr_style":
            normalized[target] = _normalize_hr_style(value)
        elif target == "code_theme":
            normalized[target] = None if value is None else str(value).strip()
        else:
            normalized[target] = value
    if heading_styles_map:
        normalized["heading_styles"] = heading_styles_map
    return {key: value for key, value in normalized.items() if value is not None and key in VALID_STYLE_KEYS}


def load_style_config_file(path: str) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    suffix = Path(path).suffix.lower()
    if suffix == ".json":
        data = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    else:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("style config must be a JSON/YAML object")
    return normalize_style_config(data)


def load_style_json(text: str) -> dict[str, Any]:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("style json must be an object")
    return normalize_style_config(data)


@dataclass(slots=True)
class RenderOptions:
    profile: str = "default"
    theme: str = "default"
    primary_color: str | None = None
    font_family: str | None = None
    font_size: int | None = None
    line_height: float | None = None
    justify: bool = False
    indent_first_line: bool = False
    code_theme: str = "github"
    hr_style: str = "dash"
    heading_style: str = "solid"
    heading_styles: dict[str, str] | None = None
    mac_code_block: bool = False
    code_line_numbers: bool = False
    caption_mode: str = "hidden"
    footnote_links: bool = False


PROFILE_DEFAULTS = {
    "default": {"primary_color": "#2f81f7", "font_size": 16, "line_height": 1.8, "justify": False, "indent_first_line": False},
    "doocs": {"primary_color": "#0F4C81", "font_size": 16, "line_height": 1.75, "justify": False, "indent_first_line": False},
    "classic": {"primary_color": "#3f51b5", "font_size": 16, "line_height": 1.78, "justify": True, "indent_first_line": False},
    "minimal": {"primary_color": "#2563eb", "font_size": 16, "line_height": 1.75, "justify": False, "indent_first_line": False},
}

THEME_OVERRIDES = {
    "default": {"bg_soft": "#f6f8fa", "text": "#24292f", "muted": "#57606a", "border": "#d0d7de", "heading_bg": None},
    "grace": {"bg_soft": "#f8f4ff", "text": "#24292f", "muted": "#6b7280", "border": "#d8b4fe", "heading_bg": None},
    "simple": {"bg_soft": "#f8fafc", "text": "#1f2937", "muted": "#6b7280", "border": "#cbd5e1", "heading_bg": None},
}

CODE_THEME_OVERRIDES = {
    "dark": {"code_bg": "#0d1117", "code_fg": "#e6edf3", "code_border": "#30363d"},
    "light": {"code_bg": "#f6f8fa", "code_fg": "#24292f", "code_border": "#d0d7de"},
    "github-dark": {"code_bg": "#15171a", "code_fg": "#c9d1d9", "code_border": "#30363d"},
    "github-dark-dimmed": {"code_bg": "#22272e", "code_fg": "#adbac7", "code_border": "#444c56"},
    "github-light": {"code_bg": "#f6f8fa", "code_fg": "#24292f", "code_border": "#d0d7de"},
    "github": {"code_bg": "#f6f8fa", "code_fg": "#24292f", "code_border": "#d0d7de"},
    "one-dark": {"code_bg": "#282c34", "code_fg": "#abb2bf", "code_border": "#3e4451"},
    "vitesse-light": {"code_bg": "#f9fafb", "code_fg": "#393a34", "code_border": "#e5e7eb"},
    "vitesse-dark": {"code_bg": "#121212", "code_fg": "#dbd7ca", "code_border": "#2a2a2a"},
}


def resolve_render_options(
    *,
    profile: str | None = None,
    theme: str | None = None,
    primary_color: str | None = None,
    font_family: str | None = None,
    font_size: int | None = None,
    line_height: float | None = None,
    justify: bool | None = None,
    indent_first_line: bool | None = None,
    code_theme: str | None = None,
    hr_style: str | None = None,
    heading_style: str | None = None,
    heading_styles: dict[str, str] | None = None,
    mac_code_block: bool | None = None,
    code_line_numbers: bool | None = None,
    caption_mode: str | None = None,
    footnote_links: bool | None = None,
) -> RenderOptions:
    resolved_profile = _normalize_profile(profile) or "default"
    resolved_theme = _normalize_theme(theme) or "default"
    if resolved_profile not in VALID_PROFILES:
        raise ValueError(f"unknown profile: {resolved_profile}")
    if resolved_theme not in VALID_THEMES:
        raise ValueError(f"unknown theme: {resolved_theme}")
    default_code_theme = "github" if resolved_profile == "doocs" else "dark"
    resolved_code_theme = (str(code_theme).strip() if code_theme is not None else None) or default_code_theme
    if resolved_code_theme not in VALID_CODE_THEMES:
        raise ValueError(f"unknown code_theme: {resolved_code_theme}")
    resolved_hr_style = _normalize_hr_style(hr_style) or "dash"
    if resolved_hr_style not in VALID_HR_STYLES:
        raise ValueError(f"unknown hr_style: {resolved_hr_style}")
    resolved_heading_style = _normalize_heading_style(heading_style) or "solid"
    if resolved_heading_style not in VALID_HEADING_STYLES:
        raise ValueError(f"unknown heading_style: {resolved_heading_style}")
    resolved_caption_mode = _normalize_caption_mode(caption_mode) or "hidden"
    if resolved_caption_mode not in VALID_CAPTION_MODES:
        raise ValueError(f"unknown caption_mode: {resolved_caption_mode}")

    defaults = PROFILE_DEFAULTS[resolved_profile]
    resolved_primary_color = COLOR_PRESETS.get(_normalize_primary_color(primary_color) or "", _normalize_primary_color(primary_color)) or defaults["primary_color"]
    resolved_heading_styles = _normalize_heading_styles(heading_styles)
    if resolved_heading_styles:
        invalid = {style for style in resolved_heading_styles.values() if style not in VALID_HEADING_LEVEL_STYLES}
        if invalid:
            raise ValueError(f"unknown heading_styles: {sorted(invalid)}")
    return RenderOptions(
        profile=resolved_profile,
        theme=resolved_theme,
        primary_color=resolved_primary_color,
        font_family=_normalize_font_family(font_family) or FONT_FAMILY_PRESETS["sans"],
        font_size=_normalize_font_size(font_size) or defaults["font_size"],
        line_height=_normalize_line_height(line_height) or defaults["line_height"],
        justify=defaults["justify"] if justify is None else (_normalize_toggle(justify) if _normalize_toggle(justify) is not None else bool(justify)),
        indent_first_line=defaults["indent_first_line"] if indent_first_line is None else (_normalize_toggle(indent_first_line) if _normalize_toggle(indent_first_line) is not None else bool(indent_first_line)),
        code_theme=resolved_code_theme,
        hr_style=resolved_hr_style,
        heading_style=resolved_heading_style,
        heading_styles=resolved_heading_styles,
        mac_code_block=False if mac_code_block is None else (_normalize_toggle(mac_code_block) if _normalize_toggle(mac_code_block) is not None else bool(mac_code_block)),
        code_line_numbers=False if code_line_numbers is None else (_normalize_toggle(code_line_numbers) if _normalize_toggle(code_line_numbers) is not None else bool(code_line_numbers)),
        caption_mode=resolved_caption_mode,
        footnote_links=False if footnote_links is None else (_normalize_toggle(footnote_links) if _normalize_toggle(footnote_links) is not None else bool(footnote_links)),
    )


def build_css_vars(options: RenderOptions) -> dict[str, str]:
    theme_values = THEME_OVERRIDES[options.theme]
    code_values = CODE_THEME_OVERRIDES[options.code_theme]
    heading_bg = theme_values["heading_bg"] or options.primary_color
    return {
        "--md-primary-color": options.primary_color or "#576b95",
        "--md-font-family": options.font_family or "sans-serif",
        "--md-font-size": f"{options.font_size}px",
        "--md-line-height": str(options.line_height),
        "--md-text-color": theme_values["text"],
        "--md-muted-color": theme_values["muted"],
        "--md-soft-bg": theme_values["bg_soft"],
        "--md-code-bg": code_values["code_bg"],
        "--md-code-fg": code_values["code_fg"],
        "--md-code-border": code_values["code_border"],
        "--md-border-color": theme_values["border"],
        "--md-heading-bg": heading_bg,
        "--md-heading-fg": "#ffffff",
    }


def css_var_style(options: RenderOptions) -> str:
    return "; ".join(f"{key}: {value}" for key, value in build_css_vars(options).items())
