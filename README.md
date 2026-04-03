# Draco Skills Collection

这是一个用来收集和整理 **Hermes skills** 的公开仓库。

你可以把它理解成一个“技能库”：
把已经验证过、能反复使用的工作流，整理成清晰的说明、脚本和目录，方便别人直接了解、复用和继续扩展。

## 这个仓库里有什么

目前已经收录：

### `epub2podcast/`

这是一个把电子书内容整理成播客形态的 skill，主要覆盖本地工作流，包括：

- 把 EPUB / PDF / MOBI / AZW3 转成双人中文播客脚本
- 生成分段音频，并合成完整音频
- 生成 Smart Slide
- 合成最终 MP4 视频
- 提供视频压缩脚本，方便后续分享或上传

示例页面预览：

![epub2podcast 示例封面页](./epub2podcast/assets/example-slide-cover.png)

更多截图、流程图和说明，请查看：
- [`epub2podcast/README.md`](./epub2podcast/README.md)

目录里目前包含：

- `SKILL.md`：核心技能说明
- `README.md`：面向普通读者的介绍
- `scripts/epub2podcast_local_run.sh`：主运行脚本
- `scripts/epub2podcast_local_regenerate_slide.sh`：重生成单页 slide
- `scripts/epub2podcast_local_compress_feishu_video.sh`：压缩视频文件

## 这个仓库适合谁

这个仓库适合：

- 想把常用能力整理成 skill 的 Hermes 用户
- 想复用成熟工作流的开发者
- 想沉淀团队技能库的人
- 想把 AI 工作流做成可分享模块的人

## 每个 skill 目录通常会有什么

一个比较完整的 skill 目录，通常会包含：

- `SKILL.md`：技能说明、适用场景、推荐命令
- `README.md`：更容易阅读的介绍文档
- `scripts/`：可直接运行的辅助脚本
- `templates/` 或 `references/`：可选的模板或参考资料

## 这个仓库希望解决什么问题

很多时候，一个工作流明明已经跑通了，但只存在于：

- 某次聊天记录里
- 某台机器里
- 某个零散脚本里

这样后面别人很难复用，也很难继续维护。

这个仓库希望把这些能力变成：

- 更容易查找
- 更容易理解
- 更容易迁移
- 更容易复用
- 更容易继续完善

## 后续计划

接下来会继续：

- 收录更多可复用的 skills
- 补充更完整的使用说明
- 统一目录结构，方便浏览和维护
- 增加更多真实场景示例
