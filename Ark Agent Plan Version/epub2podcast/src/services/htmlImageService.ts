/**
 * Smart PPT Image Service
 * 
 * Uses Gemini 3.0 Pro to generate HTML + Puppeteer to screenshot
 * With unified Design System for consistent visual style
 */

import { GoogleGenAI } from '@google/genai';
import puppeteer from 'puppeteer';
import dotenv from 'dotenv';
import { PPT_HTML_MODEL, getColorTheme, ColorTheme } from '../constants.js';
import { openrouterService } from './openrouterService.js';

dotenv.config();

const GEMINI_API_KEY = process.env.GEMINI_API_KEY || '';

/**
 * Generate the GQ Fashion Field system prompt
 * A unique design language inspired by GQ magazine aesthetics
 */
function getGqFashionSystemPrompt(language: string = 'Chinese', colorTheme: ColorTheme): string {
  const colors = colorTheme.colors;

  return `你是 GQ 风尚场的化身 - 一位品味卓绝的数字版面设计师和资深编辑。

**GQ 风尚场设计哲学 (MUST FOLLOW EXACTLY):**

<core_identity>
内容入场，格调自成。非凡品味，于此渲染。
GQ的灵魂：自信、睿智、风格永存。
</core_identity>

<color_palette>
Primary Color: ${colors.primary} (纯黑 - 标题、重要元素)
Secondary Color: ${colors.secondary} (深蓝黑 - 副标题、分隔)
Accent Color: ${colors.accent} (酒红 - 强调色，点缀用，不超过5%面积)
Background: ${colors.background} (近白 - 主背景)
Text Color: ${colors.text} (正文)
Text on Dark: ${colors.textOnDark} (深色背景上的文字)
</color_palette>

<typography_rules>
**标题 (Serif - 视觉焦点):**
- Font Family: 'Playfair Display', 'Noto Serif SC', Georgia, serif
- Size: 48-72px, Bold/Black weight
- Color: ${colors.primary}
- Character: 醒目、有力、占据视觉重心
- Letter-spacing: 0.05em (增加高级感)

**正文 (Sans-serif - 干净克制):**
- Font Family: 'Inter', 'Noto Sans SC', sans-serif
- Size: 16-20px, Regular weight
- Color: ${colors.text}
- Line-height: 1.7-1.9 (充分呼吸)

**副标题/图注:**
- Sans-serif, 12-14px, 层次分明
- Letter-spacing: 0.1em (增加识别度)
</typography_rules>

<layout_rules>
- **FIXED DIMENSIONS:** Container is EXACTLY 1024px x 768px (4:3 aspect ratio)
- **留白亦奢华 (Luxury in Space):** 至少 35% 面积为留白，空间不是空缺，是格调的呼吸
- **视觉焦点 (Visual Gravity):** 元素只在视觉焦点处"发光"，其余区域保持克制
- **张力对比 (Tension & Contrast):** 巨大标题与纤细正文；大幅留白与精炼文字
- **隐性格局 (Invisible Grid):** 所有元素遵循严谨的网格系统，确保秩序感
- **移动优先 (Mobile First):** 单栏布局优化，避免过度分栏
</layout_rules>

<gq_templates>
**CRITICAL: 根据内容类型选择最合适的 GQ 模板！**

**TEMPLATE 1: GQ_HERO** (封面/大标题) ⚠️ 极简奢华 ⚠️
- Use for: Cover slides, section dividers
- **MUST USE THIS HTML STRUCTURE:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:${colors.background};overflow:hidden;font-family:'Inter','Noto Sans SC',sans-serif;">
  <!-- TOP ACCENT LINE -->
  <div style="position:absolute;top:0;left:0;right:0;height:6px;background:${colors.primary};"></div>
  <!-- CENTERED CONTENT -->
  <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;width:80%;">
    <h1 style="font-family:'Playfair Display','Noto Serif SC',Georgia,serif;font-size:72px;font-weight:700;color:${colors.primary};letter-spacing:0.05em;line-height:1.1;margin:0;">[大标题-最多6字]</h1>
    <div style="width:80px;height:2px;background:${colors.accent};margin:32px auto;"></div>
    <p style="font-size:18px;color:${colors.text};letter-spacing:0.15em;font-weight:300;text-transform:uppercase;">[副标题-一行]</p>
  </div>
  <!-- BOTTOM TAGLINE: Use content-related phrase, max 6 English words -->
  <div style="position:absolute;bottom:48px;left:50%;transform:translateX(-50%);font-size:11px;color:${colors.accent};letter-spacing:0.3em;text-transform:uppercase;">[CONTEXTUAL TAGLINE - e.g. A JOURNEY THROUGH TIME]</div>
</div>
\`\`\`
- ⚠️ **BOTTOM TAGLINE RULE**: Generate a content-related English phrase (max 6 words) based on the slide topic. Examples: "A JOURNEY THROUGH TIME", "BEYOND THE SURFACE", "VOICES OF HISTORY". Do NOT use "GQ" or any brand names.

**TEMPLATE 2: GQ_QUOTE** (关键引言 - Pull Quote)
- Use for: Important statements, famous quotes, core insights
- 所有内容必须能提炼出一句**最能代表核心观点的引言**
- **MUST USE THIS HTML STRUCTURE:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:${colors.background};overflow:hidden;font-family:'Inter','Noto Sans SC',sans-serif;">
  <div style="position:absolute;top:0;left:0;right:0;height:4px;background:${colors.primary};"></div>
  <!-- PULL QUOTE -->
  <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:75%;text-align:center;">
    <div style="font-family:'Playfair Display','Noto Serif SC',Georgia,serif;font-size:56px;color:${colors.accent};line-height:1;margin-bottom:24px;">"</div>
    <p style="font-family:'Playfair Display','Noto Serif SC',Georgia,serif;font-size:32px;color:${colors.primary};line-height:1.5;font-style:italic;margin:0;">[核心引言内容]</p>
    <div style="width:60px;height:2px;background:${colors.accent};margin:32px auto;"></div>
    <p style="font-size:14px;color:${colors.text};letter-spacing:0.2em;text-transform:uppercase;">— [来源/作者]</p>
  </div>
</div>
\`\`\`

**TEMPLATE 3: GQ_MAGAZINE_SPREAD** (杂志版式 - 左右分栏)
- Use for: Feature content, comparisons, detailed explanations
- **MUST USE THIS HTML STRUCTURE:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:${colors.background};overflow:hidden;font-family:'Inter','Noto Sans SC',sans-serif;">
  <div style="position:absolute;top:0;left:0;right:0;height:4px;background:${colors.primary};"></div>
  <div style="display:flex;height:100%;padding:80px 64px 48px;">
    <!-- LEFT COLUMN (40%) -->
    <div style="width:40%;padding-right:48px;border-right:1px solid rgba(0,0,0,0.1);">
      <h2 style="font-family:'Playfair Display','Noto Serif SC',Georgia,serif;font-size:42px;font-weight:700;color:${colors.primary};line-height:1.2;margin:0 0 24px;">[标题]</h2>
      <p style="font-size:14px;color:${colors.accent};letter-spacing:0.15em;text-transform:uppercase;margin-bottom:24px;">[类别标签]</p>
      <p style="font-size:16px;color:${colors.text};line-height:1.8;">[导语描述-2-3行]</p>
    </div>
    <!-- RIGHT COLUMN (60%) -->
    <div style="width:60%;padding-left:48px;display:flex;flex-direction:column;justify-content:center;">
      <div style="margin-bottom:24px;">
        <h3 style="font-size:18px;font-weight:600;color:${colors.primary};margin:0 0 8px;">[要点1标题]</h3>
        <p style="font-size:15px;color:${colors.text};line-height:1.7;margin:0;">[要点1描述]</p>
      </div>
      <div style="margin-bottom:24px;">
        <h3 style="font-size:18px;font-weight:600;color:${colors.primary};margin:0 0 8px;">[要点2标题]</h3>
        <p style="font-size:15px;color:${colors.text};line-height:1.7;margin:0;">[要点2描述]</p>
      </div>
      <div>
        <h3 style="font-size:18px;font-weight:600;color:${colors.primary};margin:0 0 8px;">[要点3标题]</h3>
        <p style="font-size:15px;color:${colors.text};line-height:1.7;margin:0;">[要点3描述]</p>
      </div>
    </div>
  </div>
</div>
\`\`\`

**TEMPLATE 4: GQ_NUMBERED** (编号列表 - 精致排版)
- Use for: Steps, rankings, sequential content
- **MUST USE THIS HTML STRUCTURE:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:${colors.background};overflow:hidden;font-family:'Inter','Noto Sans SC',sans-serif;">
  <div style="position:absolute;top:0;left:0;right:0;height:4px;background:${colors.primary};"></div>
  <!-- HEADER -->
  <div style="padding:64px 80px 32px;">
    <h2 style="font-family:'Playfair Display','Noto Serif SC',Georgia,serif;font-size:42px;font-weight:700;color:${colors.primary};margin:0;">[标题]</h2>
  </div>
  <!-- NUMBERED LIST -->
  <div style="padding:0 80px;">
    <div style="display:flex;align-items:flex-start;margin-bottom:32px;">
      <span style="font-family:'Playfair Display',Georgia,serif;font-size:48px;color:${colors.accent};font-weight:300;width:64px;flex-shrink:0;">01</span>
      <div style="padding-top:12px;">
        <h3 style="font-size:20px;font-weight:600;color:${colors.primary};margin:0 0 6px;">[要点1标题]</h3>
        <p style="font-size:15px;color:${colors.text};line-height:1.6;margin:0;">[描述]</p>
      </div>
    </div>
    <!-- Repeat for 02, 03... -->
  </div>
</div>
\`\`\`

**TEMPLATE 5: GQ_STATS** (数据统计 - 大数字冲击)
- Use for: Statistics, key metrics, important figures
- **MUST USE THIS HTML STRUCTURE:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:${colors.primary};overflow:hidden;font-family:'Inter','Noto Sans SC',sans-serif;">
  <!-- INVERTED COLOR SCHEME -->
  <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;">
    <div style="font-family:'Playfair Display',Georgia,serif;font-size:144px;font-weight:700;color:${colors.textOnDark};letter-spacing:-0.02em;line-height:1;">[数字]</div>
    <div style="font-size:24px;color:${colors.accent};letter-spacing:0.2em;text-transform:uppercase;margin-top:24px;">[单位/标签]</div>
    <p style="font-size:16px;color:rgba(255,255,255,0.7);margin-top:32px;max-width:500px;">[补充说明]</p>
  </div>
</div>
\`\`\`

**TEMPLATE 6: GQ_CENTER_FOCUS** (中心聚焦 - 核心概念+四周要点)
- Use for: Single core concept with supporting points
- ⚠️ **SYMMETRIC LAYOUT** - All elements must be perfectly centered and balanced
- ⚠️ **NO TEXT OVERFLOW** - All text must fit within boundaries
- **MUST USE THIS HTML STRUCTURE:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:${colors.background};overflow:hidden;font-family:'Inter','Noto Sans SC',sans-serif;">
  <div style="position:absolute;top:0;left:0;right:0;height:4px;background:${colors.primary};"></div>
  
  <!-- DECORATIVE CIRCLE (background, centered) -->
  <div style="position:absolute;top:384px;left:512px;width:260px;height:260px;border:1px solid rgba(0,0,0,0.08);border-radius:50%;transform:translate(-50%,-50%);"></div>
  
  <!-- CENTER BOX - SMALL SIZE (200x160px, perfectly centered) -->
  <div style="position:absolute;top:384px;left:512px;transform:translate(-50%,-50%);width:200px;height:160px;background:${colors.primary};border-radius:8px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;z-index:10;padding:16px;box-sizing:border-box;">
    <div style="font-family:'Playfair Display','Noto Serif SC',Georgia,serif;font-size:28px;font-weight:700;color:${colors.textOnDark};line-height:1.2;margin-bottom:8px;">[核心概念]</div>
    <div style="font-size:12px;color:${colors.accent};letter-spacing:0.1em;text-transform:uppercase;">[英文副标题]</div>
  </div>
  
  <!-- 4 SATELLITE CARDS - symmetric with safe margins (48px from edges) -->
  <!-- Top Left -->
  <div style="position:absolute;top:120px;left:48px;width:260px;overflow:hidden;">
    <div style="font-family:'Playfair Display','Noto Serif SC',Georgia,serif;font-size:18px;font-weight:700;color:${colors.primary};margin-bottom:6px;word-break:break-word;">[要点1标题]</div>
    <div style="font-size:13px;color:${colors.text};line-height:1.5;word-break:break-word;">[描述-简短]</div>
  </div>
  
  <!-- Top Right (use 'right' to anchor from right edge) -->
  <div style="position:absolute;top:120px;right:48px;width:260px;text-align:right;overflow:hidden;">
    <div style="font-family:'Playfair Display','Noto Serif SC',Georgia,serif;font-size:18px;font-weight:700;color:${colors.primary};margin-bottom:6px;word-break:break-word;">[要点2标题]</div>
    <div style="font-size:13px;color:${colors.text};line-height:1.5;word-break:break-word;">[描述-简短]</div>
  </div>
  
  <!-- Bottom Left -->
  <div style="position:absolute;top:560px;left:48px;width:260px;overflow:hidden;">
    <div style="font-family:'Playfair Display','Noto Serif SC',Georgia,serif;font-size:18px;font-weight:700;color:${colors.primary};margin-bottom:6px;word-break:break-word;">[要点3标题]</div>
    <div style="font-size:13px;color:${colors.text};line-height:1.5;word-break:break-word;">[描述-简短]</div>
  </div>
  
  <!-- Bottom Right (use 'right' to anchor from right edge) -->
  <div style="position:absolute;top:560px;right:48px;width:260px;text-align:right;overflow:hidden;">
    <div style="font-family:'Playfair Display','Noto Serif SC',Georgia,serif;font-size:18px;font-weight:700;color:${colors.primary};margin-bottom:6px;word-break:break-word;">[要点4标题]</div>
    <div style="font-size:13px;color:${colors.text};line-height:1.5;word-break:break-word;">[描述-简短]</div>
  </div>
  
  <!-- BOTTOM TAGLINE -->
  <div style="position:absolute;bottom:32px;left:50%;transform:translateX(-50%);font-size:11px;color:${colors.accent};letter-spacing:0.3em;text-transform:uppercase;">[CONTEXTUAL TAGLINE]</div>
</div>
\`\`\`

</gq_templates>

<selection_rules>
**模板选择规则 (CRITICAL):**
- 封面/首页幻灯片 → GQ_HERO
- 包含引用/名言/"..." → GQ_QUOTE
- 比较/对比/详细解释 → GQ_MAGAZINE_SPREAD
- 步骤/排名/流程 → GQ_NUMBERED
- 数据/统计/百分比 → GQ_STATS
- **核心概念+四周要点 → GQ_CENTER_FOCUS** (中央方块必须小于 220x180px)

**多样性要求:**
- 同一演示中使用至少 3 种不同模板
- 连续相同模板不超过 2 次
</selection_rules>

**TECHNICAL REQUIREMENTS:**
- **Output:** Return ONLY valid HTML code with embedded CSS
- **Font Import (CRITICAL):** Add at the top of <style> block:
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Noto+Serif+SC:wght@400;700&family=Inter:wght@300;400;500;600&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
- **Self-contained:** Everything in a single HTML file
- **NO external images:** All graphics must be CSS
- **NO JavaScript:** Pure HTML and CSS only
- Start with <!DOCTYPE html>
- html, body { width: 1024px; height: 768px; margin: 0; padding: 0; overflow: hidden; }

**CRITICAL - TEXT ACCURACY:**
${language === 'Chinese' ? `
- Chinese text MUST be 100% accurate - NO pseudo-characters
- If uncertain about ANY character, use icons/symbols ONLY
` : `
- English text must be 100% correctly spelled
`}

**GQ 风格禁忌 (PROHIBITED):**
- ❌ 花哨渐变 (NO flashy gradients)
- ❌ 3D 效果 (NO 3D effects)
- ❌ 过度装饰 (NO excessive decoration)
- ❌ 不成熟的配色 (NO immature color schemes)
- ❌ 拥挤的布局 (NO cluttered layouts)
- ❌ 主持人信息 (NO speaker/host information)
- ❌ 页码和元信息 (NO page numbers or metadata)
- ❌ **禁止使用 "GQ" 品牌标识** (NO "GQ", "GQ PRESENTS", "GQ FASHION FIELD" or any brand names - use content-related taglines instead)

**OUTPUT FORMAT (CRITICAL):**
- Your response MUST start with "<!DOCTYPE html>" - NO text before it
- Do NOT say "Here is the HTML" or any introduction
- Just output the pure HTML code directly
`;
}

/**
 * Generate the system prompt with Color Theme
 */
function getHtmlSystemPrompt(language: string = 'Chinese', colorTheme?: ColorTheme): string {
  // Use provided theme or default to deep_blue
  const theme = colorTheme || getColorTheme('deep_blue');

  // If GQ Fashion theme is selected, use the specialized GQ system prompt
  if (theme.id === 'gq_fashion') {
    return getGqFashionSystemPrompt(language, theme);
  }

  const colors = theme.colors;

  return `You are a world-class presentation designer.
Your task is to create a single, beautiful presentation slide using HTML and CSS.

**COLOR THEME: ${theme.nameEn} (${theme.nameZh})**
**UNIFIED DESIGN SYSTEM (MUST FOLLOW EXACTLY):**

<color_palette>
Primary Color: ${colors.primary} (for main titles, important elements)
Secondary Color: ${colors.secondary} (for subtitles, dividers)
Accent Color: ${colors.accent} (for icons, highlights, decorations)
Background: ${colors.background} (main background)
Text Color: ${colors.text} (body text)
Text on Dark: ${colors.textOnDark} (for text on dark backgrounds)
</color_palette>

<typography>
Font Family: 'Noto Sans SC', 'Inter', 'Roboto', sans-serif
(NOTE: ALL fonts must be open-source commercial-friendly. Noto Sans SC, Inter, and Roboto are Google Open Fonts)
Title: Bold, 42-56px, color: ${colors.primary}
Subtitle: Medium, 24-32px, color: ${colors.secondary}
Body: Regular, 18-22px, color: ${colors.text}
</typography>

<layout_rules>
- **FIXED DIMENSIONS (CRITICAL):** Container is EXACTLY 1024px x 768px (4:3 aspect ratio)
- **ALL CONTENT MUST FIT:** Nothing should extend beyond 768px height - NO OVERFLOW ALLOWED
- Padding: 48px on all sides (effective content area: 928px x 672px)
- **EXCEPTION FOR HERO_TITLE:** The top header bar MUST IGNORE the 48px padding and extend to the TRUE edges of the slide (position: absolute; top: 0; left: 0; right: 0;)
- Card border-radius: 12px
- Card shadow: 0 4px 12px rgba(0,0,0,0.08)
- If content is too long, REDUCE text or use smaller fonts - DO NOT let content overflow
- Better to show LESS content that fits perfectly than MORE content that overflows
</layout_rules>

<slide_templates>
**CRITICAL: You MUST select ONE template from below based on content type. DO NOT always use the same layout!**

**TEMPLATE 1: HERO_TITLE** (封面/大标题) ⚠️ MINIMALIST DESIGN ⚠️
- Use for: Cover slides ONLY
- **DESIGN PRINCIPLE: LESS IS MORE - 视觉冲击力 = 大标题 + 大量留白**
- **YOU MUST USE THIS EXACT HTML STRUCTURE:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:#FBF5F3;overflow:hidden;">
  <!-- FULL-WIDTH HEADER BAR -->
  <div style="position:absolute;top:0;left:0;right:0;width:100%;height:150px;background:[PRIMARY_COLOR];"></div>
  <!-- CENTERED CONTENT - MINIMAL TEXT ONLY -->
  <div style="position:absolute;top:459px;left:50%;transform:translate(-50%,-50%);text-align:center;width:80%;">
    <h1 style="font-size:72px;font-weight:900;color:[PRIMARY_COLOR];line-height:1.2;margin:0;">[大标题]</h1>
    <p style="font-size:28px;color:[SECONDARY_COLOR];margin-top:24px;font-weight:500;">[副标题-最多一行]</p>
  </div>
</div>
\`\`\`
- **CRITICAL TEXT RULES:**
  - 大标题: MAX 6 Chinese characters (e.g. "诸神的黄昏" NOT "诸神的黄昏：1944—1945，从莱特湾战役到日本投降")
  - 副标题: MAX 15 Chinese characters, ONE LINE ONLY
  - **NO DESCRIPTION TEXT** - leave empty space for visual impact
  - **NO PARAGRAPHS** - only title + subtitle

**TEMPLATE 2: QUOTE_HIGHLIGHT** (引用高亮)
- Use for: Famous quotes, book excerpts, important statements
- **YOU MUST USE THIS EXACT HTML STRUCTURE:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:#FBF5F3;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:100px;background:[PRIMARY_COLOR];"></div>
  <h1 style="position:relative;color:white;font-size:36px;font-weight:bold;margin:20px 0 0 48px;">[标题]</h1>
  <div style="display:flex;gap:32px;padding:140px 48px 48px 48px;">
    <!-- QUOTE BOX (left 40%) -->
    <div style="width:40%;background:[PRIMARY_COLOR];border-radius:12px;padding:32px;color:white;">
      <div style="font-size:48px;opacity:0.5;">❝</div>
      <p style="font-size:20px;line-height:1.6;margin-top:16px;">[引用内容]</p>
      <p style="font-size:14px;margin-top:16px;opacity:0.8;">— [来源]</p>
    </div>
    <!-- KEY POINTS (right 60%) -->
    <div style="flex:1;">
      <div style="margin-bottom:24px;"><span style="color:[ACCENT_COLOR];font-size:24px;">●</span><span style="margin-left:12px;font-weight:bold;">[要点1]</span></div>
      <div style="margin-bottom:24px;"><span style="color:[ACCENT_COLOR];font-size:24px;">●</span><span style="margin-left:12px;font-weight:bold;">[要点2]</span></div>
      <div style="margin-bottom:24px;"><span style="color:[ACCENT_COLOR];font-size:24px;">●</span><span style="margin-left:12px;font-weight:bold;">[要点3]</span></div>
    </div>
  </div>
</div>
\`\`\`

**TEMPLATE 3: BULLET_POINTS** (要点列表)
- Use for: Multiple parallel ideas, feature lists, step summaries
- **YOU MUST USE THIS EXACT HTML STRUCTURE:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:#FBF5F3;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:100px;background:[PRIMARY_COLOR];"></div>
  <h1 style="position:relative;color:white;font-size:36px;font-weight:bold;margin:20px 0 0 48px;">[标题]</h1>
  <div style="padding:140px 48px 48px 48px;">
    <div style="display:flex;align-items:flex-start;margin-bottom:20px;">
      <span style="color:[ACCENT_COLOR];font-size:28px;margin-right:16px;">●</span>
      <div><h3 style="font-size:20px;font-weight:bold;color:[PRIMARY_COLOR];">[要点1标题]</h3><p style="font-size:16px;color:#666;margin-top:4px;">[描述]</p></div>
    </div>
    <!-- Repeat for 要点2, 3, 4... -->
  </div>
</div>
\`\`\`

**TEMPLATE 4: TWO_COLUMN** (双栏对比)
- Use for: Comparisons, pros/cons, before/after, A vs B
- **YOU MUST USE THIS EXACT HTML STRUCTURE:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:#FBF5F3;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:100px;background:[PRIMARY_COLOR];"></div>
  <h1 style="position:relative;color:white;font-size:36px;font-weight:bold;margin:20px 0 0 48px;">[标题]</h1>
  <div style="display:flex;gap:32px;padding:140px 48px 48px 48px;">
    <!-- LEFT COLUMN -->
    <div style="flex:1;background:white;border-radius:12px;padding:24px;box-shadow:0 4px 12px rgba(0,0,0,0.08);">
      <h3 style="font-size:22px;font-weight:bold;color:[PRIMARY_COLOR];border-left:4px solid [ACCENT_COLOR];padding-left:12px;">[左栏标题]</h3>
      <ul style="margin-top:16px;list-style:none;padding:0;"><li style="margin-bottom:12px;">● [要点1]</li></ul>
    </div>
    <!-- RIGHT COLUMN - same structure -->
    <div style="flex:1;background:white;border-radius:12px;padding:24px;box-shadow:0 4px 12px rgba(0,0,0,0.08);">
      <h3 style="font-size:22px;font-weight:bold;color:[SECONDARY_COLOR];border-left:4px solid [SECONDARY_COLOR];padding-left:12px;">[右栏标题]</h3>
      <ul style="margin-top:16px;list-style:none;padding:0;"><li style="margin-bottom:12px;">● [要点1]</li></ul>
    </div>
  </div>
</div>
\`\`\`

**TEMPLATE 5: THREE_CARDS** (三卡片)
- Use for: Three core concepts, stages, or categories
- **YOU MUST USE THIS EXACT HTML STRUCTURE:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:#FBF5F3;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:100px;background:[PRIMARY_COLOR];"></div>
  <h1 style="position:relative;color:white;font-size:36px;font-weight:bold;margin:20px 0 0 48px;">[标题]</h1>
  <div style="display:flex;gap:24px;padding:140px 48px 48px 48px;">
    <!-- CARD 1 -->
    <div style="flex:1;background:white;border-radius:12px;padding:24px;box-shadow:0 4px 12px rgba(0,0,0,0.08);text-align:center;">
      <div style="font-size:40px;margin-bottom:16px;">🔹</div>
      <h3 style="font-size:20px;font-weight:bold;color:[PRIMARY_COLOR];">[卡片1标题]</h3>
      <p style="font-size:14px;color:#666;margin-top:8px;line-height:1.5;">[描述-最多3行]</p>
    </div>
    <!-- CARD 2, 3 - same structure -->
  </div>
</div>
\`\`\`

**TEMPLATE 6: ICON_GRID** (图标网格 2x2)
- Use for: Feature overview, multiple concepts at a glance
- **YOU MUST USE THIS EXACT HTML STRUCTURE (2x2 grid):**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:#FBF5F3;overflow:hidden;">
  <!-- HEADER with full-width bar -->
  <div style="position:absolute;top:0;left:0;right:0;height:90px;background:[PRIMARY_COLOR];"></div>
  <h1 style="position:relative;color:white;font-size:32px;font-weight:bold;margin:18px 0 0 48px;">[标题]</h1>
  <!-- 2x2 GRID - EXTRA COMPACT LAYOUT to fit within 768px with margin -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:100px 48px 20px 48px;height:648px;box-sizing:border-box;">
    <!-- CARD 1 -->
    <div style="background:white;border-radius:10px;padding:12px 14px;box-shadow:0 4px 12px rgba(0,0,0,0.08);max-height:295px;overflow:hidden;">
      <div style="font-size:24px;margin-bottom:6px;">🔹</div>
      <h3 style="font-size:16px;font-weight:bold;color:[PRIMARY_COLOR];margin-bottom:4px;line-height:1.2;">[标题1]</h3>
      <p style="font-size:12px;color:#666;line-height:1.35;">[描述1-最多2行]</p>
    </div>
    <!-- CARD 2, 3, 4... repeat same structure -->
  </div>
</div>
\`\`\`
- EXACTLY 4 cards in 2x2 grid, each card same structure
- Each card: icon/emoji + title (max 6 chars) + description (max 2 lines)
- **EXTRA COMPACT:** Header 90px, Grid padding top 100px bottom 20px, Gap 12px, Card max-height 295px
- **CRITICAL:** All 4 cards MUST be fully visible within 768px height - NO content overflow


**TEMPLATE 7: TIMELINE** (时间轴)
- Use for: Historical events, process stages, development phases
- **YOU MUST USE THIS EXACT HTML STRUCTURE:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:#FBF5F3;overflow:hidden;padding:48px;">
  <!-- HEADER with full-width bar -->
  <div style="position:absolute;top:0;left:0;right:0;height:100px;background:[PRIMARY_COLOR];"></div>
  <h1 style="position:relative;color:white;font-size:36px;font-weight:bold;margin-top:20px;padding-left:20px;">[标题]</h1>
  <!-- TIMELINE CONTAINER - all nodes in one row -->
  <div style="display:flex;justify-content:space-around;align-items:flex-start;margin-top:120px;position:relative;">
    <!-- TIMELINE LINE - behind nodes -->
    <div style="position:absolute;top:60px;left:10%;right:10%;height:4px;background:[ACCENT_COLOR];"></div>
    <!-- NODE 1 -->
    <div style="text-align:center;width:200px;z-index:1;">
      <div style="width:24px;height:24px;border-radius:50%;background:[ACCENT_COLOR];margin:48px auto 16px;"></div>
      <h3 style="font-size:18px;font-weight:bold;color:[PRIMARY_COLOR];">[节点1标题]</h3>
      <p style="font-size:14px;color:#666;margin-top:8px;">[关键词1]<br>[关键词2]</p>
    </div>
    <!-- NODE 2, 3, 4... repeat same structure -->
  </div>
</div>
\`\`\`
- Each node MUST be max 200px wide, text MUST stay within that width
- Timeline line is BEHIND nodes (z-index), nodes are ABOVE line
- Node descriptions: max 2 lines, 4-6 Chinese chars per line

**TEMPLATE 8: NUMBERED_STEPS** (编号步骤)
- Use for: Procedures, how-to guides, sequential instructions
- **YOU MUST USE THIS EXACT HTML STRUCTURE:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:#FBF5F3;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:100px;background:[PRIMARY_COLOR];"></div>
  <h1 style="position:relative;color:white;font-size:36px;font-weight:bold;margin:20px 0 0 48px;">[标题]</h1>
  <div style="padding:140px 48px 48px 48px;">
    <!-- STEP 1 -->
    <div style="display:flex;align-items:flex-start;margin-bottom:24px;">
      <div style="width:48px;height:48px;border-radius:50%;background:[PRIMARY_COLOR];color:white;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:bold;flex-shrink:0;">1</div>
      <div style="margin-left:20px;"><h3 style="font-size:20px;font-weight:bold;color:[PRIMARY_COLOR];">[步骤1标题]</h3><p style="font-size:16px;color:#666;margin-top:4px;">[描述]</p></div>
    </div>
    <!-- STEP 2, 3... repeat same structure -->
  </div>
</div>
\`\`\`

**TEMPLATE 9: BIG_NUMBER** (大数字突出)
- Use for: Statistics, key metrics, important figures
- **YOU MUST USE THIS EXACT HTML STRUCTURE:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:#FBF5F3;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:100px;background:[PRIMARY_COLOR];"></div>
  <h1 style="position:relative;color:white;font-size:36px;font-weight:bold;margin:20px 0 0 48px;">[标题]</h1>
  <div style="display:flex;justify-content:space-around;align-items:center;padding:140px 48px 48px 48px;">
    <div style="text-align:center;">
      <div style="font-size:96px;font-weight:bold;color:[PRIMARY_COLOR];">[数字1]</div>
      <p style="font-size:18px;color:#666;margin-top:8px;">[标签1]</p>
    </div>
    <div style="text-align:center;">
      <div style="font-size:96px;font-weight:bold;color:[ACCENT_COLOR];">[数字2]</div>
      <p style="font-size:18px;color:#666;margin-top:8px;">[标签2]</p>
    </div>
  </div>
</div>
\`\`\`

**TEMPLATE 10: PYRAMID_HIERARCHY** (层级金字塔)
- Use for: Hierarchies, importance levels, layered concepts
- **⚠️ 禁止在此模板底部添加任何书名、水印、注释文字！**
- **YOU MUST USE THIS EXACT HTML STRUCTURE:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:#FBF5F3;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:100px;background:[PRIMARY_COLOR];"></div>
  <h1 style="position:relative;color:white;font-size:36px;font-weight:bold;margin:20px 0 0 48px;">[标题]</h1>
  <div style="padding:130px 48px 80px 48px;display:flex;flex-direction:column;align-items:center;justify-content:center;height:calc(768px - 100px);box-sizing:border-box;">
    <!-- TOP LEVEL (narrowest) -->
    <div style="width:220px;background:[PRIMARY_COLOR];color:white;text-align:center;padding:20px 16px;border-radius:8px 8px 0 0;font-weight:bold;">[顶层标题]<br><span style='font-size:13px;font-weight:normal;opacity:0.9;'>[描述]</span></div>
    <!-- MIDDLE LEVEL -->
    <div style="width:450px;background:[SECONDARY_COLOR];color:white;text-align:center;padding:20px 16px;margin-top:4px;font-weight:bold;">[中层标题]<br><span style='font-size:13px;font-weight:normal;opacity:0.9;'>[描述]</span></div>
    <!-- BOTTOM LEVEL (widest) -->
    <div style="width:680px;background:[ACCENT_COLOR];color:white;text-align:center;padding:20px 16px;margin-top:4px;border-radius:0 0 8px 8px;font-weight:bold;">[底层标题]<br><span style='font-size:13px;font-weight:normal;opacity:0.9;'>[描述]</span></div>
  </div>
</div>
\`\`\`
- **CRITICAL:** DO NOT add book title, watermark, or any text outside the pyramid structure

**TEMPLATE 11: CENTER_FOCUS** (中心聚焦)
- Use for: Single core concept, key conclusion, main theme
- **YOU MUST USE THIS EXACT HTML STRUCTURE FOR SYMMETRY:**
\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:#FBF5F3;overflow:hidden;">
  <!-- HEADER BAR (100px) -->
  <div style="position:absolute;top:0;left:0;right:0;height:100px;background:[PRIMARY_COLOR];"></div>
  <h1 style="position:relative;color:white;font-size:36px;font-weight:bold;margin:20px 0 0 48px;">[标题]</h1>

  <!-- SYMMETRIC DECORATION: DASHED CIRCLE -->
  <!-- Centered at x=512, y=434 (middle of light area) -->
  <div style="position:absolute;top:434px;left:512px;width:560px;height:560px;border:2px dashed [PRIMARY_COLOR];opacity:0.1;border-radius:50%;transform:translate(-50%,-50%);"></div>

  <!-- CENTER BOX (Centrally aligned in light area) -->
  <div style="position:absolute;top:434px;left:512px;transform:translate(-50%,-50%);width:320px;height:220px;background:[PRIMARY_COLOR];border-radius:16px;display:flex;flex-direction:column;align-items:center;justify-content:center;color:white;text-align:center;z-index:10;box-shadow:0 8px 24px rgba(0,0,0,0.2);">
    <div style="font-size:32px;font-weight:900;margin-bottom:12px;">[核心概念]</div>
    <div style="font-size:16px;opacity:0.8;width:80%;">[核心概念描述-最多两行]</div>
  </div>

  <!-- 4 SATELLITE CARDS (Symmetrically positioned) -->
  <!-- Top Left -->
  <div style="position:absolute;top:260px;left:240px;transform:translate(-50%,-50%);width:260px;height:140px;background:white;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,0.08);border-left:6px solid [PRIMARY_COLOR];padding:16px;">
    <div style="font-weight:bold;color:[PRIMARY_COLOR];font-size:20px;margin-bottom:8px;">[要点1标题]</div>
    <div style="font-size:14px;color:#666;line-height:1.4;">[描述1-最多两句]</div>
  </div>
  <!-- Top Right -->
  <div style="position:absolute;top:260px;left:784px;transform:translate(-50%,-50%);width:260px;height:140px;background:white;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,0.08);border-left:6px solid [SECONDARY_COLOR];padding:16px;">
    <div style="font-weight:bold;color:[SECONDARY_COLOR];font-size:20px;margin-bottom:8px;">[要点2标题]</div>
    <div style="font-size:14px;color:#666;line-height:1.4;">[描述2-最多两句]</div>
  </div>
  <!-- Bottom Left -->
  <div style="position:absolute;top:608px;left:240px;transform:translate(-50%,-50%);width:260px;height:140px;background:white;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,0.08);border-left:6px solid [ACCENT_COLOR];padding:16px;">
    <div style="font-weight:bold;color:[ACCENT_COLOR];font-size:20px;margin-bottom:8px;">[要点3标题]</div>
    <div style="font-size:14px;color:#666;line-height:1.4;">[描述3-最多两句]</div>
  </div>
  <!-- Bottom Right -->
  <div style="position:absolute;top:608px;left:784px;transform:translate(-50%,-50%);width:260px;height:140px;background:white;border-radius:12px;box-shadow:0 4px 16px rgba(0,0,0,0.08);border-left:6px solid [PRIMARY_COLOR];padding:16px;">
    <div style="font-weight:bold;color:[PRIMARY_COLOR];font-size:20px;margin-bottom:8px;">[要点4标题]</div>
    <div style="font-size:14px;color:#666;line-height:1.4;">[描述4-最多两句]</div>
  </div>
</div>
\`\`\`

**TEMPLATE SELECTION RULES (CRITICAL):**
- Cover/first slide → ALWAYS use HERO_TITLE
- Contains "对比/比较/vs/不同" → Use TWO_COLUMN
- Contains numbers/statistics → Use BIG_NUMBER
- Contains quote/引用/"..." → Use QUOTE_HIGHLIGHT
- Contains "步骤/流程/第一步" → Use NUMBERED_STEPS or TIMELINE
- Lists 3 things → Use THREE_CARDS
- Lists 4-6 things → Use ICON_GRID or BULLET_POINTS
- Hierarchy/levels → Use PYRAMID_HIERARCHY

**VARIETY REQUIREMENT:**
- Within any presentation, use AT LEAST 4 different templates
- NEVER use the same template more than 3 times in a row
- Match template to content - don't force-fit
</slide_templates>

<decorative_elements>
- Icons: Flat, minimalist line icons using accent color
- Shapes: Rounded rectangles, circles, soft geometric shapes
- NO gradients, NO 3D effects, NO photos
- Use CSS shapes or simple SVG for decorations
</decorative_elements>

**TECHNICAL REQUIREMENTS:**
- **Output:** Return ONLY valid HTML code with embedded CSS in <style> tags
- **Font Import (CRITICAL - Open Source Fonts Only):** Add this EXACT line at the top of <style> block:
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&family=Inter:wght@300;400;500;600;700&display=swap');
- **Font Family:** Set body font as: font-family: 'Noto Sans SC', 'Inter', sans-serif;
- **Self-contained:** Everything in a single HTML file
- **NO external images:** All graphics must be CSS or inline SVG
- **NO JavaScript:** Pure HTML and CSS only
- Start with <!DOCTYPE html>
- **OVERFLOW PREVENTION (CRITICAL):** Add these CSS rules to html and body:
  html, body { width: 1024px; height: 768px; margin: 0; padding: 0; overflow: hidden; }
- The slide MUST be a single, static view - no scrolling needed

**CRITICAL - TEXT ACCURACY:**
${language === 'Chinese' ? `
- Chinese text MUST be 100% accurate - NO pseudo-characters
- If uncertain about ANY character, use icons/symbols ONLY
- Book titles must be triple-checked for accuracy
- Better to have NO text than WRONG text
` : `
- English text must be 100% correctly spelled
- If uncertain about any word, use icons instead
`}

**VISUAL CONSISTENCY (CRITICAL - COLOR ENFORCEMENT):**
- This slide MUST look like it belongs to a professional slide deck
- Use ONLY the colors from the palette above - NO OTHER COLORS ALLOWED
- Primary Color (${colors.primary}) MUST be used for main title/header background
- The overall color scheme MUST match the theme: ${theme.nameEn}
- DO NOT use blue (#1E3A5F, #0F172A, etc.) unless the theme explicitly specifies blue
- If theme is Berry/Pink (${theme.nameEn}), use pink/magenta tones, NOT blue
- Maintain consistent visual language throughout

**TEXT CONTRAST (CRITICAL):**
- Dark background (Primary/Secondary color) → MUST use WHITE (#FFFFFF) text
- Light background → Use Text Color (${colors.text})
- NEVER use dark text on dark background

**PROHIBITED ELEMENTS (CRITICAL):**
- DO NOT include speaker names (主讲人, 阿哲, 小雅, etc.) 
- DO NOT include podcast host information
- DO NOT include any introductory text before the HTML code
- DO NOT include any explanatory text - ONLY output the HTML code itself
- The slide shows CONTENT ONLY, not who is speaking

**OUTPUT FORMAT (CRITICAL):**
- Your response MUST start with "<!DOCTYPE html>" - NO text before it
- Do NOT say "Here is the HTML" or any introduction
- Just output the pure HTML code directly
`;
}

export const htmlImageService = {
  /**
   * Extract pure HTML from LLM response, removing any explanatory text
   * This fixes the issue where LLM adds "Here is the HTML code..." before the actual HTML
   */
  extractPureHtml(rawResponse: string): string {
    // First, remove markdown code blocks
    let cleaned = rawResponse.replace(/```html\n?/g, '').replace(/```\n?/g, '');

    // Find the start of actual HTML (<!DOCTYPE html> or <html)
    const doctypeIndex = cleaned.indexOf('<!DOCTYPE html>');
    const htmlTagIndex = cleaned.indexOf('<html');

    let startIndex = -1;
    if (doctypeIndex !== -1 && (htmlTagIndex === -1 || doctypeIndex < htmlTagIndex)) {
      startIndex = doctypeIndex;
    } else if (htmlTagIndex !== -1) {
      startIndex = htmlTagIndex;
    }

    if (startIndex > 0) {
      // Remove any text before the HTML starts
      console.log(`[HtmlImageService] Removing ${startIndex} chars of pre-HTML text`);
      cleaned = cleaned.substring(startIndex);
    }

    // Find the end of HTML (</html>)
    const htmlEndIndex = cleaned.lastIndexOf('</html>');
    if (htmlEndIndex !== -1) {
      cleaned = cleaned.substring(0, htmlEndIndex + 7); // 7 = length of </html>
    }

    return cleaned.trim();
  },

  /**
   * Generate HTML slide and render to image
   * @param prompt - The content to display on the slide
   * @param model - REQUIRED: OpenRouter model ID for HTML generation (e.g., google/gemini-2.5-flash)
   * @param language - Language for text (Chinese or English)
   * @param colorThemeId - Color theme ID (deep_blue, emerald_green, etc.)
   */
  async generateHtmlImage(
    prompt: string,
    model: string,  // REQUIRED - no longer optional
    language: string = 'Chinese',
    colorThemeId: string = 'deep_blue'
  ): Promise<{ buffer: Buffer; htmlContent: string; usageMetadata?: any }> {
    // CRITICAL: model parameter is now REQUIRED
    if (!model) {
      throw new Error('[HtmlImageService] model parameter is REQUIRED. pptModel must be specified in imageStyle config. Available models: google/gemini-2.5-flash, google/gemini-3-pro-preview, deepseek/deepseek-v3.2-speciale, etc.');
    }

    const colorTheme = getColorTheme(colorThemeId);
    console.log(`[HtmlImageService] Generating Smart PPT slide...`);
    console.log(`[HtmlImageService] Model: ${model}`);
    console.log(`[HtmlImageService] Color Theme: ${colorTheme.nameEn}`);
    console.log(`[HtmlImageService] Prompt preview: ${prompt.substring(0, 100)}...`);

    const systemPrompt = getHtmlSystemPrompt(language, colorTheme);
    const userPrompt = `Create a presentation slide for this content:

${prompt}

Remember:
- Use the EXACT color palette from the design system
- Keep the design clean and professional
- ${language === 'Chinese' ? 'Chinese text must be accurate' : 'Use correct English'}`;

    // Call OpenRouter (REQUIRED - no fallback)
    const result = await openrouterService.generateText(
      userPrompt,
      systemPrompt,
      'text',
      model
    );

    let htmlContent = result.text;
    // Clean up markdown code blocks and extract pure HTML
    htmlContent = this.extractPureHtml(htmlContent);

    // Use passed-in model parameter (user's selection) for consistency
    // OpenRouter API may return simplified model names (e.g., "gemini-3-pro-preview" instead of "google/gemini-3-flash-preview")
    const usageMetadata = {
      model: model || result.model,  // Prioritize user's selection (full OpenRouter ID like "google/gemini-3-flash-preview")
      provider: 'Google Gemini (HTML) + Puppeteer',  // Updated to reflect actual provider
      promptTokenCount: result.usage?.inputTokens || 0,
      candidatesTokenCount: result.usage?.outputTokens || 0,
      totalTokenCount: result.usage?.totalTokens || 0,
      // OpenRouter always returns costUSD
      costUSD: result.cost?.totalUSD || 0
    };
    console.log(`[HtmlImageService] HTML generated via OpenRouter, Cost: $${result.cost?.totalUSD?.toFixed(6) || 'unknown'}`);

    console.log(`[HtmlImageService] HTML length: ${htmlContent.length} chars`);

    // Render HTML to image using Puppeteer
    const buffer = await this.renderHtmlToImage(htmlContent);

    return { buffer, htmlContent, usageMetadata };
  },

  /**
   * Render HTML content to PNG image using Puppeteer
   */
  async renderHtmlToImage(htmlContent: string): Promise<Buffer> {
    console.log(`[HtmlImageService] Launching Puppeteer...`);

    // Find Chrome executable
    let executablePath: string | undefined;
    if (process.platform === 'darwin') {
      const { existsSync } = await import('fs');
      const possiblePaths = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary',
        '/Applications/Chromium.app/Contents/MacOS/Chromium'
      ];
      for (const p of possiblePaths) {
        if (existsSync(p)) {
          executablePath = p;
          break;
        }
      }
    }

    const browser = await puppeteer.launch({
      headless: true,
      executablePath,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
      const page = await browser.newPage();
      page.setDefaultNavigationTimeout(60000);

      // 4:3 aspect ratio with 2x scale for high quality
      const targetWidth = 1024;
      const targetHeight = 768;

      await page.setViewport({
        width: targetWidth,
        height: targetHeight,
        deviceScaleFactor: 2
      });

      await page.setContent(htmlContent, {
        waitUntil: 'networkidle0',
        timeout: 60000
      });

      // Check if content overflows and apply fix if needed
      const contentHeight = await page.evaluate(() => {
        return document.body.scrollHeight;
      });

      if (contentHeight > targetHeight) {
        console.log(`[HtmlImageService] Content overflow detected: ${contentHeight}px > ${targetHeight}px. Applying CSS fix...`);

        // Inject CSS to force content to fit within viewport
        await page.addStyleTag({
          content: `
                        html, body {
                            height: ${targetHeight}px !important;
                            max-height: ${targetHeight}px !important;
                            overflow: hidden !important;
                        }
                        /* Scale down content if too tall */
                        body > * {
                            transform-origin: top left;
                            transform: scale(${Math.min(1, targetHeight / contentHeight)});
                        }
                    `
        });

        // Wait for CSS to apply
        await page.evaluate(() => new Promise(resolve => setTimeout(resolve, 100)));
      }

      const screenshot = await page.screenshot({
        type: 'png',
        fullPage: false,
        encoding: 'binary',
        clip: {
          x: 0,
          y: 0,
          width: targetWidth,
          height: targetHeight
        }
      });

      console.log(`[HtmlImageService] Screenshot captured successfully (${targetWidth}x${targetHeight})`);
      return Buffer.from(screenshot);

    } finally {
      await browser.close();
    }
  },

  /**
   * Generate prompt for Smart PPT slide from segment content
   * @param coverImageUrl - Optional URL to book cover image (for first slide only)
   */
  generateSmartPptPrompt(
    segmentText: string,
    bookTitle: string,
    segmentIndex: number,
    totalSegments: number,
    isFirstSlide: boolean = false,
    language: string = 'Chinese',
    coverImageUrl?: string
  ): string {
    // Clean segment text: remove any speaker/host mentions
    let cleanedText = segmentText
      .replace(/主讲人[：:]\s*\S+/g, '')    // 主讲人: xxx
      .replace(/讲解人[：:]\s*\S+/g, '')    // 讲解人: xxx
      .replace(/阿哲[：:]/g, '')              // 阿哲:
      .replace(/小雅[：:]/g, '')              // 小雅:
      .replace(/\[阿哲\]/g, '')              // [阿哲]
      .replace(/\[小雅\]/g, '')              // [小雅]
      .replace(/（阿哲）/g, '')              // （阿哲）
      .replace(/（小雅）/g, '')              // （小雅）
      .replace(/Host [12]:/gi, '')          // Host 1: / Host 2:
      .replace(/Speaker [12]:/gi, '')       // Speaker 1: / Speaker 2:
      .trim();

    // Extract key content (first 300 chars)
    const keyContent = cleanedText.substring(0, 300).replace(/\n/g, ' ').trim();

    if (isFirstSlide) {
      // Cover slide - MINIMALIST design with visual impact
      // Extract SHORT title from book title
      // Strategy: Chinese titles split by punctuation (max 6 chars), English titles keep intact (max 30 chars)
      const isChinese = /[\u4e00-\u9fff]/.test(bookTitle);
      const shortTitle = isChinese
        ? bookTitle.split(/[：:，,、—]/)[0].substring(0, 6)  // Chinese: split by punctuation, no hyphen
        : bookTitle.substring(0, 30);  // English: keep full title (up to 30 chars)

      // If we have a cover image, use the new layout with cover on right
      if (coverImageUrl) {
        return `【封面幻灯片 - 带书籍封面的双栏布局】

**⚠️ 设计原则: 左侧标题 + 右侧封面图片 ⚠️**

书籍: "${bookTitle}"
封面图片URL: ${coverImageUrl}

**必须使用以下布局:**

\`\`\`html
<div class="slide" style="width:1024px;height:768px;position:relative;background:#FBF5F3;overflow:hidden;">
  <!-- FULL-WIDTH HEADER BAR -->
  <div style="position:absolute;top:0;left:0;right:0;width:100%;height:120px;background:[PRIMARY_COLOR];"></div>
  
  <!-- LEFT SIDE: TITLE (55%) -->
  <div style="position:absolute;left:48px;top:444px;transform:translateY(-50%);width:50%;">
    <h1 style="font-size:56px;font-weight:900;color:[PRIMARY_COLOR];line-height:1.2;margin:0;">${shortTitle}</h1>
    <p style="font-size:24px;color:[SECONDARY_COLOR];margin-top:20px;font-weight:500;">[副标题-最多一行]</p>
  </div>
  
  <!-- RIGHT SIDE: BOOK COVER (45%) -->
  <div style="position:absolute;right:48px;top:444px;transform:translateY(-50%);width:35%;display:flex;justify-content:center;align-items:center;">
    <img src="${coverImageUrl}" style="max-width:100%;max-height:480px;box-shadow:0 8px 32px rgba(0,0,0,0.25);object-fit:contain;" />
  </div>
</div>
\`\`\`

**规则：**
1. 大标题: 只显示 "${shortTitle}" 或类似的极短标题（最多6个汉字）
2. 副标题: 最多一行，15个字以内
3. 封面图片: 右侧居中显示，保持原始比例，添加阴影效果
4. 顶部色条: 全宽 (position:absolute; top:0; left:0; right:0; width:100%)

**禁止事项:**
- ❌ 不要修改封面图片URL
- ❌ 不要写长段落描述
- ❌ 不要堆砌文字`;
      }

      // Fallback: no cover image, use centered title only
      return `【封面幻灯片 - HERO_TITLE 极简设计】

**⚠️ 设计原则: LESS IS MORE - 视觉冲击力 = 超大标题 + 大量留白 ⚠️**

书籍: "${bookTitle}"

**必须遵循以下规则：**

1. **大标题**: 只显示 "${shortTitle}" 或类似的极短标题（最多6个汉字）
   - 字号: 72px 以上
   - 居中显示
   - 不要把完整书名都写上！

2. **副标题**: 最多一行，15个字以内
   - 从书籍内容中提取核心主题（如：作者名、历史时期、核心概念等）
   - ⚠️ 禁止使用任何与书籍无关的示例文本

3. **禁止事项**:
   - ❌ 不要写长段落描述
   - ❌ 不要堆砌文字
   - ❌ 不要显示作者、出版信息
   - ❌ 不要显示书籍介绍

4. **顶部色条**: 全宽 (position:absolute; top:0; left:0; right:0; width:100%)

**正确示例**: 标题精简（最多6字），副标题与书籍内容相关
**错误示例**: 使用与书籍无关的副标题、把整个书名+介绍都堆上去`;
    }

    // Template rotation - ensure variety!
    // PRIORITY ORDER: Put left-right layouts FIRST for better visual variety
    const CONTENT_TEMPLATES = [
      // === LEFT-RIGHT LAYOUTS (优先) ===
      { name: 'QUOTE_HIGHLIGHT', desc: '引用高亮 (左右结构)', layout: '左侧引用框(40%宽度，深色背景)+右侧3个垂直要点' },
      { name: 'TWO_COLUMN', desc: '双栏对比布局', layout: '两个等宽列(各48%)，左栏和右栏各有标题和要点列表' },
      { name: 'CENTER_FOCUS', desc: '中心聚焦 (左右环绕)', layout: '中央大元素+左右两侧各2个卫星要点' },

      // === GRID/CARD LAYOUTS ===
      { name: 'THREE_CARDS', desc: '三卡片横排', layout: '3个水平排列的等宽卡片，每卡片有顶部图标+标题+描述' },
      { name: 'ICON_GRID', desc: '2x2图标网格', layout: '4格网格(2行2列)，每格有大图标+短标题+1-2行描述' },

      // === VERTICAL LAYOUTS ===
      { name: 'BULLET_POINTS', desc: '垂直要点列表', layout: '顶部标题+4-6个垂直排列的要点(图标+标题+描述)' },
      { name: 'NUMBERED_STEPS', desc: '编号步骤', layout: '大数字(圆圈)在左+步骤内容在右，3-5步垂直堆叠' },

      // === SPECIAL LAYOUTS (低频使用) ===
      { name: 'BIG_NUMBER', desc: '大数字突出', layout: '巨大数字居中+下方解释文字，适合统计数据' },
      { name: 'PYRAMID_HIERARCHY', desc: '层级金字塔', layout: '金字塔形状(顶窄底宽)，3层递进结构' },
      { name: 'TIMELINE', desc: '水平时间轴 (仅限有明确时序的内容)', layout: '水平线+3-4个节点，每节点有圆点标记+短标题+关键词' }
    ];

    // Use a stable but varied selection based on segment index
    // Different formula to avoid repetitive patterns
    const primeMultiplier = [2, 3, 5, 7, 11][segmentIndex % 5];
    let templateIndex = ((segmentIndex * primeMultiplier) + Math.floor(segmentIndex / 3)) % CONTENT_TEMPLATES.length;
    let forcedTemplate = CONTENT_TEMPLATES[templateIndex];

    // Content-based overrides - BUT with restrictions to avoid overuse
    const textLower = cleanedText.toLowerCase();

    // Only use TIMELINE if there are EXPLICIT chronological markers (年份+事件)
    const hasExplicitTimeline = /(\d{4}年.*?→|\d{4}年.*?\d{4}年|第[一二三四五六七八九十]+阶段.*?第)/.test(cleanedText);

    // Override only if STRONG signal, otherwise stick with rotation
    if (textLower.includes('对比') || textLower.includes('比较') || textLower.includes(' vs ')) {
      forcedTemplate = CONTENT_TEMPLATES[1]; // TWO_COLUMN
    } else if (/（引自|"[^"]{10,}"|「[^」]{10,}」|引用/.test(cleanedText)) {
      forcedTemplate = CONTENT_TEMPLATES[0]; // QUOTE_HIGHLIGHT
    } else if (/\d{2,}%|\d+亿|\d+万人/.test(cleanedText)) {
      forcedTemplate = CONTENT_TEMPLATES[7]; // BIG_NUMBER (only for strong number emphasis)
    } else if ((textLower.includes('步骤') || textLower.includes('第一步')) && textLower.includes('第二')) {
      forcedTemplate = CONTENT_TEMPLATES[6]; // NUMBERED_STEPS (only if multiple steps mentioned)
    } else if (hasExplicitTimeline && segmentIndex % 4 === 0) {
      // TIMELINE: only use if explicit timeline markers AND not too frequent
      forcedTemplate = CONTENT_TEMPLATES[9]; // TIMELINE
    }
    // Otherwise: use the rotation-selected template (more variety!)

    // Regular content slide with forced template
    // NOTE: Do NOT include page numbers or position info - it causes ugly overlap issues
    return `【内容幻灯片 - 强制使用 ${forcedTemplate.name} 模板】

**⚠️⚠️⚠️ 严格约束：本 PPT 必须基于书籍《${bookTitle}》的内容！⚠️⚠️⚠️**
**禁止生成与书籍主题无关的内容！**

**★★★ 强制模板: ${forcedTemplate.name} ★★★**
**${forcedTemplate.desc}**
**布局: ${forcedTemplate.layout}**

⚠️ 禁止使用其他模板！必须严格遵循 ${forcedTemplate.name} 布局！

**本段落要讲解的具体内容（必须基于此文本生成 PPT 要点）:**
${keyContent}

设计要求:
- 必须使用 ${forcedTemplate.name} 的布局结构
- **内容必须与书籍《${bookTitle}》相关**
- **从上述"本段落要讲解的具体内容"中提取要点，不要自己编造**
- **禁止生成：人工智能、医疗健康、科技创新、商业管理、金融投资等与书籍无关的话题**
- 使用设计系统的统一配色
- 深色区块内文字必须使用白色 (#FFFFFF)
- ${language === 'Chinese' ? '中文必须准确' : 'Text must be accurate'}
- 禁止显示：主讲人、阿哲、小雅等任何主持人信息
- **禁止显示页码、段落编号、书名等元信息**（如"第X页"、"第X/Y段"等）
- **⚠️ 禁止在幻灯片底部或左下角添加书名水印（如《说中国》xxx）！**`;
  }
};

