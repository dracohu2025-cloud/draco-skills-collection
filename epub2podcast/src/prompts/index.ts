/**
 * Prompts Module
 * 
 * Centralized prompt management with XML-structured templates.
 * All AI prompts are organized here by category.
 */

// Utilities
export {
    Language,
    LANGUAGE_CONFIG,
    getLanguageInstruction,
    getSlideLanguageInstruction,
    getHostNames,
    formatReferenceFilesXML,
    extractKeyPoint,
    combineSegmentTexts,
} from './utils.js';

// Script Generation
export {
    ScriptPromptParams,
    buildScriptPrompt,
    getScriptSystemPrompt,
    getImageGroupingInstructions,
    getScriptSystemPromptLegacy,
} from './script.js';

// Slide Generation (Banana Slides Style)
export {
    SlidePromptParams,
    getSlideGenerationPrompt,
    getSimpleSlidePrompt,
    getGroupSlidePrompt,
    getSlideRegenerationPrompt,
} from './slide.js';

// Marketing
export {
    getMarketingPrompt,
    getThumbnailPrompt,
} from './marketing.js';
