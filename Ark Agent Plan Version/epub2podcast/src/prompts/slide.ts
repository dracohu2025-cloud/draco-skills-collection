/**
 * Slide Generation Prompts (Unified Design System)
 * 
 * Key improvements for style consistency:
 * 1. Unified Design Tokens - consistent colors, fonts, spacing
 * 2. Style Lock - all slides share the same visual language
 * 3. Template Layouts - standardized layout patterns
 * 4. Decorative Elements - consistent graphic style
 */

import { Language, extractKeyPoint, combineSegmentTexts } from './utils.js';

// ============================================================
// DESIGN SYSTEM - Unified Visual Tokens
// ============================================================

/**
 * Design System for consistent slides
 * All slides in a podcast MUST follow this design system
 */
const DESIGN_SYSTEM = {
    // Color Palette - Deep Blue Professional Theme
    colors: {
        primary: '#1E3A5F',      // Deep navy blue - main headers
        secondary: '#2E5077',    // Medium blue - subheaders
        accent: '#4A90A4',       // Teal accent - highlights, icons
        background: '#F5F7FA',   // Light gray-blue - main background
        backgroundAlt: '#E8EDF2', // Slightly darker - card backgrounds
        text: '#2C3E50',         // Dark gray-blue - body text
        textLight: '#5D6D7E',    // Medium gray - secondary text
        white: '#FFFFFF',        // Pure white - cards, contrast
        success: '#27AE60',      // Green - positive indicators
        warning: '#F39C12',      // Orange - attention items
    },
    
    // Typography
    fonts: {
        heading: 'Sans-serif, clean geometric style (like Helvetica Neue, SF Pro)',
        body: 'Sans-serif, highly readable (like Inter, Roboto)',
        chinese: 'Noto Sans SC, PingFang SC, Microsoft YaHei',
    },
    
    // Layout Grid
    layout: {
        margin: '48px',
        gutter: '24px',
        cardRadius: '12px',
        shadowStyle: 'subtle drop shadow (0 4px 12px rgba(0,0,0,0.08))',
    },
    
    // Decorative Elements
    decorations: {
        icons: 'Flat, minimalist line icons with consistent 2px stroke',
        shapes: 'Rounded rectangles, circles, soft geometric shapes',
        illustrations: 'Flat vector illustrations, limited to 3-4 colors from palette',
        patterns: 'Subtle dot grid or line patterns in background',
    }
};

/**
 * Generate the Design System section for prompts
 */
function getDesignSystemPrompt(language: Language): string {
    const colors = DESIGN_SYSTEM.colors;
    
    return `
<design_system>
【统一设计规范 - 所有幻灯片必须严格遵循】

<color_palette>
主色调: ${colors.primary} (深海军蓝 - 标题、重要元素)
次色调: ${colors.secondary} (中蓝色 - 副标题、分隔线)
强调色: ${colors.accent} (青色 - 图标、高亮、装饰)
背景色: ${colors.background} (浅灰蓝 - 主背景)
卡片背景: ${colors.backgroundAlt} (深一点的灰蓝 - 内容区块)
正文色: ${colors.text} (深灰蓝 - 主要文字)
辅助文字: ${colors.textLight} (中灰 - 次要文字)
</color_palette>

<typography>
标题字体: 无衬线、几何风格、粗体
正文字体: 无衬线、高可读性、常规字重
${language === 'Chinese' ? '中文字体: 思源黑体风格，简洁现代' : ''}
标题大小: 大而醒目，占据视觉焦点
正文大小: 清晰可读，不要过小
</typography>

<layout_rules>
页边距: 充足的留白，不要贴边
内容区块: 使用圆角矩形卡片承载内容
对齐方式: 左对齐或居中，保持一致
视觉层次: 标题 > 副标题 > 要点 > 说明文字
</layout_rules>

<decorative_elements>
图标风格: 扁平化、线性图标，2px线宽，圆角端点
形状: 圆角矩形、圆形、柔和的几何图形
插图: 扁平矢量风格，仅使用调色板中的颜色
背景纹理: 可选用淡淡的点阵或线条图案
禁止使用: 渐变过渡、3D效果、复杂阴影、照片
</decorative_elements>

<consistency_rules>
- 所有幻灯片必须看起来属于同一套设计
- 相同类型的元素必须使用相同的样式
- 颜色只能从调色板中选择
- 保持视觉语言的统一性和连贯性
</consistency_rules>
</design_system>`;
}

export interface SlidePromptParams {
    /** Segments that this slide covers */
    segmentTexts: string[];
    /** Book title */
    bookTitle: string;
    /** Current chapter/section title (optional) */
    chapterTitle?: string;
    /** Slide index (0-based) */
    slideIndex: number;
    /** Total number of slides */
    totalSlides: number;
    /** Image style preset */
    stylePreset: string;
    /** Language */
    language: Language;
    /** Whether this is the first slide (cover/thumbnail style) */
    isFirstSlide?: boolean;
}

/**
 * Generate Slide image prompt with unified design system
 */
export function getSlideGenerationPrompt(params: SlidePromptParams): string {
    const {
        segmentTexts,
        bookTitle,
        chapterTitle,
        slideIndex,
        totalSlides,
        language,
        isFirstSlide = false,
    } = params;

    // Extract key points from each segment
    const keyPoints = segmentTexts
        .map(text => extractKeyPoint(text, language))
        .filter(point => point.length > 0);

    // Combine segment texts for context
    const combinedContent = combineSegmentTexts(segmentTexts, 600);

    // Build slide title
    const slideTitle = chapterTitle || (
        language === 'Chinese'
            ? `第 ${slideIndex + 1} 页`
            : `Slide ${slideIndex + 1}`
    );

    // Build bullet points
    const bulletPoints = keyPoints.length > 0
        ? keyPoints.map((point, i) => `${i + 1}. ${point}`).join('\n')
        : combinedContent.substring(0, 300);

    // Design system (included in every prompt for consistency)
    const designSystem = getDesignSystemPrompt(language);

    // First slide (cover) has special requirements
    if (isFirstSlide) {
        return `你是一位专业的演示文稿设计师。请生成一张**封面幻灯片**。

${designSystem}

<cover_slide_requirements>
【封面设计要求】
- 这是播客的第一张幻灯片，将用作 YouTube 缩略图
- 标题必须简短有力：${language === 'Chinese' ? '最多6个汉字' : 'MAX 6 words'}
- 标题占据画面 30-40% 的面积，高对比度
- 使用主色调 (#1E3A5F) 作为标题颜色或背景
- 添加与主题相关的简洁图标或装饰元素
- 整体感觉：专业、现代、吸引眼球
</cover_slide_requirements>

<content>
书籍标题: "${bookTitle}"
内容摘要: ${combinedContent.substring(0, 200)}
</content>

<output_requirements>
- 分辨率: 4K, 16:9 比例
- 风格: 扁平化设计，统一配色
${language === 'Chinese' ? '- 【关键】中文必须100%准确，禁止伪汉字，不确定就不写' : '- Text must be 100% accurate'}
</output_requirements>

请生成封面幻灯片。`;
    }

    // Regular content slides
    return `你是一位专业的演示文稿设计师。请生成一张**内容幻灯片**。

${designSystem}

<slide_content>
【页面标题】${slideTitle}

【核心要点】
${bulletPoints}

【详细内容】
${combinedContent}
</slide_content>

<reference_info>
书籍: "${bookTitle}"
位置: 第 ${slideIndex + 1} / ${totalSlides} 页
</reference_info>

<layout_suggestion>
推荐布局 (根据内容自动选择最佳):
- 如果是2-4个要点: 使用左右分栏或上下分区
- 如果是列表: 使用图标+文字的列表形式
- 如果是对比: 使用左右对比布局
- 如果是流程: 使用步骤流程图
- 每个要点配一个相关的小图标
</layout_suggestion>

<output_requirements>
- 分辨率: 4K, 16:9 比例
- 风格: 与整套幻灯片保持一致的扁平化设计
- 配色: 严格使用设计系统中的颜色
- 图标: 扁平线性风格，与内容相关
${language === 'Chinese' ? '- 【关键】中文必须100%准确，禁止伪汉字，不确定就用图标代替' : '- Text must be 100% accurate'}
</output_requirements>

请生成内容幻灯片。`;
}

/**
 * Simplified prompt for non-first slides (maintains design system reference)
 */
export function getSimpleSlidePrompt(params: {
    content: string;
    bookTitle: string;
    slideIndex: number;
    totalSlides: number;
    language: Language;
}): string {
    const { content, bookTitle, slideIndex, totalSlides, language } = params;

    const designSystem = getDesignSystemPrompt(language);

    return `你是一位专业的演示文稿设计师。

${designSystem}

<slide_content>
${content}
</slide_content>

<reference>
书籍: "${bookTitle}"
位置: 第 ${slideIndex + 1} / ${totalSlides} 页
</reference>

<requirements>
- 4K分辨率，16:9比例
- 严格遵循设计系统的配色和风格
- 扁平化设计，统一视觉语言
${language === 'Chinese' ? '- 中文必须准确，禁止伪汉字' : '- Accurate text only'}
</requirements>

请生成幻灯片。`;
}

/**
 * Generate prompt for a group of segments
 */
export function getGroupSlidePrompt(params: {
    segmentGroup: Array<{ text: string; speaker: string }>;
    bookTitle: string;
    chapterTitle?: string;
    groupIndex: number;
    totalGroups: number;
    stylePreset: string;
    language: Language;
}): string {
    const { segmentGroup, bookTitle, chapterTitle, groupIndex, totalGroups, stylePreset, language } = params;

    const texts = segmentGroup.map(s => s.text);
    const isFirstGroup = groupIndex === 0;

    return getSlideGenerationPrompt({
        segmentTexts: texts,
        bookTitle,
        chapterTitle,
        slideIndex: groupIndex,
        totalSlides: totalGroups,
        stylePreset,
        language,
        isFirstSlide: isFirstGroup,
    });
}

/**
 * Regeneration prompt with design system emphasis
 */
export function getSlideRegenerationPrompt(params: {
    originalPrompt: string;
    errorReason?: string;
    language: Language;
}): string {
    const { originalPrompt, errorReason, language } = params;

    return `请重新生成这张幻灯片，特别注意以下要求：

<retry_requirements>
1. 严格遵循设计系统的统一配色（深蓝主色调）
2. 保持扁平化设计风格
3. ${language === 'Chinese' ? '中文必须100%准确' : 'Text accuracy is critical'}
${errorReason ? `4. 上次问题: ${errorReason}` : ''}
</retry_requirements>

${originalPrompt}`;
}
