# Sample Commands

这里收录 `epub2podcast` 的最小可运行命令示例，适合第一次上手时直接参考。

## 1. 安装与构建

```bash
cd epub2podcast
npm install
cp .env.example .env
# 编辑 .env
npm run build
```

## 2. 运行主流程

```bash
node dist/cli/run.js --epub ./book.epub --output-dir ./deliveries
```

或使用脚本入口：

```bash
bash scripts/epub2podcast_local_run.sh --epub ./book.epub --output-dir ./deliveries
```

## 3. 重生成某一页 slide

```bash
node dist/cli/regenerate-slide.js \
  --delivery-dir ./deliveries/your-job-dir \
  --slide-index 0 \
  --recompose
```

## 4. 压缩最终视频

```bash
node dist/cli/compress-video.js \
  --input ./deliveries/your-job-dir/final_podcast.mp4 \
  --output ./deliveries/your-job-dir/final_podcast_compressed.mp4
```

## 5. 做环境与构建检查

```bash
npm run smoke-test
```
