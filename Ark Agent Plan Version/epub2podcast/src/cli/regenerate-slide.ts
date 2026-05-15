#!/usr/bin/env node

const args = process.argv.slice(2);

if (args.includes('--help') || args.includes('-h')) {
  console.log(`epub2podcast-regenerate-slide

重生成某一页 Smart Slide，并可选择是否重合成视频。

用法:
  epub2podcast-regenerate-slide --delivery-dir /path/to/delivery --slide-index 0 [--recompose]
  node dist/cli/regenerate-slide.js --delivery-dir /path/to/delivery --slide-index 0 [--recompose]

常用参数:
  --delivery-dir <dir>  已有交付目录
  --slide-index <n>     需要重生成的页码（从 0 开始）
  --recompose           重生成后顺带重合成 final_podcast.mp4
  --language <lang>     语言，默认 Chinese
  --ppt-model <model>   Slide 生成模型
  --color-theme <name>  主题，默认 gq_fashion
`);
  process.exit(0);
}

await import('../regenerateLocalSlide.js');
