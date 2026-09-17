# WeChat Engagement CTA Banner Notes

Session learning from a failed “一键三连” footer/banner image.

## What failed
- A deterministic PIL hand-drawn pixel-art banner looked crude and “engineering-made”.
- Even if the ratio and text were technically correct, it did not match the user’s expected WeChat cover quality.

## Better workflow
1. Treat CTA/footer images as a WeChat cover subcase, not as simple icon drawing.
2. Use `image_generate` for the main art direction:
   - high-end editorial WeChat banner
   - 2.35:1 final crop target
   - no rendered text in the generated image
   - clean safe area for later text overlay
3. If the user asks for voxel/体素风, use:
   - polished 3D voxel illustration
   - cream background
   - warm Doocs orange-red accent `#FA5151`
   - exactly three large glowing icons: thumbs-up, share arrow, heart/在看
   - avoid extra buildings/crosses/game clutter when possible
4. Crop/resize locally to `2350×1000`.
5. Add Chinese text locally with Noto Sans CJK / similar font to avoid AI text corruption.
6. Run `vision_analyze` twice:
   - generated base image: style, icon count, no text/watermark/clutter
   - final overlay: exact Chinese readability, no遮挡, ratio, three elements clear

## Example prompt core
```text
Premium WeChat Official Account cover banner, final crop 2.35:1, high-end voxel art.
Minimal cream-colored voxel stage with exactly three large floating glowing voxel icons arranged left to right:
1) thumbs-up icon for Like,
2) clear forward/share arrow,
3) glowing heart icon for Watching.
Warm Doocs orange-red #FA5151, soft gold glow, cream background, clean lower safe area for Chinese text overlay.
Must avoid: text, letters, numbers, UI screenshots, logos, QR codes, watermarks, clutter, flat pixel art.
```
