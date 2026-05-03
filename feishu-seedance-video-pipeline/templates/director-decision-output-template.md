# Director Decision Output Template

Use this before writing CRS, SES, or Seedance prompt. Fill it from the Feishu Base row and user constraints.

```yaml
director_plan:
  row_context:
    base_row: "<row number or record label>"
    story_goal: "<一句话剧情/笑点>"
    required_duration_seconds: 12
    aspect_ratio: "16:9"
    generate_audio: true
    user_locked_constraints:
      - "<服装/站位/风格/角色硬约束>"

  style:
    primary_style: "邵氏电影质感 / 写实古风棚拍 / 武侠喜剧质感"
    lighting: "<灯光>"
    texture: "<材质/时代/棚拍感>"
    forbidden_style_drift:
      - "现代化"
      - "卡通化，除非用户要求"
      - "字幕、文字、logo、水印"

  main_characters:
    - id: "character_a"
      display_name: "<角色名>"
      story_function: "<主角/推动冲突/笑点承接/台词角色>"
      screen_presence: "<出现时间和镜头段>"
      asset_strategy: "official_asset | existing_crs | generate_crs | text_only"
      asset_source: "<asset://... | https://... | Base附件 | none>"
      crs_needed: true
      crs_reason: "<为什么需要/不需要CRS>"
      crs_prompt_requirements:
        identity_lock: "<脸型/体态/物种/年龄/发型/花纹>"
        wardrobe_lock: "<服装硬约束>"
        expression_range: ["<表情1>", "<表情2>"]
        pose_or_action_range: ["<动作1>", "<动作2>"]
        prop_relationship: "<与道具关系>"
        forbidden_drift: ["<禁止漂移点>"]

  secondary_characters:
    - id: "secondary_1"
      display_name: "<角色名或类型>"
      reason_no_crs: "<背景/只出现一次/身份不重要>"
      text_prompt_lock: "<如仍需在视频Prompt里锁定的文字约束>"

  environment:
    location: "<场景>"
    ses_needed: true
    ses_strategy: "existing_ses | generate_ses | text_only"
    ses_reason: "<为什么需要/不需要SES>"
    spatial_layout:
      left: "<左侧锚点>"
      center: "<中央锚点>"
      right: "<右侧锚点>"
      foreground: "<前景锚点>"
      background: "<后景锚点>"
    props:
      - name: "<道具名>"
        initial_state: "<初始状态>"
        state_changes: "<变化节点>"
    forbidden_environment_drift: ["<禁止出现的环境元素>"]

  blocking_and_keyframes:
    top_down_blocking_map_needed: false
    keyframes_needed: false
    reason: "<站位/接触关系/首尾画面需求>"
    reference_order_for_seedance:
      - "content[1]: <用途说明>"
      - "content[2]: <用途说明>"

  shot_breakdown:
    - time_range: "0-2秒"
      shot_function: "建立空间、角色关系"
      framing: "<景别与构图>"
      camera_motion: "<运镜/切换>"
      character_actions: "<动作>"
      facial_expression: "<表情>"
      spatial_continuity: "<站位/空间锚点>"
      prop_continuity: "<道具状态>"
      dialogue_or_audio: "<对白/音效>"
      director_prompt_line: "<最终可复制进Seedance细导演稿的一段>"
    - time_range: "2-4秒"
      shot_function: "动作启动"
      framing: "<景别与构图>"
      camera_motion: "<运镜/切换>"
      character_actions: "<动作>"
      facial_expression: "<表情>"
      spatial_continuity: "<站位/空间锚点>"
      prop_continuity: "<道具状态>"
      dialogue_or_audio: "<对白/音效>"
      director_prompt_line: "<最终可复制进Seedance细导演稿的一段>"
    - time_range: "4-7秒"
      shot_function: "冲突/包袱推进"
      framing: "<景别与构图>"
      camera_motion: "<运镜/切换>"
      character_actions: "<动作>"
      facial_expression: "<表情>"
      spatial_continuity: "<站位/空间锚点>"
      prop_continuity: "<道具状态>"
      dialogue_or_audio: "<对白/音效>"
      director_prompt_line: "<最终可复制进Seedance细导演稿的一段>"
    - time_range: "7-10秒"
      shot_function: "反应/反转/动作高潮"
      framing: "<景别与构图>"
      camera_motion: "<运镜/切换>"
      character_actions: "<动作>"
      facial_expression: "<表情>"
      spatial_continuity: "<站位/空间锚点>"
      prop_continuity: "<道具状态>"
      dialogue_or_audio: "<对白/音效>"
      director_prompt_line: "<最终可复制进Seedance细导演稿的一段>"
    - time_range: "10-12秒"
      shot_function: "笑点落地，留停顿"
      framing: "<景别与构图>"
      camera_motion: "<运镜/切换>"
      character_actions: "<动作>"
      facial_expression: "<表情>"
      spatial_continuity: "<站位/空间锚点>"
      prop_continuity: "<道具状态>"
      dialogue_or_audio: "<对白/音效>"
      director_prompt_line: "<最终可复制进Seedance细导演稿的一段>"

  execution_plan:
    assets_to_generate:
      - "<Character Reference Sheet / Scene, Environment, and Settings reference image / Top-Down Blocking Map / keyframe>"
    assets_to_reuse:
      - "<已有URL或asset说明>"
    base_fields_to_backfill_before_submit:
      - "<字段名>"
    needs_user_review:
      - "<需要用户确认的问题；无则 []>"

  risk_notes:
    - "官方 asset 可能强锁原服装；换装不保证100%执行。"
```
