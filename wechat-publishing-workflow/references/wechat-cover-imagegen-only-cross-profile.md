# WeChat cover imagegen-only hard rule + cross-profile propagation

## Trigger
Use this when publishing or updating WeChat Official Account article drafts for this user, especially Feishu-doc → WeChat draft flows.

## Hard rule
For WeChat Official Account **article covers**, generate the complete cover via `image_generate` / `image_gen` in one image-generation step. The generated image must already contain the public-facing title, subtitle, tags, badges, and any logo-like visual elements that the prompt asks for.

Do **not**:
- generate a blank/background image and then add title/subtitle/tags with PIL, HTML, SVG, canvas, screenshots, ImageMagick, or other code;
- repair failed OCR/text locally by drawing over the image;
- paste logos, badges, or labels after image generation.

Allowed local code operations:
- crop / resize to the WeChat cover ratio, e.g. `2350×1000`;
- compress / convert format if needed for upload;
- rename / upload / replace draft cover.

If OCR or layout fails, regenerate with a simpler prompt: fewer words, larger type, fewer chips, stronger hierarchy. Do not fix text with code unless the user explicitly overrides this rule for that one task.

## QA checklist
Before uploading/replacing the cover:
1. Run `vision_analyze` on the generated image or final crop.
2. Verify exact intended OCR for main title, subtitle, and tags.
3. Verify no extra/gibberish text, watermark, QR code, draft/test/internal-production wording.
4. Verify the crop did not cut off generated text.
5. Verify the palette is bright/vivid unless the article demands a dark serious mood.

## Cross-profile propagation pattern
When the user says “让本机全部其他 Hermes 实例也记住” for a class workflow rule:
1. Put the rule in the active class-level skill `SKILL.md`.
2. Patch any active profile-local copies of the same skill under `~/.hermes/profiles/*/skills/...`.
3. Add a high-priority rule to every profile’s `SOUL.md` only for genuinely global user-critical constraints.
4. Remove profile `.skills_prompt_snapshot.json` files so new sessions rebuild skill prompts.
5. Verify every active skill copy contains the hard rule and no old contradictory wording remains.

Do not edit bundled/hub-protected skills for this; use the class-level user skill and profile-local copies instead.