# draco-skills-collection

一个用于沉淀与分享 **Hermes skills** 的公开仓库。

这个仓库的目标是：把已经验证过、可复用的能力整理成清晰、可迁移、适合公开协作的 skill 包，而不是只保留在单次对话或某一台机器里。

## 当前收录

### `epub2podcast/`

脱敏后的 **local-only** `epub2podcast` skill，聚焦本地链路：

- EPUB / PDF / MOBI / AZW3 → 双人中文播客脚本
- 音频分段与合并
- Smart Slide 生成
- 最终 MP4 合成
- 飞书上传前的视频压缩辅助脚本

该目录当前包含：

- `SKILL.md`：skill 主说明
- `README.md`：对外说明与使用边界
- `scripts/epub2podcast_local_run.sh`
- `scripts/epub2podcast_local_regenerate_slide.sh`
- `scripts/epub2podcast_local_compress_feishu_video.sh`

## 仓库原则

### 1. 只收录可复用内容

优先同步：
- 稳定的 skill 文档
- 可复用脚本
- 通用模板
- 实战中验证过的工作流

不优先同步：
- 一次性实验产物
- 与某次会话强绑定的临时文件
- 只适用于单一环境且无法抽象的实现细节

### 2. 默认做脱敏处理

这是一个公开仓库，因此同步内容时默认：

- **不提交 API keys / PAT / tokens / secrets**
- **不提交私有账号信息或内部凭证**
- **不提交仅对某一台机器有效的敏感配置**
- 尽量把本机私有绝对路径改造成环境变量或占位配置

### 3. 优先保留可迁移性

如果某个 skill 原本依赖特定机器路径、个人云资源或私有服务：

- 会优先抽象成环境变量
- 会补充使用前提说明
- 会在 README / SKILL 中明确公开版与私有版的边界

## 如何使用

不同目录通常至少会包含以下两类文件：

- `SKILL.md`：适合被 Hermes 直接加载/参考的技能说明
- `README.md`：适合人在 GitHub 中快速理解的目录介绍

对于脚本类 skill，通常还会附带 `scripts/` 目录。

以 `epub2podcast/` 为例，使用前你需要：

1. 先准备可运行的本地 `epub2podcast-local` 项目代码
2. 按目录说明设置必要环境变量
3. 再执行对应脚本

## 安全说明

本仓库**有意排除**以下内容：

- 个人 API 密钥
- GitHub PAT
- 第三方平台 secret
- 私有云服务凭证
- 用户专属敏感配置

如果你发现某个文件中可能残留敏感信息，应该在继续同步前先完成脱敏。

## 后续计划

- 持续补充更多可公开分享的 Hermes skills
- 为每个 skill 增加更完整的安装说明与示例
- 逐步统一目录结构，便于检索、复用与发布
