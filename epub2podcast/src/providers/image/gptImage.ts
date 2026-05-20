import { ImageGenerationOptions, ImageGenerationResult, ImageProvider } from './base.js';

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is required for GPT image generation`);
  return value;
}

async function downloadUrl(url: string): Promise<Buffer> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to download generated image: ${res.status} ${res.statusText}`);
  return Buffer.from(await res.arrayBuffer());
}

export class GptImageProvider implements ImageProvider {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly model: string;
  private readonly size: string;
  private readonly quality: string;

  constructor(params: { apiKey?: string; baseUrl?: string; model?: string; size?: string; quality?: string } = {}) {
    this.apiKey = params.apiKey || process.env.GPT_IMAGE_API_KEY || process.env.OPENAI_API_KEY || requiredEnv('OPENAI_API_KEY');
    this.baseUrl = (params.baseUrl || process.env.GPT_IMAGE_BASE_URL || 'https://api.openai.com/v1').replace(/\/$/, '');
    this.model = params.model || process.env.GPT_IMAGE_MODEL || 'gpt-image-2-high';
    this.size = params.size || process.env.GPT_IMAGE_SIZE || '1536x1024';
    this.quality = params.quality || process.env.GPT_IMAGE_QUALITY || 'high';
  }

  async generateImage(prompt: string, options: ImageGenerationOptions = {}): Promise<ImageGenerationResult> {
    const body: Record<string, unknown> = {
      model: this.model,
      prompt,
      n: 1,
      size: this.size,
      quality: this.quality,
    };
    if (options.aspectRatio) body.aspect_ratio = options.aspectRatio;
    if (options.resolution) body.resolution = options.resolution;

    const res = await fetch(`${this.baseUrl}/images/generations`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const text = await res.text();
    if (!res.ok) {
      throw new Error(`GPT image generation failed: ${res.status} ${res.statusText} ${text.slice(0, 500)}`);
    }

    const json = JSON.parse(text) as {
      data?: Array<{ b64_json?: string; url?: string }>;
      usage?: { input_tokens?: number; output_tokens?: number; total_tokens?: number };
    };
    const item = json.data?.[0];
    if (!item) throw new Error('GPT image generation returned no image data');
    const buffer = item.b64_json ? Buffer.from(item.b64_json, 'base64') : item.url ? await downloadUrl(item.url) : undefined;
    if (!buffer) throw new Error('GPT image generation returned neither b64_json nor url');

    return {
      buffer,
      usageMetadata: {
        model: this.model,
        provider: 'gpt-image',
        inputTokens: json.usage?.input_tokens,
        outputTokens: json.usage?.output_tokens,
        totalTokens: json.usage?.total_tokens,
      },
    };
  }
}
