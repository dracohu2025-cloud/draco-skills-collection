#!/usr/bin/env node

const args = process.argv.slice(2);

if (args.includes('--help') || args.includes('-h')) {
  console.log(`epub2podcast-run

把 EPUB 转成双人中文播客脚本、音频、Smart Slide 和最终 MP4。

用法:
  epub2podcast-run --epub ./book.epub [--output-dir ./deliveries]
  node dist/cli/run.js --epub ./book.epub [--output-dir ./deliveries]

常用参数:
  --epub <path>         输入 EPUB 文件路径
  --output-dir <dir>    输出目录，默认 ./local-deliveries
  --language <lang>     语言，默认 Chinese
  --color-theme <name>  主题，默认 gq_fashion
  --ppt-model <model>   Slide 生成模型
  --text-model <model>  脚本生成模型
  --tts-provider <name> TTS 提供商，中文默认 volcengine

说明:
  当前 standalone 版本最稳的输入类型是 EPUB。
`);
  process.exit(0);
}

await import('../localPipeline.js');
