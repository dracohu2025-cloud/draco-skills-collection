/**
 * Abstract base interface for image generation providers
 * Inspired by Banana Slides' clean provider abstraction
 */

export type AspectRatio = '1:1' | '4:3' | '16:9' | '9:16' | '3:4';
export type Resolution = '1K' | '2K' | '4K';

export interface ImageGenerationOptions {
    aspectRatio?: AspectRatio;
    resolution?: Resolution;
    referenceImages?: Buffer[];  // For style reference
}

export interface ImageGenerationResult {
    buffer: Buffer;
    usageMetadata: ImageUsageMetadata;
    htmlContent?: string;  // For PPT/HTML-based generation
}

export interface ImageUsageMetadata {
    inputTokens?: number;
    outputTokens?: number;
    totalTokens?: number;
    model: string;
    provider: string;
    costUSD?: number;
    costRMB?: number;  // For providers like 即梦 that charge in RMB
}

/**
 * ImageProvider interface
 * All image generation providers must implement this interface
 */
export interface ImageProvider {
    /**
     * Generate image from prompt
     * 
     * @param prompt - The image generation prompt
     * @param options - Optional generation options
     * @returns Generated image buffer with usage metadata
     */
    generateImage(prompt: string, options?: ImageGenerationOptions): Promise<ImageGenerationResult>;
}
