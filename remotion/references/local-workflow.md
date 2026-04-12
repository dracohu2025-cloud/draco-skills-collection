# Remotion Local Workflow

## 1. 新建项目

```bash
npx create-video@latest --yes --blank --no-tailwind my-video
cd my-video
npm install
npm i --save-exact @remotion/media @remotion/captions
```

为什么要这样：
- `--yes`：避免交互卡住
- `--blank`：从干净模板起步
- `--no-tailwind`：先少一层变量

## 2. 本地预览

```bash
npx remotion studio
```

## 3. 静音版先跑通

先别接旁白。先确认：
- composition 结构对
- 节奏对
- 页面信息密度对
- 字没有炸版

## 4. 抽关键帧

```bash
mkdir -p renders/stills
npx remotion still src/index.ts CompositionId renders/stills/frame-030.png --frame=30
npx remotion still src/index.ts CompositionId renders/stills/frame-120.png --frame=120
npx remotion still src/index.ts CompositionId renders/stills/frame-210.png --frame=210
```

建议至少抽：
- 开场
- 中段
- 结尾前

## 5. 接中文旁白

```bash
python3 /path/to/volcengine_tts.py \
  --input narration.txt \
  --output public/narration.mp3
```

然后在代码里：

```tsx
import {Audio} from '@remotion/media';
import {staticFile} from 'remotion';

<Audio src={staticFile('narration.mp3')} />
```

## 6. 接字幕

短视频首版优先手写：

```ts
const captions = [
  {text: '第一句', startMs: 0, endMs: 2500, timestampMs: 0, confidence: 1},
  {text: '第二句', startMs: 2500, endMs: 5200, timestampMs: 2500, confidence: 1},
];
```

## 7. 渲染

长渲染任务应后台跑。

```bash
npx remotion render src/index.ts CompositionId renders/final.mp4
```

## 8. 上传飞书

注意：`lark-cli drive +upload --file` 需要相对路径。

```bash
cd renders
lark-cli drive +upload --file ./final.mp4 --name final.mp4
```

然后回查链接。