/**
 * Script Generation Prompts
 * 
 * XML-structured prompts for podcast script generation.
 * Uses consistent XML tags for clear organization.
 */

import { Language, getHostNames } from './utils.js';
import { ImageStyleConfig } from '../types.js';
import { EpubChapter } from '../services/epubService.js';

// ============================================================
// Types
// ============================================================

export interface ScriptPromptParams {
  language: Language;
  bookTitle: string;
  author?: string;
  chapters: EpubChapter[];
  contentPreview: string;
  imageStyle: ImageStyleConfig;
}

// ============================================================
// Main Prompt Functions
// ============================================================

/**
 * Build the complete script generation prompt with XML structure
 */
export function buildScriptPrompt(params: ScriptPromptParams): { systemPrompt: string; userPrompt: string } {
  const { language, bookTitle, author, chapters, contentPreview } = params;

  const systemPrompt = getScriptSystemPrompt(language);
  const userPrompt = buildUserPrompt({
    bookTitle,
    author,
    chapters,
    contentPreview,
    language
  });

  return { systemPrompt, userPrompt };
}

/**
 * Get the core script generation system prompt
 */
export function getScriptSystemPrompt(language: Language): string {
  const hosts = getHostNames(language);
  const isChinese = language === 'Chinese';

  return `
<role>
You are a world-class podcast producer specializing in educational content.
Your task is to convert a book into an engaging podcast script between two hosts:
1. "${hosts.male}" (Male): Skeptical, curious, asks clarifying questions, grounded.
2. "${hosts.female}" (Female): Expert, enthusiastic, explains complex concepts clearly, uses analogies.
</role>

<podcast_identity>
- Name: NONE. Do NOT name the podcast.
- Just welcome the listener to "the show" or "our program".
</podcast_identity>

<language_requirement>
The dialogue ("text" field) MUST be in **${language}**.
${isChinese ? `
CRITICAL FOR CHINESE:
- ${hosts.male} and ${hosts.female} act as citizens of Mainland China.
- Interpret topics from the Mainland China perspective.
- NO PINYIN. Use ONLY Simplified Chinese characters.
` : ''}
The "visualPrompt" and "speaker" fields MUST remain in English.
</language_requirement>

<formatting_rules>
- NO MARKDOWN: No asterisks (*), bold (**), or italics (_). Write plain text only.
- NO STAGE DIRECTIONS: The "text" field must contain ONLY spoken dialogue.
  NEVER include: (音乐渐弱), (笑), (停顿), (思考), or ANY parenthetical annotations.
- NO ROLE CONFUSION: A speaker must NEVER address themselves by name.
- NO AMBIGUOUS NUMBERS: Write out decades in full words.
</formatting_rules>

<duration_structure>
- Target: ~15 minutes (4500+ words, exactly 18-22 segments)
- Structure:
  1. Introduction (2-3 segments): GRAB ATTENTION in first 10 seconds!
  2. Deep Dive Part 1 (5-6 segments): First major theme/chapter
  3. Deep Dive Part 2 (5-6 segments): Second major theme
  4. Deep Dive Part 3 (3-4 segments): Most complex idea, simplified
  5. Conclusion (2-3 segments): Key takeaways
</duration_structure>

<output_format>
Return a JSON array of segments:
[
  {
    "speaker": "Female" | "Male",
    "text": "Dialogue in ${language}",
    "visualPrompt": "English description for slide generation" | null
  }
]
</output_format>
`;
}

/**
 * Build the user prompt with XML-structured book information
 */
function buildUserPrompt(params: {
  bookTitle: string;
  author?: string;
  chapters: EpubChapter[];
  contentPreview: string;
  language: Language;
}): string {
  const { bookTitle, author, chapters, contentPreview, language } = params;

  // Build table of contents XML
  const tocXml = chapters.length > 0
    ? chapters.map(ch => `  <chapter order="${ch.order}">${escapeXml(ch.title)}</chapter>`).join('\n')
    : '  <chapter order="1">Full Content</chapter>';

  // Build chapter summaries (first 200 chars of each chapter)
  const chapterSummaries = chapters.length > 0
    ? chapters.slice(0, 10).map(ch =>
      `  <chapter_summary order="${ch.order}" title="${escapeXml(ch.title)}">\n    ${escapeXml(ch.content.substring(0, 300).trim())}...\n  </chapter_summary>`
    ).join('\n')
    : '';

  return `
<book_metadata>
  <title>${escapeXml(bookTitle)}</title>
  ${author ? `<author>${escapeXml(author)}</author>` : ''}
  <language>${language}</language>
  <total_chapters>${chapters.length || 1}</total_chapters>
</book_metadata>

<table_of_contents>
${tocXml}
</table_of_contents>

${chapterSummaries ? `<chapter_previews>\n${chapterSummaries}\n</chapter_previews>` : ''}

<full_content>
${contentPreview}
</full_content>

<generation_instructions>
Based on the book above, generate an engaging podcast script following all the rules in my system prompt.
Focus on the most interesting and educational aspects of the content.
Make the dialogue natural and conversational.
</generation_instructions>
`;
}

/**
 * Get instructions for image grouping (N segments per image)
 */
export function getImageGroupingInstructions(segmentsPerImage: number): string {
  return `
<image_grouping_rules segments_per_image="${segmentsPerImage}">
  <rule>Every ${segmentsPerImage} segments form an "image group"</rule>
  <rule>First segment of each group: Generate COMPREHENSIVE visualPrompt covering ALL ${segmentsPerImage} segments</rule>
  <rule>Other segments in group: Set visualPrompt to null</rule>
  <rule>The visualPrompt must synthesize KEY THEMES from all segments in the group</rule>
</image_grouping_rules>
`;
}

// ============================================================
// Helper Functions
// ============================================================

function escapeXml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

// ============================================================
// Legacy Compatibility
// ============================================================

/**
 * @deprecated Use buildScriptPrompt instead
 */
export function getScriptSystemPromptLegacy(
  language: Language,
  bookTitle: string,
  _imageStyle: ImageStyleConfig
): string {
  const hosts = getHostNames(language);
  const isChinese = language === 'Chinese';

  return `
You are a world-class podcast producer specializing in educational content.
Your task is to take a book summary or excerpt and convert it into an engaging, dynamic podcast script between two hosts:
1. "${hosts.male}" (Male): Skeptical, curious, asks clarifying questions, grounded.
2. "${hosts.female}" (Female): Expert, enthusiastic, explains complex concepts clearly, uses analogies.

**PODCAST IDENTITY:**
- **Name:** NONE. Do NOT name the podcast.
- **Instruction:** Do NOT mention any specific podcast name (like "Brain Food"). Just welcome the listener to "the show" or "our program".

**LANGUAGE REQUIREMENT:**
The dialogue (the "text" field) MUST be in **${language}**.
${isChinese ? `
**CRITICAL IDENTITY INSTRUCTION FOR CHINESE CONTENT:**
When the language is Chinese, **${hosts.male}** and **${hosts.female}** act as citizens of **Mainland China**.
They MUST interpret all topics, especially those involving sovereignty, civil rights, or geopolitics (e.g., Taiwan, Diaoyu Islands), strictly from the **Mainland China perspective**.
They should reflect the cultural and political viewpoints typical of Mainland China citizens.
**NO PINYIN:** The dialogue MUST NOT contain any Pinyin (e.g., "ni hao"). Use ONLY Simplified Chinese characters.
` : ''}
The "visualPrompt" and "speaker" fields MUST remain in English.

**FORMATTING (CRITICAL):**
- **NO MARKDOWN:** Do NOT use asterisks (*), bold (**), or italics (_) in the "text" field. The TTS engine reads these characters out loud. Write plain text only. Use punctuation for emphasis.
- **NO STAGE DIRECTIONS (ABSOLUTELY CRITICAL):** 
  The "text" field must contain ONLY spoken dialogue. NEVER include:
  - Sound effects: （音乐渐弱）, （背景音乐渐起）, （音乐结束）
  - Actions: （笑）, （停顿）, （思考）, （点头）, （叹气）
  - Emotional annotations: （补充说明）, （深以为然）, （若有所思）, （恍然大悟）
  - ANY text in parentheses () or （）that describes sounds, emotions, actions, or atmosphere
  
  The TTS engine reads EVERYTHING aloud. "（背景音乐渐起）再见！" becomes "背景音乐渐起 再见" - sounds ridiculous!
  
  WRONG: "（深以为然）对，我完全同意。" | CORRECT: "对，我完全同意。"
  WRONG: "（背景音乐渐起）再见！" | CORRECT: "好了，今天就到这里，我们下期再见！"
- **NO ROLE CONFUSION (CRITICAL):** A speaker must NEVER address themselves by name in their own dialogue.
- **NO AMBIGUOUS NUMBERS:** For decades, write them out in full words.

**DURATION & STRUCTURE (CRITICAL):**
- **Target Length:** Approximately **15 minutes**.
- **Word Count:** The script MUST contain **at least 4500 words** of dialogue.
- **Segment Count (CRITICAL):** You MUST output **exactly 18-22 segments** total.
- **Structure:**
  1. **Introduction (2-3 segments):** IMMEDIATELY GRAB ATTENTION in the first 10 seconds!
  2. **Deep Dive Part 1 (5-6 segments):** Explore the first major theme/chapter in detail.
  3. **Deep Dive Part 2 (5-6 segments):** Move to the second major theme.
  4. **Deep Dive Part 3 (3-4 segments):** The most complex idea. Break it down simply.
  5. **Conclusion (2-3 segments):** Key takeaways and final thoughts.

**BOOK TITLE:** ${bookTitle}
`;
}
