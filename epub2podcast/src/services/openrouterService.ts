/**
 * OpenRouter API Service
 * 
 * Wraps OpenRouter API calls to provide similar interface as Google GenAI
 * for text generation and image generation.
 * 
 * Supports cost tracking from OpenRouter usage response.
 */

import dotenv from 'dotenv';
dotenv.config();

const OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1';

// Get environment variables at runtime (not module load time)
function getApiKey(): string {
    return process.env.OPENROUTER_API_KEY || '';
}

function getTextModel(): string {
    return process.env.OPENROUTER_TEXT || 'google/gemini-3-pro-preview';
}

function getImageModel(): string {
    return process.env.OPENROUTER_IMAGE || 'google/gemini-3.1-flash-image-preview';
}

interface OpenRouterMessage {
    role: 'system' | 'user' | 'assistant';
    content: string | { type: string; text?: string; image_url?: { url: string } }[];
}

interface OpenRouterUsage {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    cost?: number;  // USD cost
    cost_details?: {
        upstream_inference_cost: number | null;
        upstream_inference_prompt_cost: number | null;
        upstream_inference_completions_cost: number | null;
    };
}

interface OpenRouterResponse {
    id: string;
    model: string;
    choices: {
        message: {
            content: string;
            images?: (string | {
                url?: string;
                b64_json?: string;
                image_url?: { url: string };
            })[];
        };
        finish_reason: string;
    }[];
    usage?: OpenRouterUsage;
}

export interface OpenRouterTextResult {
    text: string;
    usage?: {
        inputTokens: number;
        outputTokens: number;
        totalTokens: number;
    };
    cost?: {
        totalUSD: number;
        promptCostUSD: number;
        completionCostUSD: number;
    };
    model: string;
}

export interface OpenRouterImageResult {
    imageBase64: string;
    mimeType: string;
    usage?: {
        inputTokens: number;
        outputTokens: number;
        totalTokens: number;
    };
    cost?: {
        totalUSD: number;
    };
    model: string;
}

// Color theme structure for consistent branding
export interface ColorThemeForImage {
    nameEn: string;
    nameZh: string;
    primary: string;
    secondary: string;
    accent: string;
}

export const openrouterService = {
    /**
     * Generate text content using OpenRouter API
     */
    async generateText(
        prompt: string,
        systemInstruction?: string,
        responseFormat?: 'json' | 'text',
        model?: string // Optional model override
    ): Promise<OpenRouterTextResult> {
        const apiKey = getApiKey();
        const textModel = model || getTextModel(); // Use override if provided

        if (!apiKey) {
            throw new Error('OPENROUTER_API_KEY is not configured');
        }

        const messages: OpenRouterMessage[] = [];

        if (systemInstruction) {
            messages.push({
                role: 'system',
                content: systemInstruction
            });
        }

        messages.push({
            role: 'user',
            content: prompt
        });



        const requestBody: any = {
            model: textModel,
            messages,
            max_tokens: 65536,  // Increased from 16384 to handle large script generation
            temperature: 0.7,
            // Use Vertex AI first (no region restrictions), fallback to Google AI Studio
            provider: {
                order: ['Vertex AI']
            }
        };

        // Request JSON format if needed
        if (responseFormat === 'json') {
            requestBody.response_format = { type: 'json_object' };
        }

        console.log(`[OpenRouter] Calling ${textModel} for text generation...`);

        // Add timeout with AbortController
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10 * 60 * 1000); // 10 minute timeout

        try {
            const response = await fetch(`${OPENROUTER_BASE_URL}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://podcast.aigc.green',
                    'X-Title': 'EPUB to Podcast'
                },
                body: JSON.stringify(requestBody),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`[OpenRouter] API error: ${response.status}`, errorText);
                throw new Error(`OpenRouter API error: ${response.status} - ${errorText}`);
            }

            const data = await response.json() as OpenRouterResponse;

            const text = data.choices[0]?.message?.content || '';

            // Extract usage
            const usage = data.usage ? {
                inputTokens: data.usage.prompt_tokens,
                outputTokens: data.usage.completion_tokens,
                totalTokens: data.usage.total_tokens
            } : undefined;

            // Extract cost information
            const cost = data.usage?.cost !== undefined ? {
                totalUSD: data.usage.cost,
                promptCostUSD: data.usage.cost_details?.upstream_inference_prompt_cost || 0,
                completionCostUSD: data.usage.cost_details?.upstream_inference_completions_cost || 0
            } : undefined;

            console.log(`[OpenRouter] Text generation complete. Tokens: ${usage?.totalTokens || 'unknown'}, Cost: $${cost?.totalUSD?.toFixed(6) || 'unknown'}`);

            return { text, usage, cost, model: data.model || textModel };

        } catch (error: any) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('OpenRouter API request timed out (10 minutes)');
            }
            throw error;
        }
    },

    /**
     * Generate image using OpenRouter API
     * Note: OpenRouter's image generation may differ from Google's
     * @param prompt - The image generation prompt
     * @param aspectRatio - Optional aspect ratio (e.g., "16:9", "4:3", "1:1"). Default is "1:1"
     * @param colorTheme - Optional color theme for consistent branding
     */
    async generateImage(
        prompt: string,
        aspectRatio: string = '1:1',
        colorTheme?: ColorThemeForImage
    ): Promise<OpenRouterImageResult> {
        const apiKey = getApiKey();
        const imageModel = getImageModel();

        if (!apiKey) {
            throw new Error('OPENROUTER_API_KEY is not configured');
        }

        console.log(`[OpenRouter] Calling ${imageModel} for image generation...`);

        // For image generation, we use OpenRouter's image model with a specific prompt format
        // Include aspect ratio instruction in the prompt
        const aspectInstruction = aspectRatio !== '1:1'
            ? `IMPORTANT: Generate this image in ${aspectRatio} aspect ratio (widescreen format for ${aspectRatio === '16:9' ? 'YouTube thumbnail' : 'presentation'}). `
            : '';

        // Include color theme instruction for brand consistency
        const colorInstruction = colorTheme
            ? `\n\nCRITICAL COLOR BRANDING (for background, graphics, and design elements ONLY - NOT as visible text):
- Primary Color: ${colorTheme.primary} (main elements, headers, dominant areas)
- Secondary Color: ${colorTheme.secondary} (supporting elements, gradients)
- Accent Color: ${colorTheme.accent} (highlights, icons, decorative elements)
Use these colors for the visual design. DO NOT display color names or hex codes as text in the image.

`
            : '';

        const messages: OpenRouterMessage[] = [
            {
                role: 'user',
                content: `${aspectInstruction}${colorInstruction}Generate an image based on this description: ${prompt}`
            }
        ];

        // Add timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5 * 60 * 1000); // 5 minute timeout

        try {
            const response = await fetch(`${OPENROUTER_BASE_URL}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://podcast.aigc.green',
                    'X-Title': 'EPUB to Podcast'
                },
                body: JSON.stringify({
                    model: imageModel,
                    messages,
                    max_tokens: 4096,
                    modalities: ["image", "text"],  // Required for image generation
                    // Use Vertex AI first (no region restrictions), fallback to Google AI Studio
                    provider: {
                        order: ['Vertex AI']
                    }
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`[OpenRouter] Image API error: ${response.status}`, errorText);
                throw new Error(`OpenRouter Image API error: ${response.status} - ${errorText}`);
            }

            const data = await response.json() as OpenRouterResponse;

            // Debug: Log full response structure
            console.log(`[OpenRouter] Response keys:`, Object.keys(data));
            if (data.choices?.[0]?.message) {
                console.log(`[OpenRouter] Message keys:`, Object.keys(data.choices[0].message));
            }

            // OpenRouter may return images in different ways:
            // 1. message.images array (preferred for Gemini image models)
            // 2. message.content as data URL (data:image/png;base64,...)
            // 3. message.content as pure base64

            const message = data.choices[0]?.message;
            let imageBase64 = '';
            let mimeType = 'image/png';

            // Check for images array first (Gemini 3.0 Pro Image style)
            // Format per OpenRouter SDK: message.images[].image_url.url contains data URL
            if (message?.images && Array.isArray(message.images) && message.images.length > 0) {
                const imageData = message.images[0];
                let imageUrl = '';

                // Handle different possible formats
                if (typeof imageData === 'string') {
                    imageUrl = imageData;
                } else if (imageData?.image_url?.url) {
                    // Per OpenRouter SDK: images[].image_url.url format
                    imageUrl = imageData.image_url.url;
                } else if (imageData?.url) {
                    imageUrl = imageData.url;
                } else if (imageData?.b64_json) {
                    imageBase64 = imageData.b64_json;
                }

                // Extract base64 from data URL if we have a URL
                if (imageUrl && !imageBase64) {
                    if (imageUrl.startsWith('data:image/')) {
                        const match = imageUrl.match(/data:(image\/\w+);base64,(.+)/);
                        if (match) {
                            mimeType = match[1];
                            imageBase64 = match[2];
                        }
                    } else if (imageUrl.match(/^[A-Za-z0-9+/=]+$/) && imageUrl.length > 1000) {
                        // Pure base64
                        imageBase64 = imageUrl;
                    } else if (imageUrl.startsWith('http')) {
                        // If it's a regular URL, we'd need to fetch it (not expected for Gemini)
                        console.log(`[OpenRouter] Image returned as HTTP URL (unexpected):`, imageUrl.substring(0, 100));
                        throw new Error('Image returned as HTTP URL. Expected data URL.');
                    }
                }

                if (imageBase64) {
                    console.log(`[OpenRouter] Found image in message.images array`);
                }
            }

            // Fallback: check content field
            if (!imageBase64) {
                const content = message?.content || '';

                if (content.startsWith('data:image/')) {
                    // Format: data:image/png;base64,xxxxx
                    const match = content.match(/data:(image\/\w+);base64,(.+)/);
                    if (match) {
                        mimeType = match[1];
                        imageBase64 = match[2];
                    }
                } else if (content.match(/^[A-Za-z0-9+/=]+$/) && content.length > 1000) {
                    // Pure base64 string (must be long enough to be an image)
                    imageBase64 = content;
                }
            }

            // If still no image, provide detailed error
            if (!imageBase64) {
                console.error(`[OpenRouter] No image found in response.`);
                console.error(`[OpenRouter] message.images:`, message?.images);
                console.error(`[OpenRouter] message.content (first 500 chars):`, (message?.content || '').substring(0, 500));
                throw new Error('OpenRouter returned no image data. The model may not support image generation or the response format changed.');
            }

            const usage = data.usage ? {
                inputTokens: data.usage.prompt_tokens,
                outputTokens: data.usage.completion_tokens,
                totalTokens: data.usage.total_tokens
            } : undefined;

            // Read cost from multiple possible sources:
            // 1. data.usage.cost (standard OpenRouter format)
            // 2. (data as any).total_cost (OpenRouter /generation endpoint format)
            // 3. data.usage as number (some endpoints return usage as cost directly)
            let costValue: number | undefined;
            if (data.usage?.cost !== undefined) {
                costValue = data.usage.cost;
            } else if ((data as any).total_cost !== undefined) {
                costValue = (data as any).total_cost;
            } else if (typeof data.usage === 'number') {
                costValue = data.usage;
            }

            const cost = costValue !== undefined ? {
                totalUSD: costValue
            } : undefined;

            console.log(`[OpenRouter] Image generation complete. Tokens: ${usage?.totalTokens || 'unknown'}, Cost: $${cost?.totalUSD?.toFixed(6) || 'unknown'}`);

            return { imageBase64, mimeType, usage, cost, model: data.model || imageModel };

        } catch (error: any) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('OpenRouter Image API request timed out (5 minutes)');
            }
            throw error;
        }
    },

    /**
     * Analyze an image using Gemini 3.0 Flash (multimodal)
     * Used for watermark detection on book covers
     * @param imageBase64 - Base64 encoded image (without data:... prefix)
     * @param prompt - Analysis prompt
     * @param mimeType - Image MIME type (default: image/jpeg)
     * @returns Analysis result text
     */
    async analyzeImage(
        imageBase64: string,
        prompt: string,
        mimeType: string = 'image/jpeg'
    ): Promise<{ text: string; cost?: { totalUSD: number } }> {
        const apiKey = getApiKey();
        // Use Gemini 3.0 Flash for fast, cost-effective analysis
        const model = 'google/gemini-3-flash-preview';

        if (!apiKey) {
            throw new Error('OPENROUTER_API_KEY is not configured');
        }

        console.log(`[OpenRouter] Analyzing image with ${model}...`);

        // Build multimodal message with image
        const messages: OpenRouterMessage[] = [
            {
                role: 'user',
                content: [
                    {
                        type: 'image_url',
                        image_url: {
                            url: `data:${mimeType};base64,${imageBase64}`
                        }
                    },
                    {
                        type: 'text',
                        text: prompt
                    }
                ]
            }
        ];

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30 * 1000); // 30 second timeout

        try {
            const response = await fetch(`${OPENROUTER_BASE_URL}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://podcast.aigc.green',
                    'X-Title': 'EPUB to Podcast'
                },
                body: JSON.stringify({
                    model,
                    messages,
                    max_tokens: 100,
                    temperature: 0.1, // Low temperature for consistent detection
                    // Use Vertex AI first (no region restrictions), fallback to Google AI Studio
                    provider: {
                        order: ['Vertex AI']
                    }
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`[OpenRouter] Image analysis error: ${response.status}`, errorText);
                throw new Error(`OpenRouter Image Analysis error: ${response.status} - ${errorText}`);
            }

            const data = await response.json() as OpenRouterResponse;
            const text = data.choices[0]?.message?.content || '';

            const cost = data.usage?.cost !== undefined ? {
                totalUSD: data.usage.cost
            } : undefined;

            console.log(`[OpenRouter] Image analysis complete. Response: "${text.substring(0, 50)}...", Cost: $${cost?.totalUSD?.toFixed(6) || 'unknown'}`);

            return { text, cost };

        } catch (error: any) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('OpenRouter Image Analysis request timed out (30 seconds)');
            }
            throw error;
        }
    },

    /**
     * Check if OpenRouter is configured
     */
    isConfigured(): boolean {
        return !!getApiKey();
    },

    /**
     * Get model names for logging
     */
    getModels(): { textModel: string; imageModel: string } {
        return {
            textModel: getTextModel(),
            imageModel: getImageModel()
        };
    }
};
