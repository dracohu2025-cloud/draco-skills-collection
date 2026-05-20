#!/usr/bin/env node

const args = process.argv.slice(2);

if (args.includes('--help') || args.includes('-h')) {
  console.log(`epub2podcast-run

把 EPUB 转成双人中文播客脚本、音频、视觉页和最终 MP4。

用法:
  epub2podcast-run --epub ./book.epub [--output-dir ./deliveries]
  node dist/cli/run.js --epub ./book.epub [--output-dir ./deliveries]

常用参数:
  --epub <path>             输入 EPUB 文件路径
  --output-dir <dir>        输出目录，默认 ./local-deliveries
  --language <lang>         语言，默认 Chinese
  --color-theme <name>      HTML Slide 主题，默认 gq_fashion
  --ppt-model <model>       HTML Slide 生成模型
  --text-model <model>      脚本生成模型，默认 deepseek-v4-flash
  --tts-provider <name>     TTS 提供商，中文默认 volcengine

视觉模式:
  --visual-mode html-slide        旧 Smart Slide 路线，默认
  --visual-mode gpt-image-slide   GPT-Image-2 全图视觉页
  --image-density segment         一段一图，默认
  --aspect-ratio 4:3              视频页比例，默认 4:3
  --resolution 1440x1080          最终视频帧尺寸，默认 1440x1080
  --no-html-fallback              GPT-Image 失败时不回退 HTML Slide

说明:
  目前最稳输入是 EPUB。GPT-Image 模式需要 OPENAI_API_KEY 或 GPT_IMAGE_API_KEY。
`);
  process.exit(0);
}

await import('../localPipeline.js');
