# Changelog

All notable changes to `wechat-article-camofox` will be documented in this file.

## [1.1.1] - 2026-04-08

### Added
- Standalone project directory under `draco-skills-collection/wechat-article-camofox/`
- Public-facing `README.md` with workflow preview, setup guide, quick start, batch usage, and FAQ
- Unified CLI entry: `python3 scripts/run.py {fetch,publish-feishu}`
- `scripts/smoke-test.sh` for first-run environment verification
- `CHANGELOG.md` and `RELEASE.md` for release-oriented delivery
- SVG workflow preview asset for GitHub rendering

### Changed
- Upgraded bootstrap flow to **automatic install mode**: first run now checks `camofox-browser`, clones it when missing, runs `npm install`, and starts the local service automatically
- Fetch workflow now prints staged progress messages to stderr during health check, install, startup, and readiness wait
- Publish-to-Feishu workflow now preserves fetch progress output instead of swallowing stderr
- Root repository `README.md` now includes `wechat-article-camofox` as a first-class standalone tool
- Public docs now recommend `scripts/run.py` as the main entry point instead of Hermes-local wrapper commands

### Fixed
- Fixed nested snapshot list parsing that previously produced extra bullet glyphs and broken inline code lines
- Fixed paragraph / blockquote subtree reconstruction so structured text is emitted as one logical block
- Fixed Markdown serialization so list sections no longer swallow following正文段落 into the previous list item
- Verified real fetch and Feishu publish against a live WeChat article after the parser fixes

### Notes
- This release still depends on the host machine having `git`, `node`, and `npm`
- `camofox-browser` no longer needs to be manually preinstalled
- Complex WeChat rich-text layouts may still require more rules for pixel-perfect reconstruction
