# Changelog

All notable changes to `epub2podcast` will be documented in this file.

## [0.1.0] - 2026-04-03

### Added
- First standalone local package structure under `epub2podcast/`
- Independent `package.json`, `tsconfig.json`, `.env.example`, and `src/`
- Standalone CLI entry points:
  - `epub2podcast-run`
  - `epub2podcast-regenerate-slide`
  - `epub2podcast-compress-video`
- Shell helper scripts for run / regenerate / compress workflows
- Smoke test script for runtime and build checks
- Public-facing README with screenshots, workflow diagram, setup guide, and troubleshooting
- MIT license file

### Changed
- `epub2podcast` no longer depends on an external `EPUB2PODCAST_PROJECT_ROOT`
- Root repository README now presents `epub2podcast` as a standalone-capable project
- CLI commands now provide `--help` output
- Standalone package was validated with a real end-to-end local run using EPUB input

### Removed
- Unused standalone provider modules that were no longer required by the local-only runtime path

### Fixed
- Fixed EPUB parsing for namespace-prefixed OPF files by making metadata / manifest / spine extraction namespace-safe
- Verified the standalone pipeline end-to-end with `太平天国革命运动史` EPUB, including real content extraction, script generation, audio, slides, and final MP4 output

### Notes
- Current most stable input type is **EPUB**
- PDF / MOBI / AZW3 support may require further standalone-specific hardening before being treated as equally stable
