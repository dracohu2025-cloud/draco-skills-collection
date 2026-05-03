# Director Module

Director Module 是本 skill 的大脑。它先把 Base 行/脚本转成可执行导演方案，再让 CRS、SES、Top-Down Blocking Map、keyframes、Seedance Prompt、payload builder 进入执行层。

## Inputs

Director 至少读取：

```text
- Base row fields: 标题、剧情/脚本、角色说明、场景说明、对白、时长、比例、风格、已有附件、已有 URL、计划参数
- Existing assets: 官方 asset://、已有 Character Reference Sheet、Scene, Environment, and Settings reference image、Top-Down Blocking Map、keyframes
- User constraints: 模型、分辨率、风格、服装、站位、禁止项、是否允许烧钱
```

缺字段时先从已给脚本推断；推断会影响生成成本或资产数量时，先标为 `needs_user_review`，不要擅自提交 billable 任务。

## Outputs

Director 必须先产出结构化方案，再写 Prompt。

```yaml
director_plan:
  summary: "这一条视频的导演意图，一句话"
  duration_seconds: 12
  ratio: "16:9"
  resolution: "480p"
  model_default: "doubao-seedance-2-0-fast-260128"
  style_lock: "邵氏电影质感 / 写实古风棚拍 / 武侠喜剧质感"
  main_characters:
    - id: "character_a"
      display_name: "角色A"
      role_in_story: "推动动作/笑点/对白的主要角色"
      asset_strategy: "official_asset | existing_crs | generate_crs | text_only"
      crs_needed: true
      crs_reason: "身份稳定性会影响成片"
      crs_prompt_brief:
        identity: "外形、年龄/物种、体态、脸部核心特征"
        wardrobe: "服装/配件硬约束"
        expression_range: "需要的表情"
        action_range: "需要支持的动作"
        forbidden_drift: ["身份漂移", "服装漂移", "额外角色"]
  secondary_characters:
    - id: "background_1"
      reason_no_crs: "背景/路人/低身份连续性需求"
  environment:
    ses_needed: true
    ses_strategy: "existing_ses | generate_ses | text_only"
    location: "场景类型"
    spatial_anchors: ["左侧门", "中央桌", "右侧柜台"]
    props: ["关键道具A", "关键道具B"]
    lighting_and_texture: "灯光、材质、棚拍质感"
    forbidden_environment_drift: ["现代物件", "文字标识", "额外人物"]
  blocking:
    top_down_blocking_map_needed: false
    keyframes_needed: false
    reason: "动作简单/站位复杂/接触关系复杂等"
  shot_breakdown:
    - time: "0-2秒"
      shot_function: "建立空间与角色关系"
      framing: "中广角/中景/近景"
      camera_motion: "轻推/横移/固定/切换"
      character_actions: "角色动作"
      spatial_continuity: "左右/前后/道具位置"
      dialogue_or_audio: "对白/音效"
      seedance_prompt_line: "最终写入细导演稿的一段"
  risks:
    - "官方 asset 可能强锁原服装"
  needs_user_review:
    - "是否接受 text_only 角色而不生成 CRS"
```

## Character Decision Rules

### Main character

满足任一强条件，通常算主要角色：

- 推动剧情、笑点或冲突。
- 有台词、显著表情、连续动作或镜头特写。
- 出现超过一个镜头段，或身份连续性影响可看性。
- 与核心道具/另一个角色发生互动。
- 用户明确点名要锁定。

### CRS needed

需要独立 Character Reference Sheet 的情况：

- 角色外观必须稳定，且不是官方 `asset://` 已锁定。
- 角色是动物、怪物、非通用人物，文字描述难以稳定。
- 角色服装/配件/脸型/花纹/体态对剧情重要。
- 后续多条视频会复用。

不建议生成 CRS 的情况：

- 官方 `asset://` 已作为主要身份参考，且用户不希望混入自生成 CRS。
- 路人、背景人、只出现一瞬的手/影子。
- 角色只是台词中被提到，画面不出现。

## Environment Decision Rules

需要 Scene, Environment, and Settings reference image 的情况：

- 场景空间关系影响动作或笑点。
- 风格、时代、材质、灯光容易漂移。
- 道具位置、入口、床/桌/门/柜台等锚点必须稳定。
- 同一场景后续会复用。

可只用文本的情况：

- 背景极简单，几乎不参与动作。
- 用户明确只要快速草稿。

## Blocking / Keyframe Rules

需要 Top-Down Blocking Map：

- 左右站位、追逐、接触、遮挡、走位是核心。
- 有 3 个以上活动主体或多个空间锚点。
- 纯文字容易让 Seedance 交换角色位置。

需要 keyframes：

- 首尾画面必须稳定。
- 关键姿态、跌倒、拿放道具、拥抱、推门等动作难以靠文本锁定。

默认不滥用：参考图越多，误继承风险越高。每张图都必须在 Prompt 中说明用途。

## Shot Breakdown Rules

12 秒默认拆 4-6 组镜头，按剧情复杂度调整：

```text
0-2秒：建立镜头，锁空间和角色初始位置。
2-4秒：动作启动，交代意图。
4-7秒：冲突/误会/包袱推进。
7-10秒：反应/反转/物理动作高潮。
10-12秒：笑点落地，保留可读停顿。
```

每组镜头必须同时包含：

- 景别与构图。
- 运镜或切换方式。
- 角色位置和动作。
- 表情变化。
- 道具状态。
- 对白/音效。
- 禁止漂移项。

只写剧情等于不合格。

## Director Gate

Director 输出进入执行层前必须通过：

- [ ] 主要角色数量合理，没有把背景角色过度资产化。
- [ ] 每个主要角色都有明确 `asset_strategy`。
- [ ] Character Reference Sheet / Scene, Environment, and Settings reference image / Top-Down Blocking Map / keyframes 的生成理由明确。
- [ ] shot_breakdown 覆盖完整片长，无时间重叠或空洞。
- [ ] 每段镜头都有镜头语言，不只是动作描述。
- [ ] Prompt 中不写内部缩写；写完整英文名或中文名。
- [ ] 未经用户确认，不提交 Seedance billable POST。
