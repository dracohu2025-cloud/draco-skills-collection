/**
 * Jimeng (即梦/SeeDream) Image Provider Implementation
 * Uses Volcengine API for image generation
 * 
 * Extracted from jimengService.ts for clean separation
 */

import { ImageProvider, ImageGenerationOptions, ImageGenerationResult, Resolution } from './base.js';

const JIMENG_API_URL = 'https://ark.cn-beijing.volces.com/api/v3/images/generations';
const JIMENG_MODEL = process.env.JIMENG_MODEL || 'doubao-seedream-4-5-251128';

// Cost per image (RMB) - 即梦 4.5: ¥0.25/张
const COST_PER_IMAGE_RMB = 0.25;
const USD_TO_RMB_RATE = 7.2;

export class JimengImageProvider implements ImageProvider {
    private apiKey: string;
    private model: string;

    constructor(apiKey: string, model: string = JIMENG_MODEL) {
        if (!apiKey) {
            throw new Error('JIMENG_API_KEY is required for JimengImageProvider');
        }
        this.apiKey = apiKey;
        this.model = model;
    }

    async generateImage(prompt: string, options?: ImageGenerationOptions): Promise<ImageGenerationResult> {
        const resolution = options?.resolution || '2K';

        console.log(`[JimengImageProvider] Generating image (${resolution})...`);
        console.log(`[JimengImageProvider] Prompt: ${prompt.substring(0, 80)}...`);

        const requestBody = {
            model: this.model,
            prompt: prompt,
            sequential_image_generation: 'disabled',
            response_format: 'b64_json',
            size: resolution,
            stream: false,
            watermark: false,
        };

        const timeoutPromise = new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error('Jimeng image generation timed out after 90s')), 90000)
        );

        try {
            const response = await Promise.race([
                fetch(JIMENG_API_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.apiKey}`,
                    },
                    body: JSON.stringify(requestBody),
                }),
                timeoutPromise,
            ]);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`[JimengImageProvider] API Error: ${response.status} - ${errorText}`);
                throw new Error(`Jimeng API error: ${response.status} - ${errorText}`);
            }

            const data = await response.json();

            if (!data.data || data.data.length === 0) {
                console.error(`[JimengImageProvider] No image data in response:`, JSON.stringify(data, null, 2));
                throw new Error('Jimeng API returned no image data');
            }

            const imageData = data.data[0];
            let base64Image: string;

            if (imageData.b64_json) {
                base64Image = imageData.b64_json;
            } else if (imageData.url) {
                console.log(`[JimengImageProvider] Downloading image from URL...`);
                const imageResponse = await fetch(imageData.url);
                const imageArrayBuffer = await imageResponse.arrayBuffer();
                base64Image = Buffer.from(imageArrayBuffer).toString('base64');
            } else {
                throw new Error('Jimeng API returned neither b64_json nor url');
            }

            console.log(`[JimengImageProvider] Image generated successfully`);

            return {
                buffer: Buffer.from(base64Image, 'base64'),
                usageMetadata: {
                    model: this.model,
                    provider: 'jimeng',
                    costRMB: COST_PER_IMAGE_RMB,
                    costUSD: parseFloat((COST_PER_IMAGE_RMB / USD_TO_RMB_RATE).toFixed(4)),
                },
            };
        } catch (error: any) {
            console.error(`[JimengImageProvider] Generation failed:`, error.message);
            throw error;
        }
    }
}
