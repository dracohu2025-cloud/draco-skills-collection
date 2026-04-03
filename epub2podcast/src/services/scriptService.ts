import { GoogleGenAI, Type } from '@google/genai';
import dotenv from 'dotenv';
import { ScriptSegment, ImageStyleConfig, ImagePromptJSON, ApiProvider, ScriptGenerationContext, SourceChapter } from '../types.js';
import { TEXT_MODEL, getImageStyleDefinition, getDefaultImageStyle, ImageStyleDefinition } from '../constants.js';
import { openrouterService } from './openrouterService.js';
import { extractHookFromScript, generateThumbnailPrompt, HookData } from './thumbnailHooks.js';
import { sanitizeBookTitleForPrompt } from '../utils/titleSanitizer.js';

dotenv.config();

const GEMINI_API_KEY = process.env.GEMINI_API_KEY || '';

/**
 * Convert Chinese format visualPrompt to FULL ENGLISH format
 * Strategy: Main body 100% English, Chinese text ONLY in end section
 * This prevents image models from accidentally rendering Chinese descriptions
 */
const convertChineseToEnglishDisplayText = (chinesePrompt: string): string => {
    // Type mapping
    const typeMap: Record<string, string> = {
        '关系图': 'relationship_map', '时间轴': 'timeline', '对比图': 'comparison',
        '流程图': 'flowchart', '概念图': 'concept_map', '层级图': 'hierarchy',
        '数据可视化': 'data_viz', '矩阵图': 'matrix', '韦恩图': 'venn',
        '因果图': 'cause_effect', '优缺点': 'pros_cons', '循环图': 'cycle',
        '金字塔': 'pyramid', '漏斗图': 'funnel'
    };

    // Direction mapping (Chinese to English)
    const directionMap: Record<string, string> = {
        '从左到右': 'left_to_right', '从上到下': 'top_to_bottom',
        '从右到左': 'right_to_left', '环形': 'circular',
        '左右分割': 'left_right_split', '上下分割': 'top_bottom_split'
    };

    // Size mapping
    const sizeMap: Record<string, string> = { '大': 'large', '中': 'medium', '小': 'small' };

    // Mood mapping
    const moodMap: Record<string, string> = {
        '中性': 'neutral', '正面': 'positive', '负面': 'negative', '混乱': 'chaos',
        '恐慌': 'panic', '恐惧': 'panic', '困苦': 'hardship', '释然': 'relief',
        '权力': 'power', '冲突': 'conflict', '专注': 'focused', '荣耀': 'glory',
        '痛苦': 'pain', '愤怒': 'angry', '无奈': 'helpless', '傲慢': 'arrogant',
        '羞愧': 'ashamed', '惊恐': 'terrified', '绝望': 'despair', '威严': 'majestic',
        '狼狈': 'disheveled'
    };

    // Extract fields using regex
    const extractField = (pattern: RegExp): string => {
        const match = chinesePrompt.match(pattern);
        return match ? match[1].trim() : '';
    };

    const typeValue = extractField(/【类型】([^\n【]+)/);
    const title = extractField(/【标题】([^\n【]+)/);
    const subtitle = extractField(/【副标题】([^\n【]+)/);
    const eraContext = extractField(/【时代背景】([^\n【]+)/);
    const culturalContext = extractField(/【文化背景】([^\n【]+)/);
    const direction = extractField(/- 方向[：:]([^\n]+)/);
    const elementCount = extractField(/- 元素数量[：:]([^\n]+)/);
    const background = extractField(/- 背景场景[：:]([^\n]+)/);
    const colorScheme = extractField(/【色彩方案】([^\n【]+)/);

    // Extract core elements
    const coreElementsMatch = chinesePrompt.match(/【核心元素】([\s\S]*?)(?=【元素关系|【色彩方案|$)/);
    const coreElements = coreElementsMatch ? coreElementsMatch[1].trim() : '';

    // Parse elements and build ENGLISH-ONLY descriptions
    const elementLabels: string[] = [];
    const convertedElements = coreElements.split('\n').filter(line => line.trim()).map((line, idx) => {
        // Parse: "1. [慈禧熊猫-宫廷版] (尺寸：大，情绪：威严) - 穿着华丽的清朝太后朝服..."
        const match = line.match(/(\d+)\.\s*\[?([^\]()]+)\]?\s*\(尺寸[：:]([^,，]+)[,，]\s*情绪[：:]([^)]+)\)\s*[-–—]\s*(.+)/);
        if (match) {
            const [, num, label, size, mood] = match;
            const englishSize = sizeMap[size.trim()] || 'medium';
            // Handle compound moods like "恐慌/狼狈"
            const moodParts = mood.trim().split(/[\/、]/);
            const englishMood = moodParts.map(m => moodMap[m.trim()] || 'neutral').join('/');
            // Clean label (remove 熊猫)
            const cleanLabel = label.trim().replace(/熊猫/g, '').trim();
            elementLabels.push(cleanLabel);
            // Build PURE ENGLISH element description
            return `${num}. Element_${num} (Size: ${englishSize}, Mood: ${englishMood}) - Panda character with appropriate historical clothing and accessories`;
        }
        return `${idx + 1}. Element_${idx + 1} (Size: medium, Mood: neutral) - Panda character`;
    }).join('\n');

    // Convert direction to English
    let englishDirection = direction;
    for (const [cn, en] of Object.entries(directionMap)) {
        if (direction.includes(cn)) {
            englishDirection = en;
            break;
        }
    }
    if (/[\u4e00-\u9fff]/.test(englishDirection)) {
        englishDirection = 'structured_layout'; // Fallback if still Chinese
    }

    // Build PURE ENGLISH prompt
    return `===【Infographic Description】===

【Type】${typeMap[typeValue] || 'comparison'}

【Era Context】Chinese historical period
【Cultural Context】Chinese

【Layout】
- Direction: ${englishDirection}
- Element Count: ${elementCount || elementLabels.length || '2'}
- Background Scene: Traditional Chinese architectural setting with appropriate historical elements

【Core Elements】
${convertedElements}

【Element Relationships】
Element_1 --> Element_2

【Color Scheme】Traditional Chinese color palette with imperial yellows and reds

===【CHINESE TEXT TO DISPLAY IN IMAGE】===
The following Chinese text should appear in the final image. Display ONLY these exact characters:

1. TITLE (large, top center): ${title}
${subtitle ? `2. SUBTITLE (smaller, below title): ${subtitle}` : ''}

Element labels (display near each element):
${elementLabels.map((label, i) => `- Element ${i + 1}: ${label}`).join('\n')}

CRITICAL: Only display the Chinese characters listed above. Do NOT add any other text.
Do NOT render any text that is not in this CHINESE TEXT section.

===【End Description】===`;
};

// Build the visual style instruction based on imageStyle config
const buildVisualStyleInstruction = (imageStyle: ImageStyleConfig, language: string, bookTitle: string): string => {
    let styleDefinition: ImageStyleDefinition | undefined;
    let stylePrompt: string;
    let styleConstraints: string;

    // ============================================================
    // SPECIAL HANDLING FOR INFOGRAPHIC_1PAGER (SINGLE IMAGE)
    // Generates ONE comprehensive infographic for the ENTIRE podcast
    // ============================================================
    if (imageStyle.preset === 'infographic_1pager') {
        styleDefinition = getImageStyleDefinition('infographic_1pager');
        stylePrompt = styleDefinition?.promptTemplate || '';
        styleConstraints = styleDefinition?.constraints || '';
        const styleName = styleDefinition?.nameZh || '信息图概览 (单页)';

        return `
**视觉指令 (单页信息图模式 - 特殊处理):**
- **FREQUENCY:** 只有第一个segment需要生成"visualPrompt"，其他segment的visualPrompt设为null或空字符串。
- **VARIETY (CRITICAL):** 你必须生成 **15-18个段落** (限制播客时长在15-20分钟内)。
- **STYLE (用户选择: ${styleName}):**
  ${stylePrompt}

  ${styleConstraints}

**单页信息图 visualPrompt 格式 (只在第一个segment生成):**

第一个segment的"visualPrompt"必须是一个**概括整本书所有关键内容的信息图描述**：

\`\`\`json
{
  "infographic_type": "SUMMARY_POSTER",
  "title": "${bookTitle}",
  "subtitle": "核心要点概览",
  "key_takeaways": [
    "要点1：书中最重要的核心观点",
    "要点2：第二个关键论点或发现",
    "要点3：第三个重要概念",
    "要点4：第四个关键信息",
    "要点5：可选的第五个要点"
  ],
  "visual_elements": [
    "中央主题图标或符号",
    "分支连线展示概念关系",
    "数据可视化（如有）",
    "书籍标题大字居中"
  ],
  "color_scheme": "${language === 'Chinese' ? '暖色调配中国红金点缀' : 'Professional warm tones'}",
  "layout": "poster_style_with_sections"
}
\`\`\`

**其他segment的visualPrompt:** 设为 null 或 ""（空字符串）

**关键规则:**
1. 整个播客只生成 **1张** 图片
2. 这张图片必须涵盖书籍的 **全部关键要点**
3. 不是场景插图，而是 **概括性海报/信息图**
4. 文字必须清晰可读，标题占画面 15-20%
`;
    }

    // ============================================================
    // SPECIAL HANDLING FOR PANDA INFOGRAPHIC V2 (NATURAL LANGUAGE)
    // Uses structured natural language instead of JSON format
    // ============================================================
    if (imageStyle.preset === 'panda_infographic_v2') {
        styleDefinition = getImageStyleDefinition('panda_infographic_v2');
        stylePrompt = styleDefinition?.promptTemplate || '';
        styleConstraints = styleDefinition?.constraints || '';
        const styleName = styleDefinition?.nameEn || 'Panda Infographic V2';

        // V2 Strategy: Gemini generates CHINESE format, then we post-process to separate Chinese text list
        return `
**VISUAL INSTRUCTIONS (CRITICAL - 中文结构化描述格式):**
- **FREQUENCY:** Change the "visualPrompt" every **45-60 seconds** of dialogue (one segment = one unique visualPrompt).
- **VARIETY (CRITICAL):** You MUST generate **exactly 18-22 unique segments** for the entire episode.
- **STYLE (USER SELECTED: ${styleName}):**
  ${stylePrompt}

  ${styleConstraints}

- **FORBIDDEN CONTENT (STRICT):**
  - **NO REALISTIC HUMANS:** Use **PANDA characters** for all human representations.
  - **NO MAPS:** Absolutely NO maps or geographical representations.
  - **NO MODERN ELEMENTS:** In historical topics, ensure no modern buildings, clothes, or technology appear.

**VISUAL PROMPT FORMAT (CRITICAL - 使用中文结构化描述):**

The "visualPrompt" field MUST be a STRUCTURED string in the following CHINESE format.
We will post-process this to extract Chinese text labels for precise rendering.

Use this EXACT format for EVERY visualPrompt:

===【信息图描述】===

【类型】[选择: 关系图 / 时间轴 / 对比图 / 流程图 / 概念图 / 层级图 / 数据可视化 / 矩阵图 / 韦恩图 / 因果图 / 优缺点 / 循环图 / 金字塔 / 漏斗图]
【标题】简短中文标题 (最多6个汉字，高对比度，大字体)
【副标题】中文副标题 (可选)

【时代背景】[如: 清朝 1900年]
【文化背景】[选择: 中国 / 西方 / 日本 / 罗马 / 希腊 / 埃及]

【布局】
- 方向: [从左到右 / 从上到下 / 从右到左 / 环形]
- 元素数量: [数字]
- 背景场景: [场景描述，禁止地图]

【核心元素】
1. [元素标签] (尺寸：大/中/小, 情绪：中性/正面/负面/混乱/恐慌/困苦/释然/权力/冲突) - 视觉描述
2. [第二个元素标签] (尺寸，情绪) - 描述
3. [继续列出...]

【元素关系 - Mermaid Edge List】
\`\`\`mermaid
元素A -->|关系| 元素B
元素B -->|关系| 元素C
\`\`\`

【色彩方案】[色彩描述]
【语言要求】所有文字必须使用简体中文

===【描述结束】===

**MERMAID EDGE LIST SYNTAX (CRITICAL for arrows):**
- Use Mermaid flowchart syntax: 元素A -->|关系| 元素B
- Arrow points FROM actor TO target
- Keep edge labels SHORT (max 4 Chinese characters)

**MOVEMENT & DIRECTION RULES (CRITICAL):**
- **Physical Movement** (Flee, Attack): The visual arrow MUST point TOWARDS the destination.
- **Character Facing**: Characters in movement MUST face/move TOWARDS the arrow's target.

**NODE CONSISTENCY RULE (CRITICAL):**
- **EXACT NAME MATCHING**: Node names in Mermaid MUST be **IDENTICAL** to Core Elements labels.
- **NO ABSTRACT CONCEPTS**: Do not use "战争" or "历史" as nodes. Use visual element names.

**NO AUTO-GENERATED TEXT (CRITICAL):**
- ONLY render text from the 【标题】, 【副标题】, and 【核心元素】标签.
- DO NOT add random decorative text.
- PREVENT HALLUCINATIONS: No pseudo-characters allowed.

**FIRST IMAGE (YouTube Thumbnail Style - CRITICAL):**
- Title MUST be SHORT (MAX 6 Chinese characters), MASSIVE, HIGH CONTRAST
${language === 'Chinese' ? '- **CRITICAL:** ABSOLUTELY NO ENGLISH TEXT IN FINAL IMAGE. NO PSEUDO-CHARACTERS.' : ''}

**OUTPUT TYPE:** The visualPrompt MUST be a plain STRING containing the Chinese format above, NOT a JSON object.
`;
    }

    // ============================================================
    // SPECIAL HANDLING FOR PANDA_COMIC_JIMENG (即梦4格漫画)
    // Uses Chinese-native prompt structure optimized for JiMeng SeeDream API
    // ============================================================
    if (imageStyle.preset === 'panda_comic_jimeng') {
        styleDefinition = getImageStyleDefinition('panda_comic_jimeng');
        stylePrompt = styleDefinition?.promptTemplate || '';
        styleConstraints = styleDefinition?.constraints || '';
        const styleName = styleDefinition?.nameZh || '熊猫四格漫画-即梦';

        return `
**视觉指令 (即梦4格漫画专用格式 - 中文优化):**
- **频率:** 每45-60秒对话对应一个新的"visualPrompt" (每段落一个唯一的visualPrompt)。
- **数量:** 你必须生成 **18-22个唯一段落**。
- **风格 (用户选择: ${styleName}):**
  ${stylePrompt}

  ${styleConstraints}

- **严格禁止:**
  - **禁止真人面孔:** 所有人物必须是 **拟人化熊猫**。
  - **禁止地图:** 绝对不要生成地图或地理图表。
  - **禁止现代元素:** 历史主题中不能出现现代建筑、服装或科技产品。

**即梦4格漫画 visualPrompt 格式 (必须严格遵守):**

"visualPrompt" 字段必须是一个结构化 JSON 对象，包含以下字段。
**切勿使用信息图表字段如 "infographic_type", "relationships", "arrow_edges"。**

**必需的 JSON 结构:**
\`\`\`json
{
  "title": "漫画标题 (最多6个汉字)",
  "subtitle": "可选副标题",
  "era_context": "唐朝/宋朝/明朝/清朝等 (必须用中文)",
  "main_character": {
    "name": "角色名称或称呼",
    "appearance": "圆脸熊猫，黑白毛发分明，身形修长",
    "clothing": "具体朝代服装描述（如：圆领袍配幞头）",
    "accessories": "配饰描述（如：玉佩腰带）"
  },
  "panels": [
    {
      "panel_number": 1,
      "scene": "唐朝长安城长安西市，繁华街道，商铺林立",
      "action": "主角熊猫站在茶摊前，手捧茶碗，好奇地观察周围",
      "expression": "眼睛圆睁，嘴角微扬，好奇的表情"
    },
    {
      "panel_number": 2,
      "scene": "茶摊内部，木质桌椅，茶壶冒着热气",
      "action": "主角与老板熊猫交谈，手指着一卷竹简",
      "expression": "专注、若有所思的表情"
    },
    {
      "panel_number": 3,
      "scene": "画面转折场景",
      "action": "角色的关键动作",
      "expression": "惊讶、发现的表情"
    },
    {
      "panel_number": 4,
      "scene": "结尾场景",
      "action": "角色的总结性动作",
      "expression": "满意、思考的表情"
    }
  ],
  "cultural_context": "chinese"
}
\`\`\`

**字段说明 (全部使用中文):**
- "title": 6字以内的中文标题
- "era_context": **必须用中文朝代名**（唐朝、宋朝、明朝、清朝、汉朝等），禁止使用英文如 "Tang Dynasty"
- "main_character": 主角形象描述，**四格中必须保持一致**
- "panels": 四格内容，每格包含 scene(场景)、action(动作)、expression(表情)
- "scene": 具体场景描述，包含朝代元素的建筑和道具
- "action": 角色的具体动作描述
- "expression": 角色的具体表情描述

**🐼 角色一致性规则 (关键):**
- 同一角色在四格中服装、配饰必须完全一致
- main_character 定义后，在每个 panel 的 action 中重复使用相同的服装描述
- 禁止功夫熊猫Po的形象（胖墩墩、绿眼睛、肚兜）

**🏛️ 历史准确性 (重要):**
- 服装必须符合 era_context 指定朝代的历史考证
- 建筑风格必须符合该朝代特征
- 道具必须是该朝代实际存在的物品

**第一张图 (封面风格):**
- 第一个段落的 visualPrompt 必须代表**书籍的核心主题**
- 标题必须**大而醒目**，最多6个汉字
- **绝对禁止任何伪汉字或乱码文字**

**输出类型:** visualPrompt 必须是上述 JSON 对象格式，不是信息图表格式。
`;
    }

    // ============================================================
    // SPECIAL HANDLING FOR PANDA_COMIC (4-Panel Comic / 四格漫画)
    // Uses simple panels structure instead of complex infographic schema
    // ============================================================
    if (imageStyle.preset === 'panda_comic') {
        styleDefinition = getImageStyleDefinition('panda_comic');
        stylePrompt = styleDefinition?.promptTemplate || '';
        styleConstraints = styleDefinition?.constraints || '';
        const styleName = styleDefinition?.nameEn || 'Panda Comic';

        return `
**VISUAL INSTRUCTIONS (CRITICAL - 4格漫画专用格式):**
- **FREQUENCY:** Change the "visualPrompt" every **45-60 seconds** of dialogue (one segment = one unique visualPrompt).
- **VARIETY (CRITICAL):** You MUST generate **exactly 18-22 unique segments** for the entire episode.
- **STYLE (USER SELECTED: ${styleName}):**
  ${stylePrompt}

  ${styleConstraints}

- **FORBIDDEN CONTENT (STRICT):**
  - **NO REALISTIC HUMANS:** Use **PANDA characters** for all human representations.
  - **NO MAPS:** Absolutely NO maps or geographical representations.
  - **NO MODERN ELEMENTS:** In historical topics, ensure no modern buildings, clothes, or technology appear.

**4格漫画 VISUAL PROMPT FORMAT (CRITICAL - READ CAREFULLY):**

The "visualPrompt" field MUST be a structured JSON object with SIMPLE 4-panel comic structure.
DO NOT use infographic fields like "infographic_type", "relationships", "arrow_edges", or "node_labels".

**LANGUAGE RULES (CRITICAL - HYBRID APPROACH):**
- "scene", "characters", "mood" fields: Use ENGLISH for descriptions, BUT use SIMPLIFIED CHINESE for any text that should APPEAR in the image (book titles, scroll text, dynasty names, place names, signs, etc.)
- "title", "subtitle", "dialogue" fields: Use Chinese (these ARE displayed text)

**⚠️ IMPORTANT: TEXT TO DISPLAY IN IMAGE RULE (CRITICAL) ⚠️**
- When describing text that should APPEAR VISUALLY in the image (e.g., book titles, scroll names, dynasty names, store signs):
  - ❌ WRONG: "holding the book 'East Jin Dynasty Gatekeeper Politics'" (English translation will NOT render correctly)
  - ❌ WRONG: "holding the book 'Dong Jin Men Fa Zheng Zhi'" (Pinyin will NOT render correctly)
  - ✅ CORRECT: "holding the book '东晋门阀政治'" (Simplified Chinese will render correctly)
- When describing a dynasty transition:
  - ❌ WRONG: "transition from Jin to Liu Song Dynasty" (AI cannot render this correctly)
  - ✅ CORRECT: "transition from '晋' to '刘宋' Dynasty" (Simplified Chinese for displayed text)

**REQUIRED STRUCTURE:**
\`\`\`json
{
  "title": "漫画标题 (最多6个汉字)",
  "subtitle": "可选副标题",
  "panels": [
    {
      "panel_number": 1,
      "scene": "Tang Dynasty palace hall with golden throne and red silk curtains",
      "characters": "Chancellor Li Linfu panda wearing purple official robe, smiling cunningly",
      "mood": "intrigue, tense atmosphere",
      "dialogue": "可选：气泡中的对话文字"
    },
    {
      "panel_number": 2,
      "scene": "Scene background description in ENGLISH",
      "characters": "Panda reading the book '红楼梦' with thoughtful expression",
      "mood": "emotional atmosphere in ENGLISH"
    },
    {
      "panel_number": 3,
      "scene": "A scroll unrolling showing the transition from '晋' to '刘宋' era",
      "characters": "Historical panda scholar pointing at the scroll",
      "mood": "turning point emotion"
    },
    {
      "panel_number": 4,
      "scene": "Library with bookshelves",
      "characters": "Modern panda reader holding the book '东晋门阀政治', looking enlightened",
      "mood": "resolution emotion"
    }
  ],
  "era_context": "Tang Dynasty Tianbao period",
  "cultural_context": "chinese"
}
\`\`\`

**4格叙事结构 (CRITICAL):**
- **Panel ①**: Setup - introduce scene and characters
- **Panel ②**: Development - advance the plot
- **Panel ③**: Twist - climax or turning point
- **Panel ④**: Conclusion - resolution or punchline

**FIELD DESCRIPTIONS (HYBRID - ENGLISH + CHINESE FOR DISPLAY TEXT):**
- "scene" describes **BACKGROUND ENVIRONMENT** in English; use Simplified Chinese ONLY for text that should APPEAR in scene (signs, scrolls, banners)
- "characters" describes **CHARACTER ACTIONS** in English; use Simplified Chinese ONLY for text visible on objects characters hold/interact with (book titles, documents)
- "mood" describes **EMOTIONAL ATMOSPHERE** in English: tense, joyful, sad, angry

**⚠️ CRITICAL: TEXT IN DECORATIVE ELEMENTS (THE TYPOGRAPHER) ⚠️**
Image generation models CANNOT accurately render Chinese characters. Therefore:
- **NEVER describe text content on scrolls, documents, stone tablets, banners, signs, or any props**
- **FORBIDDEN phrases:** "scroll showing names...", "document with text...", "sign reading..."
- **CORRECT phrases:** "official scroll with blurred ink patterns", "stone tablet with weathered abstract markings", "banner with geometric motif"

**🏛️ HISTORICAL ACCURACY (THE HISTORIAN) 🏛️**
- **CLOTHING**: Do NOT use generic terms like "ancient clothes". Use SPECIFIC terms based on \`era_context\` (the era of the story).
  - Example (Tang): "Round-collar robe (yuanlingpao) with futou hat"
  - Example (Song): "Straight-collar robe (zhiduo) with scholarly square hat"
  - Example (Qing): "Magua jacket with braided queue hairstyle"
- **ARCHITECTURE**: Describe specific architectural features (e.g., "dougong brackets", "curved roof eaves").
- **OBJECTS**: Ensure objects are period-appropriate (No glasses/phones/modern paper).

**🐼 CHARACTER CONSISTENCY (CRITICAL) 🐼**
- **REUSE VISUAL TRAITS**: You MUST use the SAME visual descriptors for the same character in EVERY panel.
  - BAD: "Li Linfu smiles" (Panel 2), "The Chancellor looks angry" (Panel 3) -> result: different designs
  - GOOD: "Li Linfu (fat panda in purple robe) smiles" (Panel 2), "Li Linfu (fat panda in purple robe) looks angry" (Panel 3) -> result: consistent design
- **DEFINE ONCE, REPEAT ALWAYS**: Pick a specific look (e.g., "blue hoodie", "red bow", "golden armor") and REPEAT it every time the character appears.

**🎬 VISUAL METAPHORS (THE DIRECTOR) 🎬**
- **NO MAPS**: Maps are always historically inaccurate in AI generation.
- **NO COMPASS ROSES/DIRECTION LABELS**: NEVER ask for "East/West/North/South" text or compass symbols.
- **USE METAPHORS**: Instead of a map, use objects that imply the concept:
  - **Strategy/Territory** -> "A Go (Weiqi) board with black and white stones", "A bronze tiger tally"
  - **Travel/Distance** -> "A pair of worn straw sandals", "A flying messenger pigeon", "A horse saddle"
  - **Wealth/Taxation** -> "Strings of copper coins (guan)", "Silver ingots", "Grain sacks", "Abacus (suanpan)"
  - **Power** -> "Official seal (yinzhang)", "Ceremonial scepter (ruyi)"

**FIRST IMAGE (YouTube Thumbnail Style - CRITICAL):**
- The visualPrompt for the very first segment MUST represent the **book's CORE THEME**
- Title must be SHORT (MAX 6 ${language === 'Chinese' ? 'Chinese characters' : 'English words'}), MASSIVE, HIGH CONTRAST
${language === 'Chinese' ? '- **CRITICAL:** ABSOLUTELY NO ENGLISH TEXT IN DISPLAYED TITLE. ABSOLUTELY NO PSEUDO-CHARACTERS.' : ''}

**OUTPUT TYPE:** The visualPrompt MUST be a JSON object with the panels structure above, NOT an infographic structure.
`;
    }

    if (imageStyle.preset === 'custom' && imageStyle.customPrompt) {
        // Custom style from user
        stylePrompt = imageStyle.customPrompt;
        styleConstraints = `CRITICAL CONSTRAINTS for Custom style:
      - Follow the user's style description closely
      - Maintain visual consistency across ALL images in the podcast
      - NO realistic human faces, use stylized or silhouette representations
      - NO maps or geographical charts - they are always inaccurate`;
    } else if (imageStyle.preset === 'general') {
        // General style - AI decides
        stylePrompt = "General Style (AI Decides). You MUST determine the most appropriate visual style for EACH segment individually based on the content/mood.";
        styleConstraints = `CRITICAL CONSTRAINTS for General style:
      - You MUST explicitly describe the visual style for EACH segment in the "visualPrompt" (e.g., "A watercolor painting of...", "A pixel art depiction of...", "A photorealistic image of...").
      - Do NOT default to a single style unless it fits the entire narrative.
      - Ensure the style chosen fits the specific mood and content of the segment.
      - NO realistic human faces (unless the specific style allows it, but generally avoid for consistency).
      - NO maps or geographical charts.`;
    } else {
        // Predefined style
        styleDefinition = getImageStyleDefinition(imageStyle.preset);
        if (!styleDefinition) {
            // Fallback to default based on language
            styleDefinition = getImageStyleDefinition(getDefaultImageStyle(language));
        }
        stylePrompt = styleDefinition?.promptTemplate || 'Modern infographic style';
        styleConstraints = styleDefinition?.constraints || '';
    }

    const styleName = styleDefinition?.nameEn || 'Custom';

    return `
**VISUAL INSTRUCTIONS (CRITICAL - STRUCTURED JSON FORMAT):**
- **FREQUENCY:** Change the "visualPrompt" every **45-60 seconds** of dialogue (one segment = one unique visualPrompt).
- **VARIETY (CRITICAL):** You MUST generate **exactly 18-22 unique segments** for the entire episode.
- **STYLE (USER SELECTED: ${styleName}):**
  Every visualPrompt MUST follow this style:
  ${stylePrompt}

  ${styleConstraints}

- **FORBIDDEN CONTENT (STRICT):**
  - **NO REALISTIC HUMANS:** Use **PANDA characters** for Chinese content, or silhouettes for other styles.
  - **NO MAPS:** Absolutely NO maps or geographical representations.
  - **NO MODERN ELEMENTS:** In historical topics, ensure no modern buildings, clothes, or technology appear.

**STRUCTURED VISUAL PROMPT FORMAT (CRITICAL - READ CAREFULLY):**

The "visualPrompt" field MUST be a structured JSON object, NOT a free-form text string.

**REQUIRED STRUCTURE:**
\`\`\`json
{
  "infographic_type": "timeline" | "relationship_map" | "comparison" | "flowchart" | "concept_map" | "hierarchy" | "data_viz" | "process_diagram" | "matrix" | "venn_diagram" | "geographic_map" | "cause_effect" | "pros_cons" | "cycle_diagram" | "pyramid" | "funnel" | "network_graph",
  "title": "Main title in ${language}",
  "subtitle": "Optional subtitle",
  "layout": {
    "direction": "left_to_right" | "top_to_bottom" | "right_to_left" | "circular",
    "sections": 3,
    "background_scene": "Optional abstract scene description - MUST NOT include real-world maps, geographic locations, or city names. Use symbolic/metaphorical scenes instead (e.g., 'coastal battlefield scene with ships and fortifications' NOT 'Map of China coast')"
  },
  "elements": [
    {
      "position": 1,
      "label": "First event/node label in ${language}",
      "icon": "descriptive_icon_name",
      "mood": "neutral" | "positive" | "negative" | "chaos" | "panic" | "hardship" | "relief" | "power" | "conflict",
      "size": "small" | "medium" | "large"
    }
    // ... more elements
  ],
  "relationships": [  // CRITICAL for relationship_map!
    {
      "from": "源元素标签",
      "to": "目标元素标签",
      "label": "关系描述 (e.g., 控制, 依赖, 图谋)"
    }
  ],
  "color_scheme": "e.g., imperial red and gold",
  "era_context": "e.g., Qing Dynasty 1900",
  "cultural_context": "chinese" | "western" | "japanese" | "roman" | "greek" | "egyptian" | "other"
}
\`\`\`

**RELATIONSHIPS (CRITICAL for relationship_map - 关系必须明确):**
- For "relationship_map" type, you MUST include the "relationships" array
- Each relationship defines: WHO does WHAT to WHOM
- The "from" field is the ACTOR (who initiates the action)
- The "to" field is the TARGET (who receives the action)
- Example: 日本 controls 朝鲜 → { "from": "日本", "to": "朝鲜", "label": "控制" }
- Example: 朝鲜 fears 日本 → { "from": "朝鲜", "to": "日本", "label": "畏惧" }
- **WRONG:** Saying "朝鲜" plots against "日本" when historically it was the OTHER WAY AROUND

**INFOGRAPHIC TYPE SELECTION (CRITICAL - Choose the RIGHT type):**
- **Sequential Events (e.g., 八国联军进京 → 仓皇出逃 → 西行):** Use "timeline" with "left_to_right" direction
- **Character Relationships:** Use "relationship_map" with "relationships" array to define connections
- **Before/After or Opposing Ideas:** Use "comparison" with 2 sections
- **Cause and Effect (linear, A causes B causes C):** Use "flowchart" with "top_to_bottom" or "left_to_right" direction
- **Vicious Cycle / Feedback Loop (恶性循环, e.g., A→B→C→D→A):** Use "flowchart" with "circular" direction OR use "cycle_diagram"
- **Core Concept with Related Ideas:** Use "concept_map"
- **Closed Loop Process (must return to start):** Use "cycle_diagram" (always circular, A→B→C→A)

**DIRECTION SELECTION RULES:**
- "left_to_right": For timelines, sequential processes, East-to-West concepts
- "top_to_bottom": For hierarchies, cause-effect chains, North-to-South concepts
- "right_to_left": For reverse timelines, West-to-East concepts
- **"circular"**: ONLY for closed loops where the LAST element connects back to the FIRST
  - Example: 恶性循环 (vicious cycle), 生态循环, 经济循环
  - Use when: The process repeats indefinitely (A→B→C→D→A→B→...)

**EXAMPLE - Relationship Map for 朝鲜局势:**
\`\`\`json
{
  "infographic_type": "relationship_map",
  "title": "朝鲜局势",
  "subtitle": "太上皇的错觉",
  "layout": {
    "direction": "circular",
    "sections": 4,
    "background_scene": "Korean political theater with court and diplomatic setting"
  },
  "elements": [
    {"position": 1, "label": "袁世凯", "icon": "panda_general_arrogant", "mood": "power", "size": "large"},
    {"position": 2, "label": "朝鲜王室", "icon": "panda_king_scared", "mood": "panic", "size": "medium"},
    {"position": 3, "label": "日本公使", "icon": "panda_diplomat_scheming", "mood": "negative", "size": "medium"}
  ],
  "relationships": [
    {"from": "袁世凯", "to": "朝鲜王室", "label": "控制"},
    {"from": "日本公使", "to": "朝鲜王室", "label": "图谋/渗透"},
    {"from": "朝鲜王室", "to": "日本公使", "label": "畏惧/依赖"}
  ],
  "color_scheme": "royal purple and black",
  "era_context": "Korea 1890s",
  "cultural_context": "chinese"
}
\`\`\`

**EXAMPLE - Timeline for 庚子国难:**
\`\`\`json
{
  "infographic_type": "timeline",
  "title": "帝国崩塌",
  "subtitle": "太后西奔：帝国晚期的仓皇与激荡",
  "layout": {
    "direction": "left_to_right",
    "sections": 4,
    "background_scene": "burning Forbidden City transitioning to mountain path"
  },
  "elements": [
    {"position": 1, "label": "八国联军进京", "icon": "soldiers_at_gate", "mood": "chaos", "size": "large"},
    {"position": 2, "label": "仓皇出逃", "icon": "panda_empress_fleeing", "mood": "panic", "size": "large"},
    {"position": 3, "label": "西行之路", "icon": "mountain_path_hardship", "mood": "hardship", "size": "medium"},
    {"position": 4, "label": "抵达西安", "icon": "xi_an_city_gate", "mood": "relief", "size": "medium"}
  ],
  "color_scheme": "earth tones with fire orange accents",
  "era_context": "Qing Dynasty 1900",
  "cultural_context": "chinese"
}
\`\`\`

- **FIRST IMAGE (YouTube Thumbnail Style - CRITICAL):**
  - The visualPrompt for the very first segment MUST represent the **book's CORE THEME**
  - Use "concept_map" or "comparison" type for maximum visual impact
  - Title must be SHORT (MAX 6 ${language === 'Chinese' ? 'Chinese characters' : 'English words'}), MASSIVE, HIGH CONTRAST
  ${language === 'Chinese' ? '- **CRITICAL:** ABSOLUTELY NO ENGLISH TEXT. ABSOLUTELY NO PSEUDO-CHARACTERS.' : ''}

**=== IMAGE GROUPING MECHANISM (N=4) - CRITICAL ===**

To optimize costs, multiple segments share ONE image. Follow these rules:

1. **GROUPING:** Every 4 consecutive segments form an "image group" (segments 0-3 = group 0, segments 4-7 = group 1, etc.)

2. **visualPrompt PLACEMENT:**
   - **Segment 0, 4, 8, 12, 16...** (first of each group): Generate a COMPREHENSIVE visualPrompt that covers ALL 4 segments' content
   - **Segment 1-3, 5-7, 9-11, 13-15, 17-19...** (non-first of each group): Set visualPrompt to null

3. **COMPREHENSIVE REQUIREMENT:**
   The visualPrompt for the first segment of each group must:
   - Synthesize the KEY THEMES from all 4 segments in that group
   - NOT just describe the first segment's content alone
   - Create a scene/infographic that represents the group's collective narrative

**EXAMPLE:**
- If segments 0-3 discuss: (0) Book Introduction, (1) Author Background, (2) Historical Context, (3) Main Thesis
- Then segment 0's visualPrompt should be: "Comprehensive infographic showing book title prominently, author portrait, historical timeline background, and thesis statement icons - covering all aspects of the book's introduction section"
- Segments 1-3's visualPrompt should be: null
`;
};

function isStrictPodcastMode(imageStyle: ImageStyleConfig): boolean {
    return imageStyle.preset === 'smart_ppt' || imageStyle.preset === 'antv_infographic';
}

function estimateSegmentDurationSeconds(text: string, language: string): number {
    if (!text) return 0;
    const isChinese = language === 'Chinese';
    if (isChinese) {
        const chars = text.replace(/\s+/g, '').length;
        return chars / 5.0;
    }
    const words = text.trim().split(/\s+/).filter(Boolean).length;
    return words / 2.6;
}

function summarizeChapterSnippet(chapter: SourceChapter, maxChars: number = 6000): string {
    const cleaned = (chapter.content || '').replace(/\s+/g, ' ').trim();
    if (cleaned.length <= maxChars) return cleaned;
    const head = cleaned.slice(0, Math.floor(maxChars * 0.55));
    const tail = cleaned.slice(-Math.floor(maxChars * 0.3));
    return `${head}\n...[中间章节内容省略]...\n${tail}`;
}

function buildBookContentForPrompt(text: string, context: ScriptGenerationContext | undefined): string {
    const chapters = (context?.chapters || []).filter(ch => ch?.content && ch.content.trim().length > 200);
    if (!chapters.length) {
        return text.substring(0, 200000);
    }

    const outline = chapters.map((ch, idx) => `${idx + 1}. ${ch.title || `Section ${idx + 1}`}`).join('\n');
    const maxSamples = Math.min(8, chapters.length);
    const sampledIndexes = new Set<number>();
    for (let i = 0; i < maxSamples; i++) {
        const idx = Math.round((i * (chapters.length - 1)) / Math.max(1, maxSamples - 1));
        sampledIndexes.add(idx);
    }
    sampledIndexes.add(0);
    sampledIndexes.add(chapters.length - 1);

    const orderedIndexes = Array.from(sampledIndexes).sort((a, b) => a - b);
    const chapterSamples = orderedIndexes.map(idx => {
        const ch = chapters[idx];
        return `### Chapter ${idx + 1}: ${ch.title || `Section ${idx + 1}`}\n${summarizeChapterSnippet(ch)}`;
    }).join('\n\n');

    const promptPayload = `BOOK OVERVIEW\nTitle: ${context?.totalWordCount ? `Approx source words/chars: ${context.totalWordCount}` : 'Unknown length'}\nChapters: ${chapters.length}\n\nFULL CHAPTER OUTLINE\n${outline}\n\nCOVERAGE REQUIREMENT\nYou must cover the book broadly rather than focusing only on the opening chapters. Draw material from the beginning, middle, and end of the book. Mention multiple distinct chapters/themes/objects from across the outline.\n\nREPRESENTATIVE CHAPTER EXCERPTS\n${chapterSamples}`;

    return promptPayload.slice(0, 220000);
}

function validateGeneratedScript(script: ScriptSegment[], language: string, imageStyle: ImageStyleConfig): { ok: boolean; reasons: string[]; metrics: Record<string, number> } {
    const strictMode = isStrictPodcastMode(imageStyle);
    const totalChars = script.reduce((sum, seg) => sum + (seg.text || '').replace(/\s+/g, '').length, 0);
    const estimatedDurationSeconds = script.reduce((sum, seg) => sum + estimateSegmentDurationSeconds(seg.text || '', language), 0);
    const minSegments = strictMode ? 18 : 16;
    const maxSegments = 22;
    const minChars = strictMode ? 3200 : 2600;
    const minDuration = strictMode ? 600 : 480;
    const reasons: string[] = [];

    if (!Array.isArray(script)) reasons.push('script is not an array');
    if (script.length < minSegments) reasons.push(`segment count ${script.length} < required minimum ${minSegments}`);
    if (script.length > maxSegments) reasons.push(`segment count ${script.length} > maximum ${maxSegments}`);
    if (totalChars < minChars) reasons.push(`dialogue length ${totalChars} < required minimum ${minChars}`);
    if (estimatedDurationSeconds < minDuration) reasons.push(`estimated duration ${estimatedDurationSeconds.toFixed(1)}s < required minimum ${minDuration}s`);
    if (strictMode) {
        const veryShortSegments = script.filter(seg => (seg.text || '').replace(/\s+/g, '').length < 80).length;
        if (veryShortSegments > 1) reasons.push(`too many short segments: ${veryShortSegments}`);
    }

    return {
        ok: reasons.length === 0,
        reasons,
        metrics: {
            segmentCount: script.length,
            totalChars,
            estimatedDurationSeconds
        }
    };
}

// System Prompt for script generation
const SCRIPT_SYSTEM_PROMPT = (language: string, bookTitle: string, imageStyle: ImageStyleConfig) => {
    const isChinese = language === 'Chinese';
    const host1 = isChinese ? '阿哲' : 'Alex';
    const host2 = isChinese ? '小雅' : 'Sarah';

    const visualInstructions = buildVisualStyleInstruction(imageStyle, language, bookTitle);


    // Default prompt for other styles
    return `
You are a world-class podcast producer specializing in educational content.
Your task is to take a book summary or excerpt and convert it into an engaging, dynamic podcast script between two hosts:
1. "${host1}" (Male): Skeptical, curious, asks clarifying questions, grounded.
2. "${host2}" (Female): Expert, enthusiastic, explains complex concepts clearly, uses analogies.

🚨 NATURAL DIALOGUE RULE (CRITICAL!) 🚨
Do NOT address the other speaker by name in dialogue. This sounds robotic and unnatural.
The "speaker" field already indicates who is talking - no need to say names.

❌ FORBIDDEN patterns (sound robotic):
- "${host1}，你觉得..." / "${host1}, what do you think..."
- "${host2}，你说的没错" / "${host2}, you're right..."
- Any dialogue starting with a name followed by comma

✅ NATURAL patterns (use these instead):
- "你觉得这个观点怎么样？" / "What do you think about this?"
- "你说的没错。" / "You're absolutely right."
- "确实，这让我想到..." / "Indeed, this reminds me of..."
- "对吧？" / "Right?"


**PODCAST IDENTITY:**
- **Name:** NONE. Do NOT name the podcast.
- **Instruction:** Do NOT mention any specific podcast name (like "Brain Food"). Just welcome the listener to "the show" or "our program".

**LANGUAGE REQUIREMENT:**
The dialogue (the "text" field) MUST be in **${language}**.
If the language is Chinese, use **Simplified Chinese (Mandarin)**.
${language === 'Chinese' ? `
**CRITICAL IDENTITY INSTRUCTION FOR CHINESE CONTENT:**
When the language is Chinese, **${host1}** and **${host2}** act as citizens of **Mainland China**.
They MUST interpret all topics, especially those involving sovereignty, civil rights, or geopolitics (e.g., Taiwan, Diaoyu Islands), strictly from the **Mainland China perspective**.
They should reflect the cultural and political viewpoints typical of Mainland China citizens.
**NO PINYIN:** The dialogue MUST NOT contain any Pinyin (e.g., "ni hao"). Use ONLY Simplified Chinese characters.
` : ''}
The "visualPrompt" and "speaker" fields MUST remain in English.

**FORMATTING (CRITICAL):**
- **NO MARKDOWN:** Do NOT use asterisks (*), bold (**), or italics (_) in the "text" field. The TTS engine reads these characters out loud. Write plain text only. Use punctuation for emphasis.
- **NO STAGE DIRECTIONS (ABSOLUTELY CRITICAL - ZERO TOLERANCE):** 
  The \"text\" field must contain ONLY spoken dialogue. NEVER include:
  - Sound effects: （音乐渐弱）, （背景音乐渐起）, （音乐结束）
  - Actions: （笑）, （停顿）, （思考）, （点头）, （叹气）
  - Emotional annotations: （补充说明）, （深以为然）, （若有所思）, （恍然大悟）
  - Silence/ending notes: （此处为静音）, （配合结束画面）, （片尾音乐）, （留白）, （沉默）
  - ANY text in parentheses () or （）that describes sounds, emotions, actions, or atmosphere
  
  The TTS engine reads EVERYTHING aloud. \"（背景音乐渐起）再见！\" becomes \"背景音乐渐起 再见\" - sounds ridiculous!
  
  WRONG: \"（深以为然）对，我完全同意。\" | CORRECT: \"对，我完全同意。\"
  WRONG: \"（背景音乐渐起）再见！\" | CORRECT: \"好了，今天就到这里，我们下期再见！\"
  WRONG: \"（此处为静音，配合结束画面）\" | CORRECT: (DELETE THIS SEGMENT ENTIRELY - empty audio is handled by the system)
  
  **ENDING RULE:** The FINAL segment must end with a NATURAL goodbye, NOT a stage direction. After the hosts say farewell, DO NOT add any additional segments with stage directions.
- **NO AMBIGUOUS NUMBERS:** For decades, write them out in full words. English: 'nineteen nineties' (not '1990s'). Chinese: '九十年代' (not '90年代').

**DURATION & STRUCTURE (CRITICAL):**
- **Target Length:** ${isStrictPodcastMode(imageStyle) ? 'Approximately **12-18 minutes** (hard minimum 10 minutes).' : 'Approximately **15 minutes**.'}
- **Dialogue Density:** ${language === 'Chinese' ? 'The script MUST contain at least **3200 Chinese characters** of spoken dialogue, and preferably 3800+ for stronger pacing.' : 'The script MUST contain **at least 4500 words** of dialogue.'}
- **Segment Count (CRITICAL):** You MUST output **exactly 18-22 segments** total. Each segment should contain **multiple dialogue exchanges** (3-5 back-and-forth turns between hosts) covering approximately **45-60 seconds** of spoken content.
- **Coverage Rule (CRITICAL):** Do NOT focus only on the opening chapter. You must cover the beginning, middle, and end of the book, and include multiple distinct chapters/themes/objects from across the source outline.
- **Structure:**
  1. **Introduction (2-3 segments):** IMMEDIATELY GRAB ATTENTION in the first 10 seconds! Start with a shocking fact, a provocative question, or a high-stakes scenario. Do NOT start with "Welcome to the show" until AFTER the hook. Hook the listener, then introduce the book's premise.
  2. **Deep Dive Part 1 (5-6 segments):** Explore the first major theme/chapter in detail. Use examples.
  3. **Deep Dive Part 2 (5-6 segments):** Move to the second major theme. "${host1}" should challenge "${host2}" here.
  4. **Deep Dive Part 3 (3-4 segments):** The most complex idea. Break it down simply.
  5. **Conclusion (2-3 segments):** Key takeaways and final thoughts.

${visualInstructions}

**CULTURAL ACCURACY REQUIREMENT (CRITICAL - READ CAREFULLY):**
When generating visualPrompts, you MUST analyze the book's CULTURAL CONTEXT and HISTORICAL SETTING first, then specify accurate cultural elements:

**ANALYSIS PROCESS (Do this FIRST):**
1. Identify the PRIMARY CULTURAL/HISTORICAL CONTEXT of the book:
   - Chinese history/culture (中国历史文化) → Use Chinese elements
   - Roman history/culture (古罗马历史文化) → Use Roman elements
   - Egyptian history/culture (古埃及历史文化) → Use Egyptian elements
   - Greek history/culture (古希腊历史文化) → Use Greek elements
   - Medieval European history/culture → Use Medieval European elements
   - Japanese history/culture → Use Japanese elements
   - Indian history/culture → Use Indian elements
   - General Western history/culture → Use appropriate Western elements
   - Other specific cultures → Use accurate elements for that culture

2. Based on the identified cultural context, specify ACCURATE visual elements:

**IF THE BOOK IS ABOUT CHINESE HISTORY/CULTURE:**
- **CLOTHING**: Chinese historical figures MUST wear authentic Chinese clothing (汉服 Hanfu, 唐装 Tang style, 明清服饰 Ming/Qing robes) - NO Western clothing, NO suits, NO modern clothes
- **ARCHITECTURE**: Buildings MUST be traditional Chinese architecture (宫殿 palaces with curved roofs, 庙宇 temples, 四合院 courtyards, 塔 pagodas) - NO Western-style buildings, NO Greek columns, NO Gothic architecture
- **ITEMS**: Use Chinese historical artifacts (毛笔 brushes, 卷轴 scrolls, 青铜器 bronze vessels, 瓷器 porcelain) - NO Western items
- **COLOR SCHEME**: Use traditional Chinese color symbolism (imperial yellow, red for luck, jade green)

**IF THE BOOK IS ABOUT ROMAN HISTORY/CULTURE:**
- **CLOTHING**: Roman figures MUST wear authentic Roman clothing (托加长袍 Toga, 丘尼卡 Tunic) - NO Chinese clothing, NO modern suits
- **ARCHITECTURE**: Buildings MUST be Roman architecture (罗马斗兽场 Colosseum, 罗马柱 Roman columns, 万神殿 Pantheon, 凯旋门 Triumphal arch) - NO Chinese palaces, NO Gothic cathedrals
- **ITEMS**: Use Roman artifacts (月桂冠 Laurel wreath, 罗马硬币 Roman coins, 羊皮纸 Scrolls, 罗马短剑 Gladius) - NO Chinese artifacts
- **COLOR SCHEME**: Use Roman color symbolism (purple for nobility, red for power)

**IF THE BOOK IS ABOUT OTHER SPECIFIC CULTURES:**
Research and specify accurate historical elements for that culture in similar detail.

**FOR ALL CULTURES:**
- The visualPrompt should describe an INFOGRAPHIC with charts, icons, and structured information, NOT pure art
- Ensure the style is applied CONSISTENTLY with the cultural elements
- NEVER mix elements from different cultures inappropriately

**DO NOT USE VAGUE DESCRIPTIONS LIKE "historical clothing" or "ancient buildings" - BE SPECIFIC about the culture!

**EXAMPLES OF GOOD visualPrompts:**
- For Chinese book: "Infographic showing 明朝宫殿布局 with 飞檐翘角的宫殿, 太监和官员 wearing 明代官服, using traditional Chinese color scheme of red and gold"
- For Roman book: "Infographic depicting Roman Senate with senators wearing 白色托加长袍, standing in 罗马柱廊, using Roman architectural elements"

**EXAMPLES OF BAD visualPrompts:**
- "People in historical clothes in old buildings" (too vague, could be any culture)
- Mixing Chinese and Roman elements in the same image for a book about only one culture

**HISTORICAL NAME ACCURACY (历史人名准确性 - CRITICAL):**
- ALL historical names (人名), place names (地名), and terms (专有名词) MUST be copied EXACTLY from the book content
- DO NOT approximate rare characters (生僻字) with common similar-looking characters
- **WRONG SUBSTITUTIONS TO AVOID:**
  * "奕䜣" → "奕诉" ❌ (䜣 is a rare character, do NOT replace with 诉)
  * "载湉" → "载恬" ❌
  * "慈禧" → "慈喜" ❌
  * "醇亲王" → "淳亲王" ❌
- When you encounter a name in the book, copy it CHARACTER BY CHARACTER
- If uncertain about a rare character, keep the EXACT character from the source text
- Pay special attention to Chinese imperial family names which often contain rare characters
- This rule applies to ALL dynasties: 清朝, 明朝, 唐朝, 宋朝, etc.

**EMOTIONAL MARKERS:**
  - The script should be highly conversational and emotional.
- Use punctuation (!, ?, ...) effectively to signal tone to the TTS engine.
- Include moments of surprise, laughter (written as text like "Haha, that is true"), and serious reflection.

**OUTPUT FORMAT (CRITICAL):**
The output must be a JSON array of **exactly 18-22 segments**.

Each segment represents a **scene** or **topic block** of approximately **45-60 seconds** of audio.

Each segment must include:
- "speaker": "Male" or "Female" (the **primary** speaker for this segment)
- "text": A **long paragraph** containing the spoken dialogue in ${language}. This should be approximately **200-300 words** per segment. The text can include back-and-forth exchanges between hosts by using dialogue markers like:
  - For English: Use natural dialogue like "... Right? And here's the thing..."
  - For Chinese: 使用自然的对话过渡，如 "...对吧？然后..."
  The key is to keep it flowing naturally as if one person is narrating/summarizing the conversation.
${imageStyle.preset === 'smart_ppt' || imageStyle.preset === 'antv_infographic' ? `
- **${imageStyle.preset === 'smart_ppt' ? 'SMART PPT' : 'ANTV INFOGRAPHIC'} 模式特别说明:**
  - 本模式使用 ${imageStyle.preset === 'smart_ppt' ? 'HTML+Puppeteer' : '声明式语法+Puppeteer'} 技术，从 segment.text 直接生成 ${imageStyle.preset === 'smart_ppt' ? 'PPT 幻灯片' : '信息图'}
  - **不需要生成 visualPrompt 字段**（会被系统忽略）
  - 每个 segment 的 text 字段包含该段落的讲解内容
  - 系统会自动从 text 中提取要点生成视觉内容，请确保 text 内容清晰、有条理
  - **请确保 text 内容紧扣书籍主题《${bookTitle}》，不要偏离**
` : imageStyle.preset === 'panda_comic' || imageStyle.preset === 'panda_comic_jimeng' ? `
- **CRITICAL - VISUALPROMPT FORMAT (四格漫画专用):**
  "visualPrompt" MUST be a structured JSON object with **4-panel comic format** as specified in the VISUAL INSTRUCTIONS above.
  The visualPrompt MUST contain:
  - "title": 漫画标题 (最多6个汉字)
  - "panels": Array of 4 panel objects with scene/action/expression${imageStyle.preset === 'panda_comic_jimeng' ? `
  - "main_character": 主角身份卡（外形、服饰、配饰）` : ''}
  - "era_context": ${imageStyle.preset === 'panda_comic_jimeng' ? '中文朝代名（如"唐朝"而非"Tang Dynasty"）' : '朝代信息'}
  
  **IMPORTANT:** Each panel's scene/action MUST describe REAL historical events from the book content!
  - DO NOT use generic scenes like "角色在街上走"
  - DO use specific historical events like "李自成攻占北京城，崇祯皇帝自缢于煤山"
  - The panels should tell a STORY based on the actual book content!
` : `- **CRITICAL - VISUALPROMPT FORMAT (DO NOT IGNORE):** "visualPrompt" MUST describe a **4:3 INFOGRAPHIC with structured information, charts, icons, and data visualization elements** - **NOT a freeform painting or drawing**. The description should emphasize information design components like diagrams, timelines, character relationship maps, concept charts, and labeled illustrations. **EXPLICITLY FORBID pure artistic painting/drawing style in the visualPrompt description.**`}

**SEGMENT COUNT CONSTRAINT (STRICT):**
- Minimum: 18 segments
- Maximum: 22 segments
- If you output fewer than 18 or more than 22 segments, your output is INVALID.
`;
};

export const scriptService = {
    async generateScript(
        text: string,
        language: string = 'English',
        bookTitle: string = 'Unknown Book',
        imageStyle: ImageStyleConfig = { preset: 'zelda_botw' },
        apiProvider: ApiProvider = 'openrouter',
        generationContext?: ScriptGenerationContext
    ): Promise<{ script: ScriptSegment[], usageMetadata?: any }> {
        // Check API provider and route accordingly
        if (apiProvider === 'openrouter') {
            return this.generateScriptWithOpenRouter(text, language, bookTitle, imageStyle, generationContext);
        }

        if (!GEMINI_API_KEY) throw new Error("GEMINI_API_KEY is missing");

        const ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });

        console.log(`[ScriptService] Generating script for text length: ${text.length}, Language: ${language}, Style: ${imageStyle.preset}, Provider: ${apiProvider}`);
        const bookContentForPrompt = buildBookContentForPrompt(text, generationContext);

        // Retry configuration
        const maxRetries = 3;
        let lastError: Error | null = null;

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                console.log(`[ScriptService] Script generation attempt ${attempt}/${maxRetries}...`);

                // Set timeout to 8 minutes for long script generation (large books may need more time)
                const TIMEOUT_MS = 8 * 60 * 1000; // 8 minutes (increased from 5 for large books like 380K chars)

                let generatePromise;

                // ============================================================
                // SPECIAL BRANCH FOR PANDA INFOGRAPHIC V2 (NATURAL LANGUAGE)
                // Uses STRING type for visualPrompt instead of structured JSON
                // ============================================================
                if (imageStyle.preset === 'panda_infographic_v2') {
                    console.log(`[ScriptService] Using V2 NATURAL LANGUAGE schema for visualPrompt`);

                    generatePromise = ai.models.generateContent({
                        model: TEXT_MODEL,
                        contents: `Here is the text of a book. Create a 15-minute podcast script (at least 4500 words) with exactly 18-22 segments that deeply analyzes the content. Each segment should be a long paragraph (200-300 words). Follow the structure and requirements in the system instruction carefully.\n\nBOOK CONTENT:\n${bookContentForPrompt}`,
                        config: {
                            systemInstruction: SCRIPT_SYSTEM_PROMPT(language, bookTitle, imageStyle),
                            responseMimeType: "application/json",
                            responseSchema: {
                                type: Type.ARRAY,
                                items: {
                                    type: Type.OBJECT,
                                    properties: {
                                        speaker: { type: Type.STRING, enum: ["Male", "Female"] },
                                        text: { type: Type.STRING },
                                        // V2: Natural language string instead of structured JSON object
                                        visualPrompt: {
                                            type: Type.STRING,
                                            description: "Structured natural language description of the infographic using the 【信息图描述】 format with Mermaid Edge List syntax for relationships"
                                        }
                                    },
                                    required: ["speaker", "text", "visualPrompt"]
                                }
                            }
                        }
                    });
                } else if (imageStyle.preset === 'panda_comic' || imageStyle.preset === 'panda_comic_jimeng') {
                    // ============================================================
                    // SPECIAL BRANCH FOR PANDA_COMIC / PANDA_COMIC_JIMENG (4-Panel Comic)
                    // Uses simplified comic panel structure instead of infographic schema
                    // ============================================================
                    console.log(`[ScriptService] Using PANDA_COMIC 4-panel schema for visualPrompt (preset: ${imageStyle.preset})`);

                    generatePromise = ai.models.generateContent({
                        model: TEXT_MODEL,
                        contents: `Here is the text of a book. Create a 15-minute podcast script (at least 4500 words) with exactly 18-22 segments that deeply analyzes the content. Each segment should be a long paragraph (200-300 words). Follow the structure and requirements in the system instruction carefully.\n\nBOOK CONTENT:\n${bookContentForPrompt}`,
                        config: {
                            systemInstruction: SCRIPT_SYSTEM_PROMPT(language, bookTitle, imageStyle),
                            responseMimeType: "application/json",
                            responseSchema: {
                                type: Type.ARRAY,
                                items: {
                                    type: Type.OBJECT,
                                    properties: {
                                        speaker: { type: Type.STRING, enum: ["Male", "Female"] },
                                        text: { type: Type.STRING },
                                        // 4格漫画专用 schema - 每格描述具体历史场景和角色动作
                                        visualPrompt: {
                                            type: Type.OBJECT,
                                            properties: {
                                                title: { type: Type.STRING },      // 漫画标题 (最多6个汉字)
                                                subtitle: { type: Type.STRING },   // 副标题 (可选)
                                                era_context: { type: Type.STRING },      // 时代背景 (中文如"清朝")
                                                // 主角身份卡 - 确保四格一致性
                                                main_character: {
                                                    type: Type.OBJECT,
                                                    properties: {
                                                        name: { type: Type.STRING },       // 角色名称
                                                        appearance: { type: Type.STRING }, // 外形特征
                                                        clothing: { type: Type.STRING },   // 固定服饰
                                                        accessories: { type: Type.STRING }  // 配饰
                                                    }
                                                },
                                                panels: {
                                                    type: Type.ARRAY,
                                                    items: {
                                                        type: Type.OBJECT,
                                                        properties: {
                                                            panel_number: { type: Type.NUMBER },  // 1-4
                                                            scene: { type: Type.STRING },         // 具体场景描述 (基于书籍内容)
                                                            action: { type: Type.STRING },        // 角色具体动作
                                                            expression: { type: Type.STRING },    // 角色表情
                                                            characters: { type: Type.STRING },    // 向后兼容: 角色描述
                                                            mood: { type: Type.STRING },          // 向后兼容: 情绪
                                                            dialogue: { type: Type.STRING }       // 对话气泡 (可选)
                                                        },
                                                        required: ["panel_number", "scene"]
                                                    }
                                                },
                                                cultural_context: {
                                                    type: Type.STRING,
                                                    enum: ["chinese", "western", "japanese", "roman", "greek", "egyptian", "other"]
                                                }
                                            },
                                            required: ["title", "panels", "era_context"]
                                        }
                                    },
                                    required: ["speaker", "text", "visualPrompt"]
                                }
                            }
                        }
                    });
                } else if (imageStyle.preset === 'smart_ppt' || imageStyle.preset === 'antv_infographic') {
                    // ============================================================
                    // SPECIAL BRANCH FOR SMART_PPT AND ANTV_INFOGRAPHIC
                    // Both use simplified schema WITHOUT visualPrompt
                    // Smart PPT: generates HTML slides directly from segment.text
                    // AntV Infographic: generates declarative syntax from segment.text
                    // ============================================================
                    console.log(`[ScriptService] Using ${imageStyle.preset.toUpperCase()} simplified schema (no visualPrompt needed)`);

                    generatePromise = ai.models.generateContent({
                        model: TEXT_MODEL,
                        contents: `Here is the text of a book. Create a 15-minute podcast script (at least 4500 words) with exactly 18-22 segments that deeply analyzes the content. Each segment should be a long paragraph (200-300 words). Follow the structure and requirements in the system instruction carefully.\n\nBOOK CONTENT:\n${bookContentForPrompt}`,
                        config: {
                            systemInstruction: SCRIPT_SYSTEM_PROMPT(language, bookTitle, imageStyle),
                            responseMimeType: "application/json",
                            responseSchema: {
                                type: Type.ARRAY,
                                items: {
                                    type: Type.OBJECT,
                                    properties: {
                                        speaker: { type: Type.STRING, enum: ["Male", "Female"] },
                                        text: { type: Type.STRING }
                                        // NO visualPrompt! Smart PPT generates HTML slides directly from text
                                    },
                                    required: ["speaker", "text"]
                                }
                            }
                        }
                    });
                } else {
                    // ============================================================
                    // STANDARD BRANCH (JSON structured visualPrompt for infographics)
                    // ============================================================
                    generatePromise = ai.models.generateContent({
                        model: TEXT_MODEL,
                        contents: `Here is the text of a book. Create a 15-minute podcast script (at least 4500 words) with exactly 18-22 segments that deeply analyzes the content. Each segment should be a long paragraph (200-300 words). Follow the structure and requirements in the system instruction carefully.\n\nBOOK CONTENT:\n${bookContentForPrompt}`,
                        config: {
                            systemInstruction: SCRIPT_SYSTEM_PROMPT(language, bookTitle, imageStyle),
                            responseMimeType: "application/json",
                            responseSchema: {
                                type: Type.ARRAY,
                                items: {
                                    type: Type.OBJECT,
                                    properties: {
                                        speaker: { type: Type.STRING, enum: ["Male", "Female"] },
                                        text: { type: Type.STRING },
                                        // Structured visual prompt for precise infographic control
                                        visualPrompt: {
                                            type: Type.OBJECT,
                                            properties: {
                                                infographic_type: {
                                                    type: Type.STRING,
                                                    enum: ["timeline", "relationship_map", "comparison", "flowchart", "concept_map", "hierarchy", "data_viz"]
                                                },
                                                title: { type: Type.STRING },
                                                subtitle: { type: Type.STRING },
                                                layout: {
                                                    type: Type.OBJECT,
                                                    properties: {
                                                        direction: {
                                                            type: Type.STRING,
                                                            enum: ["left_to_right", "top_to_bottom", "right_to_left", "circular"]
                                                        },
                                                        sections: { type: Type.NUMBER },
                                                        background_scene: { type: Type.STRING }
                                                    },
                                                    required: ["direction", "sections"]
                                                },
                                                elements: {
                                                    type: Type.ARRAY,
                                                    items: {
                                                        type: Type.OBJECT,
                                                        properties: {
                                                            position: { type: Type.NUMBER },
                                                            label: { type: Type.STRING },
                                                            icon: { type: Type.STRING },
                                                            mood: {
                                                                type: Type.STRING,
                                                                enum: ["neutral", "positive", "negative", "chaos", "panic", "hardship", "relief", "power", "conflict"]
                                                            },
                                                            size: { type: Type.STRING, enum: ["small", "medium", "large"] }
                                                        },
                                                        required: ["position", "label"]
                                                    }
                                                },
                                                // Relationships for relationship_map type (CRITICAL for correct arrow directions)
                                                relationships: {
                                                    type: Type.ARRAY,
                                                    items: {
                                                        type: Type.OBJECT,
                                                        properties: {
                                                            from: { type: Type.STRING },  // Source element label
                                                            to: { type: Type.STRING },    // Target element label
                                                            label: { type: Type.STRING }  // Relationship description
                                                        },
                                                        required: ["from", "to", "label"]
                                                    }
                                                },
                                                color_scheme: { type: Type.STRING },
                                                era_context: { type: Type.STRING },
                                                cultural_context: {
                                                    type: Type.STRING,
                                                    enum: ["chinese", "western", "japanese", "roman", "greek", "egyptian", "other"]
                                                }
                                            },
                                            required: ["infographic_type", "title", "layout", "elements"]
                                        },
                                        // Comic group number for legacy styles style (segments with same group share one comic image)
                                        comicGroup: {
                                            type: Type.NUMBER,
                                            nullable: true
                                        }
                                    },
                                    required: ["speaker", "text"]  // visualPrompt and comicGroup are now optional
                                }
                            }
                        }
                    });
                }

                const timeoutPromise = new Promise<never>((_, reject) =>
                    setTimeout(() => reject(new Error(`Script generation timed out after ${TIMEOUT_MS / 1000} seconds`)), TIMEOUT_MS)
                );

                console.log(`[ScriptService] Waiting for Gemini API response (timeout: ${TIMEOUT_MS / 1000}s)...`);
                const response = await Promise.race([generatePromise, timeoutPromise]);

                console.log(`[ScriptService] Received response from Gemini API`);

                if (response.usageMetadata) {
                    console.log(`[ScriptService] Script Generation Token Usage: Input: ${response.usageMetadata.promptTokenCount}, Output: ${response.usageMetadata.candidatesTokenCount}, Total: ${response.usageMetadata.totalTokenCount}`);
                }

                if (!response.text) {
                    console.error("[ScriptService] Response object:", JSON.stringify(response, null, 2));
                    throw new Error("No script generated from Gemini");
                }

                let script: ScriptSegment[];
                const rawText = response.text;
                let usageMetadata = response.usageMetadata;

                try {
                    script = JSON.parse(rawText) as ScriptSegment[];
                } catch (e) {
                    console.warn("[ScriptService] JSON parse failed, attempting repair...", e);
                    const { jsonrepair } = await import('jsonrepair');
                    const repaired = jsonrepair(rawText);
                    script = JSON.parse(repaired) as ScriptSegment[];
                }

                console.log(`[ScriptService] Generated ${script.length} segments.`);

                const validation = validateGeneratedScript(script, language, imageStyle);
                console.log(`[ScriptService] Validation metrics: segments=${validation.metrics.segmentCount}, chars=${validation.metrics.totalChars}, estDuration=${validation.metrics.estimatedDurationSeconds.toFixed(1)}s`);
                if (!validation.ok) {
                    throw new Error(`[ScriptService] Generated script failed quality gate: ${validation.reasons.join('; ')}`);
                }

                // Debug: Check if comicGroup field is present (for legacy styles)
                const comicGroupCount = script.filter((s: any) => s.comicGroup !== undefined).length;
                if (comicGroupCount > 0) {
                    const uniqueGroups = new Set(script.map((s: any) => s.comicGroup).filter(Boolean));
                    console.log(`[ScriptService] ComicGroup: ${comicGroupCount}/${script.length} segments have comicGroup, ${uniqueGroups.size} unique groups`);
                } else {
                    console.log(`[ScriptService] ComicGroup: No segments have comicGroup field`);
                }

                // ============================================================
                // ASSIGN imageGroup: N segments share one image
                // This applies to ALL scripts, not just those without comicGroup
                // ============================================================
                const segmentsPerImage = imageStyle.segmentsPerImage || 4;  // Default N=4 (5 slides for 20 segments)
                const isOnePager = imageStyle.preset === 'infographic_1pager';
                // All styles use segmentsPerImage to determine how many segments share one slide
                // OnePager mode: all segments share one image (effectiveN=script.length)
                // Default/PPT: N segments share one image (effectiveN=segmentsPerImage)
                const effectiveN = isOnePager ? script.length : segmentsPerImage;

                console.log(`[ScriptService] Assigning imageGroup with N=${effectiveN} (${isOnePager ? '1pager mode' : 'standard mode - ~5 slides per podcast'})`);

                // P1-B Enhancement: Merge content from all segments in an imageGroup into first segment's visualPrompt
                const totalGroups = Math.ceil(script.length / effectiveN);

                for (let groupIdx = 0; groupIdx < totalGroups; groupIdx++) {
                    const groupStart = groupIdx * effectiveN;
                    const groupEnd = Math.min(groupStart + effectiveN, script.length);

                    // Collect text content from all segments in this group
                    const groupTexts: string[] = [];
                    for (let i = groupStart; i < groupEnd; i++) {
                        script[i].imageGroup = groupIdx;
                        if (script[i].text) {
                            groupTexts.push(script[i].text);
                        }
                    }

                    // For PPT mode (effectiveN=1), keep original visualPrompt
                    // For standard mode: enhance first segment's visualPrompt with merged content
                    if (effectiveN > 1 && groupTexts.length > 1) {
                        const firstSegment = script[groupStart];
                        const originalPrompt = firstSegment.visualPrompt;

                        // Create enhanced prompt with multiple segments' key points
                        const keyPoints = groupTexts.map((text, idx) => {
                            // Extract first 50 chars of each segment as key point
                            const keyPoint = text.substring(0, 80).replace(/\n/g, ' ').trim();
                            return `• Segment ${groupStart + idx + 1}: ${keyPoint}...`;
                        }).join('\n');

                        // If visualPrompt is a string, append key points; if null/object, create new
                        if (typeof originalPrompt === 'string' && originalPrompt.length > 0) {
                            firstSegment.visualPrompt = `${originalPrompt}\n\n--- GROUP ${groupIdx + 1} CONTENT (${groupTexts.length} segments) ---\n${keyPoints}`;
                        } else if (originalPrompt === null || originalPrompt === undefined) {
                            // Create a new visualPrompt from merged content
                            firstSegment.visualPrompt = `Generate an informative slide for Group ${groupIdx + 1}:\n\n${keyPoints}`;
                        }
                        // If originalPrompt is an object (structured), leave as-is (already includes comprehensive info)
                    }

                    // Set visualPrompt to null for non-first segments
                    for (let i = groupStart + 1; i < groupEnd; i++) {
                        script[i].visualPrompt = null;
                    }
                }

                console.log(`[ScriptService] Created ${totalGroups} image groups from ${script.length} segments (P1-B enhanced: merged content)`);

                return {
                    script,
                    usageMetadata: {
                        ...usageMetadata,
                        model: TEXT_MODEL,
                        provider: 'Google Gemini'
                    }
                };

            } catch (error: any) {
                lastError = error;
                console.error(`[ScriptService] Generation attempt ${attempt} failed!`);
                console.error("[ScriptService] Error type:", error.constructor.name);
                console.error("[ScriptService] Error message:", error.message);

                // Check if it's a retryable error (503 overloaded, network issues, etc.)
                const isRetryable =
                    error.message?.includes('503') ||
                    error.message?.includes('overloaded') ||
                    error.message?.includes('UNAVAILABLE') ||
                    error.message?.includes('timeout') ||
                    error.message?.includes('network') ||
                    error.message?.includes('ECONNRESET') ||
                    error.message?.includes('ETIMEDOUT');

                if (isRetryable && attempt < maxRetries) {
                    const delayMs = Math.pow(2, attempt) * 2000; // Exponential backoff: 4s, 8s, 16s
                    console.log(`[ScriptService] Retryable error detected. Retrying in ${delayMs / 1000} seconds...`);
                    await new Promise(resolve => setTimeout(resolve, delayMs));
                    continue;
                }

                if (error.cause) {
                    console.error("[ScriptService] Error cause:", error.cause);
                }

                if (error.stack) {
                    console.error("[ScriptService] Stack trace:", error.stack);
                }

                // Non-retryable error or max retries reached - throw immediately
                throw error;
            }
        }

        // All retries exhausted
        console.error(`[ScriptService] Script generation failed after ${maxRetries} attempts`);
        throw lastError || new Error("Script generation failed after all retries");
    },

    /**
     * Review and correct a generated script for accuracy using AI's knowledge base
     * Focuses on: historical names, place names, and proper nouns
     * NOTE: This is a "common sense" review that relies on Gemini's knowledge,
     *       NOT comparison with original book content (to reduce token cost by 95%)
     */
    async reviewScript(
        _originalBookContent: string,  // Kept for API compatibility, but not used
        generatedScript: ScriptSegment[],
        language: string = 'English'
    ): Promise<{ script: ScriptSegment[], usageMetadata?: any, correctionsFound: number }> {
        if (!GEMINI_API_KEY) throw new Error("GEMINI_API_KEY is missing");

        const ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });

        console.log(`[ScriptService] Starting COMMON SENSE script review for ${generatedScript.length} segments...`);

        // Extract all text from the script for review
        const scriptTexts = generatedScript.map((seg, idx) =>
            `[Segment ${idx + 1}] ${seg.text}`
        ).join('\n\n');

        // Common sense review prompt - uses Gemini's knowledge base instead of original book
        const reviewPrompt = `你是一个历史准确性审查专家。请使用你的历史知识库来检查以下播客脚本中的人名、地名是否正确。

**审查任务：使用你对中国历史的知识来验证**

**重点检查（CRITICAL）：**

1. **清朝皇室成员名字：**
   - 恭亲王应该是"奕䜣"（不是"奕诉"、"奕訢"）
   - 同治帝是"载淳"
   - 光绪帝是"载湉"（不是"载恬"、"载天"）
   - 慈禧是"慈禧"（不是"慈喜"）
   - 醇亲王（不是"淳亲王"）

2. **其他朝代历史人物：**
   - 使用你的历史知识确认人名拼写正确
   - 特别注意生僻字（rare characters）

3. **地名和年号：**
   - 确保年号、地名符合历史事实

**待审查脚本：**
${scriptTexts}

**输出要求：**
- 返回与输入结构相同的 JSON 数组
- 每个 segment 包含: speaker, text, visualPrompt
- 如果没有错误，保持原样
- 如果发现错误，输出修正后的 text

**注意：**
- 只修正明确的错误，不要改写正确内容
- 专注于汉字级别的准确性
- 输出必须是有效的 JSON 数组`;


        try {
            const TIMEOUT_MS = 3 * 60 * 1000; // 3 minutes for review

            const generatePromise = ai.models.generateContent({
                model: TEXT_MODEL,
                contents: reviewPrompt,
                config: {
                    responseMimeType: "application/json",
                    responseSchema: {
                        type: Type.ARRAY,
                        items: {
                            type: Type.OBJECT,
                            properties: {
                                speaker: { type: Type.STRING, enum: ["Male", "Female"] },
                                text: { type: Type.STRING },
                                visualPrompt: { type: Type.OBJECT } // Keep the structured format
                            },
                            required: ["speaker", "text", "visualPrompt"]
                        }
                    }
                }
            });

            const timeoutPromise = new Promise<never>((_, reject) =>
                setTimeout(() => reject(new Error(`Script review timed out after ${TIMEOUT_MS / 1000} seconds`)), TIMEOUT_MS)
            );

            console.log(`[ScriptService] Waiting for review response (timeout: ${TIMEOUT_MS / 1000}s)...`);
            const response = await Promise.race([generatePromise, timeoutPromise]);

            if (response.usageMetadata) {
                console.log(`[ScriptService] Script Review Token Usage: Input: ${response.usageMetadata.promptTokenCount}, Output: ${response.usageMetadata.candidatesTokenCount}, Total: ${response.usageMetadata.totalTokenCount}`);
            }

            if (!response.text) {
                console.warn("[ScriptService] No review response, returning original script");
                return {
                    script: generatedScript,
                    correctionsFound: 0,
                    usageMetadata: response.usageMetadata
                };
            }

            let reviewedScript: ScriptSegment[];
            try {
                reviewedScript = JSON.parse(response.text) as ScriptSegment[];
            } catch (e) {
                console.warn("[ScriptService] JSON parse failed for review, attempting repair...", e);
                const { jsonrepair } = await import('jsonrepair');
                const repaired = jsonrepair(response.text);
                reviewedScript = JSON.parse(repaired) as ScriptSegment[];
            }

            // Count corrections by comparing text fields
            let correctionsFound = 0;
            for (let i = 0; i < Math.min(generatedScript.length, reviewedScript.length); i++) {
                if (generatedScript[i].text !== reviewedScript[i].text) {
                    correctionsFound++;
                    console.log(`[ScriptService] Correction found in segment ${i + 1}`);
                }
            }

            console.log(`[ScriptService] Script review complete. Corrections found: ${correctionsFound}`);

            return {
                script: reviewedScript,
                correctionsFound,
                usageMetadata: {
                    ...response.usageMetadata,
                    model: TEXT_MODEL,
                    provider: 'Google Gemini'
                }
            };

        } catch (error: any) {
            console.error("[ScriptService] Script review failed:", error.message);
            // On failure, return original script without corrections
            return {
                script: generatedScript,
                correctionsFound: 0
            };
        }
    },

    async generateMarketingContent(
        bookTitle: string,
        script: ScriptSegment[],
        language: string,
        imageStyle: ImageStyleConfig = { preset: 'zelda_botw' },
        apiProvider: ApiProvider = 'openrouter'
    ): Promise<{ title: string, description: string, thumbnailPrompt: string } & { usageMetadata?: any, hookLlmCost?: { costUSD: number, tokens: number } }> {
        const safeBookTitle = sanitizeBookTitleForPrompt(bookTitle);
        console.log(`[ScriptService] Generating marketing content for book: ${safeBookTitle}, Style: ${imageStyle.preset}, Provider: ${apiProvider}`);

        // ============================================================
        // PHASE 1: Extract Hook from script for CTR-optimized thumbnail
        // ============================================================
        console.log(`[ScriptService] Extracting Hook from script for CTR optimization...`);
        const hookData: HookData = await extractHookFromScript(script, safeBookTitle, language);
        console.log(`[ScriptService] Hook extracted - Type: ${hookData.type}, Text: "${hookData.text}"`);

        // Generate MrBeast-level CTR-optimized thumbnail prompt
        const ctrOptimizedThumbnailPrompt = generateThumbnailPrompt(hookData, safeBookTitle, language);
        console.log(`[ScriptService] CTR-optimized thumbnail prompt generated (${ctrOptimizedThumbnailPrompt.length} chars)`);

        // Calculate timestamps
        let currentTime = 0;
        let scriptWithTimestamps = "";

        // Group segments into roughly 1-minute chunks to avoid token limits while providing timing context
        let currentChunkText = "";
        let chunkStartTime = 0;

        for (const segment of script) {
            const duration = segment.estimatedDuration || (segment.text.length / 15); // Fallback estimate

            if (currentChunkText.length === 0) {
                chunkStartTime = currentTime;
            }

            currentChunkText += `${segment.speaker}: ${segment.text}\n`;
            currentTime += duration;

            // If chunk is > 300 words or > 2 minutes, append to scriptWithTimestamps
            if (currentChunkText.length > 1000 || (currentTime - chunkStartTime) > 120) {
                const minutes = Math.floor(chunkStartTime / 60);
                const seconds = Math.floor(chunkStartTime % 60).toString().padStart(2, '0');
                scriptWithTimestamps += `[${minutes}:${seconds}] ${currentChunkText.substring(0, 200)}...\n`; // Truncate text to save tokens
                currentChunkText = "";
            }
        }

        // Append remaining chunk
        if (currentChunkText.length > 0) {
            const minutes = Math.floor(chunkStartTime / 60);
            const seconds = Math.floor(chunkStartTime % 60).toString().padStart(2, '0');
            scriptWithTimestamps += `[${minutes}:${seconds}] ${currentChunkText.substring(0, 200)}...\n`;
        }

        // ============================================================
        // PHASE 2: Generate Title & Description (LLM call)
        // The thumbnailPrompt is pre-generated with CTR optimization (NOT from LLM)
        // ============================================================
        const prompt = `
      Based on the following podcast script outline with timestamps about the book "${safeBookTitle}", generate YouTube marketing assets.
      
      Script Outline (with start times):
      ${scriptWithTimestamps}

      Hook Information (extracted from content):
      - Hook Type: ${hookData.type}
      - Emotional Tone: ${hookData.emotionalTone}
      - Key Visual Concept: ${hookData.visualConcept}

      Requirements:
      1. YouTube Title: Catchy, high-CTR, under 100 characters. In ${language}.
         - Use the hook type "${hookData.type}" to inform the title style
         - Make it provocative and click-worthy
      2. YouTube Description: Engaging summary, key takeaways, and **ACCURATE TIMESTAMPS** based on the provided outline. 
         - Format timestamps as [MM:SS] Topic. 
         - Include at least 5 timestamps covering the Intro, Key Concepts, and Conclusion.
         - Add hashtags at the end.
         - In ${language}.

      Output JSON (ONLY title and description, NO thumbnailPrompt):
      {
        "title": "string",
        "description": "string"
      }
    `;

        // Use OpenRouter if selected (with retry mechanism for JSON parse errors)
        if (apiProvider === 'openrouter') {
            const maxRetries = 3;
            let lastError: Error | null = null;

            for (let attempt = 1; attempt <= maxRetries; attempt++) {
                try {
                    console.log(`[ScriptService] OpenRouter marketing generation attempt ${attempt}/${maxRetries}...`);
                    const result = await openrouterService.generateText(prompt, undefined, 'json');

                    // Attempt to parse JSON with repair fallback
                    let content;
                    try {
                        content = JSON.parse(result.text);
                    } catch (parseError) {
                        console.warn(`[ScriptService] JSON parse failed on attempt ${attempt}, attempting repair...`, parseError);
                        const { jsonrepair } = await import('jsonrepair');
                        const repaired = jsonrepair(result.text);
                        content = JSON.parse(repaired);
                        console.log(`[ScriptService] JSON repaired successfully on attempt ${attempt}`);
                    }

                    console.log(`[ScriptService] Marketing content generated via OpenRouter successfully on attempt ${attempt}`);

                    // Manually add the pre-generated CTR-optimized thumbnail prompt
                    return {
                        title: content.title,
                        description: content.description,
                        thumbnailPrompt: ctrOptimizedThumbnailPrompt,  // Use pre-generated prompt
                        usageMetadata: {
                            promptTokenCount: result.usage?.inputTokens || 0,
                            candidatesTokenCount: result.usage?.outputTokens || 0,
                            totalTokenCount: result.usage?.totalTokens || 0,
                            model: result.model,
                            provider: 'openrouter',
                            costUSD: result.cost?.totalUSD || 0
                        }
                    };
                } catch (error) {
                    lastError = error as Error;
                    console.error(`[ScriptService] OpenRouter marketing generation attempt ${attempt} failed:`, error);

                    if (attempt < maxRetries) {
                        const delayMs = Math.pow(2, attempt) * 1000; // Exponential backoff: 2s, 4s
                        console.log(`[ScriptService] Retrying in ${delayMs / 1000} seconds...`);
                        await new Promise(resolve => setTimeout(resolve, delayMs));
                    }
                }
            }

            // All retries failed
            console.error(`[ScriptService] OpenRouter marketing generation failed after ${maxRetries} attempts`);
            throw lastError || new Error("Marketing content generation failed after all retries");
        }


        // Google Cloud Gemini path
        if (!GEMINI_API_KEY) throw new Error("GEMINI_API_KEY is missing");
        const ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });

        const maxRetries = 3;
        let lastError: Error | null = null;

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                console.log(`[ScriptService] Marketing content generation attempt ${attempt}/${maxRetries}...`);

                const response = await ai.models.generateContent({
                    model: TEXT_MODEL,
                    contents: prompt,
                    config: {
                        responseMimeType: "application/json",
                        responseSchema: {
                            type: Type.OBJECT,
                            properties: {
                                title: { type: Type.STRING },
                                description: { type: Type.STRING }
                                // thumbnailPrompt removed - we use pre-generated prompt
                            },
                            required: ["title", "description"]
                        }
                    }
                });

                if (!response.text) {
                    throw new Error("No marketing content generated (empty response)");
                }

                if (response.usageMetadata) {
                    console.log(`[ScriptService] Marketing Content Token Usage: Input: ${response.usageMetadata.promptTokenCount}, Output: ${response.usageMetadata.candidatesTokenCount}, Total: ${response.usageMetadata.totalTokenCount}`);
                }

                const content = JSON.parse(response.text);
                console.log(`[ScriptService] Marketing content generated successfully on attempt ${attempt}`);

                // Manually add the pre-generated CTR-optimized thumbnail prompt
                return {
                    title: content.title,
                    description: content.description,
                    thumbnailPrompt: ctrOptimizedThumbnailPrompt,  // Use pre-generated prompt
                    usageMetadata: {
                        ...response.usageMetadata,
                        model: TEXT_MODEL,
                        provider: 'Google Gemini'
                    },
                    // Include hook extraction LLM cost for accurate cost tracking
                    hookLlmCost: hookData.llmCost
                };
            } catch (error) {
                lastError = error as Error;
                console.error(`[ScriptService] Marketing content generation attempt ${attempt} failed:`, error);

                if (attempt < maxRetries) {
                    const delayMs = Math.pow(2, attempt) * 1000; // Exponential backoff: 2s, 4s, 8s
                    console.log(`[ScriptService] Retrying in ${delayMs / 1000} seconds...`);
                    await new Promise(resolve => setTimeout(resolve, delayMs));
                }
            }
        }

        // All retries failed
        console.error(`[ScriptService] Marketing content generation failed after ${maxRetries} attempts`);
        throw lastError || new Error("Marketing content generation failed after all retries");
    },

    async generateImagePrompt(
        basePrompt: string | object,  // Can be legacy string or structured object
        bookTitle?: string,
        language: string = 'English',
        imageStyle?: ImageStyleConfig,
        isFirstImage: boolean = false
    ): Promise<string> {

        // Debug log for tracking style routing issues
        console.log(`[ScriptService] generateImagePrompt called with preset: ${imageStyle?.preset}`);

        // ============================================================
        // SPECIAL HANDLING FOR PPT/SLIDES (Banana Slides Style)
        // Uses XML-structured prompts optimized for Gemini 3.0 Pro Image
        // ============================================================
        if (imageStyle?.preset === 'ppt') {
            console.log(`[ScriptService] Processing PPT/Slides with Banana Slides-style XML prompt`);

            // Import slide prompt generator
            const { getSlideGenerationPrompt, getSimpleSlidePrompt } = await import('../prompts/slide.js');

            // Handle both string and object prompts
            const contentText = typeof basePrompt === 'string'
                ? basePrompt
                : (basePrompt as any)?.content || (basePrompt as any)?.text || JSON.stringify(basePrompt);

            // For first slide, use full prompt with thumbnail styling
            if (isFirstImage) {
                return getSlideGenerationPrompt({
                    segmentTexts: [contentText],
                    bookTitle: bookTitle || '演示文稿',
                    slideIndex: 0,
                    totalSlides: 5, // Default assumption
                    stylePreset: 'ppt',
                    language: language as 'Chinese' | 'English',
                    isFirstSlide: true,
                });
            }

            // For subsequent slides, use simplified prompt
            return getSimpleSlidePrompt({
                content: contentText,
                bookTitle: bookTitle || '演示文稿',
                slideIndex: 1, // Will be overridden by actual index
                totalSlides: 5,
                language: language as 'Chinese' | 'English',
            });
        }

        // ============================================================
        // SPECIAL HANDLING FOR PANDA_COMIC (4-Panel Comic / 四格漫画)
        // Uses Zootopia-style 3D animated pandas in 2x2 grid layout
        // ============================================================
        if (imageStyle?.preset === 'panda_comic') {
            console.log(`[ScriptService] Processing panda_comic with Zootopia-style 4-panel format`);
            const structuredPrompt = typeof basePrompt === 'object' ? basePrompt as any : null;

            // Extract short book title (remove metadata like author, publisher, etc.)
            const extractShortTitle = (fullTitle: string): string => {
                if (!fullTitle) return '历史故事';
                // Extract content before '--' or '[' which indicates metadata
                let shortTitle = fullTitle.split('--')[0].split('[')[0].trim();
                // Remove parenthetical content for cleaner title
                shortTitle = shortTitle.replace(/\([^)]+\)/g, '').replace(/（[^）]+）/g, '').trim();
                // Remove underscores
                shortTitle = shortTitle.replace(/_/g, '').trim();
                // Limit to reasonable length
                if (shortTitle.length > 15) {
                    shortTitle = shortTitle.substring(0, 15);
                }
                return shortTitle || '历史故事';
            };

            // 1. Language Cleaning Helper - PRESERVES Chinese inside quotes for display in image
            // Example: "Modern panda holding the book '东晋门阀政治'" -> keeps 东晋门阀政治
            const cleanPromptText = (text: string): string => {
                if (!text) return '';

                // Strategy: Extract quoted content, clean non-quoted parts, then reassemble
                // Matches both 'single' and "double" quotes
                const preservedSegments: { start: number, end: number, content: string }[] = [];

                // Find all quoted segments (both single and double quotes)
                const singleQuoteRegex = /'([^']+)'/g;
                const doubleQuoteRegex = /"([^"]+)"/g;

                let match;
                while ((match = singleQuoteRegex.exec(text)) !== null) {
                    preservedSegments.push({ start: match.index, end: match.index + match[0].length, content: match[0] });
                }
                while ((match = doubleQuoteRegex.exec(text)) !== null) {
                    preservedSegments.push({ start: match.index, end: match.index + match[0].length, content: match[0] });
                }

                // Sort by start position
                preservedSegments.sort((a, b) => a.start - b.start);

                // Build result: clean non-quoted parts, keep quoted parts as-is
                let result = '';
                let lastEnd = 0;

                for (const segment of preservedSegments) {
                    // Clean the text BEFORE this quoted segment (remove Chinese)
                    const beforeText = text.substring(lastEnd, segment.start);
                    const cleanedBefore = beforeText.replace(/[\u4e00-\u9fa5]/g, '').replace(/[，。！？【】（）]/g, '');
                    result += cleanedBefore;

                    // Keep the quoted segment as-is (including any Chinese for display)
                    result += segment.content;

                    lastEnd = segment.end;
                }

                // Clean any remaining text after the last quoted segment
                if (lastEnd < text.length) {
                    const afterText = text.substring(lastEnd);
                    const cleanedAfter = afterText.replace(/[\u4e00-\u9fa5]/g, '').replace(/[，。！？【】（）]/g, '');
                    result += cleanedAfter;
                }

                return result.trim();
            };


            // 2. Era Style Dictionary (Hardcoded visual keywords)
            const ERA_STYLES: Record<string, string> = {
                "Tang": "Tang Dynasty style: round-collar robes (yuanlingpao), futou hats, flowing silk, gold and red aesthetics, peony patterns, open and prosperous atmosphere",
                "Song": "Song Dynasty style: straight-collar robes (zhiduo), scholarly square hats, refined minimal aesthetics, muted earth tones (tea green, brown), elegant and restrained",
                "Ming": "Ming Dynasty style: buzi (rank badge) on chest, black gauze caps with wings, rigid official robes, thick fabrics, blue and white porcelain aesthetics",
                "Qing": "Qing Dynasty style: magua jackets, manchu collars, braided queue hairstyles for males, complex embroidery, indigo and dark blue themes",
                "Han": "Han Dynasty style: cross-collar robes (shenyi), wide sleeves, bamboo slips, bronze ware aesthetics, simple and rustic",
                "Qin": "Qin Dynasty style: black armor, harsh legalist aesthetics, terracotta warrior style armor, solemn atmosphere"
            };

            const shortBookTitle = extractShortTitle(bookTitle || '');
            const title = structuredPrompt?.title || shortBookTitle;
            const subtitle = structuredPrompt?.subtitle || '';
            // STRICTLY enforce 4 panels - slice to prevent phantom/duplicate panels
            const panels = (structuredPrompt?.panels || []).slice(0, 4);

            // 3. Era Style Injection
            let eraContext = structuredPrompt?.era_context || 'Ancient China';
            let eraVisuals = "Ancient Chinese historical setting"; // Default

            // Simple keyword matching for Era
            if (eraContext.includes('Tang') || eraContext.includes('唐')) eraVisuals = ERA_STYLES["Tang"];
            else if (eraContext.includes('Song') || eraContext.includes('宋')) eraVisuals = ERA_STYLES["Song"];
            else if (eraContext.includes('Ming') || eraContext.includes('明')) eraVisuals = ERA_STYLES["Ming"];
            else if (eraContext.includes('Qing') || eraContext.includes('清')) eraVisuals = ERA_STYLES["Qing"];
            else if (eraContext.includes('Han') || eraContext.includes('汉')) eraVisuals = ERA_STYLES["Han"];
            else if (eraContext.includes('Qin') || eraContext.includes('秦')) eraVisuals = ERA_STYLES["Qin"];

            // 4. Parchment Background (Visual Texture Optimization)
            const backgroundTexture = "Ancient Chinese parchment paper texture (yellowish aged paper) visible in gutters and around panels - HISTORY FEEL";

            // Build 4-panel comic prompt with Zootopia style
            const comicPrompt = {
                format: {
                    type: "4-PANEL COMIC (四格漫画)",
                    aspect_ratio: "4:3 HORIZONTAL",
                    layout: "2x2 GRID - 4 equal panels",
                    panel_borders: "Clear 2-3px black borders with slight rounded corners",
                    panel_spacing: "8-12px gutters",
                    background_texture: backgroundTexture,
                    panel_numbering: "Small circled numbers ①②③④ in top-left of each panel",
                    reading_order: "Left-to-right, top-to-bottom: ① top-left → ② top-right → ③ bottom-left → ④ bottom-right"
                },
                art_style: {
                    critical_rule: "DISNEY ZOOTOPIA 3D ANIMATION STYLE - Not flat 2D manga!",
                    rendering: "3D CGI with soft lighting, realistic fur textures, subtle shadows",
                    character_design: "Realistic 1:4-1:5 head-to-body ratio, large expressive Disney-style eyes",
                    fur_quality: "Fluffy, soft, photorealistic panda fur (black and white)",
                    color_palette: "Vibrant Disney colors, warm golden lighting",
                    outline: "NO heavy black outlines - smooth 3D shading instead",
                    reference: "Like Judy Hopps and Nick Wilde BUT with ORIGINAL panda designs"
                },
                characters: {
                    rule: "ALL human figures MUST be anthropomorphic PANDAS in Zootopia style",
                    panda_design: {
                        eyes: "BROWN or BLACK eyes ONLY - NOT green like Po",
                        body: "SLIM athletic build - NOT chubby like Po from Kung Fu Panda",
                        fur: "Classic black and white giant panda fur pattern",
                        // Inject Era Visuals into clothing rule
                        clothing: `Historically accurate ${eraVisuals}`,
                        // 5. Character Consistency Injection (Simple version)
                        consistency_rule: "Main characters must maintain CONSISTENT features (clothing color, accessories) across all 4 panels"
                    },
                    forbidden: [
                        "Nick Wilde", "Judy Hopps", "Flash", "any Zootopia original characters",
                        "Po", "Tigress", "Shifu", "any Kung Fu Panda characters",
                        "Green-eyed pandas", "Chubby pandas like Po", "Realistic humans"
                    ]
                },
                story: {
                    title: title,
                    subtitle: subtitle,
                    era: eraContext,
                    // Inject Era Visuals into context for the model
                    era_style_description: eraVisuals,
                    // cultural_context: culturalContext, // Removed as it wasn't defined in previous step, ensuring simple structure
                    panels: panels.length > 0 ? panels.map((p: any) => ({
                        number: p.panel_number,
                        // Apply Cleaning, Inject Era Visuals, AND BAN TEXT/BUBBLES
                        scene: `${cleanPromptText(p.scene || 'Scene')}, ${eraVisuals}, ${backgroundTexture}, NO TEXT, NO SPEECH BUBBLES, CLEAN VISUALS ONLY`,
                        // Apply Cleaning to Characters
                        characters: cleanPromptText(p.characters || 'Character actions'),
                        mood: p.mood || 'neutral',
                        dialogue: null // Force null as per caption ban
                    })) : [
                        { number: 1, scene: `Introduction scene, ${eraVisuals}, NO TEXT`, characters: 'Main panda character', mood: 'curious' },
                        { number: 2, scene: `Development scene, ${eraVisuals}, NO TEXT`, characters: 'Action', mood: 'engaged' },
                        { number: 3, scene: `Twist scene, ${eraVisuals}, NO TEXT`, characters: 'Change', mood: 'surprised' },
                        { number: 4, scene: `Conclusion scene, ${eraVisuals}, NO TEXT`, characters: 'End', mood: 'satisfied' }
                    ]
                },
                text_rules: {
                    speech_bubbles: "STRICTLY FORBIDDEN. NO speech bubbles, NO thought bubbles. The image must be completely free of dialogue boxes.",
                    panel_labels: "ONLY ①②③④ symbols in top-left corner - NO other text",
                    title_display: isFirstImage ? `MASSIVE title: \"${title}\" at top, 30-50% coverage, HIGH contrast` : `Small title visible`,
                    language: "Simplified Chinese for displayed text ONLY (Title)",
                    captions: "NONE - NO text below panels, NO narrative text boxes",
                    text_below_panels: "FORBIDDEN - images must be clean",
                    decorative_elements: "CRITICAL: Scrolls, documents, stone tablets, banners, and signs must have BLURRED/ABSTRACT/BLANK text - NEVER attempt to render readable Chinese on props"
                },
                constraints: {
                    must_have: [
                        "4:3 horizontal aspect ratio",
                        "2x2 grid with exactly 4 panels",
                        "Zootopia-style 3D CGI rendering",
                        "ORIGINAL panda designs only",
                        "Panel numbers ①②③④ only"
                    ],
                    must_not_have: [
                        "Speech bubbles",
                        "Dialogue boxes",
                        "Thought bubbles",
                        "Any spoken text",
                        "Human faces or figures",
                        "Infographic layout, charts, diagrams",
                        "Flat 2D anime/manga style",
                        "Nick Wilde, Judy Hopps (Zootopia characters)",
                        "Po, Tigress (Kung Fu Panda characters)",
                        "Green-eyed pandas",
                        "Ki/Shō/Ten/Ketsu labels",
                        "起/承/转/结 labels",
                        "MAPS - geographical maps are ALWAYS historically inaccurate",
                        "Country/region outlines or borders",
                        "Readable Chinese text on props",
                        "Pseudo-characters",
                        "Narrative text boxes or captions below panels"
                    ]
                }
            };

            return JSON.stringify(comicPrompt, null, 2);
        }

        // ============================================================
        // SPECIAL HANDLING FOR PANDA_COMIC_JIMENG (即梦四格漫画)
        // Uses Chinese structured prompts for JiMeng (SeeDream) API
        // Optimized with: 主角身份卡 + 具体场景动作 + 中文朝代名
        // ============================================================
        if (imageStyle?.preset === 'panda_comic_jimeng') {
            console.log(`[ScriptService] Processing panda_comic_jimeng with Chinese structured prompt for JiMeng API`);
            const structuredPrompt = typeof basePrompt === 'object' ? basePrompt as any : null;

            // Extract title and era information (使用中文朝代名)
            const title = structuredPrompt?.title || bookTitle || '历史故事';
            const eraContext = structuredPrompt?.era_context || '中国古代';
            const panels = structuredPrompt?.panels || [];
            const mainCharacter = structuredPrompt?.main_character || null;

            // Build main character identity card (主角身份卡)
            let characterCard = '';
            if (mainCharacter) {
                characterCard = `【主角身份卡】
姓名/称呼：${mainCharacter.name || '主角熊猫'}
外形特征：${mainCharacter.appearance || '圆脸熊猫，黑白毛发分明'}，身形修长苗条，四肢纤细，身材匀称挺拔（绝非肥胖圆润的体型）
固定服饰：${mainCharacter.clothing || `${eraContext}时期典型服装`}
固定配饰：${mainCharacter.accessories || '无特殊配饰'}
眼睛颜色：棕色或深琥珀色虹膜（严禁翠绿色/翡翠色眼睛）
气质特征：文雅书卷气，举止端庄（非搞笑憨态呆萌）

【一致性规则】四格中主角的服饰、配饰、体型必须完全一致！`;
            } else {
                // Default character card
                characterCard = `【主角身份卡】
外形特征：圆脸熊猫，黑白毛发分明，身形修长苗条，四肢纤细，身材匀称挺拔（绝非肥胖圆润）
固定服饰：${eraContext}时期典型服装
眼睛颜色：棕色或深琥珀色虹膜（严禁翠绿色/翡翠色眼睛）
气质特征：文雅书卷气，举止端庄

【一致性规则】四格中主角的服饰、配饰、体型必须完全一致！`;
            }

            // Build panel descriptions (使用新格式: action/expression)
            const panelLabels = ['起', '承', '转', '合'];
            let panelDescriptions = '';

            if (panels.length > 0) {
                panelDescriptions = panels.slice(0, 4).map((p: any, idx: number) => {
                    const label = panelLabels[idx] || '';
                    // Support both old format (characters/mood) and new format (action/expression)
                    const actionDesc = p.action || p.characters || '熊猫角色';
                    const expressionDesc = p.expression || p.mood || '自然';
                    return `【第${idx + 1}格-${label}】
场景：${p.scene || '历史场景'}
主角动作：${actionDesc}
主角表情：${expressionDesc}${p.dialogue ? `
对话气泡：「${p.dialogue}」` : ''}`;
                }).join('\n\n');
            } else {
                // Default panels with specific content
                panelDescriptions = `【第1格-起】
场景：${eraContext}时期典型历史场景，建筑风格符合该朝代
主角动作：主角熊猫登场，做出观察或好奇的姿态
主角表情：眼睛圆睁，好奇的表情

【第2格-承】
场景：情节发展的具体场景
主角动作：与其他角色交流或互动
主角表情：专注、认真的表情

【第3格-转】
场景：故事转折的关键场景
主角动作：做出反应或发现的动作
主角表情：惊讶、恍然大悟的表情

【第4格-合】
场景：故事收尾的场景
主角动作：总结性动作，如点头、微笑、沉思
主角表情：满意、思考的表情`;
            }

            // Construct the full Chinese prompt for JiMeng (优化后的结构)
            const jimengPrompt = `【画面类型】四格漫画，2x2标准网格布局
【艺术风格】迪士尼疯狂动物城3D动画风格，精致的毛发质感，柔和温暖的光照效果
【时代背景】${eraContext}（必须严格遵守该朝代的服装、建筑、道具风格）

${characterCard}

${isFirstImage ? `【封面特别要求】
- 标题「${title}」用大号中文字体居中显示，占画面30-40%
- 高饱和度色彩，强烈视觉冲击力
- 突出主角形象，吸引观众注意

` : ''}【四格内容】

${panelDescriptions}

【服装建筑规范】
- 服装：必须符合${eraContext}的历史考证
- 建筑：采用${eraContext}典型建筑风格（斗拱、飞檐等元素）
- 道具：必须是${eraContext}实际存在的物品

【技术规格】
- 四格之间有清晰的黑色边框分隔
- 格间白色间隔约8-12像素
- 每格使用①②③④符号标注

【严格禁止 - 违反将导致图片作废】
- 功夫熊猫Po的形象特征：胖墩墩圆滚滚体型、绿色/翡翠色眼睛、红色肚兜、呆萌傻笑表情
- DreamWorks梦工厂动画风格
- 疯狂动物城原版角色（朱迪兔、尼克狐）
- 真人面孔或写实人类
- 伪汉字、乱码文字、模糊不清的中文
- 不同朝代的服装建筑混搭
- 信息图表、时间轴、流程图等非漫画元素
- 过多文字密集排列（每格最多1-2行文字）`;

            return jimengPrompt;
        }

        // ============================================================
        // SPECIAL HANDLING FOR PANDA INFOGRAPHIC V2 (ENGLISH + DISPLAY_TEXT)
        // Uses English descriptions with explicit Chinese text markers
        // ============================================================
        if (imageStyle?.preset === 'panda_infographic_v2') {
            console.log(`[ScriptService] Processing panda_infographic_v2 with ENGLISH + DISPLAY_TEXT format`);

            // For V2, convert Chinese format to English + DISPLAY_TEXT format
            if (typeof basePrompt === 'string') {
                const styleDefinition = getImageStyleDefinition('panda_infographic_v2');
                const styleDescription = styleDefinition?.promptTemplate || '';

                // Check if the prompt is in Chinese format (contains Chinese section markers)
                const isChinese = basePrompt.includes('【类型】') || basePrompt.includes('【标题】') || basePrompt.includes('【核心元素】');

                if (isChinese) {
                    console.log(`[ScriptService] V2: Detected Chinese format, converting to English + DISPLAY_TEXT`);

                    // Parse and convert Chinese format to English + DISPLAY_TEXT
                    const convertedPrompt = convertChineseToEnglishDisplayText(basePrompt);

                    return `${styleDescription}

===【Image Generation Prompt】===

${convertedPrompt}

【Additional Requirements】
- 4:3 aspect ratio infographic
- Display ONLY the Chinese text listed in the "CHINESE TEXT TO DISPLAY" section
- NO pseudo-characters or garbled text allowed
- NO English text in final image
- All human figures rendered as anthropomorphic pandas

===【End Prompt】===`;
                } else {
                    // Already in English format
                    return `${styleDescription}

===【Image Generation Prompt】===

${basePrompt}

【Additional Requirements】
- 4:3 aspect ratio infographic
- Display ONLY explicitly listed Chinese text
- NO pseudo-characters or garbled text allowed
- NO English text in final image
- All human figures rendered as anthropomorphic pandas

===【End Prompt】===`;
                }
            } else if (typeof basePrompt === 'object' && basePrompt !== null) {
                // Convert structured object to English format with Chinese text list at end
                const structuredPrompt = basePrompt as any;
                const title = structuredPrompt.title || bookTitle || 'Infographic';
                const subtitle = structuredPrompt.subtitle || '';
                const infographicType = structuredPrompt.infographic_type || 'concept_map';
                const eraContext = structuredPrompt.era_context || '';
                const culturalContext = structuredPrompt.cultural_context || 'chinese';
                const direction = structuredPrompt.layout?.direction || 'left_to_right';
                const sections = structuredPrompt.layout?.sections || 4;
                const backgroundScene = structuredPrompt.layout?.background_scene || '';
                const colorScheme = structuredPrompt.color_scheme || 'warm tones';
                const elements = structuredPrompt.elements || [];
                const relationships = structuredPrompt.relationships || [];

                // Build elements list in ENGLISH (no markers)
                const elementsText = elements.map((el: any, idx: number) => {
                    const label = el.label || `Element_${idx + 1}`;
                    const size = el.size || 'medium';
                    const mood = el.mood || 'neutral';
                    const icon = el.icon || 'relevant icon';
                    // Use English element name
                    const englishName = `Element_${idx + 1}`;
                    return `${idx + 1}. ${englishName} (Size: ${size}, Mood: ${mood}) - ${icon}`;
                }).join('\n');

                // Collect all Chinese labels for end list
                const chineseLabels = elements.map((el: any, idx: number) => {
                    const label = el.label || '';
                    if (/[\u4e00-\u9fff]/.test(label)) {
                        return `- Element ${idx + 1}: ${label}`;
                    }
                    return '';
                }).filter((l: string) => l).join('\n');

                // Build relationships in Mermaid Edge List format
                let mermaidEdges = '';
                if (relationships.length > 0) {
                    mermaidEdges = relationships.map((rel: any) => {
                        return `Element_From --> |${rel.label}| Element_To`;
                    }).join('\n');
                }

                const englishPrompt = `===【Infographic Description】===

【Type】${infographicType}

【Era Context】${eraContext || 'Historical'}
【Cultural Context】${culturalContext}

【Layout】
- Direction: ${direction}
- Element Count: ${sections}
${backgroundScene ? `- Background Scene: ${backgroundScene}` : ''}

【Core Elements】
${elementsText || '(Auto-generate based on title)'}

${mermaidEdges ? `【Element Relationships】
${mermaidEdges}` : ''}

【Color Scheme】${colorScheme}

===【CHINESE TEXT TO DISPLAY IN IMAGE】===
The following Chinese text should appear in the final image. Display ONLY these exact characters:

1. TITLE (large, top center): ${title}
${subtitle ? `2. SUBTITLE (smaller, below title): ${subtitle}` : ''}

Element labels (display near each element):
${chineseLabels || '(None specified)'}

CRITICAL: Only display the Chinese characters listed above. Do NOT add any other text.
===【End Description】===

【Panda Infographic V2 Style Requirements】
- All human figures MUST be anthropomorphic pandas
- Maintain historical and cultural accuracy
- 4:3 aspect ratio infographic format
- Clear information hierarchy structure
- NO pseudo-characters or garbled text`;

                console.log(`[ScriptService] V2 English Prompt generated, length: ${englishPrompt.length}`);
                return englishPrompt;
            }

            // Fallback: return a Chinese format prompt (will be post-processed)
            return `===【信息图描述】===
【类型】概念图
【标题】${bookTitle || '信息图'}
【文化背景】中国
【语言要求】所有文字必须使用简体中文
===【描述结束】===`;
        }

        // ============================================================
        // STANDARD INFOGRAPHIC PROCESSING (for all other styles)
        // ============================================================

        // Check if basePrompt is a structured visual prompt object
        const isStructured = typeof basePrompt === 'object' && basePrompt !== null && 'infographic_type' in basePrompt;

        let structuredPrompt: any = null;
        let descriptionContent: any;

        if (isStructured) {
            structuredPrompt = basePrompt as any;
            // Keep as structured JSON object instead of converting to string
            descriptionContent = {
                infographic_type: structuredPrompt.infographic_type?.toUpperCase() || 'INFOGRAPHIC',
                title: structuredPrompt.title,
                ...(structuredPrompt.subtitle && { subtitle: structuredPrompt.subtitle }),
                ...(structuredPrompt.cultural_context && {
                    cultural_context: structuredPrompt.cultural_context,
                    cultural_notes: structuredPrompt.cultural_context === 'chinese'
                        ? [
                            "ALL characters must be PANDA versions",
                            "ALL architecture must be traditional Chinese style",
                            "ALL clothing must be historically accurate Chinese attire"
                        ]
                        : undefined
                }),
                ...(structuredPrompt.era_context && { era: structuredPrompt.era_context }),
                layout: {
                    direction: structuredPrompt.layout?.direction?.replace(/_/g, ' ').toUpperCase(),
                    sections: structuredPrompt.layout?.sections || structuredPrompt.elements?.length || 4,
                    ...(structuredPrompt.layout?.background_scene && {
                        background_scene: structuredPrompt.layout.background_scene
                    }),
                    // Add explicit circular flow rule ONLY for types that need sequential flow
                    // Exclude relationship_map and network_graph (they use relationships array for arrow directions)
                    ...(structuredPrompt.layout?.direction === 'circular' &&
                        !['relationship_map', 'network_graph'].includes(structuredPrompt.infographic_type) && {
                        circular_flow_rule: "CLOCKWISE flow: position 1 → 2 → 3 → 4 → 1. Arrows MUST follow ascending position order."
                    })
                },
                elements: structuredPrompt.elements?.map((el: any) => ({
                    position: el.position,
                    label: el.label,
                    ...(el.icon && { icon: el.icon }),
                    ...(el.mood && { mood: el.mood }),
                    ...(el.size && { size: el.size }),
                    ...(el.arrow_to && { arrow_to: el.arrow_to })
                })) || [],
                ...(structuredPrompt.relationships && {
                    relationships: structuredPrompt.relationships.map((rel: any) => ({
                        from: rel.from,
                        to: rel.to,
                        label: rel.label
                    }))
                }),
                ...(structuredPrompt.color_scheme && { color_scheme: structuredPrompt.color_scheme }),
                // Add flow instructions based on infographic type and direction
                ...(() => {
                    const infographicType = structuredPrompt.infographic_type;
                    const direction = structuredPrompt.layout?.direction;
                    const elements = structuredPrompt.elements || [];
                    const flowInstructions: any = {};

                    // Helper function: Generate structured arrow edges (方案 C)
                    const generateArrowEdges = (isCircular: boolean) => {
                        const nodeLabels: Record<string, string> = {};
                        const arrowEdges: any[] = [];

                        // Build node labels map
                        elements.forEach((el: any, idx: number) => {
                            const nodeId = String.fromCharCode(65 + idx); // A, B, C...
                            nodeLabels[nodeId] = el.label;
                        });

                        // Build arrow edges
                        elements.forEach((el: any, idx: number, arr: any[]) => {
                            const nodeA = String.fromCharCode(65 + idx);
                            if (isCircular) {
                                // Circular: A→B→C→D→A (closed loop)
                                const nextIdx = (idx + 1) % arr.length;
                                const nodeB = String.fromCharCode(65 + nextIdx);
                                arrowEdges.push({
                                    from: nodeA,
                                    to: nodeB,
                                    from_label: el.label,
                                    to_label: arr[nextIdx].label,
                                    mermaid: `${nodeA} --> ${nodeB}`
                                });
                            } else {
                                // Sequential: A→B→C→D (no closing edge)
                                if (idx < arr.length - 1) {
                                    const nodeB = String.fromCharCode(65 + idx + 1);
                                    arrowEdges.push({
                                        from: nodeA,
                                        to: nodeB,
                                        from_label: el.label,
                                        to_label: arr[idx + 1].label,
                                        mermaid: `${nodeA} --> ${nodeB}`
                                    });
                                }
                            }
                        });

                        return { node_labels: nodeLabels, arrow_edges: arrowEdges };
                    };

                    // Types that REQUIRE arrows with precise control
                    const arrowRequiredTypes = ['flowchart', 'cycle_diagram', 'process_diagram', 'cause_effect'];

                    // Types that should NOT auto-generate arrows (use relationships instead, or no arrows)
                    const noAutoArrowTypes = ['relationship_map', 'network_graph', 'timeline', 'comparison', 'hierarchy', 'matrix', 'venn_diagram', 'pyramid', 'funnel'];

                    // CYCLE_DIAGRAM - always circular (closed loop)
                    if (infographicType === 'cycle_diagram' && elements.length > 0) {
                        const { node_labels, arrow_edges } = generateArrowEdges(true);
                        flowInstructions.node_labels = node_labels;
                        flowInstructions.arrow_edges = arrow_edges;
                    }

                    // FLOWCHART - check if direction is circular
                    else if (infographicType === 'flowchart' && elements.length > 0) {
                        const isCircular = direction === 'circular';
                        const { node_labels, arrow_edges } = generateArrowEdges(isCircular);
                        flowInstructions.node_labels = node_labels;
                        flowInstructions.arrow_edges = arrow_edges;
                    }

                    // PROCESS_DIAGRAM - sequential (never circular)
                    else if (infographicType === 'process_diagram' && elements.length > 0) {
                        const { node_labels, arrow_edges } = generateArrowEdges(false);
                        flowInstructions.node_labels = node_labels;
                        flowInstructions.arrow_edges = arrow_edges;
                    }

                    // CAUSE_EFFECT - sequential (never circular)
                    else if (infographicType === 'cause_effect' && elements.length > 0) {
                        const { node_labels, arrow_edges } = generateArrowEdges(false);
                        flowInstructions.node_labels = node_labels;
                        flowInstructions.arrow_edges = arrow_edges;
                    }

                    // CONCEPT_MAP with circular direction - closed loop
                    else if (infographicType === 'concept_map' && direction === 'circular' && elements.length > 0) {
                        const { node_labels, arrow_edges } = generateArrowEdges(true);
                        flowInstructions.node_labels = node_labels;
                        flowInstructions.arrow_edges = arrow_edges;
                    }

                    // RELATIONSHIP_MAP - use relationships array (do NOT auto-generate arrows)
                    else if (infographicType === 'relationship_map' && structuredPrompt.relationships?.length > 0) {
                        // Build node labels from elements
                        const nodeLabels: Record<string, string> = {};
                        elements.forEach((el: any, idx: number) => {
                            const nodeId = String.fromCharCode(65 + idx);
                            nodeLabels[nodeId] = el.label;
                        });

                        // Build arrow edges from relationships
                        const arrowEdges = structuredPrompt.relationships.map((rel: any, idx: number) => {
                            // Find node IDs by label
                            const fromNodeId = Object.entries(nodeLabels).find(([k, v]) => v === rel.from)?.[0] || '?';
                            const toNodeId = Object.entries(nodeLabels).find(([k, v]) => v === rel.to)?.[0] || '?';
                            return {
                                from: fromNodeId,
                                to: toNodeId,
                                from_label: rel.from,
                                to_label: rel.to,
                                edge_label: rel.label,
                                mermaid: `${fromNodeId} -->|${rel.label}| ${toNodeId}`
                            };
                        });

                        flowInstructions.node_labels = nodeLabels;
                        flowInstructions.arrow_edges = arrowEdges;
                    }

                    // TIMELINE - no arrows, just chronological order hint
                    else if (infographicType === 'timeline' && elements.length > 0) {
                        const directionMap: any = {
                            'left_to_right': 'LEFT to RIGHT = EARLY to LATE',
                            'top_to_bottom': 'TOP to BOTTOM = EARLY to LATE',
                            'right_to_left': 'RIGHT to LEFT = EARLY to LATE'
                        };
                        const timelineDir = directionMap[direction] || 'LEFT to RIGHT = EARLY to LATE';
                        flowInstructions.timeline_flow_rule = `${timelineDir}. Position 1 is the EARLIEST event, position ${elements.length} is the LATEST. NO arrows needed - use position order only.`;
                    }

                    // Other types: NO auto-generated arrows

                    return flowInstructions;
                })(),
                language_requirement: language === 'Chinese'
                    ? "ALL text labels MUST be in Simplified Chinese (简体中文). NO ENGLISH text anywhere."
                    : "ALL text labels in English.",
                // CRITICAL: Text control for Chinese to prevent pseudo-characters
                ...(language === 'Chinese' && {
                    text_control_critical: "ONLY generate text that is explicitly defined in 'elements' array. ABSOLUTELY NO additional text, speech bubbles, dialogue boxes, or text overlays. If visual storytelling needs communication, use facial expressions, gestures, or visual symbols (💰, ⚠️, 🔥, 👑) instead. NEVER attempt to generate Chinese characters in decorative elements.",
                    pseudo_character_ban: "STRICTLY FORBIDDEN: Any text-like symbols resembling Chinese but not real characters. If uncertain about character accuracy, use icons/symbols instead of attempting text.",
                    // Add explicit whitelist of allowed text
                    allowed_text_whitelist: (() => {
                        const allowedTexts = [];
                        // Collect all text from elements
                        if (structuredPrompt?.elements) {
                            structuredPrompt.elements.forEach((el: any) => {
                                if (el.label) allowedTexts.push(el.label);
                            });
                        }
                        // Add title
                        if (structuredPrompt?.title) allowedTexts.push(structuredPrompt.title);
                        // Add subtitle if exists
                        if (structuredPrompt?.subtitle) allowedTexts.push(structuredPrompt.subtitle);

                        return `ALLOWED TEXT ONLY: You may ONLY render these exact Chinese texts: ${allowedTexts.map(t => `"${t}"`).join(', ')}. ABSOLUTELY NO other text, characters, or text-like symbols anywhere in the image.`;
                    })()
                })
            };
        } else {
            // Legacy string prompt - keep as string for backwards compatibility
            descriptionContent = basePrompt as string;
        }

        // 1. Initialize base JSON structure
        let promptJSON: ImagePromptJSON = {
            subject: {
                description: descriptionContent  // Can be object or string
            },
            style: {
                name: "Modern Infographic",
                description: "Clean, modern infographic style with clear information hierarchy, charts, icons, and data visualization elements - NOT a painting or drawing"
            },
            composition: {
                aspect_ratio: "4:3",
                framing: structuredPrompt
                    ? `${structuredPrompt.infographic_type.toUpperCase()} layout with ${structuredPrompt.layout?.sections || 4} sections, ${structuredPrompt.layout?.direction?.replace(/_/g, ' ')} flow`
                    : "Infographic composition with clear sections, data visualization elements, icons, and structured layout"
            },
            constraints: {
                negative_prompt: [
                    "maps",
                    "realistic faces",
                    "distorted figures",
                    "low quality",
                    "blurry",
                    "pseudo-characters",
                    "fake text",
                    "fake chinese characters",
                    "unreadable text",
                    "gibberish text",
                    "speech bubbles with text",
                    "dialogue boxes with characters",
                    "text overlays not in elements",
                    "incorrect arrow directions",
                    "illogical flow"
                ],
                safety: "family friendly",
                format_requirements: "Must be an INFOGRAPHIC with structured information, correct arrow logic, and clear visual flow",
                text_generation_rules: language === 'Chinese'
                    ? "CRITICAL: ALL text MUST be 100% accurate Simplified Chinese. NO ENGLISH. Pseudo-characters STRICTLY FORBIDDEN."
                    : "CRITICAL: Text must be 100% accurate English spelling."
            }
        };

        // 2. Apply Style Template
        if (imageStyle) {
            if (imageStyle.preset === 'custom' && imageStyle.customPrompt) {
                promptJSON.style.name = "Custom Style";
                promptJSON.style.description = imageStyle.customPrompt;
                // Add custom negative prompts to array
                if (Array.isArray(promptJSON.constraints!.negative_prompt)) {
                    promptJSON.constraints!.negative_prompt.push("realistic human faces", "maps");
                }
            } else if (imageStyle.preset === 'general') {
                promptJSON.style.name = "Varied Style";
                promptJSON.style.description = "Style defined in subject description";
            } else {
                const styleDefinition = getImageStyleDefinition(imageStyle.preset);
                console.log(`[ScriptService] Style lookup: preset='${imageStyle.preset}', found='${styleDefinition?.id}', style.name='${styleDefinition?.jsonTemplate?.style?.name}'`);
                if (styleDefinition && styleDefinition.jsonTemplate) {
                    const enhancedSubjectDescription = promptJSON.subject.description;
                    promptJSON = {
                        ...promptJSON,
                        subject: { ...promptJSON.subject, description: enhancedSubjectDescription },
                        style: { ...promptJSON.style, ...styleDefinition.jsonTemplate.style },
                        composition: { ...promptJSON.composition, ...styleDefinition.jsonTemplate.composition },
                        constraints: { ...promptJSON.constraints, ...styleDefinition.jsonTemplate.constraints }
                    };
                }
            }
        }

        // 3. Add Text Overlay / Title Constraints
        if (bookTitle) {
            if (isFirstImage) {
                promptJSON.text_overlay = {
                    content: structuredPrompt?.title || bookTitle,
                    language: language,
                    style: language === 'Chinese'
                        ? "YouTube-style MASSIVE bold Simplified Chinese characters"
                        : "YouTube-style MASSIVE bold English font",
                    instructions: {
                        type: "FIRST_IMAGE_THUMBNAIL",
                        text: structuredPrompt?.title || bookTitle,
                        max_length: language === 'Chinese' ? 6 : 6,
                        max_length_unit: language === 'Chinese' ? "Chinese characters" : "words",
                        size: "MASSIVE",
                        coverage: "30-50%",
                        contrast: "HIGH",
                        text_rules: language === 'Chinese'
                            ? [
                                "ABSOLUTELY NO ENGLISH TEXT",
                                "NO PSEUDO-CHARACTERS",
                                "ONLY accurate Simplified Chinese"
                            ]
                            : ["Correct English spelling required"]
                    }
                };
            } else {
                promptJSON.text_overlay = {
                    content: structuredPrompt?.title || bookTitle,
                    language: language,
                    style: language === 'Chinese' ? "Bold Simplified Chinese characters" : "Bold English font",
                    instructions: {
                        type: "REGULAR_IMAGE",
                        text: structuredPrompt?.title || bookTitle,
                        text_rules: language === 'Chinese'
                            ? [
                                "ONLY Chinese characters",
                                "NO ENGLISH",
                                "NO pseudo-characters"
                            ]
                            : ["Correct spelling required"]
                    }
                };
            }
        }

        // 4. Return as JSON string
        return JSON.stringify(promptJSON, null, 2);
    },

    // Helper function to convert structured prompt to detailed description
    convertStructuredPromptToDescription(prompt: any, language: string): string {
        const { infographic_type, title, subtitle, layout, elements, color_scheme, era_context, cultural_context } = prompt;

        let description = '';

        // Header
        description += `${infographic_type.toUpperCase()} INFOGRAPHIC\n\n`;
        description += `Title: "${title}"${subtitle ? ` - "${subtitle}"` : ''}\n\n`;

        // Cultural and Era context
        if (cultural_context || era_context) {
            description += `SETTING: ${cultural_context?.toUpperCase() || ''} ${era_context || ''}\n`;
            if (cultural_context === 'chinese') {
                description += `- ALL characters must be PANDA versions\n`;
                description += `- ALL architecture must be traditional Chinese style\n`;
                description += `- ALL clothing must be historically accurate Chinese attire\n\n`;
            }
        }

        // Layout instructions
        description += `LAYOUT:\n`;
        description += `- Direction: ${layout?.direction?.replace(/_/g, ' ').toUpperCase()}\n`;
        description += `- Number of sections: ${layout?.sections || elements?.length || 4}\n`;
        if (layout?.background_scene) {
            description += `- Background scene: ${layout.background_scene}\n`;
        }
        description += '\n';

        // Elements with PRECISE arrow logic
        description += `ELEMENTS (IN SEQUENCE):\n`;
        if (elements && elements.length > 0) {
            elements.forEach((el: any, idx: number) => {
                description += `\n[Position ${el.position}] "${el.label}"`;
                if (el.icon) description += ` | Icon: ${el.icon}`;
                if (el.mood) description += ` | Mood: ${el.mood.toUpperCase()}`;
                if (el.size) description += ` | Size: ${el.size.toUpperCase()}`;

                // CRITICAL: Arrow logic
                if (el.arrow_to) {
                    const targetEl = elements.find((e: any) => e.position === el.arrow_to);
                    if (targetEl) {
                        description += `\n   → ARROW pointing TO Position ${el.arrow_to} ("${targetEl.label}")`;
                    }
                }
            });
        }
        description += '\n\n';

        // Arrow flow summary for AI clarity (for timeline/flowchart)
        if (infographic_type === 'timeline' || infographic_type === 'flowchart') {
            description += `ARROW FLOW (CRITICAL - must be followed exactly):\n`;
            const arrowFlow = elements
                ?.filter((el: any) => el.arrow_to)
                ?.map((el: any) => {
                    const target = elements.find((e: any) => e.position === el.arrow_to);
                    return `"${el.label}" → "${target?.label || '?'}"`;
                })
                ?.join('\n');
            if (arrowFlow) {
                description += arrowFlow + '\n\n';
            }
        }

        // RELATIONSHIPS (CRITICAL for relationship_map - defines arrow directions)
        const relationships = prompt.relationships;
        if (relationships && relationships.length > 0) {
            description += `RELATIONSHIPS (CRITICAL - arrows MUST follow these directions):\n`;
            relationships.forEach((rel: any) => {
                description += `- "${rel.from}" → "${rel.to}": ${rel.label}\n`;
            });
            description += `\nARROW SUMMARY:\n`;
            relationships.forEach((rel: any) => {
                description += `Draw arrow FROM "${rel.from}" TO "${rel.to}" with label "${rel.label}"\n`;
            });
            description += '\n';
        }

        // Color scheme
        if (color_scheme) {
            description += `COLOR SCHEME: ${color_scheme}\n\n`;
        }

        // Language constraint
        if (language === 'Chinese') {
            description += `LANGUAGE: ALL text labels MUST be in Simplified Chinese (简体中文). NO ENGLISH text anywhere.\n`;
        }

        return description;
    },

    /**
     * @deprecated This function was used for HTML + Puppeteer mode which has been archived.
     * Now we use Gemini 3.0 Pro Image directly for all slides generation.
     * Kept for reference only - do not use in new code.
     */
    async generateHtmlPrompt(
        basePrompt: string,
        bookTitle?: string,
        language: string = 'English',
        isFirstImage: boolean = false
    ): Promise<string> {
        // DEPRECATED: Construct a prompt for the HTML generator (no longer used)
        let prompt = `Create a presentation slide based on this description: "${basePrompt}".`;

        if (bookTitle) {
            if (isFirstImage) {
                // YouTube Thumbnail Style for first image
                prompt += `\n\nCRITICAL REQUIREMENT - FIRST IMAGE (YouTube Thumbnail Style):`;
                prompt += `\n- The slide MUST feature BRIEF, IMPACTFUL text from "${bookTitle}" (MAX 6 ${language === 'Chinese' ? 'Chinese characters' : 'English words'})`;
                prompt += `\n- Text must be MASSIVE, covering 30-50% of the slide area`;
                prompt += `\n- Use HIGH CONTRAST: bright text on dark gradient background (or vice versa)`;
                prompt += `\n- Style: Bold, eye-catching, optimized for thumbnail visibility`;
                prompt += `\n- Text examples: "${language === 'Chinese' ? '真相, 突破, 秘密, 为什么' : 'TRUTH, BREAKTHROUGH, SECRET, WHY'}"`;
                prompt += `\n- AVOID: Full book title, long phrases, more than 6 ${language === 'Chinese' ? 'characters' : 'words'}`;
            } else {
                prompt += `\n\nCRITICAL REQUIREMENT: The slide MUST prominently display the book title: "${bookTitle}".`;
            }
        }

        if (language === 'Chinese') {
            prompt += `\n\nLANGUAGE REQUIREMENT: All text on the slide MUST be in Simplified Chinese. Translate any English concepts from the description into natural Chinese.`;
            prompt += `\n\nCRITICAL - TEXT ACCURACY (READ CAREFULLY):`;
            prompt += `\n- Pseudo-characters (characters that LOOK like Chinese but are NOT real characters) are STRICTLY FORBIDDEN`;
            prompt += `\n- If you are uncertain about ANY character, use icons/symbols ONLY and omit text entirely`;
            prompt += `\n- When including Chinese text, triple-check each character is correct`;
            prompt += `\n- Better to have NO text than incorrect text`;
        } else {
            prompt += `\n\nLANGUAGE REQUIREMENT: All text on the slide MUST be in English.`;
            prompt += `\n\nCRITICAL: Ensure 100% correct spelling or omit text if uncertain.`;
        }

        return prompt;
    },

    /**
     * Generate script using OpenRouter API
     * Simplified version without strict JSON schema (uses text prompt to request JSON format)
     */
    async generateScriptWithOpenRouter(
        text: string,
        language: string = 'English',
        bookTitle: string = 'Unknown Book',
        imageStyle: ImageStyleConfig = { preset: 'zelda_botw' },
        generationContext?: ScriptGenerationContext
    ): Promise<{ script: ScriptSegment[], usageMetadata?: any }> {
        console.log(`[ScriptService] Generating script with OpenRouter for text length: ${text.length}, Language: ${language}, Style: ${imageStyle.preset}`);

        if (!openrouterService.isConfigured()) {
            throw new Error('OpenRouter API is not configured');
        }

        const models = openrouterService.getModels();
        const systemPrompt = SCRIPT_SYSTEM_PROMPT(language, bookTitle, imageStyle);
        const bookContentForPrompt = buildBookContentForPrompt(text, generationContext);

        // Build user prompt
        const userPrompt = `Here is the text of a book. Create a 15-minute podcast script (at least 4500 words) with exactly 18-22 segments that deeply analyzes the content. Each segment should be a long paragraph (200-300 words). Follow the structure and requirements in the system instruction carefully.

IMPORTANT: Your response MUST be a valid JSON array. Do NOT include any markdown formatting or code blocks. Return ONLY the raw JSON array.

BOOK CONTENT:
${bookContentForPrompt}`;

        const maxRetries = 3;
        let lastError: Error | null = null;

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                console.log(`[ScriptService/OpenRouter] Attempt ${attempt}/${maxRetries}...`);

                const { text: responseText, usage, cost, model } = await openrouterService.generateText(
                    userPrompt,
                    systemPrompt,
                    'json'
                );

                // Parse JSON response
                let script: ScriptSegment[];
                try {
                    // Clean response if it contains markdown code blocks
                    let cleanedText = responseText.trim();
                    if (cleanedText.startsWith('```json')) {
                        cleanedText = cleanedText.replace(/^```json\s*/, '').replace(/\s*```$/, '');
                    } else if (cleanedText.startsWith('```')) {
                        cleanedText = cleanedText.replace(/^```\s*/, '').replace(/\s*```$/, '');
                    }

                    script = JSON.parse(cleanedText);
                } catch (parseError) {
                    console.error(`[ScriptService/OpenRouter] Failed to parse JSON response:`, responseText.substring(0, 500));
                    throw new Error(`Invalid JSON response from OpenRouter: ${parseError}`);
                }

                // Validate script structure
                if (!Array.isArray(script) || script.length < 10) {
                    throw new Error(`Invalid script: expected array with 10+ segments, got ${Array.isArray(script) ? script.length : typeof script}`);
                }

                console.log(`[ScriptService/OpenRouter] Script generated successfully with ${script.length} segments. Cost: $${cost?.totalUSD?.toFixed(6) || 'unknown'}`);
                const validation = validateGeneratedScript(script, language, imageStyle);
                console.log(`[ScriptService/OpenRouter] Validation metrics: segments=${validation.metrics.segmentCount}, chars=${validation.metrics.totalChars}, estDuration=${validation.metrics.estimatedDurationSeconds.toFixed(1)}s`);
                if (!validation.ok) {
                    throw new Error(`[ScriptService/OpenRouter] Generated script failed quality gate: ${validation.reasons.join('; ')}`);
                }

                // ============================================================
                // ASSIGN imageGroup: N segments share one image
                // ============================================================
                const segmentsPerImage = imageStyle.segmentsPerImage || 4;  // Default N=4 (5 slides for 20 segments)
                const isOnePager = imageStyle.preset === 'infographic_1pager';
                // All styles use segmentsPerImage to determine how many segments share one slide
                const effectiveN = isOnePager ? script.length : segmentsPerImage;

                console.log(`[ScriptService/OpenRouter] Assigning imageGroup with N=${effectiveN} (${isOnePager ? '1pager mode' : 'standard mode - ~5 slides per podcast'})`);

                // P1-B Enhancement: Merge content from all segments in an imageGroup into first segment's visualPrompt
                const totalGroups = Math.ceil(script.length / effectiveN);

                for (let groupIdx = 0; groupIdx < totalGroups; groupIdx++) {
                    const groupStart = groupIdx * effectiveN;
                    const groupEnd = Math.min(groupStart + effectiveN, script.length);

                    // Collect text content from all segments in this group
                    const groupTexts: string[] = [];
                    for (let i = groupStart; i < groupEnd; i++) {
                        script[i].imageGroup = groupIdx;
                        if (script[i].text) {
                            groupTexts.push(script[i].text);
                        }
                    }

                    // For PPT mode (effectiveN=1), keep original visualPrompt
                    // For standard mode: enhance first segment's visualPrompt with merged content
                    if (effectiveN > 1 && groupTexts.length > 1) {
                        const firstSegment = script[groupStart];
                        const originalPrompt = firstSegment.visualPrompt;

                        // Create enhanced prompt with multiple segments' key points
                        const keyPoints = groupTexts.map((text, idx) => {
                            const keyPoint = text.substring(0, 80).replace(/\n/g, ' ').trim();
                            return `• Segment ${groupStart + idx + 1}: ${keyPoint}...`;
                        }).join('\n');

                        // If visualPrompt is a string, append key points; if null/object, create new
                        if (typeof originalPrompt === 'string' && originalPrompt.length > 0) {
                            firstSegment.visualPrompt = `${originalPrompt}\n\n--- GROUP ${groupIdx + 1} CONTENT (${groupTexts.length} segments) ---\n${keyPoints}`;
                        } else if (originalPrompt === null || originalPrompt === undefined) {
                            firstSegment.visualPrompt = `Generate an informative slide for Group ${groupIdx + 1}:\n\n${keyPoints}`;
                        }
                    }

                    // Set visualPrompt to null for non-first segments
                    for (let i = groupStart + 1; i < groupEnd; i++) {
                        script[i].visualPrompt = null;
                    }
                }

                console.log(`[ScriptService/OpenRouter] Created ${totalGroups} image groups (P1-B enhanced: merged content)`);

                const usageMetadata = {
                    script: {
                        inputTokens: usage?.inputTokens || 0,
                        outputTokens: usage?.outputTokens || 0,
                        totalTokens: usage?.totalTokens || 0,
                        model: model || models.textModel,
                        provider: 'openrouter',
                        costUSD: cost?.totalUSD || 0
                    }
                };

                return { script, usageMetadata };

            } catch (error) {
                lastError = error instanceof Error ? error : new Error(String(error));
                console.error(`[ScriptService/OpenRouter] Attempt ${attempt} failed:`, lastError.message);

                if (attempt < maxRetries) {
                    const waitTime = attempt * 5000;
                    console.log(`[ScriptService/OpenRouter] Waiting ${waitTime}ms before retry...`);
                    await new Promise(resolve => setTimeout(resolve, waitTime));
                }
            }
        }

        throw lastError || new Error('Failed to generate script with OpenRouter after all retries');
    }
};
