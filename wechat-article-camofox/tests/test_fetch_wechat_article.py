import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fetch_wechat_article.py"
spec = importlib.util.spec_from_file_location("fetch_wechat_article", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_nested_list_inline_code_renders_single_bullet_item():
    snapshot = """- heading \"标题\" [level=1]
- paragraph: 引言
- list:
  - listitem:
    - text: •
    - code: skills_list
  - listitem:
    - text: • 可以在完成安装之后，在终端（Terminal）输入
    - code: hermes gateway setup
    - text: 来触发添加新的聊天软件channel入口：
"""

    meta, blocks = module._parse_snapshot(snapshot, images=[])

    assert meta["title"] == "标题"
    assert blocks == [
        "引言",
        "- `skills_list`",
        "- 可以在完成安装之后，在终端（Terminal）输入`hermes gateway setup`来触发添加新的聊天软件channel入口：",
    ]


def test_paragraph_children_stay_in_same_block_without_extra_line_breaks():
    snapshot = """- heading \"标题\" [level=1]
- paragraph:
  - strong: Hermes 把 skill 做成了学习闭环的一部分
  - text: ，而不只是插件系统。可以拆成 5 点看：
- blockquote:
  - paragraph:
    - text: 这是引用里的正文。
"""

    meta, blocks = module._parse_snapshot(snapshot, images=[])

    assert meta["title"] == "标题"
    assert blocks == [
        "**Hermes 把 skill 做成了学习闭环的一部分**，而不只是插件系统。可以拆成 5 点看：",
        "> 这是引用里的正文。",
    ]


def test_markdown_keeps_paragraphs_outside_list_items():
    markdown = module._to_markdown(
        {"title": "标题", "author": "", "published_at": ""},
        [
            "- 第一项",
            "- 第二项",
            "后续正文",
        ],
    )

    assert "- 第二项\n\n后续正文" in markdown


def test_install_camofox_repo_clones_and_installs_when_repo_missing(tmp_path, monkeypatch):
    repo = tmp_path / "camofox-browser"
    calls = []

    def fake_require(command):
        calls.append(("require", command))

    def fake_run(command, check, cwd=None, timeout=None):
        calls.append(("run", tuple(command), cwd, timeout))
        if command[:2] == ["git", "clone"]:
            repo.mkdir(parents=True, exist_ok=True)
            (repo / "server.js").write_text("console.log('ok')")
            (repo / "package.json").write_text("{}")

    monkeypatch.setattr(module, "_require_command", fake_require)
    monkeypatch.setattr(module.subprocess, "run", fake_run)

    installed = module._install_camofox_repo(repo)

    assert installed == repo
    assert calls[0] == ("require", "git")
    assert calls[1] == ("require", "npm")
    assert any(call[1][:2] == ("git", "clone") for call in calls if call[0] == "run")
    assert any(call[1][:2] == ("npm", "install") and call[2] == repo for call in calls if call[0] == "run")



def test_ensure_camofox_bootstraps_and_starts_when_health_unavailable(tmp_path, monkeypatch):
    repo = tmp_path / "camofox-browser"
    transitions = {"health_checks": 0, "install": 0, "start": 0}

    def fake_http(method, path, timeout=60, payload=None):
        assert method == "GET"
        assert path == "/health"
        transitions["health_checks"] += 1
        if transitions["health_checks"] == 1:
            raise OSError("down")
        return {"ok": True}

    def fake_install(repo_path=None):
        transitions["install"] += 1
        return repo

    def fake_start(repo_path=None):
        transitions["start"] += 1
        assert repo_path == repo

    monkeypatch.setattr(module, "_http", fake_http)
    monkeypatch.setattr(module, "_install_camofox_repo", fake_install)
    monkeypatch.setattr(module, "_start_camofox_server", fake_start)

    module._ensure_camofox()

    assert transitions == {"health_checks": 2, "install": 1, "start": 1}



def test_ensure_camofox_reports_bootstrap_progress(tmp_path, monkeypatch, capsys):
    repo = tmp_path / "camofox-browser"
    checks = {"count": 0}

    def fake_http(method, path, timeout=60, payload=None):
        checks["count"] += 1
        if checks["count"] == 1:
            raise OSError("down")
        return {"ok": True}

    monkeypatch.setattr(module, "_http", fake_http)
    monkeypatch.setattr(module, "_install_camofox_repo", lambda repo_path=None: repo)
    monkeypatch.setattr(module, "_start_camofox_server", lambda repo_path=None: None)

    module._ensure_camofox()

    captured = capsys.readouterr()
    assert "Checking camofox-browser health" in captured.err
    assert "Installing camofox-browser" in captured.err
    assert "Starting camofox-browser" in captured.err
    assert "camofox-browser is healthy" in captured.err
