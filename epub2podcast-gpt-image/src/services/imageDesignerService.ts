import { SourceChapter, ScriptSegment } from '../types.js';

export type ImageDensity = 'segment' | 'chapter';

export type ImageDesignStrategy =
  | 'cinematic-poster'
  | 'knowledge-comic'
  | 'infographic-spread'
  | 'documentary-still'
  | 'concept-metaphor'
  | 'quote-poster'
  | 'map-timeline'
  | 'closing-key-visual';

export interface EpisodeStyleBible {
  episodeTitle: string;
  visualThesis: string;
  globalStyle: string;
  palette: string[];
  typography: string;
  compositionRules: string[];
  avoid: string[];
}

export interface ImageDesignSpec {
  segmentIndex: number;
  segmentIndexes: number[];
  strategy: ImageDesignStrategy;
  title: string;
  subtitle: string;
  keyLine: string;
  requiredText: string[];
  visualHook: string;
  contentLogic: string;
  sceneElements: string[];
  layoutDirection: string;
  ratio: string;
  targetResolution: string;
  speaker: string;
  estimatedDuration?: number;
  sourceTextExcerpt: string;
  previousContext?: string;
  nextContext?: string;
  avoid: string[];
}

export interface DesignFramesParams {
  bookTitle: string;
  language: string;
  script: ScriptSegment[];
  chapters?: SourceChapter[];
  imageDensity?: ImageDensity;
  aspectRatio?: string;
  targetResolution?: string;
}

export interface PromptRetryContext {
  attempt?: number;
  forbiddenWrongTexts?: string[];
  previousFailureReason?: string;
}

export interface VisionQaObservation {
  requiredTextPresent: string[];
  extraText: string[];
  observedWrongTexts: string[];
  isPptLike: boolean;
  isVisuallyStriking: boolean;
  isGrounded: boolean;
  isLegible: boolean;
  notes?: string;
}

export interface ImageQaDecision {
  passed: boolean;
  reason: string;
  retryForbiddenTexts: string[];
}

const STRATEGY_ROTATION: ImageDesignStrategy[] = [
  'cinematic-poster',
  'infographic-spread',
  'knowledge-comic',
  'documentary-still',
  'concept-metaphor',
  'quote-poster',
  'map-timeline',
];

function compactWhitespace(text: string): string {
  return String(text || '').replace(/\s+/g, ' ').trim();
}

function truncate(text: string, maxChars: number): string {
  const clean = compactWhitespace(text);
  return clean.length > maxChars ? `${clean.slice(0, maxChars - 1)}…` : clean;
}

function uniqueNonEmpty(items: string[]): string[] {
  return Array.from(new Set(items.map(item => compactWhitespace(item)).filter(Boolean)));
}

function chapterHint(chapters: SourceChapter[] | undefined, segmentText: string): string | undefined {
  if (!chapters?.length) return undefined;
  const text = segmentText.toLowerCase();
  const scored = chapters.map(chapter => {
    const title = chapter.title || '';
    const titleTokens = title.split(/[\s、，,。:：·《》]+/).filter(token => token.length >= 2);
    const contentHint = truncate(chapter.content || '', 160);
    const contentTokens = contentHint.split(/[\s、，,。:：·《》]+/).filter(token => token.length >= 2).slice(0, 20);
    const score = [...titleTokens, ...contentTokens].reduce((sum, token) => sum + (text.includes(token.toLowerCase()) ? 1 : 0), 0);
    return { chapter, score };
  }).sort((a, b) => b.score - a.score);
  return scored[0]?.score ? scored[0].chapter.title : undefined;
}

function selectStrategy(segment: ScriptSegment, index: number, total: number): ImageDesignStrategy {
  const text = segment.text || '';
  if (index === total - 1 || /最后|结尾|回到全书|总结|收束/.test(text)) return 'closing-key-visual';
  if (/地图|路线|丝路|远行|贵霜|东非|城市|迁徙|网络|钱币|贸易/.test(text)) return 'map-timeline';
  if (/耳环|谈判|人物|故事|争执|身份|权力|审美/.test(text)) return 'knowledge-comic';
  if (/数据|系统|结构|比较|三层|四个|为什么|机制|技术|日历/.test(text)) return 'infographic-spread';
  if (/引用|他说|她说|一句话|关键/.test(text)) return 'quote-poster';
  if (/抽象|意义|文明|时间|记忆|观念/.test(text)) return 'concept-metaphor';
  return STRATEGY_ROTATION[index % STRATEGY_ROTATION.length];
}

function titleFor(text: string, index: number, strategy: ImageDesignStrategy): string {
  if (/钱币/.test(text)) return '一枚钱币的远行';
  if (/耳环/.test(text)) return '一只耳环的谈判';
  if (/日历|历法|时间/.test(text)) return '时间被重新计算';
  if (/贸易|丝路|网络/.test(text)) return '文明在交易中流动';
  if (/宗教|信仰|修道院/.test(text)) return '信仰沿路迁移';
  if (/技术|工艺/.test(text)) return '技术在器物中转译';
  if (strategy === 'closing-key-visual') return '文明在器物中回响';
  return `第${index + 1}幕：物的证词`;
}

function subtitleFor(text: string, strategy: ImageDesignStrategy): string {
  if (/贵霜|东非|钱币/.test(text)) return '从贵霜腹地，到东非修道院';
  if (/耳环/.test(text)) return '审美、身份与权力的小型现场';
  if (/贸易|丝路|网络/.test(text)) return '丝路不是路线，而是交换系统';
  if (/日历|历法|时间/.test(text)) return '历法背后，是权力与技术的协商';
  if (strategy === 'closing-key-visual') return '古物不是终点，而是文明互相改写的现场';
  return '一个细节，打开一段世界史';
}

function keyLineFor(text: string, strategy: ImageDesignStrategy): string {
  if (/钱币|贸易|丝路|网络/.test(text)) return '商品、技术、宗教与审美一起迁移';
  if (/耳环|身份|权力|审美/.test(text)) return '小器物里，藏着大时代的协商';
  if (/日历|历法|时间/.test(text)) return '时间制度，也是一种文明接口';
  if (strategy === 'closing-key-visual') return '看见物的流动，也看见人的选择';
  return '把抽象历史，压缩成可见画面';
}

function sceneElementsFor(text: string, strategy: ImageDesignStrategy): string[] {
  if (strategy === 'map-timeline') return ['ancient coin', 'glowing trade routes', 'city silhouettes', 'monastery', 'caravan traces'];
  if (strategy === 'knowledge-comic') return ['expressive hands', 'gold earring', 'split comic panels', 'negotiation table', 'ancient market'];
  if (strategy === 'infographic-spread') return ['diagram arrows', 'artifact close-up', 'layered data labels', 'editorial grid', 'symbolic icons'];
  if (strategy === 'closing-key-visual') return ['museum darkness', 'floating artifacts', 'golden route lines', 'human silhouettes', 'dramatic spotlight'];
  if (strategy === 'quote-poster') return ['large Chinese quote typography', 'single artifact', 'deep shadow', 'cinematic texture'];
  return ['hero artifact', 'dramatic light', 'historical texture', 'editorial typography'];
}

function visualHookFor(text: string, strategy: ImageDesignStrategy): string {
  if (strategy === 'map-timeline') return 'a glowing ancient route map where a coin travels between cities, ports, and sacred spaces';
  if (strategy === 'knowledge-comic') return 'a premium knowledge-comic page showing an artifact passing between hands as status and taste are negotiated';
  if (strategy === 'infographic-spread') return 'a dense but readable editorial infographic turning the segment logic into arrows, layers, and artifact close-ups';
  if (strategy === 'closing-key-visual') return 'a final cinematic tableau of artifacts floating like constellations over moving human silhouettes';
  if (strategy === 'concept-metaphor') return 'a symbolic editorial image where an artifact becomes a portal between civilizations';
  if (strategy === 'quote-poster') return 'a bold quote-poster with the key Chinese line integrated into dramatic artifact photography';
  return 'a cinematic editorial poster built around the segment’s central artifact and conflict';
}

function contentLogicFor(text: string): string {
  return `Visualize this segment specifically: ${truncate(text, 260)}`;
}

function groupScript(script: ScriptSegment[], imageDensity: ImageDensity): Array<{ start: number; indexes: number[]; text: string; speaker: string; estimatedDuration?: number }> {
  if (imageDensity === 'segment') {
    return script.map((seg, index) => ({
      start: index,
      indexes: [index],
      text: seg.text || '',
      speaker: seg.speaker || '',
      estimatedDuration: seg.estimatedDuration,
    }));
  }

  const groups = new Map<number, number[]>();
  for (let i = 0; i < script.length; i++) {
    const explicit = script[i].imageGroup;
    const groupId = typeof explicit === 'number' ? explicit : Math.floor(i / 3);
    const existing = groups.get(groupId) || [];
    existing.push(i);
    groups.set(groupId, existing);
  }

  return Array.from(groups.values()).map(indexes => {
    const first = script[indexes[0]];
    return {
      start: indexes[0],
      indexes,
      text: indexes.map(i => script[i].text || '').join(' '),
      speaker: first.speaker || '',
      estimatedDuration: indexes.reduce((sum, i) => sum + (script[i].estimatedDuration || 0), 0) || undefined,
    };
  });
}

export const imageDesignerService = {
  createEpisodeStyleBible(params: { bookTitle: string; language: string; chapters?: SourceChapter[]; aspectRatio?: string; targetResolution?: string }): EpisodeStyleBible {
    const chapterThemes = (params.chapters || []).slice(0, 6).map(chapter => chapter.title).filter(Boolean).join('、');
    const ratio = params.aspectRatio || '4:3';
    const targetResolution = params.targetResolution || '1440x1080';
    return {
      episodeTitle: params.bookTitle,
      visualThesis: chapterThemes ? `围绕「${chapterThemes}」展现文明如何在器物中流动` : '文明在物的流动中彼此改写',
      globalStyle: 'premium Chinese editorial documentary, cinematic realism mixed with graphic infographic design, high-impact visual storytelling',
      palette: ['warm ivory', 'deep ink black', 'aged gold', 'oxide red', 'porcelain blue'],
      typography: 'bold readable Simplified Chinese editorial typography, accurate text, strong hierarchy, safe margins',
      compositionRules: [
        `${ratio} frame, final ${targetResolution} video-safe composition`,
        'large visual hook in every frame',
        'never look like a corporate PowerPoint slide',
        'text integrated into the image as poster/editorial typography',
        'safe margins around all text',
      ],
      avoid: ['stiff PPT', 'generic flat icons', 'random English text', 'watermark', 'logo', 'small unreadable text'],
    };
  },

  designFrames(params: DesignFramesParams): ImageDesignSpec[] {
    const imageDensity = params.imageDensity || 'segment';
    const ratio = params.aspectRatio || '4:3';
    const targetResolution = params.targetResolution || '1440x1080';
    const groups = groupScript(params.script, imageDensity);

    return groups.map(group => {
      const text = compactWhitespace(group.text);
      const strategy = selectStrategy({ speaker: group.speaker as 'Male' | 'Female', text, visualPrompt: null, estimatedDuration: group.estimatedDuration }, group.start, params.script.length);
      const title = titleFor(text, group.start, strategy);
      const subtitle = subtitleFor(text, strategy);
      const keyLine = keyLineFor(text, strategy);
      const chapter = chapterHint(params.chapters, text);
      const requiredText = uniqueNonEmpty([title, subtitle, keyLine].slice(0, 4));
      return {
        segmentIndex: group.start,
        segmentIndexes: group.indexes,
        strategy,
        title,
        subtitle,
        keyLine,
        requiredText,
        visualHook: visualHookFor(text, strategy),
        contentLogic: contentLogicFor(text),
        sceneElements: sceneElementsFor(text, strategy),
        layoutDirection: `${strategy}; high-impact editorial frame; not a presentation slide`,
        ratio,
        targetResolution,
        speaker: group.speaker,
        estimatedDuration: group.estimatedDuration,
        sourceTextExcerpt: truncate(text, 520),
        previousContext: group.start > 0 ? truncate(params.script[group.start - 1]?.text || '', 160) : chapter,
        nextContext: group.start < params.script.length - 1 ? truncate(params.script[group.start + 1]?.text || '', 160) : undefined,
        avoid: ['PowerPoint look', 'generic business icons', 'random English text', 'watermark', 'logo', 'wrong Chinese characters', 'extra on-image text'],
      };
    });
  },

  buildPrompt(spec: ImageDesignSpec, bible: EpisodeStyleBible, retryContext: PromptRetryContext = {}): string {
    const attempt = retryContext.attempt || 1;
    const forbidden = uniqueNonEmpty([...(retryContext.forbiddenWrongTexts || []), ...spec.avoid.filter(item => /English|watermark|logo|PowerPoint/.test(item))]);
    const exactTextLines = spec.requiredText.map((text, idx) => `${idx + 1}. 「${text}」`).join('\n');
    const forbiddenLines = forbidden.length ? forbidden.map(text => `- 「${text}」`).join('\n') : '- any text not listed in the exact text block';
    const retryBlock = attempt > 1
      ? `\nSTRICT RETRY MODE. Previous failure: ${retryContext.previousFailureReason || 'image QA failed'}. Use fewer decorative labels and obey the exact text block literally.\n`
      : '';

    return `Create a complete high-impact ${spec.ratio} editorial podcast visual page, final target ${spec.targetResolution}.${retryBlock}

This image is NOT a PowerPoint slide. It should look like a cinematic magazine poster, knowledge comic, premium infographic, documentary editorial image, or concept poster.

Episode: ${bible.episodeTitle}
Visual thesis: ${bible.visualThesis}
Global style: ${bible.globalStyle}
Palette: ${bible.palette.join(', ')}
Typography: ${bible.typography}

This frame MUST be grounded in this exact podcast segment:
Segment index: ${spec.segmentIndex}
Speaker: ${spec.speaker}
Estimated duration: ${spec.estimatedDuration || 'unknown'} seconds
Segment excerpt: ${spec.sourceTextExcerpt}
Previous context: ${spec.previousContext || 'none'}
Next context: ${spec.nextContext || 'none'}

Visual strategy: ${spec.strategy}
Visual hook: ${spec.visualHook}
Content logic: ${spec.contentLogic}
Scene elements: ${spec.sceneElements.join(', ')}
Layout direction: ${spec.layoutDirection}

Include ONLY these exact Simplified Chinese texts, clearly readable and correctly written:
${exactTextLines}

Do NOT write these incorrect or unwanted texts:
${forbiddenLines}

Typography requirements:
- Chinese text must be accurate, legible, and not misspelled.
- No extra words, no random English, no watermark, no logo.
- Strong hierarchy: title large, subtitle medium, key line smaller but readable.
- Text should be integrated into the poster/comic/infographic composition, not pasted as plain PPT boxes.
- Keep safe margins for all text.

Composition rules:
${bible.compositionRules.map(rule => `- ${rule}`).join('\n')}

Avoid:
${uniqueNonEmpty([...bible.avoid, ...spec.avoid]).map(rule => `- ${rule}`).join('\n')}`;
  },

  evaluateTextQa(spec: ImageDesignSpec, observation: VisionQaObservation): ImageQaDecision {
    const present = new Set(observation.requiredTextPresent.map(compactWhitespace));
    const missing = spec.requiredText.filter(text => !present.has(compactWhitespace(text)));
    const retryForbiddenTexts = uniqueNonEmpty([...observation.observedWrongTexts, ...observation.extraText]);
    const failures: string[] = [];

    if (missing.length) failures.push(`missing required text: ${missing.join(' / ')}`);
    if (observation.extraText.length) failures.push(`extra text detected: ${observation.extraText.join(' / ')}`);
    if (observation.observedWrongTexts.length) failures.push(`wrong text detected: ${observation.observedWrongTexts.join(' / ')}`);
    if (observation.isPptLike) failures.push('image looks like a PowerPoint slide');
    if (!observation.isVisuallyStriking) failures.push('visual impact is weak');
    if (!observation.isGrounded) failures.push('image is not grounded in the segment');
    if (!observation.isLegible) failures.push('text is not legible');

    return {
      passed: failures.length === 0,
      reason: failures.length ? failures.join('; ') : 'passed',
      retryForbiddenTexts,
    };
  },
};
