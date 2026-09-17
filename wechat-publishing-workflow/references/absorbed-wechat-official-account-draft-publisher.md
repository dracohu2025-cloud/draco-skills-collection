# Archived skill: wechat-official-account-draft-publisher

Original path: `productivity/wechat-official-account-draft-publisher`

Consolidation reason: Official draft publishing is the final API stage of the WeChat workflow.

---

---
name: wechat-official-account-draft-publisher
description: 用微信公众号官方 API 把 Markdown 渲染后发布到草稿箱；包含 access_token、图片上传、封面上传、draft_add 以及真实联调踩坑。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [wechat, official-account, draft, markdown, publishing, mvp]
---

# WeChat Official Account Draft Publisher

适用于：
- 用户要把 Markdown / 文章内容发布到**微信公众号草稿箱**
- 希望用**官方 API**，而不是浏览器自动化
- 需要把方案做成可独立运行的 standalone 工具

## 核心流程

按这个顺序做：

1. 准备公众号凭证
   - `AppID`
   - `AppSecret`
   - 公众号名称 / 类型（可选，但建议记录）
2. 确认调用服务器公网 IP
3. 要求用户把该 IP 加入公众号后台 **开发者 IP 白名单**
4. 先单独验证 `access_token`
5. 再单独验证素材上传
   - 正文图片：`cgi-bin/media/uploadimg`
   - 封面图：`cgi-bin/material/add_material?type=image`
6. 最后再调用草稿箱接口
   - `cgi-bin/draft/add`

不要一上来就直接调 `draft/add`。先把 token 和两类图片上传拆开验证，排错会快很多。

## 推荐项目结构

最小可用 Python 项目可拆成：

- `loader.py`：读 Markdown + frontmatter
- `renderer.py`：渲染微信公众号友好 HTML
- `validation.py`：本地发布前校验
- `wechat_api.py`：微信接口客户端
- `draft.py`：组装 `draft/add` payload
- `pipeline.py`：串联完整发布流程
- `cli.py`：CLI 入口
- `tests/`：TDD 回归测试

## 接口分工

## 实战补充：当现场没有 AppID / AppSecret，但本机仍有有效 access_token 缓存

真实联调里遇到过一种情况：
- 当前 shell / `.env` 里拿不到 `WECHAT_APP_ID`、`WECHAT_APP_SECRET`
- 但机器上之前已经成功联调过，`~/.cache/wechat-draft-publisher/access_token.json` 里仍有**未过期 token**

这时不要立刻判定“完全无法继续”。

只要目标动作是：
- 上传正文图
- 上传封面图
- 调 `draft/add`

那么**只要 token 仍有效，就仍可继续完成一次真实发布**。因为这些接口本身只需要 `access_token`。

可行做法：
1. 先读取 token cache，确认 token 未过期
2. 构造 `WechatClient` 时可先放占位 `appid/appsecret`
3. 不调用 `get_access_token()` 刷新 token
4. 直接把缓存 token 传给：
   - `upload_content_image(..., access_token)`
   - `upload_cover_image(..., access_token)`
   - `add_draft(payload, access_token)`

适用边界：
- **只适合已存在有效缓存 token 的续跑 / 救场场景**
- **不能替代正式凭证配置**
- 一旦 token 过期，仍必须回到 `AppID + AppSecret` 正常取 token

经验结论：
- token 刷新依赖 `AppID/AppSecret`
- 但 token 使用阶段不依赖再次提供凭证
- 所以遇到“凭证暂时缺失但缓存 token 还活着”的场景，可以先把发布任务完成，再补回正式配置

### 1. 获取 token

接口：
- `GET https://api.weixin.qq.com/cgi-bin/token`

参数：
- `grant_type=client_credential`
- `appid`
- `secret`

建议：
- 做本地 token 缓存
- 加 300 秒左右的过期提前量（skew）

## 2. 上传正文图片

接口：
- `POST https://api.weixin.qq.com/cgi-bin/media/uploadimg`

用途：
- 获取可放进文章 HTML `img src` 的微信 URL

关键点：
- HTML 正文里的图片，不能保留本地路径 / 外部原图路径
- 要先上传到微信，再把返回 URL 回填进 HTML

## 3. 上传封面图

接口：
- `POST https://api.weixin.qq.com/cgi-bin/material/add_material?type=image`

用途：
- 获取 `thumb_media_id`

关键点：
- `draft/add` 用的是 `thumb_media_id`
- 正文图和封面图不是同一个接口

## 4. 创建草稿

接口：
- `POST https://api.weixin.qq.com/cgi-bin/draft/add`

payload 核心字段：
- `title`
- `author`
- `digest`
- `content`
- `thumb_media_id`
- `content_source_url`（可选）

## 真实联调踩坑

### 1. 必须先配 IP 白名单

如果服务器公网 IP 没加入白名单，常见会在 token 或后续接口阶段失败。

所以第一步先查公网 IP，再让用户去公众号后台加白名单。

### 2. 过于极简的测试 PNG 可能被微信拒收

真实联调中，微信返回：
- `invalid image format`

经验：
- 不要用过度极简、奇怪编码方式的伪 PNG 测试图
- 尽量使用正常生成的标准 PNG / JPG
- 联调时最好用尺寸稍正常的图片，比如 96x96、128x128 之类

### 3. `author` 有长度限制

真实联调中，`draft/add` 返回：
- `author size out of limit`

本次验证里，保守做法是：
- 本地校验 `author` 最多 8 个字符

如果用户 author 很长，先在本地拦截，不要等微信报错。

### 4. `digest` 也应在本地限长

保守做法：
- 本地校验 `digest` 最多 120 个字符

### 5. 没有 `thumb_media_id` 时，必须保证 `cover_image` 本地存在

不要等上传封面时报错。
先在本地检查封面文件是否存在。

## 推荐本地校验

在真正发请求前，至少校验：

- `title` 非空
- `title` 不过长（可先保守限制）
- `author` 最多 8 个字符
- `digest` 最多 120 个字符
- `thumb_media_id` 非空，或 `cover_image` 文件存在

## HTML 图片替换策略

渲染 HTML 后，扫描 `<img src="...">`：

- 如果已是 `http://` / `https://`，可按策略决定是否保留
- 如果是相对路径 / 本地路径：
  1. 解析到文章目录下真实文件路径
  2. 调 `uploadimg`
  3. 用微信返回的 URL 替换原 `src`

## TDD 建议

至少写这些测试：

1. token 缓存命中
2. token 拉取后写入缓存
3. HTML 图片替换
4. 封面上传调用参数正确
5. `draft/add` payload 正确
6. real publish pipeline：
   - 上传正文图
   - 上传封面
   - 创建草稿
7. 本地校验：
   - author 超长
   - digest 超长
   - title 为空
   - 封面不存在

## CLI 最小形态

不要只做一个 `publish`。更实用的正式 CLI 至少支持三条命令：

### validate

先做本地校验，不发请求：

```bash
python -m wechat_draft_publisher.cli validate \
  --input examples/sample.md \
  --thumb-media-id thumb123
```

### render-preview

先生成本地 HTML 预览，让用户确认“当前可发布效果”：

```bash
python -m wechat_draft_publisher.cli render-preview \
  --input examples/sample.md \
  --output examples/sample.preview.html
```

### dry-run publish
```bash
python -m wechat_draft_publisher.cli publish \
  --input examples/sample.md \
  --thumb-media-id thumb123 \
  --dry-run
```

### 真实发布
```bash
export WECHAT_APP_ID="你的 AppID"
export WECHAT_APP_SECRET="你的 AppSecret"

python -m wechat_draft_publisher.cli publish \
  --input examples/sample.md
```

## 工程化经验

如果是独立项目：
- 及时补 `.env.example`
- 及时补 `.gitignore`
- 不要把 `__pycache__`、`*.egg-info` 提交进 git
- 初始化 git 后如误提交生成物，立刻 `git rm --cached` 后 amend 清理

## 完成标准

满足以下条件，可视为“真实可用 MVP”：

- `access_token` 获取成功
- 正文图上传成功
- 封面图上传成功
- `draft/add` 创建成功
- 本地测试全绿
- CLI 同时支持 dry-run 与真实发布

## 交付时应告诉用户

完成后明确告知：
- 已成功创建测试草稿
- 给出草稿标题 / `draft_media_id`
- 提醒用户去公众号后台草稿箱验收
- 说明真实踩到的接口约束（尤其是 author 长度与图片格式）

如果用户关心“效果长什么样”，不要只说 API 成功。

至少额外交付一项：
- 本地 HTML 预览文件
- 预览截图
- 飞书云盘里的可点开预览图链接

实践上，先 `render-preview`，再用本机浏览器/截图工具导出 PNG，必要时上传飞书，用户确认效果后再继续精修样式。
