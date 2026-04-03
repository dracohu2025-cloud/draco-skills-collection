/**
 * Marketing Content Prompts
 * 
 * Prompts for generating marketing assets (titles, descriptions, thumbnails)
 */

import { Language, getLanguageInstruction } from './utils.js';

/**
 * Generate prompt for YouTube marketing content
 */
export function getMarketingPrompt(
    bookTitle: string,
    scriptSummary: string,
    language: Language
): string {
    const langInstruction = getLanguageInstruction(language);
    const isChinese = language === 'Chinese';

    return `
Based on the following podcast script about "${bookTitle}", generate compelling YouTube marketing content.

Script Summary:
${scriptSummary}

Generate the following in JSON format:
{
  "title": "${isChinese ? '吸引人的中文标题 (最多60个字符)' : 'Catchy title (max 60 chars)'}",
  "description": "${isChinese ? '详细的视频描述 (200-500字)' : 'Detailed video description (200-500 words)'}",
  "thumbnailPrompt": "A visual prompt for generating a YouTube thumbnail image"
}

Requirements:
- Title should be attention-grabbing and SEO-friendly
- Description should include key topics and timestamps
- Thumbnail prompt should describe a visually striking image that represents the content
${langInstruction}

Output only the JSON, no additional text.
`;
}

/**
 * Generate prompt for podcast thumbnail
 */
export function getThumbnailPrompt(
    bookTitle: string,
    keyTheme: string,
    language: Language
): string {
    const isChinese = language === 'Chinese';

    return `
Create a YouTube-optimized thumbnail image for a podcast about "${bookTitle}".

Key Theme: ${keyTheme}

Requirements:
- 16:9 aspect ratio, 1280x720 resolution
- Bold, readable text (${isChinese ? 'Chinese characters only' : 'English only'})
- High contrast colors for visibility
- Dramatic visual composition
- Text should be SHORT (${isChinese ? 'max 6 Chinese characters' : 'max 4 words'})
- Professional podcast/educational content aesthetic
${isChinese ? '- CRITICAL: NO pseudo-characters or gibberish text' : ''}

Generate a visually stunning thumbnail that will maximize click-through rate.
`;
}
