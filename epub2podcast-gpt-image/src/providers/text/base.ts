/**
 * Abstract base interface for text generation providers
 * Inspired by Banana Slides' clean provider abstraction
 */

export interface TextGenerationOptions {
    temperature?: number;
    maxTokens?: number;
    thinkingBudget?: number;  // For models that support thinking/reasoning
    responseSchema?: object;   // For structured JSON output
}

export interface TextGenerationResult {
    text: string;
    usageMetadata: UsageMetadata;
}

export interface JSONGenerationResult<T> {
    data: T;
    usageMetadata: UsageMetadata;
}

export interface UsageMetadata {
    inputTokens: number;
    outputTokens: number;
    totalTokens: number;
    model: string;
    provider: string;
    costUSD?: number;
}

/**
 * TextProvider interface
 * All text generation providers must implement this interface
 */
export interface TextProvider {
    /**
     * Generate text content from prompt
     */
    generateText(prompt: string, options?: TextGenerationOptions): Promise<TextGenerationResult>;

    /**
     * Generate and parse JSON response
     */
    generateJSON<T>(prompt: string, options?: TextGenerationOptions): Promise<JSONGenerationResult<T>>;
}
