# Draco Skills Collection

A public collection of reusable Hermes skills for real-world workflows.

This repository packages proven skills into shareable, easy-to-browse folders so builders can understand a workflow quickly and adapt it to their own environment.

## What’s inside

### `epub2podcast/`

A local-first skill package for turning books into podcast-style media assets.

It focuses on a practical EPUB-to-podcast workflow:

- EPUB / PDF / MOBI / AZW3 → two-host Chinese podcast script
- segmented audio generation and merged podcast audio
- Smart Slide generation
- final MP4 composition
- helper script for compressing video before sharing

Inside the folder you’ll find:

- `SKILL.md` — the main skill specification
- `README.md` — a human-friendly overview
- `scripts/epub2podcast_local_run.sh`
- `scripts/epub2podcast_local_regenerate_slide.sh`
- `scripts/epub2podcast_local_compress_feishu_video.sh`

## Repository goals

This repo is intended to make Hermes skills easier to:

- discover
- reuse
- adapt
- publish
- maintain over time

Each skill directory is expected to be self-contained enough for someone to understand:

- what the skill does
- when to use it
- what commands or scripts are available
- what environment or dependencies are required

## Structure

A typical skill folder may include:

- `SKILL.md` — skill definition and workflow guidance
- `README.md` — user-facing introduction
- `scripts/` — runnable helper scripts
- `templates/` or `references/` — optional supporting assets

## Who this repo is for

This repository is useful for:

- Hermes users building repeatable workflows
- developers who want reusable automation patterns
- teams curating internal or public skill libraries
- creators packaging working AI-assisted pipelines into understandable modules

## Roadmap

Planned improvements include:

- more skill packages beyond `epub2podcast`
- more polished installation and usage guides
- more standardized folder conventions across skills
- better examples for adapting skills to new environments
