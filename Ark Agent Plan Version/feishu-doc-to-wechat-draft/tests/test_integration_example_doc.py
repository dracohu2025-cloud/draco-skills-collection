from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLE_FEISHU_DOC = "https://g1mu6da08l.feishu.cn/docx/H0TZdmw3GoW2JSxGBFacw2jdnV8?from=from_copylink"


def run_cli(*args: str) -> dict:
    script = Path(__file__).resolve().parents[1] / "scripts" / "run.py"
    cmd = [sys.executable, str(script), *args]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(result.stdout.strip().split("\n")[-1])

def test_example_doc_can_be_fetched_via_cli() -> None:
    output = run_cli(
        "render-preview-feishu-doc-default",
        "--doc",
        EXAMPLE_FEISHU_DOC,
        "--output",
        "/tmp/feishu_doc_preview_smoke.html",
    )
    assert output["ok"] is True
    assert output["command"] == "render-preview-feishu-doc-default"
    assert output["summary"]["title"]
    assert output["summary"].get("doc_id")
    assert isinstance(output["summary"].get("used_images"), list)


@pytest.mark.parametrize("command", ["publish-feishu-doc-default"])
def test_publish_dry_run_returns_valid_payload(command: str) -> None:
    output = run_cli(
        command,
        "--doc",
        EXAMPLE_FEISHU_DOC,
        "--thumb-media-id",
        "thumb_dry_run_ci",
        "--dry-run",
    )
    assert output["ok"] is True
    assert output["command"] == command
    assert output["dry_run"] is True
    assert output["draft_media_id"] is None
    assert isinstance(output["payload"], dict)
    assert output["payload"].get("articles") and isinstance(output["payload"]["articles"], list)
    assert output["payload"]["articles"][0]["title"]
    assert isinstance(output["payload"]["articles"][0]["content"], str)
    assert output["payload"]["articles"][0]["content"].startswith("<section ") or output["payload"]["articles"][0]["content"].startswith("<html")


@pytest.mark.skipif(not Path("/tmp").is_dir(), reason="requires /tmp")
def test_render_preview_command_with_temp_output() -> None:
    output_path = Path("/tmp") / "wechat_draft_preview_from_example.html"
    if output_path.exists():
        output_path.unlink()

    output = run_cli(
        "render-preview-feishu-doc-default",
        "--doc",
        EXAMPLE_FEISHU_DOC,
        "--output",
        str(output_path),
    )

    assert output["ok"] is True
    assert output["output_path"] == str(output_path)
    assert output_path.exists()
    assert output_path.stat().st_size > 100
