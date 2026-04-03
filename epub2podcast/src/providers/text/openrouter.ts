/**
 * OpenRouter Text Provider Implementation
 * Uses OpenRouter API for text generation with multiple model support
 * 
 * Extracted from openrouterService.ts for clean separation
 */

import { TextProvider, TextGenerationOptions, TextGenerationResult, JSONGenerationResult } from './base.js';

const OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1';

interface OpenRouterMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
}

interface OpenRouterResponse {
    id: string;
    model: string;
    choices: {
        message: {
            content: string;
        };
        finish_reason: string;
    }[];
    usage?: {
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
        cost?: number;
    };
}

export class OpenRouterTextProvider implements TextProvider {
    private apiKey: string;
    private model: string;

    constructor(apiKey: string, model: string = 'google/gemini-2.5-flash') {
        if (!apiKey) {
            throw new Error('OPENROUTER_API_KEY is required for OpenRouterTextProvider');
        }
        this.apiKey = apiKey;
        this.model = model;
    }

    async generateText(prompt: string, options?: TextGenerationOptions): Promise<TextGenerationResult> {
        const messages: OpenRouterMessage[] = [
            { role: 'user', content: prompt }
        ];

        const requestBody: any = {
            model: this.model,
            messages,
            max_tokens: options?.maxTokens || 65536,
            temperature: options?.temperature ?? 0.7,
        };

        console.log(`[OpenRouterTextProvider] Calling ${this.model} for text generation...`);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10 * 60 * 1000);

        try {
            const response = await fetch(`${OPENROUTER_BASE_URL}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://podcast.aigc.green',
                    'X-Title': 'EPUB to Podcast',
                },
                body: JSON.stringify(requestBody),
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`OpenRouter API error: ${response.status} - ${errorText}`);
            }

            const data = await response.json() as OpenRouterResponse;
            const text = data.choices[0]?.message?.content || '';

            console.log(`[OpenRouterTextProvider] Complete. Tokens: ${data.usage?.total_tokens || 'unknown'}, Cost: $${data.usage?.cost?.toFixed(6) || 'unknown'}`);

            return {
                text,
                usageMetadata: {
                    inputTokens: data.usage?.prompt_tokens || 0,
                    outputTokens: data.usage?.completion_tokens || 0,
                    totalTokens: data.usage?.total_tokens || 0,
                    model: data.model || this.model,
                    provider: 'openrouter',
                    costUSD: data.usage?.cost,
                },
            };
        } catch (error: any) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('OpenRouter API request timed out (10 minutes)');
            }
            throw error;
        }
    }

    async generateJSON<T>(prompt: string, options?: TextGenerationOptions): Promise<JSONGenerationResult<T>> {
        const messages: OpenRouterMessage[] = [
            { role: 'user', content: prompt }
        ];

        const requestBody: any = {
            model: this.model,
            messages,
            max_tokens: options?.maxTokens || 65536,
            temperature: options?.temperature ?? 0.7,
            response_format: { type: 'json_object' },
        };

        console.log(`[OpenRouterTextProvider] Calling ${this.model} for JSON generation...`);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10 * 60 * 1000);

        try {
            const response = await fetch(`${OPENROUTER_BASE_URL}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://podcast.aigc.green',
                    'X-Title': 'EPUB to Podcast',
                },
                body: JSON.stringify(requestBody),
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`OpenRouter API error: ${response.status} - ${errorText}`);
            }

            const responseData = await response.json() as OpenRouterResponse;
            const text = responseData.choices[0]?.message?.content || '';

            // Parse JSON
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
                console.error('[OpenRouterTextProvider] Failed to parse JSON:', cleanedText.substring(0, 500));
                throw new Error(`Failed to parse JSON response: ${parseError}`);
            }

            console.log(`[OpenRouterTextProvider] JSON Complete. Tokens: ${responseData.usage?.total_tokens || 'unknown'}`);

            return {
                data,
                usageMetadata: {
                    inputTokens: responseData.usage?.prompt_tokens || 0,
                    outputTokens: responseData.usage?.completion_tokens || 0,
                    totalTokens: responseData.usage?.total_tokens || 0,
                    model: responseData.model || this.model,
                    provider: 'openrouter',
                    costUSD: responseData.usage?.cost,
                },
            };
        } catch (error: any) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('OpenRouter API request timed out (10 minutes)');
            }
            throw error;
        }
    }
}
