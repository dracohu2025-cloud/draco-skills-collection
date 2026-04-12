# Remotion Pitfalls

## 1. `Sequence` 偏移减了两次

常见错误：

```tsx
<Sequence from={SECTION}>
  <Scene />
</Sequence>
```

然后在 `Scene` 里又写：

```ts
const local = frame - SECTION;
```

这会把局部帧再减一次。

### 症状
- 后面页面像空白
- 动画不出现
- 文字留白很怪

### 先试这个
如果组件已经在 `Sequence` 里，默认先用：

```ts
const local = frame;
```

## 2. 一上来就渲整片
错。先抽 still。

## 3. 旁白、字幕、画面一起开做
也错。先静音画面，再音频，再字幕。

## 4. 只在 Studio 看，不抽关键帧
Studio 看顺滑，不代表某几帧不炸版。

## 5. 忘了 lint

```bash
npm run lint
```

这能提前抓出不少低级问题。

## 6. 上传飞书用绝对路径
会被 `lark-cli` 判 unsafe。用相对路径。 

## 7. 长任务前台死等
渲染可能很慢。后台跑并轮询，别装死。