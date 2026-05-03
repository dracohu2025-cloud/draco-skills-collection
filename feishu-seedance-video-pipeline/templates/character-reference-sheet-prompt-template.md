# Character Reference Sheet Prompt Template

Use this template when creating a main character reference asset for later Seedance video generation.

## Template

```text
Create a single unified MASTER CHARACTER REFERENCE SHEET for one fictional character.

STYLE: [visual style, e.g. Shao Brothers-inspired cinematic realism / stylized 3D cinematic comedy / premium animation visual bible / clean character continuity sheet]
SUBJECT: [character name or role]
IDENTITY: [species / gender / age range if relevant / body type / face shape / hair or fur / eyes / signature silhouette]
COSTUME OR SURFACE DESIGN: [outfit, fur pattern, fabric, accessories, color blocking]
PERSONALITY: [3 to 6 traits visible in posture and expression]
STORY FUNCTION: [protagonist, rival, comic relief, customer, villain, etc.]
FORBIDDEN DRIFT: [identity traits that must never change]

Create the board in a 4:3 horizontal layout. The board layout, background, typography and spacing must be clean, neutral, minimal and technical, on a pure white or clean off-white background. Use clear section titles, readable English labels, balanced spacing, no clutter, no watermark, no logo. Apply the style only to the character and visual elements, not to the board layout or UI. All text must be clearly readable at normal viewing size. Avoid tiny or dense text.

Use this exact layout:
Top row = left: title + horizontal info block, right: COLOR PALETTE.
Center = large MAIN IDENTITY + SCALE SHEET as the biggest section.
Right column = EXPRESSION PROGRESSION + HEAD DETAIL SHEET + NEUTRAL BASELINE + POSTURE VARIATION + CLOSE-UP POSE.
Bottom = WARDROBE / ACCESSORIES DETAILS + PROP + HAND GESTURES.

Include title: CHARACTER REFERENCE SHEET.
1. TOP INFO BLOCK: Name, Alias, Role, Age, Personality, Core Theme, Speech Accent.
2. COLOR PALETTE: 6 to 8 clean swatches, no labels.
3. MAIN IDENTITY + SCALE SHEET: largest section. Same subject only. Show Front, 3/4 View, Side, Back over subtle measurement guide lines. Include small SILHOUETTE GUIDE.
4. EXPRESSION PROGRESSION: exactly 8 panels: Neutral, Curious, Worried, Surprised, Afraid, Sad, Determined, Relieved. MICRO EXPRESSIONS: exactly 5 panels: subtle eye tension, smug smirk, lip tension, micro fear, controlled breath.
5. HEAD DETAIL SHEET: 3/4 Headshot, Side Headshot, Top Angle, Low Angle, Diagonal Angle.
6. NEUTRAL BASELINE: 1 relaxed panel.
7. POSTURE VARIATION: 3 panels: relaxed, tense, confident.
8. CLOSE-UP POSE: exactly 1 cinematic chest-up close-up.
9. WARDROBE / ACCESSORIES DETAILS: exactly 4 close-up callouts.
10. PROP: exactly 1 isolated story-relevant prop with info block.
11. HAND / PAW GESTURES: relaxed hand/paw, tense hand/paw, pointing, gripping sleeve or object, subtle gesture near face.

Keep the subject fully consistent across all panels. MAIN IDENTITY + SCALE SHEET must visually dominate. No extra characters, no extra animals, no environment, no storyboard panels, no speech bubbles, no unrelated species traits, no Chinese characters on clothing, no badges, no logos, no watermark.
```

## QA Gate

Reject or mark as candidate if:

- More than one main character appears.
- Identity changes across views.
- Human character becomes animal-like unintentionally.
- Animal character becomes the wrong species.
- Clothes, fur patterns, or signature colors drift heavily.
- Text, badges, logos, watermarks, fake glyphs, or symbols pollute the character.
- Important views are cropped.
- The board is too dense for a video model to interpret.
- `HAND / PAW GESTURES` is missing or only implied.
- A scene/environment background leaks into the sheet.

If hand/paw gestures are missing, regenerate with this hard requirement:

```text
重点：底部必须清楚出现一个独立大区块，英文标题必须是 HAND / PAW GESTURES。
这个区块中必须有 5 个分格：relaxed hand/paw、tense hand/paw、pointing hand/paw、gripping sleeve or object、subtle hand/paw near face。
每格必须能看见手形/爪形、抓握或指向动作。不要省略，不要只画袖口。
```
