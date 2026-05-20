#!/usr/bin/env node

const args = process.argv.slice(2);

if (args.includes('--help') || args.includes('-h')) {
  console.log(`epub2podcast-generate-gpt-images

对已有 delivery 生成 / 重生 GPT-Image-2 视觉页，可选重新合成 MP4。

用法:
  epub2podcast-generate-gpt-images --delivery-dir ./deliveries/book-xxx [--recompose]
  node dist/cli/generate-gpt-images.js --delivery-dir ./deliveries/book-xxx [--recompose]

常用参数:
  --delivery-dir <dir>      已有交付目录，需包含 metadata/script.json 和 metadata/book.json
  --image-density <mode>    segment 或 chapter，默认 segment
  --aspect-ratio <ratio>    默认 4:3
  --resolution <WxH>        默认 1440x1080
  --max-retries <n>         单帧 QA 失败后的重试次数，默认 2
  --recompose              生成图片后重写 final_podcast.mp4
`);
  process.exit(0);
}

await import('../generateGptImageSlides.js');
