# Release Notes

## epub2podcast v0.1.0

`epub2podcast` is now available as a **standalone local-first package** inside this repository.

### What this release means

This is the first version where users can:

- download the `epub2podcast/` directory
- install dependencies locally
- configure `.env`
- build and run the project directly
- generate a full local pipeline result from EPUB to:
  - podcast script
  - audio
  - Smart Slides
  - MP4 video

### Highlights

- standalone package structure
- independent CLI commands
- smoke test support
- public README with screenshots and setup instructions
- real end-to-end validation completed

### Recommended positioning

This version should be described as:

> an independently runnable **early release / v0.1 standalone build**

rather than a fully polished stable product.

### Current strongest path

- EPUB input
- Chinese podcast generation
- Smart Slide generation
- MP4 composition

### Verified sample in this release cycle

The standalone build has now been verified with a real EPUB sample:

- `太平天国革命运动史`
- parsed title / author correctly
- handled namespace-prefixed OPF metadata / manifest / spine correctly
- completed real end-to-end generation for:
  - script
  - audio
  - Smart Slides
  - MP4 video

### Fixes validated by this sample

This release cycle confirmed a real compatibility fix for EPUB parsing:

- namespace-safe OPF parsing for metadata extraction
- namespace-safe manifest extraction
- namespace-safe spine extraction

### Suggested next release goals

- further dependency cleanup
- better first-run diagnostics
- more polished CLI UX
- stronger standalone support for PDF / MOBI / AZW3
