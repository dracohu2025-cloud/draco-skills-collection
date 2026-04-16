#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("seedance_prompt_generator.py")
spec = importlib.util.spec_from_file_location("seedance_prompt_generator", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class TestSeedancePromptGenerator(unittest.TestCase):
    def test_parse_chinese_time_ranges(self):
        brief = "2-4 秒：手把苹果投入雪克杯并摇晃。4-6秒：成品特写，镜头拉近。"
        shots = mod.parse_timecoded_shots(brief)
        self.assertEqual(len(shots), 2)
        self.assertEqual(shots[0]["start"], 2)
        self.assertEqual(shots[0]["end"], 4)

    def test_parse_hhmm_timeline_ranges(self):
        brief = "[00:00-00:04] 镜头1：壁咚。 [00:04-00:07] 镜头2：对望。"
        shots = mod.parse_timecoded_shots(brief)
        self.assertEqual(len(shots), 2)
        self.assertEqual(shots[0]["start"], 0)
        self.assertEqual(shots[0]["end"], 4)
        self.assertIn("壁咚", shots[0]["text"])

    def test_parse_decimal_second_timeline_ranges(self):
        brief = "[0.0-0.8s] 举枪。 [0.8-1.6s] 子弹充能。 [1.6-2.8s] 子弹飞行。"
        shots = mod.parse_timecoded_shots(brief)
        self.assertEqual(len(shots), 3)
        self.assertEqual(shots[0]["start"], 0.0)
        self.assertEqual(shots[0]["end"], 0.8)
        self.assertIn("举枪", shots[0]["text"])

    def test_repair_vague_words(self):
        text = "cinematic, amazing, lots of movement"
        repaired, notes = mod.repair_vague_words(text)
        self.assertIn("cinematic film tone, 35mm", repaired)
        self.assertTrue(any("lots of movement" in n for n in notes))

    def test_repair_bible_degrading_keywords(self):
        text = "fast camera with glow and glimmer highlights"
        repaired, notes = mod.repair_vague_words(text)
        self.assertIn("single fast element", repaired)
        self.assertIn("steady intensity diffuse light", repaired)
        self.assertTrue(any("fast" in n for n in notes))

    def test_generate_structured_prompt_has_five_layers(self):
        brief = "第一视角少女在茶饮店摇果茶，镜头推近，golden hour，避免抖动"
        result = mod.generate_structured_prompt(brief)
        layers = result["layers"]
        self.assertIn("subject", layers)
        self.assertIn("action", layers)
        self.assertIn("camera", layers)
        self.assertIn("style", layers)
        self.assertIn("constraints", layers)
        self.assertIn("avoid jitter", result["final_prompt"])

    def test_subject_action_should_not_duplicate_with_semicolon_brief(self):
        brief = "首帧固定为给定女孩持枪画面；子弹出膛后短暂停格；镜头跟随子弹并逐渐拉远。"
        result = mod.generate_structured_prompt(brief)
        self.assertNotEqual(result["layers"]["subject"], result["layers"]["action"])
        self.assertIn("子弹", result["layers"]["action"])

    def test_camera_single_primary_movement_without_timeline(self):
        brief = "角色在街道奔跑，镜头推近并环绕拍摄，golden hour"
        result = mod.generate_structured_prompt(brief)
        self.assertEqual(result["layers"]["camera"], "slow dolly-in")

    def test_section_headers_should_drive_subject_action(self):
        brief = """
Core Subject:
A young male speedster with super-speed abilities.

Main Action:
Only the male protagonist retains the ability to move at super speed.

Action Sequence:
He rescues civilians and hurls a steel beam at the monster.

Cinematography:
Dynamic cinematic camera movement with low-angle tracking shots.
"""
        result = mod.generate_structured_prompt(brief)
        self.assertIn("speedster", result["layers"]["subject"].lower())
        self.assertIn("retains the ability", result["layers"]["action"].lower())
        self.assertIn("tracking", result["layers"]["camera"].lower())

    def test_case2_style_and_timeline_headers(self):
        brief = """
[CINEMATIC SETUP]
Film Style: Ultra-realistic 35mm anamorphic.
Camera Behavior: One continuous unbroken Steadicam glide.

[IMAGE REFERENCE]
Night market street with crowded lane and wet pavement.

[TIMELINE — CONTINUOUS SHOT]
[00:00-00:04] HOLD. Medium-wide matching image1.
[00:04-00:07] DRIFT LEFT. Slow Steadicam glide left.
[00:07-00:11] REVERSE. Camera drifts back right.
[00:11-00:15] WOK FLARE. Camera settles on the lead cook.
"""
        result = mod.generate_structured_prompt(brief)
        self.assertNotEqual(result["layers"]["subject"], "[CINEMATIC SETUP]")
        self.assertEqual(len(result["timeline"]), 4)
        self.assertIn("steadicam glide", result["layers"]["camera"].lower())

    def test_bracket_cn_headers_should_parse(self):
        brief = """
【风格】都市情感短片（Urban Romance）
【场景】黄昏天台角落
【角色】小灰@图片1；小青@图片2
[00:00-00:04] 镜头1：壁咚
[00:04-00:07] 镜头2：对望
"""
        result = mod.generate_structured_prompt(brief)
        self.assertIn("小灰", result["layers"]["subject"])
        self.assertIn("都市情感短片", result["layers"]["style"])
        self.assertEqual(len(result["timeline"]), 2)


if __name__ == "__main__":
    unittest.main()
