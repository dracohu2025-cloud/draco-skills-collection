from manim import *
import numpy as np

# Color Palette
BG          = "#0A0A0F"      # deep void black
SIN_COLOR   = "#FF4D4D"      # coral red — target curve
APPROX_COLOR= "#00F5FF"      # electric cyan — approximation
TEXT_COLOR  = "#FFFFFF"      # pure white
ACCENT      = "#FFD93D"      # golden yellow
GRID_COLOR  = "#2A2A3A"      # dim purple-grey
MONO        = "FreeMono"     # or "DejaVu Sans Mono"

# Axes configuration
AXES_CONFIG = {
    "x_range":       [-PI, PI, PI/2],
    "y_range":       [-3.5, 3.5, 1],
    "x_length":      12,
    "y_length":      7,
    "axis_config":   {"color": GRID_COLOR, "stroke_width": 1.5, "include_ticks": True, "include_tip": False},
    "tips":          False,
}

# Example polynomial approximations
def p1(x):  return x
def p3(x):  return x - x**3/6

def target_func(x):
    """The mathematical function being explained."""
    return np.sin(x)

# ═══════════════════════════════════════════════════════════════
#  Scene 1 — Title Hook
#  Audio duration: {{D1}}s
# ═══════════════════════════════════════════════════════════════
class S1_Title(Scene):
    def construct(self):
        self.camera.background_color = BG
        title = Text("{{TITLE}}", font_size=64, color=TEXT_COLOR, weight=BOLD, font=MONO)
        subtitle = Text("{{SUBTITLE}}", font_size=26, color=APPROX_COLOR, font=MONO).next_to(title, DOWN, buff=0.6)
        group = VGroup(title, subtitle).move_to(ORIGIN)

        self.play(FadeIn(title, shift=UP*0.3), run_time=1.0)
        self.wait(0.5)
        self.play(FadeIn(subtitle, shift=DOWN*0.2), run_time=0.8)
        self.wait(0.5)
        self.play(FadeOut(group), run_time=0.5)
        self.wait(0.5)
        # total: 1.0+0.5+0.8+0.5+0.5+0.5 = 3.8s (adjust waits to match audio)

# ═══════════════════════════════════════════════════════════════
#  Scene 2 — Introduce Target Function
#  Audio duration: {{D2}}s
# ═══════════════════════════════════════════════════════════════
class S2_TargetFunction(Scene):
    def construct(self):
        self.camera.background_color = BG
        axes = Axes(**AXES_CONFIG)
        target = axes.plot(target_func, x_range=[-PI, PI], color=SIN_COLOR, stroke_width=4)
        label = Text("{{TARGET_LABEL}}", font_size=28, color=SIN_COLOR, font=MONO).next_to(axes.c2p(PI/2, 1), UR, buff=0.2)

        self.play(Create(axes), run_time=1.0)
        self.wait(0.2)
        self.play(Create(target), run_time=2.0)
        self.wait(0.3)
        self.play(Write(label), run_time=0.8)
        self.wait(1.0)
        self.play(FadeOut(label), run_time=0.3)
        self.wait(1.0)
        # total: ~6.6s (adjust waits to match audio)

# ═══════════════════════════════════════════════════════════════
#  Scene 3 — First Approximation
#  Audio duration: {{D3}}s
# ═══════════════════════════════════════════════════════════════
class S3_FirstApprox(Scene):
    def construct(self):
        self.camera.background_color = BG
        axes = Axes(**AXES_CONFIG)
        target = axes.plot(target_func, x_range=[-PI, PI], color=SIN_COLOR, stroke_width=4)
        approx = axes.plot(p1, x_range=[-PI, PI], color=APPROX_COLOR, stroke_width=4)

        subtitle = Text("{{S3_SUBTITLE}}", font_size=22, color=ACCENT, font=MONO).to_edge(UP, buff=0.6)
        formula = MathTex(r"{{S3_FORMULA}}", color=APPROX_COLOR, font_size=32).to_edge(DOWN, buff=0.8)

        self.add(axes, target)
        self.play(Write(subtitle), run_time=1.0)
        self.wait(0.3)
        self.play(Create(approx), run_time=1.5)
        self.wait(0.5)
        self.play(Write(formula), run_time=1.0)
        self.wait(0.5)

        # Highlight region
        vline_l = DashedLine(axes.c2p(-0.8, -3.5), axes.c2p(-0.8, 3.5), color=ACCENT, stroke_width=1.5, dash_length=0.1)
        vline_r = DashedLine(axes.c2p(0.8, -3.5), axes.c2p(0.8, 3.5), color=ACCENT, stroke_width=1.5, dash_length=0.1)
        region = Text("{{S3_REGION_LABEL}}", font_size=18, color=ACCENT, font=MONO).move_to(axes.c2p(0, -2.8))
        self.play(Create(vline_l), Create(vline_r), FadeIn(region), run_time=0.8)
        self.wait(0.3)

        self.play(FadeOut(subtitle), FadeOut(formula), FadeOut(vline_l), FadeOut(vline_r), FadeOut(region), run_time=0.5)
        self.wait(2.0)
        # total: ~8.9s (adjust waits to match audio)
