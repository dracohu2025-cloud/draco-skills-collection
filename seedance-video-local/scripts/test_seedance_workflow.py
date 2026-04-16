#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("seedance_workflow.py")
spec = importlib.util.spec_from_file_location("seedance_workflow", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class DummyPromptModule:
    def __init__(self):
        self.calls = []

    def generate_structured_prompt(
        self,
        brief,
        include_default_constraints=True,
        extra_constraints=None,
        profile="stable",
    ):
        self.calls.append(
            {
                "brief": brief,
                "include_default_constraints": include_default_constraints,
                "extra_constraints": extra_constraints,
                "profile": profile,
            }
        )
        return {
            "method": "subject > action > camera > style > constraints",
            "profile": profile,
            "rewrite_notes": [],
            "layers": {"subject": "demo"},
            "timeline": [],
            "final_prompt": f"FINAL::{brief}",
        }


class DummyVideoModule:
    DEFAULT_MODEL = "doubao-seedance-2-0-260128"

    def __init__(self):
        self.created_payload = None
        self.create_called = 0
        self.poll_called = 0
        self.downloaded = None

    @staticmethod
    def get_base_url():
        return "https://ark.cn-beijing.volces.com/api/v3"

    def build_payload(self, args):
        return {
            "model": args.model,
            "resolution": args.resolution,
            "ratio": args.ratio,
            "duration": args.duration,
            "watermark": args.watermark,
            "ref_image_url": list(args.ref_image_url or []),
            "ref_video_url": list(args.ref_video_url or []),
            "ref_audio_url": list(args.ref_audio_url or []),
            "content": [{"type": "text", "text": args.prompt}],
        }

    def create_task(self, payload, *, api_key, base_url):
        self.create_called += 1
        self.created_payload = payload
        return {"id": "cgt-test-1"}

    @staticmethod
    def extract_task_id(resp):
        return resp.get("id")

    def poll_task(self, task_id, *, api_key, base_url, interval, timeout):
        self.poll_called += 1
        return {
            "id": task_id,
            "status": "succeeded",
            "content": {"video_url": "https://example.com/out.mp4"},
        }

    @staticmethod
    def extract_video_url(task):
        return task.get("content", {}).get("video_url")

    def download_file(self, url, path):
        self.downloaded = (url, path)


class DummyCostModule:
    @staticmethod
    def estimate_from_video_params(*, resolution, ratio, duration, fps=24, count=1, price_per_1k=0.046, width=None, height=None):
        tokens = float(duration) * float(fps) * float(count)
        return {
            "width": width or 854,
            "height": height or 480,
            "fps": fps,
            "duration": duration,
            "count": count,
            "tokens": tokens,
            "price_per_1k_cny": price_per_1k,
            "estimated_cost_cny": tokens / 1000 * float(price_per_1k),
        }


class TestSeedanceWorkflow(unittest.TestCase):
    def _args(self, mode="preview"):
        return Namespace(
            mode=mode,
            brief="第一视角果茶广告",
            brief_file=None,
            extra_constraint=[],
            no_default_constraints=False,
            profile="stable",
            api_key="k-test",
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            model="doubao-seedance-2-0-260128",
            resolution="480p",
            ratio="16:9",
            duration=5,
            seed=None,
            watermark=False,
            generate_audio=False,
            extra_json=None,
            ref_image_url=[],
            ref_video_url=[],
            ref_audio_url=[],
            first_frame_url=[],
            last_frame_url=[],
            poll_interval=1,
            poll_timeout=10,
            download=None,
            auto_submit_from_file=None,
            continue_on_error=False,
            batch_output=None,
            template=None,
            fps=24,
            video_count=1,
            token_price_cny_per_1k=0.046,
            width=None,
            height=None,
        )

    def test_preview_mode_generates_payload_only(self):
        pmod = DummyPromptModule()
        vmod = DummyVideoModule()
        args = self._args("preview")

        out = mod.run_workflow(args, pmod, vmod, DummyCostModule())

        self.assertEqual(out["mode"], "preview")
        self.assertEqual(vmod.create_called, 0)
        self.assertEqual(out["payload"]["resolution"], "480p")
        self.assertIn("FINAL::", out["prompt_package"]["final_prompt"])
        self.assertIn("cost_estimate", out)
        self.assertGreater(out["cost_estimate"]["tokens"], 0)
        self.assertIn("cost_summary_human", out)
        self.assertIn("预计 ¥", out["cost_summary_human"])
        self.assertEqual(pmod.calls[-1]["profile"], "stable")

    def test_submit_mode_creates_task(self):
        pmod = DummyPromptModule()
        vmod = DummyVideoModule()
        args = self._args("submit")

        out = mod.run_workflow(args, pmod, vmod, DummyCostModule())

        self.assertEqual(vmod.create_called, 1)
        self.assertEqual(out["task_id"], "cgt-test-1")

    def test_run_mode_polls_and_downloads(self):
        pmod = DummyPromptModule()
        vmod = DummyVideoModule()
        args = self._args("run")
        with tempfile.TemporaryDirectory() as td:
            args.download = str(Path(td) / "out.mp4")
            out = mod.run_workflow(args, pmod, vmod, DummyCostModule())

        self.assertEqual(vmod.create_called, 1)
        self.assertEqual(vmod.poll_called, 1)
        self.assertEqual(out["status"], "succeeded")
        self.assertEqual(vmod.downloaded[0], "https://example.com/out.mp4")

    def test_batch_submit_from_file(self):
        pmod = DummyPromptModule()
        vmod = DummyVideoModule()
        args = self._args("submit")

        with tempfile.TemporaryDirectory() as td:
            batch_file = Path(td) / "batch.json"
            batch_file.write_text(
                json.dumps(
                    [
                        {"brief": "第一条需求", "duration": 6},
                        {"brief": "第二条需求", "resolution": "720p"},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            args.auto_submit_from_file = str(batch_file)
            out = mod.run_batch_workflow(args, pmod, vmod, DummyCostModule())

        self.assertEqual(out["summary"]["total"], 2)
        self.assertEqual(out["summary"]["ok"], 2)
        self.assertEqual(vmod.create_called, 2)
        self.assertTrue(out["results"][0]["ok"])
        self.assertEqual(out["summary"]["estimated_video_count"], 2.0)
        self.assertIn("cost_summary_human", out["summary"])
        self.assertIn("批量总计", out["summary"]["cost_summary_human"])

    def test_batch_with_template_supplies_default_refs(self):
        pmod = DummyPromptModule()
        vmod = DummyVideoModule()
        args = self._args("preview")

        with tempfile.TemporaryDirectory() as td:
            batch_file = Path(td) / "batch.json"
            batch_file.write_text(
                json.dumps([
                    {"brief": "第一条需求"},
                    {"brief": "第二条需求", "resolution": "720p"}
                ], ensure_ascii=False),
                encoding="utf-8",
            )
            tpl_file = Path(td) / "template.json"
            tpl_file.write_text(
                json.dumps(
                    {
                        "ref_image_url": ["https://example.com/ref1.jpg"],
                        "duration": 9,
                        "resolution": "480p"
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            args.auto_submit_from_file = str(batch_file)
            args.template = str(tpl_file)
            out = mod.run_batch_workflow(args, pmod, vmod, DummyCostModule())

        self.assertEqual(out["summary"]["ok"], 2)
        first_payload = out["results"][0]["result"]["payload"]
        second_payload = out["results"][1]["result"]["payload"]
        self.assertEqual(first_payload["duration"], 9)
        self.assertEqual(first_payload["ref_image_url"], ["https://example.com/ref1.jpg"])
        self.assertEqual(second_payload["resolution"], "720p")

    def test_batch_item_can_override_profile(self):
        pmod = DummyPromptModule()
        vmod = DummyVideoModule()
        args = self._args("preview")

        with tempfile.TemporaryDirectory() as td:
            batch_file = Path(td) / "batch.json"
            batch_file.write_text(
                json.dumps(
                    [
                        {"brief": "第一条需求", "profile": "strict"},
                        {"brief": "第二条需求", "profile": "cinematic"},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            args.auto_submit_from_file = str(batch_file)
            out = mod.run_batch_workflow(args, pmod, vmod, DummyCostModule())

        self.assertEqual(out["summary"]["ok"], 2)
        self.assertEqual(pmod.calls[0]["profile"], "strict")
        self.assertEqual(pmod.calls[1]["profile"], "cinematic")


if __name__ == "__main__":
    unittest.main()
