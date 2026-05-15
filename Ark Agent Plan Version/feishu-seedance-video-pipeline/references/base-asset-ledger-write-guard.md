# Base Asset Ledger Write Guard

This guard exists because the Feishu Base row is the asset management platform. A wrong Base field can poison later production.

## Core Principle

Do not treat Base fields as casual notes. Treat them as production metadata.

For all Character Reference Sheet, Scene, Environment, and Settings reference image, Wardrobe Reference image, keyframe, prompt, payload, and output assets:

1. Local `asset_manifest.json` is the staging source of truth before writing Base.
2. Base is updated only from the manifest, never from hand-written summaries.
3. Every Base write is followed by `record-get` and exact audit.
4. If audit fails, mark the row `BLOCKED_LEDGER_AUDIT_FAILED` or equivalent and do not generate or reuse outputs.

## Mandatory Manifest Fields

Each asset entry must include:

```json
{
  "asset_key": "main_cat_character_reference_sheet",
  "asset_kind": "Character Reference Sheet",
  "subject": "Main Cat",
  "generation_tool": "Hermes image_generate",
  "generation_model": "gpt-image-2-medium",
  "generation_params": {"aspect_ratio": "landscape", "size": "1536x1024"},
  "original_prompt_path": "prompt/...txt",
  "original_prompt_sha256": "...",
  "original_prompt_text": "FULL ORIGINAL PROMPT TEXT",
  "artifact_path": "images/...png",
  "artifact_sha256": "...",
  "reuse_source": "record/path/session/task, or null",
  "base_attachment_field": "输入资产_...",
  "base_prompt_field": "角色参考图（CRS）_..._Prompt",
  "base_prompt_file_uploaded_name": "...txt"
}
```

## Write Rules

- Prompt fields must be generated mechanically from `original_prompt_text` plus provenance and hashes.
- Prompt fields must never be manually summarized.
- If a text field cannot safely hold the full prompt, it must contain a clear canonical pointer: `CANONICAL_PROMPT_FILE=<name>; sha256=<hash>; do not use this field as prompt text`, and downstream tools must read the Prompt file / manifest instead.
- Reused assets still require the original full generation Prompt, source path/record, and artifact hash.
- Never use vague phrases as Prompt fields: “用于锁定服装”, “真实猫身体”, “软萌”, “参考图已复用”. These are descriptions, not provenance.

## Read-after-write Audit

After every Base update, fetch the row and verify:

1. Each expected attachment filename exists in the target field.
2. Each prompt file filename exists in `Prompt文件` or the agreed audit field.
3. Each Base prompt field contains either:
   - the exact full original prompt text; or
   - a canonical pointer with matching filename and sha256.
4. The manifest hash in Base matches local `asset_manifest.json`.
5. No known bad summary-only phrases are present in prompt fields unless accompanied by the full prompt or canonical pointer.

Any failure: `BLOCKED_LEDGER_AUDIT_FAILED`.

## Reviewer Integration

Reviewer PASS is invalid unless the Base Asset Ledger Write Guard audit also passes.

Reviewer must cite:

- `asset_manifest.json` path
- write payload path
- `record_get_after_write.json` path
- audit result path

No audit evidence means `BLOCKED`.
