// Force rebuild
export interface ScriptSegment {
  speaker: 'Male' | 'Female';
  text: string;
  visualPrompt: string | object | null;
  startTime?: number;
  estimatedDuration?: number;
  generatedImageUrl?: string;
  htmlUrl?: string;  // For PPT style: URL to the original HTML source file
  imageGroup?: number;  // Segments with same imageGroup share one image (N segments per image)
  comicGroup?: number;  // Legacy: For panda_topdown style (deprecated, use imageGroup)
}

export interface MarketingAssets {
  title: string;
  description: string;
  thumbnailPrompt: string;
}

export interface SourceChapter {
  title: string;
  content: string;
  order?: number;
}

export interface ScriptGenerationContext {
  chapters?: SourceChapter[];
  totalWordCount?: number;
}

export interface UsageMetadata {
  script: {
    inputTokens: number;
    outputTokens: number;
    totalTokens: number;
    model?: string;
    provider?: string;
    costUSD?: number;  // OpenRouter real-time cost
  };
  marketing: {
    inputTokens: number;
    outputTokens: number;
    totalTokens: number;
    model?: string;
    provider?: string;
    costUSD?: number;
  };
  images: {
    count: number;
    inputTokens: number;
    outputTokens: number;
    totalTokens: number;
    model?: string;
    provider?: string;
    costUSD?: number;
  };
  tts: {
    provider: string;
    characterCount: number;
    model?: string;
  };
}

export type Language = 'English' | 'Chinese';

// API Provider for LLM/Image generation
// FORCED to openrouter only - no Gemini direct API allowed
export type ApiProvider = 'openrouter';

// Text generation model selection
export type TextModel = 'gemini-3-flash' | 'gemini-3-pro';

// Image style presets for podcast visuals
export type ImageStylePreset =
  | 'ink_wash'           // 水墨画
  | 'zelda_botw'         // Zelda: Breath of the Wild
  | 'pixel_art'          // Pixel Art
  | 'hearthstone'        // 炉石传说
  | 'witcher3'           // 巫师3
  | 'ghibli'             // 吉卜力
  | 'cute_hand_drawn'    // 手绘可爱
  | 'ppt'                // 智能幻灯片 (Gemini Image)
  | 'smart_ppt'          // 智能PPT (HTML+Puppeteer, 每段一图)
  | 'panda_infographic'  // 熊猫信息图
  | 'panda_infographic_v2' // 熊猫信息图V2 (自然语言prompt)
  | 'panda_comic'        // 熊猫漫画 (四格漫画)
  | 'panda_comic_jimeng' // 熊猫四格漫画-即梦 (使用即梦AI)
  // panda_topdown archived - no longer used
  | 'infographic_1pager' // 信息图概览 (只生成1张)
  | 'antv_infographic'   // AntV 信息图 (声明式信息图渲染)
  | 'general'            // 通用 (AI决定)
  | 'custom';            // 用户自定义

export interface ImageStyleConfig {
  preset: ImageStylePreset;
  customPrompt?: string; // Only used when preset is 'custom'
  segmentsPerImage?: number;  // N value: how many segments share one image (default: 4)
  pptModel?: string; // Optional: Specific model for PPT generation
  colorTheme?: string; // For 'smart_ppt': color theme ID (deep_blue, emerald_green, etc.)
}

// JSON Prompt Structure
export interface ImagePromptJSON {
  subject: {
    description: string | object;  // Can be string (legacy) or structured object
    main_elements?: string[];
    [key: string]: any;
  };
  style: {
    name: string;
    description: string;
    color_palette?: string | object | string[];  // Support structured color palette
    [key: string]: any;
  };
  composition: {
    aspect_ratio: string;
    framing?: string;
    lighting?: string;
    [key: string]: any;
  };
  constraints?: {
    negative_prompt?: string | string[];  // Support array format
    panda_rules?: string | string[];      // Support array format
    [key: string]: any;
  };
  text_overlay?: {
    content?: string;
    language?: string;
    style?: string;
    instructions?: string | object;  // Support structured instructions
    [key: string]: any;
  };
}
