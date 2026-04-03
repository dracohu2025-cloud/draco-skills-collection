# epub2podcast v0.1.0

`epub2podcast` 现已完成第一轮 standalone 化，可以作为一个**可独立运行的本地项目**使用。

## 这次发布意味着什么

从这个版本开始，用户不再需要额外依赖外部 `epub2podcast-local` 项目目录。

只要：

1. 下载当前 `epub2podcast/` 目录
2. 安装依赖
3. 配置 `.env`
4. 运行命令

就可以完成一条本地端到端链路：

- EPUB → 双人中文播客脚本
- 分段音频与完整播客音频
- Smart Slide HTML / PNG
- 最终 MP4 视频

## 本次版本亮点

- 独立 `package.json` / `tsconfig.json` / `.env.example`
- 独立 `src/` 源码目录
- 独立 CLI 入口：
  - `epub2podcast-run`
  - `epub2podcast-regenerate-slide`
  - `epub2podcast-compress-video`
- 增加 `smoke-test` 环境检查
- README 已补齐示例图、流程图、快速开始与排查说明
- 已完成一次真实 EPUB 端到端运行验证

## 当前最稳的支持范围

- **EPUB 输入**
- 中文播客脚本生成
- Volcengine TTS 路径
- Smart Slide 生成
- MP4 合成

## 当前版本定位

这是一个：

> **v0.1.0 early standalone release**

它已经能独立运行，但还不是最终 fully polished 稳定版本。

## 下一步计划

- 进一步清理历史依赖
- 提升 CLI 一致性与首跑体验
- 加强 PDF / MOBI / AZW3 的 standalone 支持
- 增强诊断与错误提示
