# Scene, Environment, and Settings Reference Image Prompt Template

Use this template when creating the environment reference asset for later Seedance video generation. This image locks the world, not the characters.

## Default Style

If the user does not specify another style, use:

```text
Shao Brothers-inspired cinematic realism, Chinese period studio-set texture, martial-arts comedy atmosphere, warm practical lantern lighting, readable spatial staging, rich but controlled camera mood.
```

## Template

```text
Create a single clean cinematic Scene, Environment, and Settings reference image.

PURPOSE: This image defines only the environment, lighting, spatial layout, material palette, camera mood, and key props for a later video generation. It is not a storyboard and not a character sheet.

STYLE: [default Shao Brothers-inspired cinematic realism / or user-specified style]
SETTING: [place, era, culture, genre]
SPATIAL LAYOUT: [main anchor object, entrances, exits, windows, stairs, tables, bed, counter, stage, doorway, vehicle, or other stable geometry]
KEY PROPS: [only the important props that should persist; include their initial state if relevant]
LIGHTING: [motivated light sources, time of day, contrast, haze, rim light, practical lamps]
COLOR PALETTE: [dominant colors and accent colors]
MATERIALS: [wood, stone, metal, fabric, glass, dust, rain, paper, ceramic, etc.]
CAMERA FEEL: [cinematic medium-wide establishing frame, stable perspective, readable depth, lens feel]
MOOD: [comedy, suspense, warmth, tension, absurd romance, martial-arts farce, etc.]

Generate one coherent environment image in 16:9 landscape format. Make it a single cinematic frame, not a collage, not a multi-panel board, not a blueprint, not a concept sheet with labels.

No characters, no people, no animals, no faces, no silhouettes of main characters. No text, no captions, no labels, no title, no signs with readable writing, no logos, no watermark, no arrows, no diagrams, no panel borders. Keep the main spatial anchor clearly visible and reusable for video continuity.
```

## Spatial Specificity

Do not rely on mood words. If the video depends on a table, bed, doorway, counter, stage, window, staircase, or other blocking anchor, state exactly where it is in frame.

Good:

```text
SPATIAL LAYOUT: A rectangular wooden table sits slightly left of center in the foreground; the room entrance is at rear right; a warm lantern hangs above the table; the camera sees both the entrance and the table in one stable medium-wide angle.
```

Bad:

```text
SPATIAL LAYOUT: a nice ancient room with cinematic atmosphere.
```

## QA Gate

Reject or mark as candidate if:

- Main characters appear.
- Any readable text, labels, signs, arrows, panels, or diagrams appear.
- The core spatial anchor is missing or off-frame.
- The scene contradicts the script.
- Key props are present in the wrong state and would confuse the video prompt.
- The image is a collage, storyboard, blueprint, or labeled concept sheet.
