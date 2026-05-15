/**
 * Prompt Utility Functions
 * 
 * Inspired by Banana Slides' prompts.py - provides multi-language support
 * and common formatting utilities for prompts.
 */

export type Language = 'Chinese' | 'English';

/**
 * Language configuration for prompts
 */
export const LANGUAGE_CONFIG: Record<Language, {
    instruction: string;
    slideText: string;
    hostMale: string;
    hostFemale: string;
}> = {
    Chinese: {
        instruction: '请使用全中文输出。',
        slideText: 'Slide 上的文字必须使用简体中文。',
        hostMale: '阿哲',
        hostFemale: '小雅',
    },
    English: {
        instruction: 'Please output all in English.',
        slideText: 'Use English for all slide text.',
        hostMale: 'Alex',
        hostFemale: 'Sarah',
    },
};

/**
 * Get language instruction for prompts
 */
export function getLanguageInstruction(language: Language): string {
    return LANGUAGE_CONFIG[language]?.instruction || LANGUAGE_CONFIG.English.instruction;
}

/**
 * Get slide text language instruction
 */
export function getSlideLanguageInstruction(language: Language): string {
    return LANGUAGE_CONFIG[language]?.slideText || LANGUAGE_CONFIG.English.slideText;
}

/**
 * Get host names for podcast scripts
 */
export function getHostNames(language: Language): { male: string; female: string } {
    const config = LANGUAGE_CONFIG[language] || LANGUAGE_CONFIG.English;
    return {
        male: config.hostMale,
        female: config.hostFemale,
    };
}

/**
 * Format reference files as XML (inspired by Banana Slides)
 * This helps models understand file boundaries clearly
 */
export function formatReferenceFilesXML(files: Array<{ name: string; content: string }>): string {
    if (!files || files.length === 0) {
        return '';
    }

    const filesXML = files.map(file => `
  <file name="${file.name}">
    <content>${file.content}</content>
  </file>`).join('\n');

    return `<uploaded_files>${filesXML}
</uploaded_files>

`;
}

/**
 * Extract key point from segment text (for slide bullet points)
 * Keeps text concise (15-25 characters for Chinese, ~30 words for English)
 */
export function extractKeyPoint(text: string, language: Language): string {
    const maxLength = language === 'Chinese' ? 25 : 100;

    // Get first sentence
    const firstSentence = text.split(/[。！？.!?]/)[0];

    if (firstSentence.length <= maxLength) {
        return firstSentence;
    }

    return firstSentence.substring(0, maxLength) + '...';
}

/**
 * Combine multiple segment texts into a single description
 */
export function combineSegmentTexts(texts: string[], maxLength: number = 500): string {
    const combined = texts.join('\n\n');
    if (combined.length <= maxLength) {
        return combined;
    }
    return combined.substring(0, maxLength) + '...';
}
