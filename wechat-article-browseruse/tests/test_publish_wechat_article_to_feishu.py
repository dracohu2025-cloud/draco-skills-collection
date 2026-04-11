import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "publish_wechat_article_to_feishu.py"
spec = importlib.util.spec_from_file_location("publish_wechat_article_to_feishu", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_clean_body_removes_h1_and_prepends_original_url():
    markdown = "# 标题\n\n_作者：A_\n\n## 一\n\n正文\n"

    cleaned = module._clean_body(markdown, "https://mp.weixin.qq.com/s/demo")

    assert cleaned.startswith("> 原文链接：https://mp.weixin.qq.com/s/demo\n\n_作者：A_\n\n## 一")
    assert "# 标题" not in cleaned
    assert cleaned.endswith("正文\n")


def test_select_best_search_result_prefers_exact_title_and_latest_update_time():
    payload = {
        "data": {
            "results": [
                {
                    "title_highlighted": "<h>Hermes Agent 的七个冷知识</h>",
                    "result_meta": {
                        "token": "***",
                        "url": "https://feishu.cn/docx/older",
                        "update_time": 100,
                    },
                },
                {
                    "title_highlighted": "<h>Hermes Agent 的七个冷知识</h>",
                    "result_meta": {
                        "token": "***",
                        "url": "https://feishu.cn/docx/newer",
                        "update_time": 200,
                    },
                },
                {
                    "title_highlighted": "<h>Hermes Agent 的七个冷知识（旧稿）</h>",
                    "result_meta": {
                        "token": "***",
                        "url": "https://feishu.cn/docx/fuzzy",
                        "update_time": 999,
                    },
                },
            ]
        }
    }

    best = module._select_best_search_result(payload, "Hermes Agent 的七个冷知识")

    assert best == {"doc_id": "newer", "doc_url": "https://feishu.cn/docx/newer"}


def test_resolve_doc_reference_returns_immediate_create_result_without_search():
    create_payload = {
        "data": {
            "doc_id": "doc-123",
            "doc_url": "https://feishu.cn/docx/doc-123",
            "status": "done",
        }
    }
    called = []

    def fake_search(title: str):
        called.append(title)
        return {}

    resolved = module._resolve_doc_reference(create_payload, "标题", fake_search, retries=2, delay_seconds=0)

    assert resolved == {"doc_id": "doc-123", "doc_url": "https://feishu.cn/docx/doc-123"}
    assert called == []


def test_resolve_doc_reference_falls_back_to_search_for_async_create(monkeypatch):
    create_payload = {
        "data": {
            "status": "running",
            "task_id": "task-1",
        }
    }
    calls = []

    def fake_search(title: str):
        calls.append(title)
        return {
            "data": {
                "results": [
                    {
                        "title_highlighted": "<h>标题</h>",
                        "result_meta": {
                            "token": "***",
                            "url": "https://feishu.cn/docx/doc-456",
                            "update_time": 300,
                            "create_time": 250,
                        },
                    }
                ]
            }
        }

    monkeypatch.setattr(module.time, "sleep", lambda _: None)

    resolved = module._resolve_doc_reference(
        create_payload,
        "标题",
        fake_search,
        retries=3,
        delay_seconds=0,
        min_create_time=200,
    )

    assert resolved == {"doc_id": "doc-456", "doc_url": "https://feishu.cn/docx/doc-456"}
    assert calls == ["标题"]


def test_resolve_doc_reference_waits_for_doc_created_after_current_run(monkeypatch):
    create_payload = {
        "data": {
            "status": "running",
            "task_id": "task-2",
        }
    }
    responses = [
        {
            "data": {
                "results": [
                    {
                        "title_highlighted": "<h>标题</h>",
                        "result_meta": {
                            "token": "***",
                            "url": "https://feishu.cn/docx/old-doc",
                            "update_time": 150,
                            "create_time": 150,
                        },
                    }
                ]
            }
        },
        {
            "data": {
                "results": [
                    {
                        "title_highlighted": "<h>标题</h>",
                        "result_meta": {
                            "token": "***",
                            "url": "https://feishu.cn/docx/new-doc",
                            "update_time": 250,
                            "create_time": 250,
                        },
                    }
                ]
            }
        },
    ]

    def fake_search(title: str):
        return responses.pop(0)

    monkeypatch.setattr(module.time, "sleep", lambda _: None)

    resolved = module._resolve_doc_reference(
        create_payload,
        "标题",
        fake_search,
        retries=2,
        delay_seconds=0,
        min_create_time=200,
    )

    assert resolved == {"doc_id": "new-doc", "doc_url": "https://feishu.cn/docx/new-doc"}


def test_import_doc_file_uses_relative_path_and_returns_final_doc(tmp_path, monkeypatch):
    markdown_file = tmp_path / "article.md"
    markdown_file.write_text("hello")
    calls = []

    def fake_run(command, capture_output, text, check, cwd=None):
        calls.append({"command": command, "cwd": cwd})

        class Result:
            stdout = '{"ok":true,"data":{"token": "***","url":"https://feishu.cn/docx/doc-import"}}'
            stderr = ""

        return Result()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module, "_lark_cli_cmd", lambda: ["lark-cli"])

    imported = module._import_doc_file(markdown_file, "标题", folder_token="fld123")

    assert imported == {"ok": True, "data": {"token": "***", "url": "https://feishu.cn/docx/doc-import"}}
    assert calls == [{
        "command": [
            "lark-cli",
            "drive",
            "+import",
            "--as",
            "user",
            "--file",
            "./article.md",
            "--type",
            "docx",
            "--name",
            "标题",
            "--folder-token",
            "fld123",
        ],
        "cwd": str(tmp_path),
    }]
