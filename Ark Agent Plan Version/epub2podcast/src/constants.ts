import { ImageStylePreset, ImageStyleConfig } from './types.js';

// Models
export const TEXT_MODEL = 'gemini-2.5-flash'; // Logic & Scripting (changed from gemini-3-pro to avoid quota limits)
export const PPT_HTML_MODEL = 'gemini-3-pro-preview'; // PPT HTML generation uses gemini-3-pro-preview for better quality
export const TTS_MODEL = 'gemini-2.5-flash-preview-tts'; // Audio
export const IMAGE_MODEL = 'models/gemini-3-pro-image-preview'; // High quality visuals

// PPT Generation Models (OpenRouter)
// EXPERIMENT: Testing DeepSeek as default for cheaper PPT generation
export const PPT_MODELS = [
  { id: 'deepseek/deepseek-v3.2-speciale', name: 'DeepSeek V3.2 Speciale', provider: 'DeepSeek' },
  { id: 'google/gemini-3-flash-preview', name: 'Gemini 3.0 Flash', provider: 'Google' },
  { id: 'google/gemini-3-pro-preview', name: 'Gemini 3.0 Pro', provider: 'Google' },
];

// Default PPT Model (EXPERIMENT: Using DeepSeek for cheaper generation)
export const DEFAULT_PPT_MODEL = 'deepseek/deepseek-v3.2-speciale';

// Configuration
export const SAMPLE_RATE = 44100;

// --- ELEVENLABS CONFIGURATION ---
export const ELEVENLABS_CONFIG = {
  apiKey: process.env['11LABS_API_KEY'] || '',
  voiceIdFemale: process.env['11LABS_FEMALE_VOICE_ID'] || '',
  voiceIdMale: process.env['11LABS_MALE_VOICE_ID'] || ''
};

// --- MINIMAX CONFIGURATION ---
export const MINIMAX_CONFIG = {
  bearerToken: process.env['MINIMAX_BEARER_TOKEN'] || '',
  voiceIdMale: process.env['MINIMAX_MALE_ID'] || 'English_Explanatory_Man',
  voiceIdFemale: process.env['MINIMAX_FEMALE_ID'] || 'English_Upbeat_Woman',
  modelId: 'speech-2.6-hd',
};

// --- VOLCENGINE CONFIGURATION ---
export const VOLCENGINE_CONFIG = {
  accessToken: process.env.VOLCENGINE_TTS_ACCESS_TOKEN || '',
  appId: process.env.VOLCENGINE_TTS_APP_ID || '',
  voiceIdMale: 'zh_male_dayi_saturn_bigtts',
  voiceIdFemale: 'zh_female_mizai_saturn_bigtts',
  resourceId: process.env.VOLCENGINE_TTS_2_RESOURCE_ID || 'seed-tts-2.0',
};

// --- TTS PROVIDER CONFIGURATION ---
export type TTSProviderType = 'google' | 'elevenlabs' | 'minimax' | 'volcengine';

// Default TTS provider
export const DEFAULT_TTS_PROVIDER: TTSProviderType = 'minimax';

// ========== SMART PPT COLOR THEMES ==========
export interface ColorTheme {
  id: string;
  nameEn: string;
  nameZh: string;
  colors: {
    primary: string;      // Main color for titles, headers
    secondary: string;    // Secondary elements
    accent: string;       // Highlights, icons
    background: string;   // Slide background
    text: string;         // Body text
    textOnDark: string;   // Text on dark backgrounds
  };
  preview: string;        // CSS gradient for preview
}

export const PPT_COLOR_THEMES: ColorTheme[] = [
  // ============================================================
  // 📰 GQ风尚 (GQ Fashion) - 高端杂志、奢华留白、衬线标题
  // ============================================================
  {
    id: 'gq_fashion',
    nameEn: 'GQ Fashion Field',
    nameZh: 'GQ风尚场',
    colors: {
      primary: '#000000',      // 纯黑 - GQ 核心色
      secondary: '#1a1a2e',    // 深蓝黑
      accent: '#722F37',       // 酒红强调色
      background: '#FAFAFA',   // 近白背景
      text: '#1a1a1a',         // 深灰正文
      textOnDark: '#FFFFFF'    // 白色反色
    },
    preview: 'linear-gradient(135deg, #000000 0%, #722F37 100%)'
  }
];

export const getColorTheme = (themeId: string): ColorTheme => {
  return PPT_COLOR_THEMES.find(t => t.id === themeId) || PPT_COLOR_THEMES[0];
};

// ========== IMAGE STYLE CONFIGURATION ==========
export interface ImageStyleDefinition {
  id: ImageStylePreset;
  nameEn: string;
  nameZh: string;
  description: string;
  promptTemplate: string;
  constraints: string;
  jsonTemplate?: any; // Partial JSON structure for the style
}

export const IMAGE_STYLE_DEFINITIONS: ImageStyleDefinition[] = [
  {
    id: 'ink_wash',
    nameEn: 'Chinese Ink Wash',
    nameZh: '水墨画',
    description: 'Traditional Chinese ink wash painting style with precise composition control',
    promptTemplate: `Chinese Ink Wash Painting (水墨画) style infographic with STRICT COMPOSITION RULES.
      
      **CANVAS & LAYOUT:**
      - Format: 4:3 infographic composition
      - Background: Rice paper texture with subtle, uneven fiber patterns
      - Negative space: Minimum 30% of canvas must be white/blank space
      
      **INK APPLICATION HIERARCHY (from foreground to background):**
      1. FOREGROUND (darkest ink, 80-100% opacity): Primary subject, boldest elements
      2. MID-GROUND (medium ink, 50-70% opacity): Supporting elements, transitional forms
      3. BACKGROUND (lightest ink, 20-40% opacity): Atmospheric effects, distant silhouettes
      
      **COLOR PALETTE (strictly limited):**
      - Primary: Black ink gradients (from pitch black to light grey)
      - Accent 1: Vermillion red (朱红) - use sparingly, max 5% of total area
      - Accent 2: Muted earth tones (umber, ochre) - max 10% of total area
      - Background: White/off-white rice paper
      
      **BRUSHWORK TECHNIQUES:**
      - Use cunfa (皴法) texture strokes for mountains/rocks
      - Use sumi-e (墨絵) wet-on-wet techniques for clouds/mist
      - Use feibai (飞白) dry-brush techniques for aged wood/metal
      - All strokes must show clear brush direction and pressure variation
      
      **HUMAN FIGURES (when required):**
      - Style: STRICTLY silhouette or back-view only
      - Size: Max 15% of canvas height for foreground figures
      - Detailing: NO facial features, NO fingers, NO realistic anatomy
      - Representation: Use simple geometric forms combined with flowing lines
      
      **TEXT INTEGRATION (CRITICAL):**
      - Font style: Modern Kaishu (楷书) - clean, legible, NOT traditional calligraphy
      - Stroke weight: Bold, uniform thickness (3-5px stroke width)
      - Placement: Center or upper-third of composition
      - Size: Book titles 8-12% of canvas height; smaller text 4-6% of canvas height
      - Ink density: 100% black, NO feathering or artistic variation
      - Alignment: Horizontal left-to-right (modern Chinese), NOT vertical traditional
      
      **COMMON ELEMENTS & THEIR SPECIFIC RENDERING:**
      - Mountains: Layered peaks with clear foreground/midground/background distinction
      - Water: Flowing lines with varying thickness, NO solid fills
      - Trees: Pine trees with needle clusters in feibai technique, willows with curved hanging branches
      - Architecture: Simplified rooflines and wall silhouettes, NOT detailed structures
      - Weapons: Abstract silhouette forms, NO realistic detailing
      
      **LIGHTING & ATMOSPHERE:**
      - Light source: Always implied top-left or top-center
      - Shadows: Created by darker ink washes, NOT solid black
      - Mist: Soft grey gradients between elements, minimum 15% opacity
      - Texture: Visible but subtle rice paper grain throughout`,
    constraints: `CRITICAL CONSTRAINTS for Ink Wash style (MUST FOLLOW):
      
      **ELEMENT CONTROL:**
      - Maximum 3-5 distinct elements per composition to avoid clutter
      - Each element must occupy clearly defined space (NO overlapping chaos)
      - Foreground elements: 40-50% of canvas area
      - Mid-ground elements: 25-35% of canvas area  
      - Background elements: 15-25% of canvas area
      
      **TEXT SPECIFICATIONS:**
      - LANGUAGE: Simplified Chinese characters ONLY (简体中文)
      - FONT: Modern, bold Kaishu (楷书) - legible, NOT artistic caoshu (草书) or traditional seal script
      - SIZE: Primary text 8-12% canvas height; secondary text 4-6% canvas height
      - PLACEMENT: Top-third or center of composition, NEVER bottom edge
      - INK: Pure black (100% opacity), uniform thickness, NO artistic variation
      - FORBIDDEN: Traditional Chinese characters (繁体字), English letters, vertical text layout
      
      **FIGURE REPRESENTATION:**
      - HUMANS: Silhouette or back-view ONLY, max 15% canvas height, NO faces/no hands/no realistic anatomy
      - ANIMALS: Simplified forms, symbolic representation, NOT realistic
      - OBJECTS: Essential elements only, each with clear purpose and placement
      
      **PROHIBITED ELEMENTS:**
      - NO photorealistic rendering of ANY kind
      - NO western perspective techniques (use Chinese floating perspective)
      - NO solid color fills (except text) - everything must be ink wash gradients
      - NO geometric patterns or decorative borders
      - NO maps, charts, or diagrammatic elements
      - NO modern objects (phones, guns with detailed mechanisms, vehicles with wheels)
      - NO gradients using colors other than black/grey/red (NO blue/green/yellow gradients)
      
      **COMPOSITION RULES:**
      - Follow rule of thirds for major element placement
      - Leading lines: Use ink strokes to guide viewer eye to focal point
      - Balance: Asymmetric but visually balanced (NOT symmetrical)
      - Breathing space: Minimum 30% white/negative space
      - Focal point: ONE primary element, clearly dominant (50%+ visual weight)
      
      **VISUAL STORYTELLING (Make it INTERESTING):**
      - Use **ink density to show importance**: Darker ink = more important elements
      - Use **negative space (留白) to create tension**: Empty space around key elements draws attention
      - Use **mist/fog (雾气) for mystery**: Obscure less important elements, reveal key information
      - Use **scale contrast**: Tiny figures against vast landscapes for awe, large figures for intimacy
      - Use **flowing water/wind lines** to guide viewer's eye through information
      - Use **mountain layering (层峦叠嶂)** to show progression or hierarchy
      
      **INFOGRAPHIC TYPE GUIDANCE:**
      - Many characters → Use **silhouette groupings** with labeled connections (like shadows around a table)
      - Historical events → Use **flowing scroll timeline** with key moments as ink splashes
      - Comparing ideas → Use **yin-yang composition** (dark vs light areas for contrast)
      - Concepts → Use **central figure with radiating brush strokes** connecting to related ideas
      
      **INFORMATION ACCURACY:**
      - ALL facts must come from the book - NO fabrication
      - Use conceptual representations when specific numbers are unavailable`,
    jsonTemplate: {
      style: {
        name: "Chinese Ink Wash Painting (水墨画)",
        description: "Traditional Chinese ink wash painting style with precise composition control",
        color_palette: "Strictly limited: Black ink gradients (pitch black to light grey), Vermillion red (max 5%), Muted earth tones (max 10%), White rice paper background",
        brushwork: "Cunfa (texture strokes), Sumi-e (wet-on-wet), Feibai (dry-brush). Visible brush direction and pressure variation."
      },
      composition: {
        aspect_ratio: "4:3",
        framing: "Infographic composition with minimum 30% negative space (white/blank space)",
        lighting: "Implied top-left or top-center light source, shadows created by darker ink washes",
        depth: "Layered peaks, atmospheric mist between elements"
      },
      constraints: {
        negative_prompt: "photorealistic, western perspective, solid color fills, geometric patterns, maps, charts, modern objects, gradients other than black/grey/red",
        safety: "family friendly"
      }
    }
  },
  {
    id: 'pixel_art',
    nameEn: 'Pixel Art',
    nameZh: '像素艺术',
    description: 'Retro 8-bit/16-bit game aesthetic with chunky pixels and vibrant colors',
    promptTemplate: `Pixel Art style infographic.
      Use a retro 8-bit or 16-bit video game aesthetic.
      **VISUALS:** Chunky, visible pixels, limited color palette, isometric or side-scrolling perspective.
      **COLORS:** Vibrant, saturated colors typical of SNES or Sega Genesis era.
      **TEXT:** Use a blocky, pixelated font for all text elements.`,
    constraints: `CRITICAL CONSTRAINTS for Pixel Art style:
      - EVERYTHING must look like it is made of pixels
      - NO smooth gradients or anti-aliasing
      - Characters and objects should be simplified and iconic
      - Text MUST be in a pixel font style
      
      **VISUAL STORYTELLING (Make it INTERESTING):**
      - Use **sprite animation frames** to show progression (like a game tutorial)
      - Use **health bars/progress bars** to show quantities or progress
      - Use **inventory grid layouts** to organize multiple items or concepts
      - Use **game UI elements**: XP bars for growth, hearts for importance, coins for value
      - Use **platform game layouts**: characters jumping between concept "platforms"
      - Use **boss battle composition**: key challenge as big sprite, solutions as power-ups
      
      **INFOGRAPHIC TYPE GUIDANCE:**
      - Many characters → Use **character select screen** layout with stats
      - Historical events → Use **level progression map** (like Super Mario World)
      - Comparing ideas → Use **versus screen** (character A vs character B with stats)
      - Concepts → Use **skill tree layout** branching from central idea
      - Data/statistics → Use **score counter or XP bar** representations
      
      **INFORMATION ACCURACY:**
      - ALL facts must come from the book - NO fabrication
      - Use game-like representations but with accurate information`,
    jsonTemplate: {
      style: {
        name: "Pixel Art",
        description: "Retro 8-bit/16-bit game aesthetic with chunky pixels and vibrant colors",
        color_palette: "Vibrant, saturated colors typical of SNES or Sega Genesis era",
        visuals: "Chunky, visible pixels, limited color palette"
      },
      composition: {
        aspect_ratio: "4:3",
        framing: "Isometric or side-scrolling perspective",
        lighting: "Flat or simple shading typical of retro games"
      },
      constraints: {
        negative_prompt: "smooth gradients, anti-aliasing, realistic, vector art, high resolution, blur",
        safety: "family friendly"
      }
    }
  },
  {
    id: 'zelda_botw',
    nameEn: 'Zelda: Breath of the Wild',
    nameZh: 'Zelda 旷野之息',
    description: 'Cel-shaded watercolor style inspired by Nintendo\'s masterpiece',
    promptTemplate: `Zelda: Breath of the Wild style infographic.
      Use cel-shaded watercolor aesthetic with soft gradients, vibrant natural colors, and dreamy lighting.
      Color palette: Soft pastels, sky blues, lush greens, golden sunlight, with white highlights.
      Aesthetic: Whimsical, adventurous, serene nature scenes with fantasy elements.`,
    constraints: `CRITICAL CONSTRAINTS for Zelda BOTW style:
      - Use stylized, cartoon-like character designs if humans are needed
      - Focus on nature: rolling hills, ancient ruins, magical forests, celestial elements
      - Soft, diffused lighting with warm golden hours or cool twilight tones
      - NO realistic humans, NO dark/horror themes, maintain family-friendly adventure tone
      
      **VISUAL STORYTELLING (Make it INTERESTING):**
      - Use **adventure map layouts**: Show concepts as destinations on a winding path
      - Use **shrine puzzle composition**: Key concept as glowing orb, related ideas as puzzle pieces
      - Use **Sheikah Slate UI**: Present information like in-game menus with icons
      - Use **paraglider perspective**: Bird's eye view showing relationships between areas
      - Use **cooking pot metaphor**: Combine ingredients (ideas) to create something new
      - Use **climbing progression**: Characters ascending toward goals, with stamina-like progress
      
      **INFOGRAPHIC TYPE GUIDANCE:**
      - Many characters → Use **character profiles** like Sheikah Slate entries with icons
      - Historical events → Use **memory fragments** floating in chronological order
      - Comparing ideas → Use **dual shrines** (two glowing structures representing opposites)
      - Concepts → Use **tower activation** spreading knowledge like revealing the map
      - Data/statistics → Use **heart containers or stamina wheels** as progress indicators
      
      **INFORMATION ACCURACY:**
      - ALL facts must come from the book - NO fabrication
      - Use adventure metaphors but with accurate information`,
    jsonTemplate: {
      style: {
        name: "Zelda: Breath of the Wild",
        description: "Cel-shaded watercolor style inspired by Nintendo's masterpiece",
        color_palette: "Soft pastels, sky blues, lush greens, golden sunlight, white highlights",
        aesthetic: "Whimsical, adventurous, serene nature scenes with fantasy elements"
      },
      composition: {
        aspect_ratio: "4:3",
        framing: "Wide shots emphasizing nature, rolling hills, ancient ruins",
        lighting: "Soft, diffused lighting with warm golden hours or cool twilight tones"
      },
      constraints: {
        negative_prompt: "realistic humans, dark themes, horror, gore, modern technology, sharp edges",
        safety: "family friendly"
      }
    }
  },
  {
    id: 'cute_hand_drawn',
    nameEn: 'Cute Hand-drawn',
    nameZh: '手绘可爱',
    description: 'Gentle and cute hand-drawn style with soft colors, rounded lines, and a girly aesthetic',
    promptTemplate: `Cute Hand-drawn illustration style infographic (Girl's hand-drawn style).
      
      **LINEWORK & STROKES:**
      - Hand-drawn quality: Visible, slightly wobbly lines that show human touch
      - Line weight: Soft, rounded strokes (2-4px thickness) with gentle tapering
      - Line character: Friendly, approachable, NOT sharp or aggressive
      - Outline style: Continuous, confident lines with occasional sketchy double-lines for texture
      
      **COLOR PALETTE (少女心色系):**
      - Primary colors: Soft pastels - baby pink, lavender, mint green, peach, creamy yellow
      - Secondary colors: Warm beige, soft coral, powder blue, lilac
      - Accent colors: Rosy pink, warm orange (used sparingly for highlights)
      - Neutral: Cream white, light grey (not pure white)
      - Saturation: Low to medium (20-50%), avoiding harsh or neon colors
      - Overall vibe: Warm, gentle, soothing, creates emotional comfort
      
      **SHADING & TEXTURING:**
      - Shading: Soft cell shading with smooth gradients (NOT harsh cel-shading)
      - Blending: Gentle color transitions with watercolor-like softness
      - Texture: Subtle paper texture visible throughout, occasional colored pencil strokes
      - Highlights: Small, rounded sparkle points or gentle glow effects
      
      **CHARACTER & FIGURE STYLE (when included):**
      - Proportions: Chibi or slightly deformed cute style (1:2 or 1:3 head-to-body ratio)
      - Facial features: Large, sparkly eyes; small dot noses; gentle curved mouths
      - Expression: Gentle smiles, curious looks, warm emotions (NOT angry/sad)
      - Body language: Soft gestures, welcoming poses, gentle hand positions
      - Detailing: Minimal, essential details only - focus on cuteness over accuracy
      
      **COMMON MOTIFS & DECORATIONS:**
      - Decorations: Small hearts, stars, flowers, bows, ribbons scattered tastefully
      - Floral elements: Simplified cherry blossoms, daisies, leaf patterns
      - Sparkle effects: Soft glowing dots around important elements
      - Borders: Rounded corner frames, dashed lines, wavy divider lines
      
      **TEXT INTEGRATION:**
      - Font style: Rounded, friendly handwritten font (模拟女生手写)
      - Letterforms: Slightly irregular, organic shapes with consistent baseline
      - Weight: Medium to bold for readability
      - Decorations: Text may have subtle underline, small heart/dot accents
      - Color: Dark grey or soft black (NOT harsh pure black), occasionally matching theme colors
      - Spacing: Generous letter spacing for approachable feel
      
      **COMPOSITION LAYOUT:**
      - Structure: Clear information hierarchy with gentle section divisions
      - Spacing: Ample white space, uncluttered, breathing room between elements
      - Flow: Gentle curves and rounded shapes guide the eye
      - Balance: Asymmetrical but harmonious, NOT rigid or formal
      - Sections: Clearly defined with rounded boxes, soft shadows, or decorative dividers
      
      **BACKGROUND TREATMENT:**
      - Base: Solid pastel color or extremely subtle gradient (light to lighter)
      - Patterns: Optional subtle dot grid, soft geometric patterns, or gentle texture
      - Depth: Minimal, focus on flat design with slight dimensional hints
      
      **MOOD & ATMOSPHERE:**
      - Emotional tone: Cheerful, warm, encouraging, supportive
      - Energy: Gentle and calm, NOT hyperactive
      - Personality: Thoughtful, caring, nurturing (女生手绘的温暖感)`,
    constraints: `CRITICAL CONSTRAINTS for Cute Hand-drawn style:
      
      **LINE & STROKE RULES:**
      - All lines must be rounded, soft, and friendly (NO sharp corners or aggressive angles)
      - Stroke ends must be rounded or slightly tapered (NOT blunt or square)
      - Maximum line weight: 4px for outlines, 2px for details
      - NO messy sketch lines or chaotic cross-hatching
      
      **COLOR RESTRICTIONS:**
      - Color palette: STRICTLY pastel and warm tones only
      - FORBIDDEN: Neon colors, high saturation (>60%), dark browns/greys, pure black backgrounds
      - Each element max 3 colors (base + shadow + highlight)
      - Background must be light (cream, light grey, pastel) - NO dark or black backgrounds
      
      **TEXT SPECIFICATIONS:**
      - LANGUAGE: Simplified Chinese characters (简体中文) for Chinese content
      - FONT STYLE: Rounded, hand-lettered appearance with slight organic irregularity
      - LEGIBILITY: High contrast against background (no light-on-light)
      - SIZE: Title text 12-18% canvas height, body text 6-10% canvas height
      - FORBIDDEN: Traditional Chinese (繁体字), English (unless decorative), vertical layout, sharp/blocky fonts
      
      **CHARACTER & FIGURE GUIDELINES:**
      - Facial expressions: ONLY positive emotions (gentle, curious, happy) - NO anger/sadness/scary faces
      - Body proportions: Cute/deformed style ONLY - NO realistic human proportions
      - Maximum figure size: 20% canvas height for foreground characters
      - NO realistic anatomy or detailed clothing textures
      
      **PROHIBITED ELEMENTS:**
      - NO photorealistic rendering or 3D effects
      - NO harsh geometric shapes (sharp squares, triangles, hard edges)
      - NO dark, moody, or horror themes
      - NO violent imagery (weapons, blood, fighting poses)
      - NO complex perspective or foreshortening
      - NO harsh drop shadows or strong contrast lighting
      - NO texture overlays that obscure the hand-drawn feel
      
      **COMPOSITION LIMITS:**
      - Element density: LOW - generous spacing required
      - Max decorative elements: 5-7 small hearts/stars/sparkles per image
      - Section separation: Clear visual breaks between content areas
      - Focal point: ONE primary subject per image, clearly dominant
      
      **TECHNICAL REQUIREMENTS:**
      - Resolution: High enough to show hand-drawn texture, but NOT pixel-perfect digital
      - Line quality: Slight imperfections welcome (shows human touch)
      - Color blending: Soft gradients allowed for depth, NO harsh color blocks
      
      **VISUAL STORYTELLING (Make it INTERESTING):**
      - Use **speech bubbles and thought clouds** for quotes and ideas
      - Use **bullet journals/planner layouts** to organize information
      - Use **doodle arrows and hand-drawn underlines** to connect concepts
      - Use **cute character reactions** (sparkly eyes for excitement, sweat drops for stress)
      - Use **sticker-like callouts** to highlight key points
      - Use **hand-lettered headers** with decorative flourishes
      
      **INFOGRAPHIC TYPE GUIDANCE:**
      - Many characters → Use **cute character lineup** with name tags and mini descriptions
      - Historical events → Use **diary entry timeline** with dates and doodles
      - Comparing ideas → Use **this vs that** layout with cute icons
      - Concepts → Use **mind map with flowers/hearts** as connection nodes
      - Data/statistics → Use **progress bars decorated with stars** or **pie charts with cute faces**
      
      **INFORMATION ACCURACY:**
      - ALL facts must come from the book - NO fabrication
      - Use cute representations but with accurate information`,
    jsonTemplate: {
      style: {
        name: "Cute Hand-drawn",
        description: "Gentle and cute hand-drawn style with soft colors, rounded lines, and a girly aesthetic",
        color_palette: "Soft pastels (baby pink, lavender, mint green), warm beige, cream white. Low to medium saturation.",
        linework: "Visible, slightly wobbly lines, soft rounded strokes (2-4px), friendly and approachable."
      },
      composition: {
        aspect_ratio: "4:3",
        framing: "Clear information hierarchy, generous white space, gentle curves",
        lighting: "Soft, flat lighting with gentle highlights"
      },
      constraints: {
        negative_prompt: "sharp corners, aggressive angles, neon colors, dark backgrounds, photorealistic, 3D effects, violence, horror",
        safety: "family friendly"
      }
    }
  },
  {
    id: 'hearthstone',
    nameEn: 'Hearthstone',
    nameZh: '炉石传说',
    description: 'Blizzard\'s iconic hand-painted fantasy card game style',
    promptTemplate: `Hearthstone card game style infographic.
      Use Blizzard's signature hand-painted fantasy art with warm tavern lighting and whimsical charm.
      Color palette: Rich golds, warm oranges, deep purples, magical blues on parchment textures.
      Aesthetic: Cozy fantasy tavern feel, ornate golden borders, magical glows, and playful characters.`,
    constraints: `CRITICAL CONSTRAINTS for Hearthstone style:
      - Use fantasy metaphors: mana crystals for energy, gold coins for value, scrolls for information
      - Characters should be stylized and exaggerated, NOT realistic
      - Include ornate frame borders, parchment paper textures, and magical particle effects
      - Warm, inviting atmosphere - NO dark horror or grim themes
      
      **VISUAL STORYTELLING (Make it INTERESTING):**
      - Use **card layouts** for character profiles (with mana cost, attack, health as metaphors)
      - Use **mana crystals** to represent importance levels or stages
      - Use **golden borders and legendary glow** for key information
      - Use **spell effects and magical particles** to show connections
      - Use **tavern board game layouts** for comparing options
      - Use **discover/choose mechanic** style for presenting alternatives
      
      **INFOGRAPHIC TYPE GUIDANCE:**
      - Many characters → Use **card collection gallery** with stats and abilities
      - Historical events → Use **quest chain progression** with objectives and rewards
      - Comparing ideas → Use **deck building** layout (two decks representing different approaches)
      - Concepts → Use **spell effect spreading** from central source with branches
      - Data/statistics → Use **mana curve or attack/health bars** as representations
      
      **INFORMATION ACCURACY:**
      - ALL facts must come from the book - NO fabrication
      - Use card game metaphors but with accurate information`,
    jsonTemplate: {
      style: {
        name: "Hearthstone",
        description: "Blizzard's iconic hand-painted fantasy card game style",
        color_palette: "Rich golds, warm oranges, deep purples, magical blues",
        aesthetic: "Cozy fantasy tavern feel, ornate golden borders, magical glows, playful characters"
      },
      composition: {
        aspect_ratio: "4:3",
        framing: "Card-like framing, tavern table perspective",
        lighting: "Warm tavern lighting, magical glows"
      },
      constraints: {
        negative_prompt: "realistic, dark horror, grim, sci-fi, modern",
        safety: "family friendly"
      }
    }
  },
  {
    id: 'witcher3',
    nameEn: 'The Witcher 3',
    nameZh: '巫师3',
    description: 'Dark fantasy oil painting style with atmospheric lighting',
    promptTemplate: `The Witcher 3 style infographic.
      Use rich oil painting aesthetic with dramatic lighting, atmospheric fog, and medieval fantasy elements.
      Color palette: Muted earth tones, deep forest greens, autumn oranges, with dramatic golden hour lighting.
      Aesthetic: Dark fantasy, atmospheric, painterly brushstrokes, moody but beautiful landscapes.`,
    constraints: `CRITICAL CONSTRAINTS for Witcher 3 style:
      - Focus on atmospheric landscapes: dense forests, medieval villages, ancient ruins
      - Use dramatic lighting: shafts of sunlight, firelight, moonlight through clouds
      - Human figures should be distant silhouettes or back views, NO detailed faces
      - Maintain dark fantasy tone but AVOID gore, explicit violence, or horror imagery
      
      **VISUAL STORYTELLING (Make it INTERESTING):**
      - Use **path divergence** (crossroads) to show choices and consequences
      - Use **notice board layouts** for presenting key information points
      - Use **witcher senses highlights** (red/orange glow) to emphasize important elements
      - Use **atmospheric depth layers** (foreground/midground/background) to show relationships
      - Use **weathered map/bestiary layouts** for organizing information
      - Use **potion/alchemy diagrams** for showing cause and effect
      
      **INFOGRAPHIC TYPE GUIDANCE:**
      - Many characters → Use **character profiles** with silhouettes and key traits
      - Historical events → Use **weathered chronicle scroll** with aged paper timeline
      - Comparing ideas → Use **moral choice layout** (left path vs right path from crossroads)
      - Concepts → Use **monster lore page** with central subject and surrounding annotations
      - Data/statistics → Use **potion brewing ingredients** as visual metaphor for components
      
      **INFORMATION ACCURACY:**
      - ALL facts must come from the book - NO fabrication
      - Use dark fantasy metaphors but with accurate information`,
    jsonTemplate: {
      style: {
        name: "The Witcher 3",
        description: "Dark fantasy oil painting style with atmospheric lighting",
        color_palette: "Muted earth tones, deep forest greens, autumn oranges",
        aesthetic: "Dark fantasy, atmospheric, painterly brushstrokes, moody landscapes"
      },
      composition: {
        aspect_ratio: "4:3",
        framing: "Cinematic, atmospheric landscapes",
        lighting: "Dramatic lighting, shafts of sunlight, firelight, moonlight"
      },
      constraints: {
        negative_prompt: "cartoon, anime, bright colors, happy, cute, modern",
        safety: "family friendly"
      }
    }
  },
  {
    id: 'ghibli',
    nameEn: 'Studio Ghibli',
    nameZh: '吉卜力',
    description: 'Miyazaki\'s signature hand-drawn anime style with dreamy landscapes',
    promptTemplate: `Studio Ghibli anime style infographic.
      Use Hayao Miyazaki's signature hand-drawn aesthetic with lush landscapes and expressive characters.
      Color palette: Soft watercolors, sky blues, grass greens, fluffy white clouds, warm sunset oranges.
      Aesthetic: Whimsical, heartwarming, detailed natural environments with a sense of wonder.`,
    constraints: `CRITICAL CONSTRAINTS for Ghibli style:
      - Emphasize beautiful nature: rolling hills, fluffy clouds, detailed foliage, flowing water
      - Characters should be simple and expressive in classic anime style
      - Include magical realism elements: floating objects, spirit creatures, fantastical machines
      - Maintain wholesome, family-friendly tone - NO violence or dark themes
      
      **VISUAL STORYTELLING (Make it INTERESTING):**
      - Use **flying sequences** (on brooms, airships, dragons) to show journeys or progress
      - Use **spirit forest layouts** with glowing creatures highlighting key points
      - Use **moving castle/machine diagrams** showing interconnected parts
      - Use **wind and flowing elements** (hair, leaves, water) to create visual flow
      - Use **window/door framing** to present key scenes or concepts
      - Use **food preparation layouts** (like cooking in Howl's Castle) for processes
      
      **INFOGRAPHIC TYPE GUIDANCE:**
      - Many characters → Use **spirit gathering** with each spirit representing a character
      - Historical events → Use **flight path timeline** showing journey from point to point
      - Comparing ideas → Use **two windows/doors** showing contrasting worlds
      - Concepts → Use **magical transformation sequence** spreading from center
      - Data/statistics → Use **floating lanterns or fireflies** for quantities, clouds for groups
      
      **INFORMATION ACCURACY:**
      - ALL facts must come from the book - NO fabrication
      - Use whimsical metaphors but with accurate information`,
    jsonTemplate: {
      style: {
        name: "Studio Ghibli",
        description: "Miyazaki's signature hand-drawn anime style with dreamy landscapes",
        color_palette: "Soft watercolors, sky blues, grass greens, fluffy white clouds, warm sunset oranges",
        aesthetic: "Whimsical, heartwarming, detailed natural environments"
      },
      composition: {
        aspect_ratio: "4:3",
        framing: "Wide landscape shots, detailed foliage",
        lighting: "Natural daylight, warm sunlight"
      },
      constraints: {
        negative_prompt: "violence, dark themes, horror, realistic, 3D, low quality",
        safety: "family friendly"
      }
    }
  },
  {
    id: 'ppt',
    nameEn: 'Smart Slides',
    nameZh: '智能幻灯片',
    description: 'Professional presentation slides with Banana Slides-style design (Gemini 3.0 Pro Image)',
    promptTemplate: `Professional Presentation Slide (Banana Slides Style).
      **RESOLUTION:** 4K quality, 16:9 aspect ratio
      **TEXT:** Clear, sharp, high-contrast typography
      **LAYOUT:** Automatic optimal composition based on content
      **DESIGN:** Modern professional aesthetic with decorative graphics
      **LANGUAGE:** Chinese text must use Simplified Chinese (简体中文)`,
    constraints: `CRITICAL CONSTRAINTS for Slides style (Banana Slides Reference):
      
      **TEXT ACCURACY (MOST IMPORTANT):**
      - Chinese text must be 100% accurate - NO pseudo-characters (伪汉字)
      - If uncertain about any character, use icons/symbols ONLY
      - Better to have NO text than WRONG text
      - Triple-check book titles and important text
      
      **DESIGN GUIDELINES:**
      - 4K resolution, 16:9 aspect ratio
      - Text must be clear and sharp
      - Automatically design optimal composition
      - Use appropriately sized decorative graphics to fill empty spaces
      - Each bullet point: 15-25 characters (Chinese) or concise phrases (English)
      - NO markdown symbols (like # or *) unless absolutely necessary
      
      **VISUAL HIERARCHY:**
      - Clear information hierarchy
      - Professional color palette
      - Use icons and vector graphics instead of photos
      - Clean, uncluttered layout
      
      **FIRST SLIDE (YouTube Thumbnail Style):**
      - Text: MAX 6 Chinese characters or 6 English words
      - Size: MASSIVE, covering 30-50% of slide
      - Contrast: HIGH contrast for visibility
      - Style: Dramatic, attention-grabbing
      
      **INFORMATION ACCURACY:**
      - ALL facts must come from the book - NO fabrication`,
    jsonTemplate: {
      style: {
        name: "Smart Slides (Banana Slides Style)",
        description: "Professional presentation slides optimized for Gemini 3.0 Pro Image",
        color_palette: "Professional modern palette with good contrast",
        visuals: "Clean typography, vector icons, decorative graphics"
      },
      composition: {
        aspect_ratio: "16:9",
        framing: "Presentation slide layout with clear hierarchy",
        lighting: "Clean, professional lighting"
      },
      constraints: {
        negative_prompt: "pseudo-characters, gibberish text, cluttered, hard to read, realistic photos, messy, markdown symbols",
        safety: "family friendly",
        text_rules: [
          "Chinese: 100% accurate Simplified Chinese only",
          "No pseudo-characters allowed",
          "Use icons if text uncertain"
        ]
      }
    }
  },
  {
    id: 'smart_ppt',
    nameEn: 'Smart PPT (HTML)',
    nameZh: '智能PPT (HTML)',
    description: 'HTML-based slides with Puppeteer screenshot. One slide per segment, consistent design system.',
    promptTemplate: `Smart Presentation Slide Style.
      **VISUAL STYLE:** Clean, professional slide design with deep blue theme
      **DESIGN:** Flat design with line icons and clear typography
      **IMPORTANT:** Do NOT include any technical labels, watermarks, or metadata text in the image. Focus purely on the visual content.
      **OUTPUT:** Professional slide suitable for educational content`,
    constraints: `CRITICAL CONSTRAINTS for Smart PPT:
      
      **UNIFIED DESIGN SYSTEM:**
      - Primary: #1E3A5F (deep navy blue - titles)
      - Secondary: #2E5077 (medium blue - subtitles)
      - Accent: #4A90A4 (teal - icons, highlights)
      - Background: #F5F7FA (light gray-blue)
      - Text: #2C3E50 (dark gray-blue)
      
      **ONE SLIDE PER SEGMENT:**
      - Each segment gets its own slide (no grouping)
      - Detailed content coverage per slide
      - Better for content-heavy books
      
      **TEXT ACCURACY:**
      - Chinese must be 100% accurate
      - Use Noto Sans SC font
      - If uncertain, use icons only`,
    jsonTemplate: {
      style: {
        name: "Smart PPT (HTML+Puppeteer)",
        description: "HTML-based slides with unified design system",
        color_palette: "Deep blue professional theme (#1E3A5F, #2E5077, #4A90A4)",
        visuals: "Flat design, line icons, CSS shapes"
      },
      composition: {
        aspect_ratio: "4:3",
        framing: "HTML rendered slide layout",
        lighting: "Flat, clean rendering"
      },
      constraints: {
        negative_prompt: "gradients, 3D effects, photos, complex shadows",
        safety: "family friendly",
        mode: "html_puppeteer",
        segments_per_image: 1
      }
    }
  },
  {
    id: 'panda_infographic',
    nameEn: 'Panda Infographic',
    nameZh: '熊猫信息图',
    description: 'Exquisitely hand-drawn infographic style where ALL human characters are replaced with anthropomorphic PANDAS while preserving cultural accuracy of clothing, architecture, and historical elements',
    promptTemplate: `Panda Infographic Style - Exquisitely Hand-Drawn Infographic Illustration.

      **CORE CONCEPT (CRITICAL - READ CAREFULLY):**
      ALL human figures MUST be replaced with anthropomorphic PANDAS. However, EVERYTHING ELSE must maintain historical and cultural accuracy.
      
      **PANDA CHARACTER DESIGN:**
      - Body: Anthropomorphic panda with human-like posture (standing upright, gesturing, etc.)
      - Face: Cute panda face with expressive eyes, black eye patches, round ears
      - Proportions: Slightly chibi/cute style (1:3 or 1:4 head-to-body ratio)
      - Size: Main panda characters should be 15-30% of canvas height
      - Expression: Expressive and emotive, matching the dialogue mood
      
      **CLOTHING & ACCESSORIES (MUST PRESERVE CULTURAL ACCURACY):**
      - For Chinese historical content: Pandas wear authentic Chinese clothing (汉服 Hanfu, 唐装 Tang robes, 明清官服 Ming/Qing official robes, 盔甲 armor for warriors)
      - For Western historical content: Pandas wear appropriate Western attire (togas, medieval armor, Victorian dress, etc.)
      - For modern content: Pandas wear contemporary clothing appropriate to the context
      - ALL clothing details, patterns, and accessories must be historically accurate to the book's setting
      
      **ARCHITECTURE & ENVIRONMENT (MUST PRESERVE CULTURAL ACCURACY):**
      - For Chinese content: Traditional Chinese architecture (宫殿 palaces with curved roofs, 庙宇 temples, 四合院 courtyards, 塔 pagodas)
      - For Western content: Appropriate Western architecture (Greek columns, Gothic cathedrals, Roman forums, etc.)
      - NEVER mix architectural styles from different cultures inappropriately
      
      **INFOGRAPHIC STYLE (CRITICAL):**
      - Format: 4:3 aspect ratio INFOGRAPHIC with clear information hierarchy
      - Layout: Structured sections with icons, charts, timelines, or relationship diagrams
      - NOT a freeform painting - must have infographic elements like labeled sections, data visualization, or concept maps
      - Include visual elements that convey INFORMATION, not just decoration
      
      **COLOR PALETTE:**
      - Primary: Warm, vibrant colors with good contrast
      - Panda colors: Classic black and white with soft shading
      - Background: Light, clean backgrounds that don't compete with characters
      - Accents: Cultural-appropriate accent colors (red/gold for Chinese, purple/gold for royal, etc.)
      
      **LINEWORK:**
      - Clean, confident ink lines with slight variation in weight
      - Smooth, professional comic illustration quality
      - NOT sketchy or rough - polished hand-drawn look
      
      **TEXT INTEGRATION:**
      - Font: Clean, legible font appropriate to the cultural context
      - Placement: Integrated into the infographic layout
      - Size: Title text 10-15% of canvas height; labels 5-8%`,
    constraints: `CRITICAL CONSTRAINTS for Panda Infographic style (MUST FOLLOW):

      **PANDA TRANSFORMATION RULES:**
      1. ALL humans become PANDAS - no exceptions
      2. Pandas retain human posture, gestures, and body language
      3. Pandas wear historically accurate clothing from the book's cultural context
      4. Pandas use historically accurate props/tools/weapons from the book's setting
      
      **CULTURAL ACCURACY (EXTREMELY IMPORTANT):**
      - For Chinese historical books: 
        * Buildings MUST be Chinese architecture (飞檐翘角, 红墙金瓦)
        * Clothing MUST be Chinese historical attire (NOT Western suits)
        * Objects MUST be Chinese artifacts (毛笔, 卷轴, 青铜器)
      - For Western historical books:
        * Buildings MUST be Western architecture appropriate to the era
        * Clothing and objects MUST match the Western historical period
      - NEVER mix elements from different cultures
      
      **INFOGRAPHIC REQUIREMENTS:**
      - MUST include structured information elements (NOT pure illustration)
      - Include at least ONE of: timeline, chart, diagram, labeled sections, concept map, or data visualization
      - Clear visual hierarchy with sections and organization
      - Educational and informative, not just decorative
      
      **TEXT SPECIFICATIONS:**
      - LANGUAGE: If Chinese content, use ONLY Simplified Chinese (简体中文)
      - ACCURACY: All text must be 100% accurate - NO pseudo-characters
      - FIRST IMAGE: MAX 6 Chinese characters or 6 English words, MASSIVE and eye-catching
      - When in doubt about text accuracy, use icons/symbols instead
      
      **FIRST IMAGE (YouTube Thumbnail Style):**
      - Text: BRIEF, impactful (MAX 6 characters/words)
      - Size: Text covers 30-50% of image
      - Contrast: HIGH contrast (bright on dark or vice versa)
      - Impact: Visually striking, vibrant colors, dramatic composition
      - Style: Similar to successful YouTube thumbnails - attention-grabbing
      
      **VISUAL STORYTELLING (Make it INTERESTING - CRITICAL):**
      - Use **visual metaphors** that match the content:
        * Power struggle → Pandas in tug-of-war or chess game
        * Growth/Progress → Pandas climbing stairs/ladder/mountain
        * Conflict → Two groups of pandas facing off
        * Discovery → Panda with magnifying glass or lightbulb
        * Tragedy → Pandas with bowed heads, muted colors
      - Create **contrast and tension** in the composition:
        * Show opposing forces on left and right
        * Use before/after comparisons
        * Highlight problem vs solution
      - Use **exaggerated proportions** to emphasize importance:
        * Key characters as LARGER pandas
        * Critical text/numbers in BIGGER font
        * Important objects shown prominently
      - Add **visual narratives** with directional elements:
        * Arrows showing cause and effect
        * Paths showing journey/progress
        * Numbered steps for sequences
      
      **INFOGRAPHIC TYPE GUIDANCE:**
      - For books with many characters: Use RELATIONSHIP MAP with labeled connections
      - For historical narratives: Use TIMELINE with key events marked
      - For comparing ideas/groups: Use COMPARISON CHART side-by-side
      - For explaining concepts: Use CONCEPT MAP with central idea and branches
      - For data/statistics: Use DATA VISUALIZATION with charts
      - For processes: Use FLOW CHART with steps
      - For manufacturing/creation processes: Use PROCESS DIAGRAM with sequential stages
      - For 2x2 categorization/prioritization: Use MATRIX (e.g., Eisenhower Matrix)
      - For showing overlaps/commonalities: Use VENN DIAGRAM with intersecting circles
      - For geographic locations/routes: Use GEOGRAPHIC MAP showing places and paths
      - For showing causality: Use CAUSE EFFECT diagram (fishbone/Ishikawa)
      - For listing advantages/disadvantages: Use PROS CONS with split layout
      - For cyclical processes: Use CYCLE DIAGRAM with circular flow
      - For hierarchical progression: Use PYRAMID showing levels from base to top
      - For conversion/filtering processes: Use FUNNEL showing narrowing stages
      - For complex interconnected relationships: Use NETWORK GRAPH with nodes and edges
      
      **INFORMATION ACCURACY:**
      - ALL facts in the infographic MUST come from the book
      - DO NOT fabricate statistics or dates
      - Use conceptual descriptions if specific numbers are not in the book
      
      **PROHIBITED ELEMENTS:**
      - NO realistic human faces (only panda faces)
      - NO maps or geographical charts
      - NO pseudo-characters or gibberish text
      - NO mixing of cultural elements inappropriately
      - NO dark, horror, or violent imagery
      - NO freeform paintings without infographic structure
      - NO fabricated data or made-up statistics`,
    jsonTemplate: {
      style: {
        name: "Panda Infographic",
        description: "Hand-drawn infographic style where ALL humans become pandas while preserving cultural accuracy. Visual storytelling through character poses, facial expressions, and icons - avoiding text-heavy dialogue boxes or speech bubbles.",
        color_palette: {
          primary: ["warm tones", "vibrant colors"],
          character: ["classic panda black", "panda white"],
          accents: ["cultural-appropriate colors"]
        },
        linework: "Clean, confident ink lines with professional comic illustration quality",
        character_design: "Anthropomorphic pandas with expressive faces, wearing historically accurate clothing"
      },
      composition: {
        aspect_ratio: "4:3",
        framing: "INFOGRAPHIC layout with structured sections, charts, diagrams, or timelines",
        lighting: "Bright, clean lighting with good contrast"
      },
      constraints: {
        negative_prompt: [
          "realistic humans",
          "human faces",
          "maps",
          "charts",
          "pseudo-characters",
          "mixed cultural elements",
          "horror",
          "violence",
          "dark themes",
          "freeform painting without structure"
        ],
        safety: "family friendly",
        panda_rules: [
          "ALL humans become pandas",
          "pandas wear culturally accurate clothing",
          "maintain historical accuracy for architecture and objects"
        ],
        infographic_requirement: "MUST include structured information elements - NOT pure illustration"
      }
    }
  },
  {
    id: 'panda_infographic_v2',
    nameEn: 'Panda Infographic V2',
    nameZh: '熊猫信息图V2',
    description: 'Experimental panda infographic style using NATURAL LANGUAGE prompts instead of JSON, aiming to improve Chinese character accuracy in generated images',
    promptTemplate: `Panda Infographic V2 Style - NATURAL LANGUAGE Description Format.

      **CORE CONCEPT (CRITICAL - READ CAREFULLY):**
      ALL human figures MUST be replaced with anthropomorphic PANDAS. However, EVERYTHING ELSE must maintain historical and cultural accuracy.
      
      **OUTPUT FORMAT (CRITICAL - NATURAL LANGUAGE, NOT JSON):**
      This style uses structured natural language descriptions INSTEAD of JSON format.
      The visualPrompt should be a flowing narrative description, NOT a JSON object.
      
      **PANDA CHARACTER DESIGN:**
      - Body: Anthropomorphic panda with human-like posture (standing upright, gesturing, etc.)
      - Face: Cute panda face with expressive eyes, black eye patches, round ears
      - Proportions: Slightly chibi/cute style (1:3 or 1:4 head-to-body ratio)
      - Size: Main panda characters should be 15-30% of canvas height
      - Expression: Expressive and emotive, matching the scene mood
      
      **CLOTHING & ACCESSORIES (MUST PRESERVE CULTURAL ACCURACY):**
      - For Chinese historical content: Pandas wear authentic Chinese clothing (汉服 Hanfu, 唐装 Tang robes, 明清官服 Ming/Qing official robes)
      - For Western historical content: Pandas wear appropriate Western attire
      - ALL clothing details, patterns, and accessories must be historically accurate to the book's setting
      
      **ARCHITECTURE & ENVIRONMENT (MUST PRESERVE CULTURAL ACCURACY):**
      - For Chinese content: Traditional Chinese architecture (宫殿 palaces with curved roofs, 庙宇 temples, 四合院 courtyards)
      - For Western content: Appropriate Western architecture
      - NEVER mix architectural styles from different cultures inappropriately
      
      **INFOGRAPHIC STYLE (CRITICAL):**
      - Format: 4:3 aspect ratio INFOGRAPHIC with clear information hierarchy
      - Layout: Structured sections with icons, charts, timelines, or relationship diagrams
      - NOT a freeform painting - must have infographic elements like labeled sections, data visualization, or concept maps`,
    constraints: `CRITICAL CONSTRAINTS for Panda Infographic V2 style (MUST FOLLOW):

      **中文结构化描述格式 (CRITICAL - V2 uses Chinese format):**
      
      Use this format for your visualPrompt output:
      
      ===【信息图描述】===
      
      【类型】[选择: 关系图/时间轴/对比图/流程图/概念图/层级图/数据可视化]
      【标题】简短中文标题 (最多6个汉字)
      【副标题】中文副标题 (可选)
      
      【时代背景】[如: 清朝 1900年]
      【文化背景】[选择: 中国/西方/日本/罗马/希腊/埃及/其他]
      
      【布局】
      - 方向: [从左到右/从上到下/从右到左/环形]
      - 元素数量: [数字]
      - 背景场景: [场景描述，禁止地图]
      
      【核心元素】
      1. [元素标签] (尺寸：大/中/小, 情绪：中性/正面/负面/混乱/恐慌) - 视觉描述
      2. [第二个元素标签] (尺寸，情绪) - 描述
      3. [继续列出所有元素...]
      
      【元素关系 - Mermaid Edge List】
      \`\`\`mermaid
      元素A -->|关系| 元素B
      元素B -->|关系| 元素C
      \`\`\`
      
      【色彩方案】[色彩描述]
      【语言要求】所有文字必须使用简体中文
      
      ===【描述结束】===
      
      **PANDA TRANSFORMATION RULES:**
      1. ALL humans become PANDAS - no exceptions
      2. Pandas retain human posture, gestures, and body language
      3. Pandas wear historically accurate clothing from the book's cultural context
      4. Pandas use historically accurate props/tools/weapons from the book's setting
      
      **CULTURAL ACCURACY (EXTREMELY IMPORTANT):**
      - For Chinese historical books: 
        * Buildings MUST be Chinese architecture
        * Clothing MUST be Chinese historical attire (NOT Western suits)
        * Objects MUST be Chinese artifacts
      - For Western historical books:
        * Buildings MUST be Western architecture appropriate to the era
        * Clothing and objects MUST match the Western historical period
      - NEVER mix elements from different cultures
      
      **MERMAID EDGE LIST FOR RELATIONSHIPS (CRITICAL):**
      - Format: 元素A -->|关系| 元素B
      - Arrow direction: FROM actor TO target
      - Keep edge labels SHORT (max 4 characters)
      
      **NODE CONSISTENCY RULE (CRITICAL):**
      - Node names in Mermaid MUST match Core Elements labels EXACTLY
      
      **NO AUTO-GENERATED TEXT (CRITICAL):**
      - ONLY render text from 【标题】, 【副标题】, and 【核心元素】标签
      - DO NOT add random decorative text
      - PREVENT HALLUCINATIONS: No pseudo-characters allowed
      
      **PROHIBITED ELEMENTS:**
      - NO realistic human faces (only panda faces)
      - NO maps or geographical charts
      - NO pseudo-characters or gibberish text
      - NO mixing of cultural elements inappropriately
      - NO dark, horror, or violent imagery
      - NO freeform paintings without infographic structure
      - NO fabricated data or made-up statistics`,
    jsonTemplate: {
      style: {
        name: "Panda Infographic V2 (Natural Language)",
        description: "Hand-drawn infographic style where ALL humans become pandas. Uses NATURAL LANGUAGE descriptions instead of JSON for improved Chinese text accuracy.",
        color_palette: {
          primary: ["warm tones", "vibrant colors"],
          character: ["classic panda black", "panda white"],
          accents: ["cultural-appropriate colors"]
        },
        linework: "Clean, confident ink lines with professional comic illustration quality",
        character_design: "Anthropomorphic pandas with expressive faces, wearing historically accurate clothing"
      },
      composition: {
        aspect_ratio: "4:3",
        framing: "INFOGRAPHIC layout with structured sections, charts, diagrams, or timelines",
        lighting: "Bright, clean lighting with good contrast"
      },
      constraints: {
        negative_prompt: [
          "realistic humans",
          "human faces",
          "maps",
          "pseudo-characters",
          "mixed cultural elements",
          "horror",
          "violence",
          "freeform painting without structure"
        ],
        safety: "family friendly",
        panda_rules: [
          "ALL humans become pandas",
          "pandas wear culturally accurate clothing",
          "maintain historical accuracy for architecture and objects"
        ],
        infographic_requirement: "MUST include structured information elements - NOT pure illustration",
        output_format: "NATURAL LANGUAGE description with Mermaid Edge List for relationships"
      }
    }
  },
  {
    id: 'panda_comic',
    nameEn: 'Panda Comic',
    nameZh: '熊猫漫画',
    description: '4-panel comic (四格漫画) with Zootopia-style anthropomorphic pandas, using ①②③④ numbered panels',
    promptTemplate: `Panda 4-Panel Comic (四格漫画) - Disney Zootopia Animation Style.

      ** CORE CONCEPT(CRITICAL - READ CAREFULLY):**
  This is a TRADITIONAL 4 - PANEL COMIC(四格漫画 / Yonkoma), NOT an infographic!
      ALL human figures MUST be replaced with anthropomorphic PANDAS.
      EVERYTHING ELSE must maintain historical and cultural accuracy.
      
      ** LAYOUT FORMAT(CRITICAL - 2x2 GRID):**
   - Canvas: 4: 3 aspect ratio divided into 2x2 GRID(4 equal panels)
     - Panel arrangement: 
         * Top - left: Panel ① (Setup / Introduction)
   * Top - right: Panel ② (Development)
     * Bottom - left: Panel ③ (Twist / Climax)
       * Bottom - right: Panel ④ (Conclusion / Punchline)
         - Each panel: Clear black border(2 - 3px), slight rounded corners optional
           - Panel spacing: 8 - 12px white gutter between panels
             - Panel numbering: ONLY the circled number symbol (①②③④) - ABSOLUTELY NO TEXT next to the number!
               * FORBIDDEN: "① 起 (Ki)", "② 承 (Shō)", "③ 転 (Ten)", "④ 結 (Ketsu)"
               * FORBIDDEN: Any Chinese characters (起/承/转/结) or Japanese romanization (Ki/Shō/Ten/Ketsu)
               * CORRECT: Just "①", "②", "③", "④" with NO additional text

              ** NARRATIVE STRUCTURE:**
                 - Panel ①: Introduce the scene, characters, and situation
                   - Panel ②: Develop the story, add detail or action
                     - Panel ③: Introduce a twist, surprise, or turning point
                       - Panel ④: Resolution, punchline, or conclusion

                        ** PANDA CHARACTER DESIGN (ZOOTOPIA-INSPIRED STYLE - CRITICAL):**
                          - ART STYLE: Disney Zootopia 3D animation STYLE - NOT Japanese manga/anime!
                          - IMPORTANT COPYRIGHT NOTICE:
                            * DO NOT include any Zootopia original characters (Nick Wilde, Judy Hopps, Flash, etc.)
                            * DO NOT make pandas look like Po from Kung Fu Panda (no green eyes, no belly patterns)
                            * Create ORIGINAL panda characters inspired by Zootopia's art style only
                            - RENDERING: 3D CGI look with soft lighting and subtle shadows
                              - FUR TEXTURE: Realistic, fluffy fur texture visible on panda characters
                                - EYES: Large, expressive eyes with detailed iris - use BROWN or BLACK iris, NOT green
                                  - FACIAL FEATURES: Cute panda face with black eye patches, round ears, small black nose
                                    - EXPRESSIONS: Highly expressive and emotive (joy, surprise, anger, concern)
                                      - BODY: Anthropomorphic panda with human-like posture, SLIM build (NOT chubby like Po)
                                        - PROPORTIONS: Realistic animal proportions (1:4 to 1:5 head-to-body), NOT the chunky Po build
                                          - SIZE: Main characters should fill 40-60% of each panel vertically
                                            - PERSONALITY: Each panda should have distinct personality shown through body language

                                    ** CLOTHING & ACCESSORIES(MUST PRESERVE CULTURAL ACCURACY):**
                                      - For Chinese historical content: Authentic Chinese clothing(汉服, 唐装, 明清官服)
                                        - For Western historical content: Appropriate Western attire for the era
                                          - ALL clothing must be historically accurate to the book's dynasty/period
                                            - NO mixing of Chinese and Western elements inappropriately

                                              ** BACKGROUNDS & ENVIRONMENTS:**
                                                - Simple, non - distracting backgrounds appropriate to scene
                                                  - For Chinese content: Traditional Chinese architecture and objects
                                                    - Use speed lines, emotion bubbles(💢😰💦), and manga effects
                                                      - Background complexity should NOT compete with characters

                                                      ** DIALOGUE & TEXT:**
                                                        - Speech bubbles: Round / oval bubbles with tails pointing to speaker
                                                          - Text: Clean, legible Simplified Chinese(简体中文) ONLY
                                                            - Font: Clear sans - serif or slightly rounded font
                                                              - NO pseudo - characters or gibberish - ALL text must be accurate
                                                                - Thought bubbles: Cloud - shaped for internal thoughts
                                                                  - Sound effects: Stylized onomatopoeia in Chinese(if needed)
      
      ** ART STYLE (ZOOTOPIA/疑狂动物城 AESTHETIC):**
  - STYLE: Disney Zootopia 3D animation look - polished, professional, cinematic
    - RENDERING: Soft 3D CGI rendering with ambient occlusion and subtle shadows
      - LIGHTING: Warm, natural lighting with soft highlights and shadows
        - TEXTURES: Realistic fur, fabric, and material textures
          - QUALITY: High-quality Disney/Pixar animation studio level
            - NO LINEWORK: Avoid heavy black outlines - use soft edges and 3D shading instead

              ** COLOR PALETTE (VIBRANT ZOOTOPIA COLORS):**
                - Characters: Classic panda black & white with realistic fur shading and warm highlights
                  - Clothes: Vibrant, saturated colors - culturally appropriate (red/gold for Chinese, etc.)
                    - Backgrounds: Rich, detailed environments with depth and atmosphere
                      - Overall: Bright, cheerful, optimistic Disney color grading
                        - Lighting: Warm golden hour or soft studio lighting`,
    constraints: `CRITICAL CONSTRAINTS for Panda Comic(4 - Panel) style(MUST FOLLOW):

      ** PANEL LAYOUT(NON - NEGOTIABLE):**
  - MUST be exactly 4 panels in a 2x2 grid layout
    - Panels MUST be clearly separated with visible borders
      - Panel order: Read left - to - right, top - to - bottom(① → ② → ③ → ④)
        - Each panel tells one beat of the story

          ** NARRATIVE REQUIREMENTS:**
             - MUST follow the 4-panel structure:
         * Panel ①: Setup - introduce situation
   * Panel ②: Development - build on the setup
     * Panel ③: Twist - introduce unexpected element
       * Panel ④: Conclusion - resolve with impact
      - The 4 panels should tell a COMPLETE mini - story
        - Content must be based ONLY on the book - NO fabrication

          ** PANDA TRANSFORMATION RULES:**
            1. ALL humans become PANDAS - no exceptions
2. Pandas retain human posture, gestures, and clothing
3. Pandas MUST be expressive - emotions clearly visible
4. NO realistic human faces or figures

  ** CULTURAL ACCURACY(EXTREMELY IMPORTANT):**
    - For Chinese historical books:
        * Clothing MUST match the correct dynasty(汉 / 唐 / 宋 / 明 / 清)
  * Architecture MUST be Chinese style(飞檐翘角, 红墙金瓦)
    * Objects MUST be period - accurate Chinese items
      - For Western historical books:
        * Use appropriate Western elements for the era
  - NEVER mix Chinese and Western elements inappropriately
    - Dynasty accuracy: 唐朝 ≠ 明朝 ≠ 清朝 - get it RIGHT

      ** TEXT SPECIFICATIONS(CRITICAL - NO ERRORS ALLOWED):**
        - LANGUAGE: ONLY Simplified Chinese(简体中文) for Chinese content
          - ACCURACY: Every character must be 100 % correct - NO pseudo - characters(伪汉字)
            - FORBIDDEN: 
        * NO gibberish or made - up characters
  * NO Traditional Chinese(繁体字) mixed in
        * NO English text(unless book is in English)
  * NO random strokes that look like Chinese
    - Speech bubbles: Keep text SHORT and legible(max 15 characters per bubble)
      - If unsure about a character, use a different word or omit text

        ** VISUAL ELEMENTS:**
          - Manga - style expressions: sweat drops(😰), anger veins(💢), sparkles(✨)
            - Motion lines for action scenes
              - Emphasis effects(bold lines, zoom effects) for dramatic moments
                - Background patterns for mood(flower petals for romance, dark lines for tension)
      
      ** FIRST IMAGE(Cover / Thumbnail Style):**
  - Can be a compelling single panel OR the full 4 - panel layout
    - Must grab attention with vibrant colors and clear subject
      - Title text: MAX 6 Chinese characters, large and prominent
        - Style: Eye - catching like a manga cover or YouTube thumbnail

          ** PROHIBITED ELEMENTS:**
            - NO infographic - style layouts(this is a COMIC, not an infographic)
              - NO charts, diagrams, timelines, or data visualizations
                - NO realistic human faces
                  - NO pseudo - characters or text errors
                    - NO mixing of cultural elements(Chinese clothes with Western buildings, etc.)
- NO dark, horror, or violent imagery
  - NO more than 4 panels(stick to the format)
    - NO fabricated content or made - up statistics

      ** COPYRIGHT PROTECTION (CRITICAL - LEGAL REQUIREMENT):**
        - ABSOLUTELY NO Zootopia original characters: Nick Wilde (fox), Judy Hopps (rabbit), Flash (sloth), etc.
        - ABSOLUTELY NO Kung Fu Panda characters: Po (chubby panda with green eyes), Tigress, Shifu, etc.
        - Pandas MUST be ORIGINAL designs, NOT copies of existing movie characters
        - Pandas should have BROWN or BLACK eyes, NOT green eyes like Po
        - Pandas should have SLIM or NORMAL build, NOT chubby like Po
        - If the image contains ANY recognizable copyrighted character, it will be REJECTED
      
      ** PANEL NUMBERING (CRITICAL - NO EXTRA TEXT):**
        - Panel labels MUST be ONLY the circled number: ①, ②, ③, ④
          - ABSOLUTELY FORBIDDEN to add ANY text next to panel numbers:
            * NO "① 起 (Ki)" - just "①"
            * NO "② 承 (Shō)" - just "②"
            * NO "③ 転 (Ten)" - just "③"
            * NO "④ 結 (Ketsu)" - just "④"
          - If you add Chinese characters or Japanese romanization to panel labels, the image is REJECTED`,
    jsonTemplate: {
      // 4格漫画专用的简洁结构 - 移除所有infographic相关字段
      title: "漫画标题 (最多6个汉字)",
      subtitle: "可选副标题",
      panels: [
        {
          panel_number: 1,
          scene: "场景背景描述",
          characters: "角色和动作描述",
          mood: "情绪氛围",
          dialogue: "可选：气泡中的对话"
        },
        {
          panel_number: 2,
          scene: "第二格场景",
          characters: "第二格角色和动作",
          mood: "第二格情绪"
        },
        {
          panel_number: 3,
          scene: "第三格场景（转折点）",
          characters: "第三格角色和动作",
          mood: "第三格情绪"
        },
        {
          panel_number: 4,
          scene: "第四格场景（结局）",
          characters: "第四格角色和动作",
          mood: "第四格情绪"
        }
      ],
      era_context: "时代背景",
      cultural_context: "chinese",
      // 保留的约束规则
      constraints: {
        negative_prompt: [
          "realistic humans",
          "human faces",
          "infographic layout",
          "charts",
          "diagrams",
          "maps",
          "geographical maps",
          "country outlines",
          "region borders",
          "Nick Wilde",
          "Judy Hopps",
          "Zootopia characters",
          "Po from Kung Fu Panda",
          "Kung Fu Panda characters",
          "green-eyed panda",
          "chubby panda like Po"
        ],
        safety: "family friendly",
        panda_rules: [
          "ALL humans become pandas",
          "ORIGINAL panda designs only",
          "pandas have BROWN or BLACK eyes, NOT green",
          "pandas are SLIM, NOT chubby like Po",
          "pandas wear dynasty-accurate clothing"
        ],
        text_rules: [
          "ONLY Simplified Chinese (简体中文)",
          "NO pseudo-characters",
          "ALL text must be 100% accurate"
        ],
        panel_numbering: "ONLY use ①②③④ symbols - NO additional text"
      }
    }
  },
  {
    id: 'panda_comic_jimeng',
    nameEn: 'Panda Comic (JiMeng AI)',
    nameZh: '熊猫四格漫画-即梦',
    description: '使用火山引擎即梦AI生成的四格漫画，成本更低，中文理解更好。所有角色都是拟人化熊猫，保持疯狂动物城风格。',
    promptTemplate: `【画面类型】四格漫画，2x2标准网格布局
【艺术风格】迪士尼疯狂动物城3D动画风格，不使用日本漫画风格
【角色设定】所有人物角色都是拟人化的熊猫，穿着符合历史背景的服饰

【四格漫画结构】
- 左上格①：起（引入场景，介绍情境）
- 右上格②：承（发展情节，推进故事）
- 左下格③：转（转折或高潮，出现意外）
- 右下格④：合（结局或点题，收尾）

【熊猫角色规范】
- 身体：直立行走的拟人化熊猫，身材修长（非胖墩墩的功夫熊猫Po造型）
- 面部：可爱的熊猫脸，黑色眼圈，圆耳朵，小黑鼻子
- 眼睛：大而有神，使用棕色或黑色虹膜（禁止绿色眼睛）
- 表情：丰富的情感表达（喜怒哀乐清晰可见）
- 毛发：柔软蓬松的黑白毛发质感

【服装要求】
- 严格按照书籍中的历史朝代和文化背景设计服装
- 中国历史内容：使用对应朝代的汉服/官服/铠甲
- 西方历史内容：使用对应时期的西方服饰
- 服装细节必须符合历史考证

【场景背景】
- 根据故事内容设置合适的历史场景
- 中国历史：传统中式建筑（飞檐翘角、红墙金瓦）
- 保持背景简洁，不抢夺角色焦点

【画面技术规范】
- 画风：3D渲染效果，柔和光影
- 光线：自然温暖的光照
- 构图：每格内主体人物占40-60%高度
- 分隔：四格之间有清晰的黑色边框（2-3像素）

【文字与对话】
- 使用圆形/椭圆形对话气泡
- 文字使用清晰易读的简体中文
- 每个气泡最多15个汉字
- 如需表情符号可适当使用

【严格禁止】
- 功夫熊猫Po的形象特征（胖墩墩身材、绿色眼睛、肚兜）
- 疯狂动物城原版角色（朱迪、尼克等）
- 真人面孔或写实人类
- 不同文化元素的混搭
- 伪汉字或乱码文字
- 恐怖、暴力、血腥内容`,
    constraints: `【即梦四格漫画约束条件】

【布局规范】
- 必须是标准的2x2四格布局
- 每格都有清晰可见的黑色边框
- 格与格之间有白色间隔（8-12像素）
- 四格顺序：①左上 → ②右上 → ③左下 → ④右下

【角色一致性要求】
- 同一角色在四格中必须保持相同外观
- 服装、配饰、体型在四格中保持一致
- 每个主要角色需要有可识别的个人特征

【历史准确性】
- 汉朝内容：汉服（深衣、直裾）、汉代建筑
- 唐朝内容：唐装（圆领袍、襦裙）、唐代宫殿
- 宋朝内容：宋服（交领长衫）、宋代园林
- 明朝内容：明服（曳撒、补服）、明代城墙
- 清朝内容：清服（马褂、旗装）、清代府邸
- 严禁混淆朝代！

【文字规范】
- 仅使用简体中文
- 每个汉字必须100%准确
- 如不确定某字，使用同义词替代
- 禁止繁体字、日文、韩文混入

【第一张图特别要求】
- 可以是吸引人的封面单图或完整四格
- 标题文字：最多6个汉字，大而醒目
- 色彩饱和度高，视觉冲击力强

【禁止元素】
- 信息图表、流程图、时间轴等信息图类型
- 地图或地理图表
- 写实人类或真人照片风格
- 现代电子设备（手机、电脑等）
- 与书籍无关的虚构内容`,
    jsonTemplate: null  // 即梦风格不使用JSON，使用中文结构化描述
  },
  {
    id: 'infographic_1pager',
    nameEn: 'Infographic Overview (1-Pager)',
    nameZh: '信息图概览 (单页)',
    description: 'A single comprehensive infographic that summarizes the entire podcast content with key takeaways, themes, and visual representations.',
    promptTemplate: `Single-Page Infographic Overview Style.
      
      **CORE CONCEPT:**
      Create ONE comprehensive, visually stunning infographic that captures the ENTIRE book/podcast content.
      This is NOT a scene-by-scene illustration - it's a summary poster that covers all key points.
      
      **LAYOUT PRINCIPLES:**
      - Central theme/title prominently displayed
      - Key concepts organized in logical sections
      - Visual hierarchy guiding the viewer's eye
      - Icons and symbols representing main ideas
      - Data visualization where appropriate
      
      **VISUAL REQUIREMENTS:**
      - High-quality, polished design
      - Clear typography with excellent readability
      - Harmonious color palette
      - Professional infographic aesthetic
      - 4:3 aspect ratio
      
      **CONTENT REQUIREMENTS:**
      - Book/Podcast title as main heading
      - 4-6 key takeaways or themes
      - Visual representations of core concepts
      - Logical flow and information hierarchy`,
    constraints: `CRITICAL CONSTRAINTS for Infographic 1-Pager style:
      
      **SINGLE IMAGE RULE:**
      - ONLY ONE image will be generated for the ENTIRE podcast
      - This image must comprehensively represent all key content
      
      **CONTENT EXTRACTION:**
      - Extract 4-6 most important themes/takeaways
      - Represent relationships between concepts
      - Include the book title prominently
      
      **TEXT SPECIFICATIONS:**
      - LANGUAGE: Match the book language (Chinese or English)
      - Title: Large, bold, 15-20% of canvas height
      - Key points: Clear, readable, 6-10% of canvas height
      - NO pseudo-characters or gibberish text
      
      **DESIGN QUALITY:**
      - Professional, polished appearance
      - Consistent visual style throughout
      - Clear visual hierarchy
      - Balanced composition
      
      **PROHIBITED ELEMENTS:**
      - NO scene illustrations
      - NO character narratives
      - NO maps or geographical charts
      - NO realistic human faces`,
    jsonTemplate: {
      style: {
        name: "Infographic Overview (1-Pager)",
        description: "Single comprehensive infographic summarizing entire podcast content"
      },
      composition: {
        aspect_ratio: "4:3",
        framing: "Poster-style infographic with central theme and organized sections"
      },
      constraints: {
        single_image: true,
        safety: "family friendly"
      }
    }
  }
];

// Get style definition by preset ID
export const getImageStyleDefinition = (preset: ImageStylePreset): ImageStyleDefinition | undefined => {
  return IMAGE_STYLE_DEFINITIONS.find(style => style.id === preset);
};

// Get default style based on language
export const getDefaultImageStyle = (language: string): ImageStylePreset => {
  return language === 'Chinese' ? 'ink_wash' : 'zelda_botw';
};