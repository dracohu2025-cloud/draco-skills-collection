# epub2podcast

这是一个**公开可分享的、脱敏后的 local 版 epub2podcast skill**。

## 包含内容

- `SKILL.md`：技能说明与推荐命令
- `scripts/epub2podcast_local_run.sh`：本地主运行入口
- `scripts/epub2podcast_local_regenerate_slide.sh`：只重生单页 slide
- `scripts/epub2podcast_local_compress_feishu_video.sh`：压缩 MP4 以适配飞书上传

## 已做的脱敏与整理

- **未同步 remote 版 skill**
- **未同步任何 API key / token / secret**
- **未同步用户私有账号信息**
- 将脚本中的机器私有绝对路径改成了可配置环境变量 `EPUB2PODCAST_PROJECT_ROOT`

## 使用前需要自行准备

你需要在本机已有可运行的 `epub2podcast-local` 项目代码，并设置：

```bash
export EPUB2PODCAST_PROJECT_ROOT=/path/to/your/epub2podcast-local/frontend/server
```

然后再执行 `scripts/` 下的脚本。

## 设计边界

这个目录只收录 **local-only** 路径：
- 本地生成中文双人播客脚本
- 本地生成音频
- 本地生成 Smart Slide
- 本地合成最终 MP4

不包含：
- remote service 调用逻辑
- 用户 CVM 专属配置
- 任何私有密钥或凭证
