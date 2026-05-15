#!/usr/bin/env node

const args = process.argv.slice(2);

if (args.includes('--help') || args.includes('-h')) {
  console.log(`epub2podcast-compress-video

压缩最终 MP4，方便上传或分享。

用法:
  epub2podcast-compress-video --input /path/to/final_podcast.mp4 [--output /path/to/output.mp4]
  node dist/cli/compress-video.js --input /path/to/final_podcast.mp4 [--output /path/to/output.mp4]

常用参数:
  --input <path>        输入 MP4 路径
  --output <path>       输出 MP4 路径，可选
`);
  process.exit(0);
}

await import('../compressLocalVideoForFeishu.js');
