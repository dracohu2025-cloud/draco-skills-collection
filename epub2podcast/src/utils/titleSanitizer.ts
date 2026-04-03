// Utilities for cleaning noisy book titles (e.g. filenames, mirrors, tracking tags)
// before feeding them into LLM/image prompts.

const NOISE_KEYWORDS = [
    'z-library',
    'zlibrary',
    'z-lib',
    '1lib',
    'libgen',
    'annas-archive',
];

function hasNoise(s: string): boolean {
    const lower = s.toLowerCase();
    if (NOISE_KEYWORDS.some(k => lower.includes(k))) return true;
    if (lower.includes('http://') || lower.includes('https://')) return true;
    // Common mirror/source domains
    if (/\b[a-z0-9.-]+\.(sk|rs|is|io|org|net|com)\b/i.test(s)) return true;
    return false;
}

function stripUrls(s: string): string {
    return s.replace(/https?:\/\/\S+/gi, '');
}

// Remove bracket/parenthesis segments that likely represent sources/credits.
function stripNoisyBrackets(s: string): string {
    const patterns = [
        // (...) or （...）
        /[（(][^（）()]*[)）]/g,
        // [...] or 【...】
        /\[[^\]]*\]/g,
        /【[^】]*】/g,
    ];

    let out = s;
    for (const re of patterns) {
        out = out.replace(re, (m) => {
            const inner = m.slice(1, -1);
            // Keep short, meaningful qualifiers like "(第2版)" / "(修订版)"
            // Drop if it looks like author list, source, or long metadata.
            const looksLikeAuthorList = /[,，]/.test(inner) || /[A-Za-z]/.test(inner);
            const tooLong = inner.trim().length > 10;
            if (hasNoise(inner) || looksLikeAuthorList || tooLong) return '';
            return m; // keep
        });
    }
    return out;
}

export function sanitizeBookTitleForPrompt(title: string): string {
    if (!title) return '';
    let t = title.trim();

    // Strip obvious URLs first.
    t = stripUrls(t);

    // Strip noisy bracket segments (sources, authors, mirrors).
    t = stripNoisyBrackets(t);

    // Remove remaining noise keywords anywhere in the string.
    for (const k of NOISE_KEYWORDS) {
        const re = new RegExp(k.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&'), 'ig');
        t = t.replace(re, '');
    }

    // Drop leftover mirror-like domain tokens.
    t = t.replace(/\b[a-z0-9.-]+\.(sk|rs|is|io|org|net|com)\b/gi, '');

    // Drop common ebook extensions.
    t = t.replace(/\.(epub|pdf|mobi|azw3)\b/ig, '');

    // Normalize whitespace/punctuation.
    t = t.replace(/[|]+/g, ' ');
    t = t.replace(/\s{2,}/g, ' ').trim();
    t = t.replace(/[（(]\s*[)）]/g, '').trim();

    return t;
}

