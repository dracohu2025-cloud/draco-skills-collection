# EPUB Namespace Compatibility Notes

这份文档记录了 standalone `epub2podcast` 在处理某些 EPUB 时遇到的一个真实兼容性问题，以及对应修复思路。

## 触发样本

- `太平天国革命运动史`

## 问题表现

在修复前，standalone 版本虽然能把整条流程跑完，但会出现：

- 书名变成 `Unknown Book`
- 作者变成 `Unknown`
- `Chapters: 0`
- `Words: 0`

后续脚本、音频、Slide、MP4 仍然会被生成，但这些内容已经不是基于真实书正文，而是模型在“空文本上下文”里生成的结果。

## 根因

问题不在 TTS、Slide 或 ffmpeg，而在 EPUB 解析阶段：

- 某些 EPUB 的 `content.opf` 使用了带 namespace 前缀的 XML 结构
- 旧逻辑直接使用：
  - `getElementsByTagName("metadata")`
  - `getElementsByTagName("item")`
  - `getElementsByTagName("itemref")`
- 在 namespace 场景下，这些查找会失效或返回空结果

于是就会连锁导致：

- metadata 解析失败
- manifest 解析失败
- spine 解析失败
- 正文提取失败

## 修复思路

采用 **namespace-safe** 的节点查找方式，不再依赖固定前缀名，而是按节点 local name 做匹配。

例如：

- `metadata`
- `title`
- `creator`
- `language`
- `item`
- `itemref`

### 关键方法

建议保留这类辅助函数：

```ts
function getLocalName(node: any): string {
  const tag = String(node?.tagName || node?.nodeName || '');
  return tag.includes(':') ? tag.split(':').pop() || tag : tag;
}

function getElementsByLocalName(root: any, localName: string): any[] {
  const results: any[] = [];
  const all = root?.getElementsByTagName?.('*') || [];
  for (let i = 0; i < all.length; i++) {
    const node = all[i];
    if (getLocalName(node) === localName) results.push(node);
  }
  return results;
}
```

## 修复后验证结果

修复后再次对该样本运行 standalone e2e，结果恢复正常：

- 正确解析书名：`太平天国革命运动史`
- 正确解析作者：`简又文`
- 正确提取章节：`295`
- 正确提取正文：`4366158` 字
- 成功完成：
  - 脚本生成
  - 音频生成
  - Smart Slide 生成
  - MP4 合成

## 对未来的建议

以后遇到 EPUB 解析异常时，优先先检查：

1. `META-INF/container.xml` 是否正常
2. `content.opf` 是否带 namespace 前缀
3. `metadata / manifest / spine` 是否被正确解析
4. `chapters` 与 `fullText` 是否非空

如果日志里出现：

- `Unknown Book`
- `Unknown`
- `Chapters: 0`
- `Words: 0`

应优先怀疑 **OPF namespace 兼容问题**，而不是先怀疑模型或 TTS。
