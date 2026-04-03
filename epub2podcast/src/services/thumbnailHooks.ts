/**
 * YouTube Thumbnail Hook Extraction Service
 * 
 * Extracts high-impact "hooks" from podcast scripts to generate
 * MrBeast-level CTR-optimized thumbnails.
 */

import { ScriptSegment } from '../types.js';
import { openrouterService } from './openrouterService.js';
import { sanitizeBookTitleForPrompt } from '../utils/titleSanitizer.js';

/**
 * Hook types that drive different visual strategies
 */
export type HookType =
    | 'controversy'  // 争议性观点 - uses red/black for urgency
    | 'mystery'      // 历史悬案 - uses deep blue/gold for intrigue
    | 'reveal'       // 揭秘真相 - uses yellow/black for attention
    | 'emotion'      // 情感高峰 - uses warm colors for connection
    | 'action'       // 战争/冲突 - uses red/orange for energy
    | 'wisdom';      // 哲理智慧 - uses gold/black for authority

/**
 * Color scheme optimized for YouTube CTR
 */
export interface ColorScheme {
    primary: string;      // Main background/accent color
    secondary: string;    // Supporting color
    textColor: string;    // Text overlay color (high contrast)
    textStroke: string;   // Text stroke/shadow for readability
    gradient?: string;    // Optional gradient direction
}

/**
 * Extracted hook data for thumbnail generation
 */
export interface HookData {
    type: HookType;
    text: string;           // Main title (Chinese ≤6 chars, English ≤4 words)
    subtitle: string;       // Subtitle providing context (Chinese ≤8 chars, English ≤5 words)
    visualConcept: string;  // English scene description for image generation
    colorScheme: ColorScheme;
    emotionalTone: string;  // e.g., "shock", "curiosity", "urgency"
    llmCost?: {             // LLM cost for hook extraction (optional)
        costUSD: number;
        tokens: number;
    };
}

/**
 * Predefined color schemes based on hook type
 * Inspired by MrBeast's high-CTR thumbnail aesthetics
 */
const COLOR_SCHEMES: Record<HookType, ColorScheme> = {
    controversy: {
        primary: '#FF0000',      // Vibrant red
        secondary: '#000000',    // Pure black
        textColor: '#FFFFFF',    // White text
        textStroke: '#000000',   // Black stroke
        gradient: 'radial'       // Radial gradient from center
    },
    mystery: {
        primary: '#1A1A2E',      // Deep navy
        secondary: '#FFD700',    // Gold
        textColor: '#FFD700',    // Gold text
        textStroke: '#000000',   // Black stroke
        gradient: 'linear-bottom'
    },
    reveal: {
        primary: '#FFD700',      // Bright gold/yellow
        secondary: '#000000',    // Black
        textColor: '#000000',    // Black text
        textStroke: '#FFFFFF',   // White stroke for pop
        gradient: 'radial'
    },
    emotion: {
        primary: '#FF6B35',      // Warm orange
        secondary: '#1A1A2E',    // Deep contrast
        textColor: '#FFFFFF',    // White text
        textStroke: '#000000',   // Black stroke
        gradient: 'linear-diagonal'
    },
    action: {
        primary: '#DC143C',      // Crimson red
        secondary: '#FF8C00',    // Dark orange
        textColor: '#FFFFFF',    // White text
        textStroke: '#000000',   // Black stroke
        gradient: 'diagonal-explosion'
    },
    wisdom: {
        primary: '#2C1810',      // Rich brown
        secondary: '#FFD700',    // Gold
        textColor: '#FFD700',    // Gold text
        textStroke: '#000000',   // Black stroke
        gradient: 'vignette'
    }
};

/**
 * Hook detection keywords for different types
 */
const HOOK_KEYWORDS = {
    controversy: {
        zh: ['争议', '颠覆', '错误', '谎言', '真相', '被骗', '误解', '推翻', '揭露', '隐瞒'],
        en: ['controversial', 'wrong', 'lie', 'truth', 'deceived', 'misunderstood', 'exposed', 'hidden']
    },
    mystery: {
        zh: ['悬案', '未解', '神秘', '消失', '谜团', '诡异', '离奇', '不可思议', '疑点'],
        en: ['mystery', 'unsolved', 'disappeared', 'enigma', 'bizarre', 'inexplicable', 'strange']
    },
    reveal: {
        zh: ['揭秘', '真相', '内幕', '秘密', '发现', '原来', '竟然', '背后', '鲜为人知'],
        en: ['reveal', 'secret', 'truth', 'behind', 'discover', 'actually', 'unknown', 'hidden']
    },
    emotion: {
        zh: ['悲剧', '牺牲', '感人', '泪目', '震撼', '心痛', '绝望', '希望', '奇迹'],
        en: ['tragedy', 'sacrifice', 'touching', 'tears', 'shocking', 'heartbreak', 'hope', 'miracle']
    },
    action: {
        zh: ['战争', '决战', '灭亡', '崩溃', '入侵', '反击', '血战', '突围', '覆灭'],
        en: ['war', 'battle', 'fall', 'collapse', 'invasion', 'fight', 'destruction', 'defeat']
    },
    wisdom: {
        zh: ['智慧', '哲理', '启示', '思考', '本质', '规律', '人性', '教训', '意义'],
        en: ['wisdom', 'philosophy', 'lesson', 'insight', 'essence', 'nature', 'meaning', 'truth']
    }
};

/**
 * Visual concept templates based on hook type
 */
const VISUAL_TEMPLATES: Record<HookType, string[]> = {
    controversy: [
        'A dramatic split-screen showing two opposing viewpoints with lightning between them',
        'A shattered monument or statue with cracks revealing light behind',
        'A person pointing accusingly with dramatic backlight'
    ],
    mystery: [
        'A shadowy figure silhouetted against a misty ancient backdrop',
        'An old document or map with a glowing mysterious symbol',
        'A locked chest or door with ethereal light seeping through cracks'
    ],
    reveal: [
        'A curtain being pulled back to reveal a shocking scene',
        'A magnifying glass revealing hidden details in a historical scene',
        'Light breaking through darkness, illuminating a hidden truth'
    ],
    emotion: [
        'A powerful moment of human connection or sacrifice',
        'A lone figure standing against a dramatic sunset or storm',
        'Hands reaching toward each other across a divide'
    ],
    action: [
        'An epic battle scene with dramatic lighting and motion blur',
        'A falling empire with crumbling architecture and fire',
        'A charging warrior or army with dynamic perspective'
    ],
    wisdom: [
        'An ancient sage or scholar in contemplation',
        'A book opening with golden light emanating',
        'A mountain peak with sunrise, symbolizing enlightenment'
    ]
};

/**
 * Generate provocative question templates based on hook type
 * Optimized for CTR without being clickbait
 */
function getQuestionTemplate(hookType: HookType, language: string): string[] {
    // Templates designed to be intriguing but honest - NOT clickbait
    const templates = {
        controversy: {
            zh: ['重新认识{X}', '{X}背后的博弈', '被误读的{X}'],
            en: ['Rethinking {X}', 'The Politics Behind {X}', 'Misunderstood {X}']
        },
        mystery: {
            zh: ['{X}的迷局', '{X}疑云', '解密{X}'],
            en: ['The {X} Enigma', 'Decoding {X}', 'Inside {X}']
        },
        reveal: {
            zh: ['深度解读{X}', '读懂{X}', '{X}全解析'],
            en: ['Deep Dive: {X}', 'Understanding {X}', '{X} Explained']
        },
        emotion: {
            zh: ['{X}的兴衰', '{X}沉浮录', '见证{X}'],
            en: ['Rise and Fall of {X}', 'The {X} Story', 'Witnessing {X}']
        },
        action: {
            zh: ['{X}风云', '{X}变局', '动荡中的{X}'],
            en: ['The {X} Upheaval', '{X} in Turmoil', 'Crisis of {X}']
        },
        wisdom: {
            zh: ['{X}的启示', '从{X}看今天', '品读{X}'],
            en: ['Lessons from {X}', '{X} and Today', 'Reflecting on {X}']
        }
    };

    return language === 'Chinese' ? templates[hookType].zh : templates[hookType].en;
}

/**
 * Use LLM to extract a compelling hook from the script
 * This generates hooks based on actual content, not just title templates
 */
async function extractHookWithLLM(
    script: ScriptSegment[],
    bookTitle: string,
    language: string,
    hookType: HookType
): Promise<{ hookText: string; subtitle: string; visualConcept: string; llmCost: { costUSD: number; tokens: number } }> {
    // Extract key content from script (first 3000 chars to stay within token limits)
    const scriptExcerpt = script.slice(0, 10).map(s => `${s.speaker}: ${s.text}`).join('\n').slice(0, 3000);

    const langInstruction = language === 'Chinese'
        ? `所有输出必须是中文。hookText 最多 8 个汉字，subtitle 最多 10 个汉字。`
        : `All output must be in English. hookText max 5 words, subtitle max 6 words.`;

    const hookStrategies: Record<HookType, string> = {
        controversy: '找出书中最具争议或颠覆认知的观点',
        mystery: '找出最神秘、未解之谜或令人好奇的悬念',
        reveal: '找出最令人惊讶的真相或内幕',
        emotion: '找出最感人或震撼人心的时刻',
        action: '找出最激烈的冲突、战争或转折点',
        wisdom: '找出最深刻的人生智慧或启示'
    };

    const prompt = `你是一位资深 YouTuber 和视觉设计专家，擅长制作高点击率 (CTR) 的 YouTube 缩略图。

分析以下播客脚本，提取一个最能激发观众点击欲望的"钩子"。

## 规则（严格遵守）：
1. **钩子必须来自脚本的真实内容**，不能编造
2. **不要简单复述书名**，书名是「${bookTitle}」
3. ${hookStrategies[hookType]}
4. 使用以下策略之一：
   - 设问：提出一个引发好奇的问题（如"如果秦朝没有灭亡？"）
   - 冲突：展示矛盾对立（如"商鞅：功臣还是罪人？"）
   - 悬念：暗示关键信息但不说破（如"历史遗漏的那一页"）
   - 人物决策：聚焦关键决策时刻（如"嬴政的两难选择"）
5. **绝对禁止**标题党词汇：震惊、99%的人不知道、居然、竟然、必看等
6. ${langInstruction}

## 脚本内容：
${scriptExcerpt}

## 输出格式（严格 JSON）：
{
  "hookText": "主标题文字（极短，吸引眼球）",
  "subtitle": "副标题（补充说明，增加点击欲望）",
  "visualConcept": "Describe in ENGLISH: A dramatic visual scene that matches the hook, cinematic quality, no text in scene"
}`;

    try {
        const result = await openrouterService.generateText(prompt, undefined, 'json');
        const parsed = JSON.parse(result.text);

        console.log(`[ThumbnailHooks] LLM extracted hook: "${parsed.hookText}" / "${parsed.subtitle}", Cost: $${result.cost?.totalUSD?.toFixed(4) || 0}`);

        return {
            hookText: parsed.hookText || bookTitle.slice(0, 6),
            subtitle: parsed.subtitle || '',
            visualConcept: parsed.visualConcept || VISUAL_TEMPLATES[hookType][0],
            // Include LLM cost for proper tracking
            llmCost: {
                costUSD: result.cost?.totalUSD || 0,
                tokens: result.usage?.totalTokens || 0
            }
        };
    } catch (error) {
        console.error('[ThumbnailHooks] LLM hook extraction failed:', error);
        // Fallback to old template method
        const questionTemplates = getQuestionTemplate(hookType, language);
        const template = questionTemplates[Math.floor(Math.random() * questionTemplates.length)];
        const shortTitle = extractShortSubject(bookTitle, language);

        return {
            hookText: template.replace('{X}', shortTitle),
            subtitle: generateSubtitle(hookType, bookTitle, language),
            visualConcept: VISUAL_TEMPLATES[hookType][0],
            // Fallback has no LLM cost
            llmCost: { costUSD: 0, tokens: 0 }
        };
    }
}

/**
 * Extract the most impactful hook from a podcast script
 */
export async function extractHookFromScript(
    script: ScriptSegment[],
    bookTitle: string,
    language: string
): Promise<HookData> {
    // Combine all script text for analysis
    const fullText = script.map(s => s.text).join(' ');

    // Score each hook type based on keyword matches
    const scores: Record<HookType, number> = {
        controversy: 0,
        mystery: 0,
        reveal: 0,
        emotion: 0,
        action: 0,
        wisdom: 0
    };

    const lang = language === 'Chinese' ? 'zh' : 'en';

    for (const [hookType, keywords] of Object.entries(HOOK_KEYWORDS)) {
        const langKeywords = keywords[lang as 'zh' | 'en'];
        for (const keyword of langKeywords) {
            const regex = new RegExp(keyword, 'gi');
            const matches = fullText.match(regex);
            if (matches) {
                scores[hookType as HookType] += matches.length;
            }
        }
    }

    // Find the dominant hook type
    let dominantType: HookType = 'reveal'; // Default fallback
    let maxScore = 0;

    for (const [type, score] of Object.entries(scores)) {
        if (score > maxScore) {
            maxScore = score;
            dominantType = type as HookType;
        }
    }

    // If no clear winner, analyze book title for clues
    if (maxScore === 0) {
        const titleLower = bookTitle.toLowerCase();
        if (titleLower.includes('战') || titleLower.includes('war') || titleLower.includes('battle')) {
            dominantType = 'action';
        } else if (titleLower.includes('秘') || titleLower.includes('secret') || titleLower.includes('hidden')) {
            dominantType = 'mystery';
        } else if (titleLower.includes('亡') || titleLower.includes('fall') || titleLower.includes('end')) {
            dominantType = 'action';
        } else {
            dominantType = 'reveal'; // Safe default for educational content
        }
    }

    console.log(`[ThumbnailHooks] Detected hook type: ${dominantType} (score: ${maxScore})`);

    // ============================================================
    // Use LLM to extract a compelling hook instead of static templates
    // ============================================================
    const llmHook = await extractHookWithLLM(script, bookTitle, language, dominantType);

    // Get color scheme based on detected hook type
    const colorScheme = COLOR_SCHEMES[dominantType];

    // Determine emotional tone
    const emotionalTones: Record<HookType, string> = {
        controversy: 'shock and disbelief',
        mystery: 'intrigue and curiosity',
        reveal: 'surprise and enlightenment',
        emotion: 'deep empathy and connection',
        action: 'intensity and urgency',
        wisdom: 'contemplation and insight'
    };

    return {
        type: dominantType,
        text: llmHook.hookText,
        subtitle: llmHook.subtitle,
        visualConcept: llmHook.visualConcept,
        colorScheme,
        emotionalTone: emotionalTones[dominantType],
        llmCost: llmHook.llmCost
    };
}

/**
 * Generate a compelling subtitle based on hook type
 * Provides additional context to make the thumbnail more intriguing
 */
function generateSubtitle(hookType: HookType, bookTitle: string, language: string): string {
    // Subtitle templates that add context and intrigue
    const subtitleTemplates: Record<HookType, { zh: string[]; en: string[] }> = {
        controversy: {
            zh: ['被隐藏的真相', '历史的另一面', '你不知道的内幕'],
            en: ['The Hidden Truth', 'The Other Side', 'What They Didn\'t Tell You']
        },
        mystery: {
            zh: ['历史的迷雾', '千年的疑问', '謎一样的往事'],
            en: ['Lost to History', 'An Ancient Mystery', 'The Untold Story']
        },
        reveal: {
            zh: ['古人的智慧', '被遗忘的历史', '全新视角'],
            en: ['Ancient Wisdom', 'Forgotten History', 'A Fresh Perspective']
        },
        emotion: {
            zh: ['人性的光辉', '历史的波澜', '千古的回音'],
            en: ['The Human Spirit', 'Echoes of History', 'Timeless Lessons']
        },
        action: {
            zh: ['帝国的命运', '权力的游戏', '改变历史的瞬间'],
            en: ['The Fate of Empires', 'The Power Struggle', 'History\'s Turning Point']
        },
        wisdom: {
            zh: ['经典的力量', '超越时代的智慧', '古今的对话'],
            en: ['Timeless Wisdom', 'Lessons for Today', 'Past Meets Present']
        }
    };

    const templates = language === 'Chinese' ? subtitleTemplates[hookType].zh : subtitleTemplates[hookType].en;
    return templates[Math.floor(Math.random() * templates.length)];
}

/**
 * Extract a short subject from the book title for hook text
 * Optimized to preserve meaning and avoid truncation
 */
function extractShortSubject(title: string, language: string): string {
    // Remove common prefixes/suffixes and metadata
    let cleaned = title
        .replace(/《|》|"|"/g, '')
        .replace(/\(.*?\)/g, '')
        .replace(/（.*?）/g, '')
        .replace(/--.*$/g, '')  // Remove everything after "--" (metadata)
        .replace(/_/g, '')       // Remove underscores
        .trim();

    if (language === 'Chinese') {
        // Split on common separators
        const parts = cleaned.split(/[：:，,——]/);
        const mainPart = parts[0].trim();

        // For short titles (≤6 chars), return as-is to avoid truncation
        // e.g., "危机与重构" (5 chars) should be kept complete
        if (mainPart.length <= 6) {
            return mainPart;
        }

        // For longer titles, try to extract a meaningful phrase
        // Pattern 1: "X与Y" - keep both parts (e.g., "危机与重构")
        const andMatch = mainPart.match(/^(.{2,4})[与和及](.{2,4})$/);
        if (andMatch) {
            return mainPart; // Keep the full "X与Y" pattern
        }

        // Pattern 2: "X的Y" or "X之Y" - extract the object Y
        const ofMatch = mainPart.match(/(.{2,6})[的之](.{2,4})/);
        if (ofMatch) {
            return ofMatch[2];
        }

        // Pattern 3: Extract dynasty/era names for history books
        const dynastyMatch = mainPart.match(/(唐|宋|元|明|清|汉|秦|晋|隋|周|战国|春秋)/);
        if (dynastyMatch) {
            // Try to get "唐朝" or just the dynasty character
            const dynastyIdx = mainPart.indexOf(dynastyMatch[1]);
            // Take up to 4 chars starting from dynasty
            return mainPart.slice(dynastyIdx, Math.min(dynastyIdx + 4, mainPart.length));
        }

        // Fallback: take first 5 chars (safer than 4 to avoid mid-word cuts)
        return mainPart.slice(0, 5);
    } else {
        // For English, take first 2-3 significant words
        const words = cleaned.split(/\s+/);
        const significantWords = words.filter(w =>
            !['the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for'].includes(w.toLowerCase())
        );
        return significantWords.slice(0, 3).join(' ');
    }
}

/**
 * Generate the complete thumbnail prompt using hook data
 */
export function generateThumbnailPrompt(
    hookData: HookData,
    bookTitle: string,
    language: string
): string {
    const { type, text, subtitle, visualConcept, colorScheme, emotionalTone } = hookData;
    const safeBookTitle = sanitizeBookTitleForPrompt(bookTitle);

    // Two-line text layout: main title (larger) + subtitle (smaller)
    const textInstruction = language === 'Chinese'
        ? `TWO-LINE TEXT OVERLAY:
   - LINE 1 (MAIN TITLE): "${text}" - MASSIVE, covering 25-30% of image width
   - LINE 2 (SUBTITLE): "${subtitle}" - Smaller (60% of main title size), positioned directly below
   - FONT: Bold Chinese brush-stroke style, SIMPLIFIED CHINESE only. NO English letters.
   - LAYOUT: Main title at top-left or center, subtitle directly below it`
        : `TWO-LINE TEXT OVERLAY:
   - LINE 1 (MAIN TITLE): "${text}" - MASSIVE, covering 25-30% of image width
   - LINE 2 (SUBTITLE): "${subtitle}" - Smaller (60% of main title size), positioned directly below
   - FONT: Bold impact-style font like Obelix Pro or Impact
   - LAYOUT: Main title at top-left or center, subtitle directly below it`;

    return `
=== YOUTUBE THUMBNAIL DIRECTIVE (MRBEAST-LEVEL CTR OPTIMIZATION) ===

**TOPIC THEME (DO NOT RENDER AS TEXT):** "${safeBookTitle}"
**HOOK TYPE:** ${type.toUpperCase()} - Evoking ${emotionalTone}

**MANDATORY TEXT OVERLAY (TWO LINES):**
${textInstruction}
- TOTAL TEXT AREA: Covering 35-45% of the image area
- POSITION: Rule of thirds intersection point (upper left or center)
- CONTRAST: Maximum contrast with background
- STYLE: 3D effect with drop shadow, slight bevel, or glow
- STROKE: Heavy ${colorScheme.textStroke} outline (3-5px) for readability
- MAIN TITLE COLOR: ${colorScheme.textColor}
- SUBTITLE COLOR: Slightly lighter or same as main title

**VISUAL SCENE:**
${visualConcept}
- Incorporate the core theme (NOT the literal book title text) into the scene
- The scene should instantly communicate "${emotionalTone}"
- Include a FOCAL POINT (person, object, or symbol) that draws the eye

**COLOR PALETTE (MANDATORY):**
- PRIMARY: ${colorScheme.primary} (dominant 60% of image)
- SECONDARY: ${colorScheme.secondary} (accent 30%)
- TEXT: ${colorScheme.textColor} with ${colorScheme.textStroke} stroke
- LIGHTING: Dramatic rim lighting and high contrast
- SATURATION: HIGH (avoid muted or grey tones)

**COMPOSITION RULES:**
1. Rule of thirds - main subject at power points
2. Leading lines directing to text or focal point
3. Depth through foreground blur or atmospheric haze
4. Dynamic angle (not flat, head-on shots)
5. Clear visual hierarchy: TEXT > SUBJECT > BACKGROUND

**QUALITY STANDARDS:**
- Resolution: Sharp, high-detail, suitable for 1280x720
- Style: Photorealistic or high-quality digital art (NOT cartoon/clipart)
- Lighting: Cinematic with dramatic shadows
- Overall: Must look like a AAA game screenshot or movie poster

**FORBIDDEN ELEMENTS:**
- No extra text besides the two required lines (no book title, author names, subtitles, or credits)
- No URLs, domain names, or source/mirror references (e.g. z-lib, 1lib, .sk, .rs)
- No parenthesis/bracketed text like "(...)" "（...）" "[...]" "【...】"
- No flat, solid color backgrounds
- No small or regular-weight text
- No centered, static, passport-photo compositions
- No dark, muted, grey, or washed-out colors
- No generic clip-art or icon-style graphics
- No horror, gore, or disturbing imagery
- No maps or infographics
- No text in the wrong language

**ASPECT RATIO:** 16:9 (YouTube standard)
`;
}

export default {
    extractHookFromScript,
    generateThumbnailPrompt,
    COLOR_SCHEMES,
    HOOK_KEYWORDS
};
