# Seedance Row-24 / Row-28 Director Prompt Template

Use this template for detailed Chinese Seedance short-drama prompts. A prompt is not acceptable if the timeline only describes character actions. Each time segment must bind camera language to action, spatial continuity, props, and audio.

## Required Structure

1. Overall hard constraints
   - duration / ratio / resolution / `generate_audio`
   - model expectation: Seedance 2.0 Fast unless user specifies otherwise
   - visual style and genre
   - exact visible cast count
   - outfit / identity / species locks

2. Reference image usage by `content[]` order
   - reference item 1: official `asset://...` human asset or Character Reference Sheet usage
   - reference items 2..N: Character Reference Sheet / Scene, Environment, and Settings reference image / Top-Down Blocking Map / keyframe usage
   - explicitly say not to reproduce labels, panels, charts, text, arrows, grid lines, or sheet layout
   - do not write `@Image1`

3. Spatial hard constraints
   - fixed screen sides / entrances / exits / final positions
   - stable anchor object such as table, bed, counter, doorway, stage
   - no cross-axis cuts or position swaps

4. Prop or object-state hard constraints
   - initial state
   - state changes by story beat
   - forbidden inherited props from the scene reference image

5. Timeline with embedded camera language

Each block must follow this pattern:

```text
[0-2秒] 镜头构图与运镜：...。角色动作：...。空间锚点/道具连续性：...。对白/音效：...。
```

Every timeline block must include at least:

- shot size or composition: 建立镜头 / 中广角 / 中近景 / 近景 / 反应近景 / 稳定广角
- camera movement or cut: 轻推近 / 切到 / 切回 / 摇移 / 拉回 / 低机位 / 稳定停留
- action and expression
- spatial continuity: left/right, foreground/background, anchor object, prop state
- dialogue or sound when relevant

Bad timeline block:

```text
[3-4秒] 角色A放下书，问：“什么区别？”
```

Good timeline block:

```text
[3-4秒] 切到角色A反应近景，暖色灯光勾勒脸部，书从前景轻轻放低。角色A仍在床右侧，微笑疑惑地看向左侧角色B，问：“什么区别？”背景床位和角色B轮廓保持可辨。
```

6. Camera guidance
   - rich camera only when it protects spatial clarity
   - dialogue uses gentle push-ins and medium close-ups
   - final physical action uses stable wide shot
   - no chaotic cuts or axis breaks

7. Audio guidance
   - `generate_audio=true/false`
   - exact dialogue lines in speaker order
   - ambience and key sound effects

8. Restrictions
   - no subtitles, speech bubbles, visible text, panels, labels, arrows, watermark
   - no duplicate characters, extra cats/people, identity drift, outfit drift, prop drift
   - no scene-reference contamination

## Chinese Skeleton

```text
生成一条 [时长] 秒、[比例]、[分辨率] 的 Seedance 视频，generate_audio=[true/false]。

【整体风格与硬约束】
默认采用邵氏电影质感、写实古风棚拍、武侠喜剧氛围；如果用户指定其他风格，则改用用户指定风格。
全片可见角色数量固定为：[角色数量与名单]。
角色身份、服装、左右站位、道具状态必须连续，禁止新增背景角色或复制角色。

【参考图使用方式】
content[] 中第 1 个 reference_image 项是：[用途]。只用于：[身份/脸型/服装/动作/场景等]。
content[] 中第 2 个 reference_image 项是：[用途]。只用于：[用途]。
content[] 中第 N 个 reference_image 项是场景、环境与设定参考图。只用于环境、光线、材质、空间锚点和镜头气质。
不要复现任何参考图中的文字、标签、箭头、网格、分镜格、色卡、版式或说明文字。

【空间关系硬约束】
[写清左/右、前/后、入口/出口、最终位置、稳定锚点。]
禁止反打跨轴导致左右互换，禁止角色瞬移，禁止额外角色。

【道具与状态硬约束】
[写清道具初始状态、出现时机、变化时机、禁止继承的错误道具。]

【逐秒时间轴】
[0-2秒] 镜头构图与运镜：...。角色动作：...。空间锚点/道具连续性：...。对白/音效：...。
[2-4秒] 镜头构图与运镜：...。角色动作：...。空间锚点/道具连续性：...。对白/音效：...。
[4-6秒] 镜头构图与运镜：...。角色动作：...。空间锚点/道具连续性：...。对白/音效：...。
[6-8秒] 镜头构图与运镜：...。角色动作：...。空间锚点/道具连续性：...。对白/音效：...。
[8-10秒] 镜头构图与运镜：...。角色动作：...。空间锚点/道具连续性：...。对白/音效：...。
[10-12秒] 镜头构图与运镜：...。角色动作：...。空间锚点/道具连续性：...。对白/音效：...。

【镜头指导】
使用 rich camera，但必须服务于空间清晰。对白段落以稳定中近景和轻推近为主；关键动作使用稳定广角或中广角。禁止快速混乱切镜、跨轴、错位、角色身份漂移。

【音频指导】
[写明环境声、背景音乐或无音乐。若有对白，逐句写明说话者与原句。]

【限制项】
禁止字幕、气泡、可读文字、标题、标签、箭头、网格、分镜格、水印、Logo、额外角色、重复角色、背景猫/人、身份漂移、服装漂移、道具漂移、肢体崩坏、脸部变形、闪烁模糊。
```

## Verification Gate

Before uploading or building payload, check:

- `Prompt == Seedance视频_Prompt == payload.content[0].text == local prompt file`
- model is `doubao-seedance-2-0-fast-260128` unless user explicitly overrides
- no `@Image`
- no unexplained `CRS`, `SES`, `TDBM`, `BGM`, or internal shorthand in model-facing text
- every timeline block has camera language
- no billable Seedance submission without user confirmation
