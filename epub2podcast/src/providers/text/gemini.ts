/**
 * Gemini Text Provider Implementation
 * Uses Google GenAI SDK for text generation
 * 
 * Extracted from scriptService.ts for clean separation
 */

import { GoogleGenAI, Type } from '@google/genai';
import { TextProvider, TextGenerationOptions, TextGenerationResult, JSONGenerationResult } from './base.js';

export class GeminiTextProvider implements TextProvider {
    private client: GoogleGenAI;
    private model: string;

    constructor(apiKey: string, model: string = 'gemini-2.5-flash') {
        if (!apiKey) {
            throw new Error('GEMINI_API_KEY is required for GeminiTextProvider');
        }
        this.client = new GoogleGenAI({ apiKey });
        this.model = model;
    }

    async generateText(prompt: string, options?: TextGenerationOptions): Promise<TextGenerationResult> {
        const config: any = {
            temperature: options?.temperature ?? 0.7,
        };

        if (options?.maxTokens) {
            config.maxOutputTokens = options.maxTokens;
        }

        // Add thinking budget for models that support it
        if (options?.thinkingBudget && this.model.includes('flash')) {
            config.thinkingConfig = { thinkingBudget: options.thinkingBudget };
        }

        console.log(`[GeminiTextProvider] Calling ${this.model} for text generation...`);

        const response = await this.client.models.generateContent({
            model: this.model,
            contents: prompt,
            config,
        });

        const text = response.text || '';
        const usageMetadata = response.usageMetadata;

        return {
            text,
            usageMetadata: {
                inputTokens: usageMetadata?.promptTokenCount || 0,
                outputTokens: usageMetadata?.candidatesTokenCount || 0,
                totalTokens: usageMetadata?.totalTokenCount || 0,
                model: this.model,
                provider: 'gemini',
            },
        };
    }

    async generateJSON<T>(prompt: string, options?: TextGenerationOptions): Promise<JSONGenerationResult<T>> {
        const config: any = {
            temperature: options?.temperature ?? 0.7,
            responseMimeType: 'application/json',
        };

        if (options?.maxTokens) {
            config.maxOutputTokens = options.maxTokens;
        }

        // Add response schema if provided
        if (options?.responseSchema) {
            config.responseSchema = options.responseSchema;
        }

        console.log(`[GeminiTextProvider] Calling ${this.model} for JSON generation...`);

        const response = await this.client.models.generateContent({
            model: this.model,
            contents: prompt,
            config,
        });

        const text = response.text || '';
        const usageMetadata = response.usageMetadata;

        // Parse JSON - handle potential markdown code blocks
        let cleanedText = text;
        if (cleanedText.startsWith('```json')) {
            cleanedText = cleanedText.replace(/^```json\s*/, '').replace(/\s*```$/, '');
        } else if (cleanedText.startsWith('```')) {
            cleanedText = cleanedText.replace(/^```\s*/, '').replace(/\s*```$/, '');
        }

        let data: T;
        try {
            data = JSON.parse(cleanedText);
        } catch (parseError) {
            console.error('[GeminiTextProvider] Failed to parse JSON:', cleanedText.substring(0, 500));
            throw new Error(`Failed to parse JSON response: ${parseError}`);
        }

        return {
            data,
            usageMetadata: {
                inputTokens: usageMetadata?.promptTokenCount || 0,
                outputTokens: usageMetadata?.candidatesTokenCount || 0,
                totalTokens: usageMetadata?.totalTokenCount || 0,
                model: this.model,
                provider: 'gemini',
            },
        };
    }
}
