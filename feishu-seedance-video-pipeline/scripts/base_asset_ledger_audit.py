#!/usr/bin/env python3
"""Audit a Feishu Base asset ledger row against a local asset_manifest.json.

Usage:
  python scripts/base_asset_ledger_audit.py asset_manifest.json record_get_after_write.json

The script is intentionally local-only. It does not call Feishu. Fetch the row first,
then audit exact field contents and attachment filenames.
"""
import hashlib
import json
import sys
from pathlib import Path

BAD_SUMMARY_ONLY_PHRASES = [
    "用于锁定服装",
    "真实猫身体",
    "软萌",
    "参考图已复用",
    "禁止衣服、拟人身体",
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_fields(record_get_path: Path) -> dict:
    obj = json.loads(record_get_path.read_text(encoding="utf-8"))
    fields = obj.get("data", {}).get("record", {})
    return fields.get("fields", fields)


def attachment_names(value):
    if not isinstance(value, list):
        return set()
    return {x.get("name") for x in value if isinstance(x, dict) and x.get("name")}


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: base_asset_ledger_audit.py asset_manifest.json record_get_after_write.json", file=sys.stderr)
        return 2

    manifest_path = Path(sys.argv[1])
    record_path = Path(sys.argv[2])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fields = load_fields(record_path)
    assets = manifest.get("assets", manifest if isinstance(manifest, list) else [])

    failures = []
    evidence = []

    for asset in assets:
        key = asset.get("asset_key", "<missing asset_key>")
        prompt_field = asset.get("base_prompt_field")
        prompt_text = asset.get("original_prompt_text") or ""
        prompt_sha = asset.get("original_prompt_sha256") or (sha256_text(prompt_text) if prompt_text else "")
        prompt_file_name = asset.get("base_prompt_file_uploaded_name")
        attachment_field = asset.get("base_attachment_field")
        artifact_name = Path(asset.get("artifact_path", "")).name if asset.get("artifact_path") else None

        if prompt_field:
            actual = fields.get(prompt_field) or ""
            prompt_not_applicable = bool(asset.get("prompt_not_applicable"))
            has_full_prompt = bool(prompt_text and prompt_text in actual)
            has_pointer = bool(prompt_file_name and prompt_sha and prompt_file_name in actual and prompt_sha in actual)
            if not prompt_not_applicable and not (has_full_prompt or has_pointer):
                failures.append(f"{key}: prompt field {prompt_field} lacks exact full prompt or canonical pointer+sha256")
            if actual.strip() in BAD_SUMMARY_ONLY_PHRASES or any(p == actual.strip() for p in BAD_SUMMARY_ONLY_PHRASES):
                failures.append(f"{key}: prompt field {prompt_field} is summary-only bad phrase")
            evidence.append({"asset_key": key, "prompt_field": prompt_field, "prompt_not_applicable": prompt_not_applicable, "has_full_prompt": has_full_prompt, "has_pointer": has_pointer})

        if prompt_file_name:
            names = attachment_names(fields.get("Prompt文件"))
            if prompt_file_name not in names:
                failures.append(f"{key}: prompt file not uploaded to Prompt文件: {prompt_file_name}")

        if attachment_field and artifact_name:
            names = attachment_names(fields.get(attachment_field))
            if artifact_name not in names:
                failures.append(f"{key}: artifact attachment missing in {attachment_field}: {artifact_name}")

    result = {
        "result": "BLOCKED_LEDGER_AUDIT_FAILED" if failures else "PASS_LEDGER_AUDIT",
        "manifest_path": str(manifest_path),
        "record_get_path": str(record_path),
        "failures": failures,
        "evidence": evidence,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
