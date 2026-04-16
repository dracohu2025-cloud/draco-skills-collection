# Seedance 2.0 视频生成（本地工作流）

用火山引擎 Ark 的 Seedance 2.0，在本地完成：

- Prompt 结构化
- 成本预估
- 任务提交与轮询
- 成片下载

默认策略：**480p + 短时长先验证**，避免无效烧钱。

![Seedance 2.0 系统框架预览](./assets/seedance-architecture-preview.png)

---

## 适合谁

- 你已经有 Seedance API Key
- 你希望先 `preview` 再 `submit/run`
- 你想把单次试片升级成可重复脚本流程

---

## 目录结构

- `scripts/seedance_video.py`：底层任务客户端（check/preview/submit/get/run/cancel）
- `scripts/seedance_prompt_generator.py`：把自然语言需求转成更稳的结构化 Prompt
- `scripts/seedance_workflow.py`：统一入口（prompt 生成 + 提交/轮询）
- `scripts/seedance_cost_estimator.py`：成本估算
- `scripts/test_*.py`：回归测试
- `SKILL.md`：Hermes skill 元数据与完整说明

---

## Profile 速查表（Prompt Generator / Workflow）

用于 `--profile strict|stable|cinematic`：

| Profile | 适用场景 | 行为特点 |
|---|---|---|
| `strict` | 商业交付、剧情必须完整复现 | 约束最强、非 timeline 默认单主镜头、最稳但更保守 |
| `stable` | 日常生产（默认） | 稳定性与表现力平衡 |
| `cinematic` | 风格探索、氛围片 | 默认约束更轻，非 timeline 可保留最多两个镜头指令 |

示例：

```bash
python3 scripts/seedance_workflow.py \
  --mode preview \
  --brief "9:16 动作短片，女孩举枪，子弹飞行，结尾收枪离场" \
  --profile stable \
  --json
```

---

## 快速开始

### 1) 先检查环境

```bash
python3 scripts/seedance_video.py check --api-key "$VOLCENGINE_API_KEY"
```

### 2) 零成本预览 payload

```bash
python3 scripts/seedance_video.py preview \
  --prompt "9:16 动作短片，女孩举枪，子弹飞行，结尾收枪离场" \
  --first-frame-url "https://example.com/first-frame.jpg" \
  --resolution 480p \
  --ratio 9:16 \
  --duration 5
```

### 3) 正式生成并下载

```bash
python3 -u scripts/seedance_video.py run \
  --api-key "$VOLCENGINE_API_KEY" \
  --prompt "9:16 动作短片，女孩举枪，子弹飞行，结尾收枪离场" \
  --first-frame-url "https://example.com/first-frame.jpg" \
  --resolution 480p \
  --ratio 9:16 \
  --duration 5 \
  --download ./outputs/demo.mp4
```

---

## 推荐工作方式

1. 先用 `seedance_prompt_generator.py` 生成结构化 prompt
2. 用 `seedance_video.py preview` 校验 payload
3. 确认后再 `run`
4. 成功后立即下载（`video_url` 有时效）

---

## 常见坑

- `first_frame/last_frame` 不能和 `reference_image/reference_video/reference_audio` 混用
- 参考资源 URL 必须公网可访问
- 高分辨率和长时长成本上升很快
- 任务轮询看不到日志时，用 `-u` 无缓冲模式

---

## 安全建议

- 不要把 API Key 写进脚本
- 用环境变量传入：`VOLCENGINE_API_KEY`
- 提交到 GitHub 前先跑凭据扫描
