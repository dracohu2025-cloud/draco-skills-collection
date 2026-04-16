#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("seedance_cost_estimator.py")
spec = importlib.util.spec_from_file_location("seedance_cost_estimator", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class TestSeedanceCostEstimator(unittest.TestCase):
    def test_dimensions_from_resolution_ratio(self):
        w, h = mod.estimate_dimensions("480p", "16:9")
        self.assertEqual((w, h), (854, 480))

    def test_tokens_and_cost_formula(self):
        out = mod.estimate_from_video_params(
            resolution="480p",
            ratio="16:9",
            duration=5,
            fps=24,
            count=1,
            price_per_1k=0.046,
        )
        self.assertAlmostEqual(out["tokens"], 48037.5, places=3)
        self.assertAlmostEqual(out["estimated_cost_cny"], 2.209725, places=6)


if __name__ == "__main__":
    unittest.main()
