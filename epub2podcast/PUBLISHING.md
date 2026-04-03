# Publishing Guide

这份文档用于记录 `epub2podcast` 对外发布时的建议步骤。

## 当前发布定位

- 项目：`epub2podcast`
- 当前版本：`v0.1.0`
- 阶段：**early standalone release**

## 发布前检查清单

### 代码与运行

- [ ] `npm install` 可正常完成
- [ ] `npm run build` 通过
- [ ] `npm run smoke-test` 通过
- [ ] `node dist/cli/run.js --help` 正常输出
- [ ] `node dist/cli/regenerate-slide.js --help` 正常输出
- [ ] `node dist/cli/compress-video.js --help` 正常输出

### 文档

- [ ] `README.md` 已更新为当前版本说明
- [ ] `CHANGELOG.md` 已记录本次版本变化
- [ ] `RELEASE.md` 已更新
- [ ] `LICENSE` 已存在
- [ ] 示例图片与流程图可正常显示

### 发布表述

- [ ] 明确说明当前最稳输入类型是 EPUB
- [ ] 不夸大 PDF / MOBI / AZW3 的稳定性
- [ ] 明确说明这是 early standalone release，而不是 fully polished stable product

## 推荐发布步骤

1. 确认 README、CHANGELOG、RELEASE 文案已更新
2. 完成一轮 build + smoke test
3. 如有必要，再做一次真实 EPUB 端到端验证
4. 提交代码并 push
5. 在 GitHub 上创建 release
6. 使用 `RELEASE.md` / GitHub Release 文案作为发布说明基础

## 当前建议

在 `v0.1.0` 阶段，更适合强调：

- 已可独立运行
- 已完成真实端到端验证
- 当前重点支持 EPUB
- 后续还会继续打磨依赖、CLI 和多格式支持
