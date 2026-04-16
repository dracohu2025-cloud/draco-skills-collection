#!/usr/bin/env python3
"""Unified Seedance workflow.

输入视频需求 -> 结构化 Prompt -> 提交 Seedance 任务（可轮询到完成）。
支持批量模式：从 JSON/JSONL 文件逐条执行。
默认沿用低成本配置：480p。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from types import ModuleType

BATCH_OVERRIDABLE_FIELDS = {
    "brief",
    "brief_file",
    "extra_constraint",
    "no_default_constraints",
    "model",
    "resolution",
    "ratio",
    "duration",
    "seed",
    "generate_audio",
    "watermark",
    "extra_json",
    "ref_image_url",
    "ref_video_url",
    "ref_audio_url",
    "first_frame_url",
    "last_frame_url",
    "download",
    "poll_interval",
    "poll_timeout",
    "mode",
    "fps",
    "video_count",
    "token_price_cny_per_1k",
    "width",
    "height",
}


def _fmt_money_cny(value: float) -> str:
    return f"¥{float(value):.2f}"


def _fmt_tokens(value: float) -> str:
    return f"{float(value):,.1f}"


def build_single_cost_summary(cost_estimate: dict) -> str:
    if not cost_estimate:
        return ""
    count = float(cost_estimate.get("count", 1) or 1)
    total_cost = float(cost_estimate.get("estimated_cost_cny", 0.0))
    per_video_cost = total_cost / count if count else total_cost
    tokens = float(cost_estimate.get("tokens", 0.0))
    return (
        f"预计 {_fmt_money_cny(per_video_cost)} / 条"
        f"，本次合计 {_fmt_money_cny(total_cost)}（{count:g} 条，约 {_fmt_tokens(tokens)} tokens）"
    )


def build_batch_cost_summary(*, total_cost_cny: float, total_tokens: float, total_video_count: float) -> str:
    if total_video_count <= 0:
        return (
            f"预计 {_fmt_money_cny(0)} / 条"
            f"，批量总计 {_fmt_money_cny(total_cost_cny)}（约 {_fmt_tokens(total_tokens)} tokens）"
        )
    per_video_cost = float(total_cost_cny) / float(total_video_count)
    return (
        f"预计 {_fmt_money_cny(per_video_cost)} / 条"
        f"，批量总计 {_fmt_money_cny(total_cost_cny)}"
        f"（{total_video_count:g} 条，约 {_fmt_tokens(total_tokens)} tokens）"
    )


def load_sibling_module(module_name: str, file_name: str) -> ModuleType:
    here = Path(__file__).resolve().parent
    path = here / file_name
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"无法加载模块: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_brief(args: argparse.Namespace) -> str:
    if args.brief:
        return args.brief
    if args.brief_file:
        return Path(args.brief_file).read_text(encoding="utf-8")
    raise ValueError("必须提供 --brief 或 --brief-file")


def build_video_args(args: argparse.Namespace, final_prompt: str) -> argparse.Namespace:
    return argparse.Namespace(
        model=args.model,
        prompt=final_prompt,
        prompt_file=None,
        ref_image_url=args.ref_image_url or [],
        ref_video_url=args.ref_video_url or [],
        ref_audio_url=args.ref_audio_url or [],
        first_frame_url=args.first_frame_url or [],
        last_frame_url=args.last_frame_url or [],
        resolution=args.resolution,
        ratio=args.ratio,
        duration=args.duration,
        seed=args.seed,
        generate_audio=args.generate_audio,
        watermark=args.watermark,
        extra_json=args.extra_json,
    )


def run_workflow(
    args: argparse.Namespace,
    prompt_mod: ModuleType,
    video_mod: ModuleType,
    cost_mod: ModuleType | None = None,
) -> dict:
    brief = read_brief(args)

    prompt_package = prompt_mod.generate_structured_prompt(
        brief,
        include_default_constraints=not args.no_default_constraints,
        extra_constraints=args.extra_constraint,
    )
    final_prompt = prompt_package["final_prompt"]

    video_args = build_video_args(args, final_prompt)
    payload = video_mod.build_payload(video_args)

    if cost_mod is None:
        cost_mod = load_sibling_module("seedance_cost_estimator", "seedance_cost_estimator.py")

    cost_estimate = cost_mod.estimate_from_video_params(
        resolution=args.resolution,
        ratio=args.ratio,
        duration=args.duration,
        fps=args.fps,
        count=args.video_count,
        price_per_1k=args.token_price_cny_per_1k,
        width=args.width,
        height=args.height,
    )

    result: dict = {
        "mode": args.mode,
        "brief": brief,
        "prompt_package": prompt_package,
        "payload": payload,
        "cost_estimate": cost_estimate,
        "cost_summary_human": build_single_cost_summary(cost_estimate),
    }

    if args.mode == "preview":
        return result

    if not args.api_key:
        raise ValueError("submit/run 模式必须提供 --api-key")

    base_url = args.base_url.rstrip("/")
    create_resp = video_mod.create_task(payload, api_key=args.api_key, base_url=base_url)
    task_id = video_mod.extract_task_id(create_resp)
    if not task_id:
        raise RuntimeError(f"创建任务成功但未解析到 task_id: {json.dumps(create_resp, ensure_ascii=False)}")

    result.update({
        "task_id": task_id,
        "create_response": create_resp,
    })

    if args.mode == "submit":
        return result

    task = video_mod.poll_task(
        task_id,
        api_key=args.api_key,
        base_url=base_url,
        interval=args.poll_interval,
        timeout=args.poll_timeout,
    )
    status = task.get("status")
    video_url = video_mod.extract_video_url(task)

    result.update(
        {
            "status": status,
            "video_url": video_url,
            "task": task,
        }
    )

    if status == "succeeded" and video_url and args.download:
        video_mod.download_file(video_url, args.download)
        result["downloaded_to"] = str(Path(args.download).resolve())

    return result


def _load_batch_items(file_path: str) -> list[dict]:
    path = Path(file_path)
    text = path.read_text(encoding="utf-8")

    def _validate(items: list) -> list[dict]:
        out: list[dict] = []
        for i, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"批量文件第 {i} 项不是对象")
            out.append(item)
        return out

    if path.suffix.lower() == ".jsonl":
        rows = []
        for i, line in enumerate(text.splitlines(), start=1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            try:
                rows.append(json.loads(s))
            except Exception as ex:
                raise ValueError(f"JSONL 第 {i} 行解析失败: {ex}") from ex
        return _validate(rows)

    data = json.loads(text)
    if isinstance(data, list):
        return _validate(data)
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return _validate(data["items"])
    raise ValueError("批量文件必须是 JSON 数组，或 {\"items\": [...]}，或 JSONL")


def _load_template_data(file_path: str) -> dict:
    path = Path(file_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("template 文件必须是 JSON object")
    return data


def _merge_item_args(base_args: argparse.Namespace, item: dict) -> argparse.Namespace:
    merged = argparse.Namespace(**vars(base_args))
    for key, value in item.items():
        if key not in BATCH_OVERRIDABLE_FIELDS:
            continue
        if key == "extra_json" and isinstance(value, dict):
            setattr(merged, key, json.dumps(value, ensure_ascii=False))
        else:
            setattr(merged, key, value)
    return merged


def run_batch_workflow(
    args: argparse.Namespace,
    prompt_mod: ModuleType,
    video_mod: ModuleType,
    cost_mod: ModuleType | None = None,
) -> dict:
    if not args.auto_submit_from_file:
        raise ValueError("批量模式需要 --auto-submit-from-file")

    items = _load_batch_items(args.auto_submit_from_file)
    template_data = _load_template_data(args.template) if getattr(args, "template", None) else {}
    args_base = _merge_item_args(args, template_data) if template_data else argparse.Namespace(**vars(args))

    results = []
    ok = 0
    total_tokens = 0.0
    total_cost_cny = 0.0
    total_video_count = 0.0

    for idx, item in enumerate(items, start=1):
        item_args = _merge_item_args(args_base, item)
        try:
            out = run_workflow(item_args, prompt_mod, video_mod, cost_mod)
            ok += 1
            total_tokens += float((out.get("cost_estimate") or {}).get("tokens", 0.0))
            total_cost_cny += float((out.get("cost_estimate") or {}).get("estimated_cost_cny", 0.0))
            total_video_count += float((out.get("cost_estimate") or {}).get("count", 0.0))
            results.append({"index": idx, "ok": True, "input": item, "result": out})
        except Exception as ex:
            results.append({"index": idx, "ok": False, "input": item, "error": str(ex)})
            if not args.continue_on_error:
                break

    processed = len(results)
    failed = processed - ok
    summary = {
        "total": len(items),
        "processed": processed,
        "ok": ok,
        "failed": failed,
        "estimated_tokens": total_tokens,
        "estimated_cost_cny": total_cost_cny,
        "estimated_video_count": total_video_count,
        "cost_summary_human": build_batch_cost_summary(
            total_cost_cny=total_cost_cny,
            total_tokens=total_tokens,
            total_video_count=total_video_count,
        ),
    }

    out = {
        "mode": "batch",
        "source_file": str(Path(args.auto_submit_from_file).resolve()),
        "summary": summary,
        "results": results,
    }
    if getattr(args, "template", None):
        out["template_file"] = str(Path(args.template).resolve())

    if args.batch_output:
        p = Path(args.batch_output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        out["batch_output"] = str(p.resolve())

    return out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Seedance workflow: brief -> structured prompt -> submit/run")
    p.add_argument("--mode", choices=["preview", "submit", "run"], default="submit")

    p.add_argument("--brief", help="自然语言视频需求")
    p.add_argument("--brief-file", help="从文件读取自然语言需求")

    p.add_argument("--extra-constraint", action="append", default=[], help="追加约束，可重复")
    p.add_argument("--no-default-constraints", action="store_true", help="不注入默认约束")

    p.add_argument("--api-key", help="Ark API Key（submit/run 必填）")
    p.add_argument("--base-url", default="https://ark.cn-beijing.volces.com/api/v3")

    p.add_argument("--model", default="doubao-seedance-2-0-260128")
    p.add_argument("--resolution", default="480p", choices=["480p", "720p"])
    p.add_argument("--ratio", default="16:9")
    p.add_argument("--duration", type=int, default=5)
    p.add_argument("--seed", type=int)
    p.add_argument("--generate-audio", action="store_true")
    p.add_argument("--watermark", action="store_true", default=False)
    p.add_argument("--extra-json", help="附加 JSON object，会 merge 到 payload")

    p.add_argument("--ref-image-url", action="append", default=[])
    p.add_argument("--ref-video-url", action="append", default=[])
    p.add_argument("--ref-audio-url", action="append", default=[])
    p.add_argument("--first-frame-url", action="append", default=[])
    p.add_argument("--last-frame-url", action="append", default=[])

    p.add_argument("--poll-interval", type=int, default=20)
    p.add_argument("--poll-timeout", type=int, default=1800)
    p.add_argument("--download", help="run 成功后下载 mp4")

    # 成本估算参数（仅估算，不影响实际扣费）
    p.add_argument("--fps", type=float, default=24, help="估算帧率，默认 24")
    p.add_argument("--video-count", type=float, default=1, help="估算条数，默认 1")
    p.add_argument("--token-price-cny-per-1k", type=float, default=0.046, help="每1000 tokens 单价，默认 ¥0.046")
    p.add_argument("--width", type=int, help="手动指定宽（像素），覆盖 resolution+ratio 推导")
    p.add_argument("--height", type=int, help="手动指定高（像素），覆盖 resolution+ratio 推导")

    p.add_argument("--auto-submit-from-file", help="批量输入文件（JSON/JSONL）")
    p.add_argument("--template", help="模板 JSON（常用 refs/duration/ratio 等默认值）")
    p.add_argument("--continue-on-error", action="store_true", help="批量模式遇错继续")
    p.add_argument("--batch-output", help="批量结果写入 JSON 文件")

    p.add_argument("--json", action="store_true", help="输出 JSON")
    return p


def main() -> int:
    args = build_parser().parse_args()
    prompt_mod = load_sibling_module("seedance_prompt_generator", "seedance_prompt_generator.py")
    video_mod = load_sibling_module("seedance_video", "seedance_video.py")
    cost_mod = load_sibling_module("seedance_cost_estimator", "seedance_cost_estimator.py")

    try:
        if args.auto_submit_from_file:
            out = run_batch_workflow(args, prompt_mod, video_mod, cost_mod)
            has_fail = out["summary"]["failed"] > 0
            if args.json:
                print(json.dumps(out, ensure_ascii=False, indent=2))
                return 1 if has_fail else 0

            print("mode: batch")
            print(f"source_file: {out['source_file']}")
            print(
                f"summary: total={out['summary']['total']} processed={out['summary']['processed']} "
                f"ok={out['summary']['ok']} failed={out['summary']['failed']} "
                f"estimated_tokens={out['summary']['estimated_tokens']} "
                f"estimated_cost_cny={out['summary']['estimated_cost_cny']}"
            )
            print(f"cost_summary: {out['summary']['cost_summary_human']}")
            if out.get("template_file"):
                print(f"template_file: {out['template_file']}")
            if out.get("batch_output"):
                print(f"batch_output: {out['batch_output']}")
            return 1 if has_fail else 0

        if args.template:
            args = _merge_item_args(args, _load_template_data(args.template))

        out = run_workflow(args, prompt_mod, video_mod, cost_mod)
        if args.json:
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0

        print(f"mode: {out['mode']}")
        print(f"method: {out['prompt_package']['method']}")
        print("\n[final_prompt]")
        print(out["prompt_package"]["final_prompt"])
        if out.get("cost_estimate"):
            ce = out["cost_estimate"]
            print("\n[cost_estimate]")
            print(f"tokens: {ce.get('tokens')}")
            print(f"estimated_cost_cny: {ce.get('estimated_cost_cny')}")
            print(f"formula: {ce.get('formula')}")
            if out.get("cost_summary_human"):
                print(f"cost_summary: {out['cost_summary_human']}")
        if out.get("task_id"):
            print(f"\ntask_id: {out['task_id']}")
        if out.get("status"):
            print(f"status: {out['status']}")
        if out.get("video_url"):
            print(f"video_url: {out['video_url']}")
        if out.get("downloaded_to"):
            print(f"downloaded_to: {out['downloaded_to']}")
        return 0
    except Exception as ex:
        print(f"ERROR: {ex}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
