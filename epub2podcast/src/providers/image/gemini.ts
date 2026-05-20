/**
 * Gemini Image Provider Implementation
 * Uses Google GenAI SDK for image generation
 * 
 * Extracted from imageService.ts for clean separation
 */

import { GoogleGenAI } from '@google/genai';
import { ImageProvider, ImageGenerationOptions, ImageGenerationResult, AspectRatio } from './base.js';

const IMAGE_MODEL = 'gemini-3-pro-image-preview';

export class GeminiImageProvider implements ImageProvider {
    private client: GoogleGenAI;
    private model: string;

    constructor(apiKey: string, model: string = IMAGE_MODEL) {
        if (!apiKey) {
            throw new Error('GEMINI_API_KEY is required for GeminiImageProvider');
        }
        this.client = new GoogleGenAI({ apiKey });
        this.model = model;
    }

    async generateImage(prompt: string, options?: ImageGenerationOptions): Promise<ImageGenerationResult> {
        const aspectRatio = options?.aspectRatio || '1:1';
        const resolution = options?.resolution || '1K';

        // Add Chinese character constraints to prompt
        const enhancedPrompt = prompt + `\n\n--- ADDITIONAL CONSTRAINTS ---
If this prompt contains Chinese text requirements, you MUST:
1. Ensure EVERY Chinese character is 100% accurate and real
2. STRICTLY FORBID pseudo-characters that look Chinese but are incorrect
3. When uncertain, MINIMIZE or OMIT text entirely, use icons/symbols instead
4. Absolutely NO gibberish or nonsensical character combinations`;

        console.log(`[GeminiImageProvider] Generating image (${aspectRatio}, ${resolution})...`);

        const timeoutPromise = new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error('Image generation timed out after 120s')), 120000)
        );

        const response = await Promise.race([
            this.client.models.generateContent({
                model: this.model,
                contents: {
                    parts: [{ text: enhancedPrompt }]
                },
                config: {
                    imageConfig: {
                        aspectRatio: aspectRatio,
                        imageSize: resolution,
                    }
                }
            }),
            timeoutPromise
        ]);

        console.log('[GeminiImageProvider] Response received');

        if (response.usageMetadata) {
            console.log(`[GeminiImageProvider] Token Usage: Input: ${response.usageMetadata.promptTokenCount}, Output: ${response.usageMetadata.candidatesTokenCount}`);
        }

        if (!response.candidates || response.candidates.length === 0) {
            throw new Error('Image generation failed: No candidates returned.');
        }

        let base64Image: string | null = null;
        for (const part of response.candidates[0].content?.parts || []) {
            if (part.inlineData) {
                base64Image = part.inlineData.data as string;
                break;
            }
        }

        if (!base64Image) {
            console.error('[GeminiImageProvider] Full Response:', JSON.stringify(response, null, 2));
            throw new Error('No image data returned from Gemini');
        }

        return {
            buffer: Buffer.from(base64Image, 'base64'),
            usageMetadata: {
                inputTokens: response.usageMetadata?.promptTokenCount,
                outputTokens: response.usageMetadata?.candidatesTokenCount,
                totalTokens: response.usageMetadata?.totalTokenCount,
                model: this.model,
                provider: 'gemini',
            },
        };
    }
}
