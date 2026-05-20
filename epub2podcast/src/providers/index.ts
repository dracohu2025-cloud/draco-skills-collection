/**
 * AI Provider Factory Module
 * 
 * Provides factory functions to get the appropriate text/image generation providers
 * based on configuration. Inspired by Banana Slides' clean provider abstraction.
 * 
 * Usage:
 *   const textProvider = getTextProvider({ provider: 'gemini', model: 'gemini-2.5-flash' });
 *   const result = await textProvider.generateText('Hello, world!');
 */

import dotenv from 'dotenv';
dotenv.config();

// Text Provider exports
export { TextProvider, TextGenerationOptions, TextGenerationResult, JSONGenerationResult, UsageMetadata } from './text/index.js';
export { GeminiTextProvider } from './text/gemini.js';
export { OpenRouterTextProvider } from './text/openrouter.js';

// Image Provider exports  
export { ImageProvider, ImageGenerationOptions, ImageGenerationResult, ImageUsageMetadata, AspectRatio, Resolution } from './image/index.js';
export { GeminiImageProvider } from './image/gemini.js';
export { JimengImageProvider } from './image/jimeng.js';

import { TextProvider } from './text/index.js';
import { GeminiTextProvider } from './text/gemini.js';
import { OpenRouterTextProvider } from './text/openrouter.js';

import { ImageProvider } from './image/index.js';
import { GeminiImageProvider } from './image/gemini.js';
import { JimengImageProvider } from './image/jimeng.js';

// Provider types
export type TextProviderType = 'gemini' | 'openrouter';
export type ImageProviderType = 'gemini' | 'jimeng' | 'openrouter';

export interface TextProviderConfig {
    provider: TextProviderType;
    model?: string;
    apiKey?: string;
}

export interface ImageProviderConfig {
    provider: ImageProviderType;
    model?: string;
    apiKey?: string;
}

/**
 * Factory function to get text generation provider based on configuration
 * 
 * @param config - Provider configuration
 * @returns TextProvider instance
 */
export function getTextProvider(config: TextProviderConfig): TextProvider {
    const { provider, model, apiKey } = config;

    switch (provider) {
        case 'openrouter': {
            const key = apiKey || process.env.OPENROUTER_API_KEY || '';
            const modelName = model || process.env.OPENROUTER_TEXT || 'google/gemini-2.5-flash';
            console.log(`[ProviderFactory] Creating OpenRouterTextProvider, model: ${modelName}`);
            return new OpenRouterTextProvider(key, modelName);
        }

        case 'gemini':
        default: {
            const key = apiKey || process.env.GEMINI_API_KEY || '';
            const modelName = model || 'gemini-2.5-flash';
            console.log(`[ProviderFactory] Creating GeminiTextProvider, model: ${modelName}`);
            return new GeminiTextProvider(key, modelName);
        }
    }
}

/**
 * Factory function to get image generation provider based on configuration
 * 
 * @param config - Provider configuration
 * @returns ImageProvider instance
 */
export function getImageProvider(config: ImageProviderConfig): ImageProvider {
    const { provider, model, apiKey } = config;

    switch (provider) {
        case 'jimeng': {
            const key = apiKey || process.env.JIMENG_API_KEY || process.env.SEEDREAM_API_KEY || '';
            const modelName = model || process.env.JIMENG_MODEL || 'doubao-seedream-4-5-251128';
            console.log(`[ProviderFactory] Creating JimengImageProvider, model: ${modelName}`);
            return new JimengImageProvider(key, modelName);
        }

        case 'gemini':
        default: {
            const key = apiKey || process.env.GEMINI_API_KEY || '';
            const modelName = model || 'gemini-3-pro-image-preview';
            console.log(`[ProviderFactory] Creating GeminiImageProvider, model: ${modelName}`);
            return new GeminiImageProvider(key, modelName);
        }
    }
}

/**
 * Get default provider based on environment
 */
export function getDefaultTextProviderType(): TextProviderType {
    return process.env.OPENROUTER_API_KEY ? 'openrouter' : 'gemini';
}

export function getDefaultImageProviderType(): ImageProviderType {
    return process.env.JIMENG_API_KEY ? 'jimeng' : 'gemini';
}
