# Release Notes

## wechat-article-camofox v1.1.1

`wechat-article-camofox` is now available as a more complete **standalone local-first WeChat article extraction tool** inside this repository.

### What this release means

This version is the first one in this repository that gives public users a smoother out-of-the-box path:

- clone the repository
- enter `wechat-article-camofox/`
- verify the machine with `scripts/smoke-test.sh`
- run `python3 scripts/run.py fetch ...`
- let the tool automatically bootstrap `camofox-browser` when missing

### Highlights

- automatic CamouFox / `camofox-browser` bootstrap on first run
- staged progress output during install and startup
- unified public CLI entry (`scripts/run.py`)
- standalone README with workflow preview and batch examples
- Feishu publish workflow kept in the standalone directory
- smoke test script for environment validation

### Verified in this release cycle

This release was validated with a real public WeChat article URL and a real Feishu publish flow:

- fetch to JSON succeeded
- stderr progress output was verified
- publish-to-Feishu succeeded
- the generated doc was read back for validation
- parser regression tests all passed locally

### Recommended positioning

This version should be described as:

> a practical standalone early release for WeChat article extraction and Feishu delivery

rather than a fully mature universal web extraction product.

### Current strongest path

- public WeChat article URL
- extraction to Markdown / JSON
- native Feishu doc publishing
- automatic first-run browser bootstrap

### Known boundaries

- still requires host-level `git`, `node`, and `npm`
- still relies on the `camofox-browser` ecosystem rather than embedding a browser runtime directly in this directory
- still may need more cleanup rules for edge-case WeChat layouts and exotic card components

### Suggested next release goals

- remove more公众号页头残留（如账号展示文案）
- add optional fallback backend when `camofox-browser` bootstrap fails
- ship a small set of example inputs / expected outputs for faster public validation
- add richer release assets or screenshots from real article conversions
