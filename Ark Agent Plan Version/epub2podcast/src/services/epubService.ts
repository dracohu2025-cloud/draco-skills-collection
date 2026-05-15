import JSZip from 'jszip';
import { DOMParser } from '@xmldom/xmldom';

// ============================================================
// Types
// ============================================================

export interface EpubChapter {
    title: string;
    content: string;
    order: number;
    href?: string;
}

export interface EpubStructure {
    title: string;
    author?: string;
    language?: string;
    chapters: EpubChapter[];
    totalWordCount: number;
    /** Legacy: full text for backward compatibility */
    fullText: string;
    /** Book cover image as Base64 data URL (e.g., data:image/jpeg;base64,...) */
    coverImageBase64?: string;
}

// ============================================================
// Helper Functions
// ============================================================

function resolvePath(base: string, relative: string): string {
    if (relative.startsWith('/')) return relative.substring(1);
    // Remove query string and fragment
    relative = relative.split('#')[0].split('?')[0];
    const stack = base === '' ? [] : base.split('/').filter(x => x);
    const parts = relative.split('/');
    for (const part of parts) {
        if (part === '.') continue;
        if (part === '..') stack.pop();
        else stack.push(part);
    }
    return stack.join('/');
}

function extractTextFromHtml(parser: DOMParser, htmlContent: string): string {
    try {
        const doc = parser.parseFromString(htmlContent, "text/html");
        const text = doc.documentElement?.textContent || "";
        return text.trim();
    } catch (e) {
        return "";
    }
}

function countWords(text: string): number {
    // For Chinese: count characters; for English: count words
    const chineseChars = (text.match(/[\u4e00-\u9fff]/g) || []).length;
    const englishWords = text.replace(/[\u4e00-\u9fff]/g, ' ').split(/\s+/).filter(w => w.length > 0).length;
    return chineseChars + englishWords;
}

function getLocalName(node: any): string {
    const tag = String(node?.tagName || node?.nodeName || '');
    return tag.includes(':') ? tag.split(':').pop() || tag : tag;
}

function getElementsByLocalName(root: any, localName: string): any[] {
    const results: any[] = [];
    const all = root?.getElementsByTagName?.('*') || [];
    for (let i = 0; i < all.length; i++) {
        const node = all[i];
        if (getLocalName(node) === localName) results.push(node);
    }
    return results;
}

function getFirstByLocalName(root: any, localName: string): any | undefined {
    return getElementsByLocalName(root, localName)[0];
}

// ============================================================
// EPUB Service
// ============================================================

export const epubService = {
    /**
     * Parse EPUB and extract structured information
     * This is the new enhanced method with TOC and chapter extraction
     */
    async parseEpubStructured(buffer: Buffer): Promise<EpubStructure> {
        const zip = new JSZip();
        const content = await zip.loadAsync(buffer);
        const parser = new DOMParser();

        const getFileContent = async (path: string): Promise<string | null> => {
            let f = content.file(path);
            if (!f) f = content.file(decodeURIComponent(path));
            if (!f) {
                const lower = path.toLowerCase();
                const match = Object.keys(content.files).find(k => k.toLowerCase() === lower);
                if (match) f = content.file(match);
            }
            return f ? await f.async("text") : null;
        };

        // 1. Locate OPF
        const container = await getFileContent("META-INF/container.xml");
        if (!container) throw new Error("Invalid EPUB: META-INF/container.xml missing");

        const containerDoc = parser.parseFromString(container, "application/xml");
        const rootFile = containerDoc.getElementsByTagName("rootfile")[0];
        const opfPath = rootFile?.getAttribute("full-path");
        if (!opfPath) throw new Error("Invalid EPUB: No rootfile found");

        // 2. Parse OPF
        const opfContent = await getFileContent(opfPath);
        if (!opfContent) throw new Error(`Invalid EPUB: OPF file not found at ${opfPath}`);

        const opfDoc = parser.parseFromString(opfContent, "application/xml");
        const opfDir = opfPath.substring(0, opfPath.lastIndexOf('/') + 1);

        // 3. Extract Metadata (namespace-safe)
        const metadata = getFirstByLocalName(opfDoc, "metadata");
        let title = "Unknown Book";
        let author: string | undefined;
        let language: string | undefined;

        if (metadata) {
            const titleElem = metadata.getElementsByTagName("dc:title")[0] || getFirstByLocalName(metadata, "title");
            if (titleElem?.textContent) {
                title = titleElem.textContent
                    .replace(/\.(epub|mobi|pdf|txt)$/i, '')
                    .replace(/_/g, ' ')
                    .replace(/^\d+[\s_]+/, '')
                    .replace(/\(z-lib\.org\)/i, '')
                    .trim();
            }

            const authorElem = metadata.getElementsByTagName("dc:creator")[0] || getFirstByLocalName(metadata, "creator");
            if (authorElem?.textContent) {
                author = authorElem.textContent.trim();
            }

            const langElem = metadata.getElementsByTagName("dc:language")[0] || getFirstByLocalName(metadata, "language");
            if (langElem?.textContent) {
                language = langElem.textContent.trim();
            }
        }

        // 4. Build manifest map + detect cover image (namespace-safe)
        const manifestItems = getElementsByLocalName(opfDoc, "item");
        const manifest: Record<string, { href: string; mediaType: string; properties?: string }> = {};

        let tocNcxId: string | null = null;
        let navHref: string | null = null;
        let coverImageId: string | null = null;

        // Helper to get binary file content
        const getFileContentBinary = async (path: string): Promise<Buffer | null> => {
            let f = content.file(path);
            if (!f) f = content.file(decodeURIComponent(path));
            if (!f) {
                const lower = path.toLowerCase();
                const match = Object.keys(content.files).find(k => k.toLowerCase() === lower);
                if (match) f = content.file(match);
            }
            return f ? await f.async("nodebuffer") : null;
        };

        manifestItems.forEach(item => {
            const id = item.getAttribute("id");
            const href = item.getAttribute("href");
            const mediaType = item.getAttribute("media-type") || "";
            const properties = item.getAttribute("properties") || "";

            if (id && href) {
                manifest[id] = { href, mediaType, properties };

                // Detect TOC
                if (mediaType === "application/x-dtbncx+xml") {
                    tocNcxId = id;
                }
                if (properties.includes("nav")) {
                    navHref = href;
                }
                // Detect cover image (EPUB 3 standard: properties="cover-image")
                if (properties.includes("cover-image")) {
                    coverImageId = id;
                    console.log(`[EpubService] Found cover by properties: ${id}`);
                }
            }
        });

        // Fallback cover detection: look for id/href containing "cover"
        if (!coverImageId) {
            for (const [id, item] of Object.entries(manifest)) {
                if (item.mediaType.startsWith("image/")) {
                    const idLower = id.toLowerCase();
                    const hrefLower = item.href.toLowerCase();
                    if (idLower.includes("cover") || hrefLower.includes("cover")) {
                        coverImageId = id;
                        console.log(`[EpubService] Found cover by name pattern: ${id} -> ${item.href}`);
                        break;
                    }
                }
            }
        }

        // Last fallback: use first image in manifest
        if (!coverImageId) {
            for (const [id, item] of Object.entries(manifest)) {
                if (item.mediaType.startsWith("image/") &&
                    (item.mediaType.includes("jpeg") || item.mediaType.includes("png") || item.mediaType.includes("jpg"))) {
                    coverImageId = id;
                    console.log(`[EpubService] Using first image as cover: ${id} -> ${item.href}`);
                    break;
                }
            }
        }

        // Extract cover image as Base64
        let coverImageBase64: string | undefined;
        if (coverImageId && manifest[coverImageId]) {
            try {
                const coverPath = resolvePath(opfDir, manifest[coverImageId].href);
                const coverBuffer = await getFileContentBinary(coverPath);
                if (coverBuffer && coverBuffer.length > 0) {
                    const mediaType = manifest[coverImageId].mediaType;
                    coverImageBase64 = `data:${mediaType};base64,${coverBuffer.toString('base64')}`;
                    console.log(`[EpubService] Cover extracted: ${coverPath} (${Math.round(coverBuffer.length / 1024)}KB)`);
                }
            } catch (e) {
                console.warn(`[EpubService] Failed to extract cover image:`, e);
            }
        }


        // 5. Extract TOC (try nav.xhtml first, then toc.ncx)
        let tocEntries: Array<{ title: string; href: string }> = [];

        // Try EPUB 3 nav.xhtml
        if (navHref) {
            const navPath = resolvePath(opfDir, navHref);
            const navContent = await getFileContent(navPath);
            if (navContent) {
                tocEntries = this.parseNavXhtml(parser, navContent);
                console.log(`[EpubService] Parsed nav.xhtml: ${tocEntries.length} entries`);
            }
        }

        // Fallback to EPUB 2 toc.ncx
        if (tocEntries.length === 0 && tocNcxId && manifest[tocNcxId]) {
            const ncxPath = resolvePath(opfDir, manifest[tocNcxId].href);
            const ncxContent = await getFileContent(ncxPath);
            if (ncxContent) {
                tocEntries = this.parseTocNcx(parser, ncxContent);
                console.log(`[EpubService] Parsed toc.ncx: ${tocEntries.length} entries`);
            }
        }

        // 6. Extract chapters based on TOC or spine
        const chapters: EpubChapter[] = [];
        const spineItems = getElementsByLocalName(opfDoc, "itemref");

        if (tocEntries.length > 0) {
            // Use TOC to create chapters
            for (let i = 0; i < tocEntries.length; i++) {
                const entry = tocEntries[i];
                const chapterPath = resolvePath(opfDir, entry.href.split('#')[0]);
                const htmlContent = await getFileContent(chapterPath);

                if (htmlContent) {
                    const text = extractTextFromHtml(parser, htmlContent);
                    if (text.length > 50) { // Skip very short chapters
                        chapters.push({
                            title: entry.title,
                            content: text,
                            order: i + 1,
                            href: entry.href
                        });
                    }
                }
            }
        }

        // Fallback: Use spine if no TOC
        if (chapters.length === 0) {
            console.log(`[EpubService] No TOC found, using spine order`);
            let order = 1;
            for (const item of spineItems) {
                const idref = item.getAttribute("idref");
                if (!idref || !manifest[idref]) continue;

                const href = manifest[idref].href;
                const absolutePath = resolvePath(opfDir, href);
                const htmlContent = await getFileContent(absolutePath);

                if (htmlContent) {
                    const text = extractTextFromHtml(parser, htmlContent);
                    if (text.length > 100) {
                        chapters.push({
                            title: `Section ${order}`,
                            content: text,
                            order: order,
                            href: href
                        });
                        order++;
                    }
                }
            }
        }

        // 7. Build full text (for backward compatibility)
        const fullText = chapters.map(ch => ch.content).join('\n\n');
        const totalWordCount = countWords(fullText);

        console.log(`[EpubService] Parsed: "${title}" by ${author || 'Unknown'}`);
        console.log(`[EpubService] Chapters: ${chapters.length}, Words: ${totalWordCount}`);

        // Limit text size
        const CHAR_LIMIT = 3000000;
        const limitedFullText = fullText.length > CHAR_LIMIT ? fullText.slice(0, CHAR_LIMIT) : fullText;

        return {
            title,
            author,
            language,
            chapters,
            totalWordCount,
            fullText: limitedFullText,
            coverImageBase64
        };
    },

    /**
     * Parse EPUB 3 nav.xhtml
     */
    parseNavXhtml(parser: DOMParser, content: string): Array<{ title: string; href: string }> {
        const entries: Array<{ title: string; href: string }> = [];
        try {
            const doc = parser.parseFromString(content, "application/xhtml+xml");
            const navElements = doc.getElementsByTagName("nav");

            for (let i = 0; i < navElements.length; i++) {
                const nav = navElements[i];
                const type = nav.getAttribute("epub:type") || nav.getAttribute("type");

                if (type === "toc" || !type) {
                    const links = nav.getElementsByTagName("a");
                    for (let j = 0; j < links.length; j++) {
                        const link = links[j];
                        const href = link.getAttribute("href");
                        const title = link.textContent?.trim();

                        if (href && title) {
                            entries.push({ title, href });
                        }
                    }
                    if (entries.length > 0) break;
                }
            }
        } catch (e) {
            console.warn("[EpubService] Failed to parse nav.xhtml:", e);
        }
        return entries;
    },

    /**
     * Parse EPUB 2 toc.ncx
     */
    parseTocNcx(parser: DOMParser, content: string): Array<{ title: string; href: string }> {
        const entries: Array<{ title: string; href: string }> = [];
        try {
            const doc = parser.parseFromString(content, "application/xml");
            const navPoints = doc.getElementsByTagName("navPoint");

            for (let i = 0; i < navPoints.length; i++) {
                const navPoint = navPoints[i];
                const textElem = navPoint.getElementsByTagName("text")[0];
                const contentElem = navPoint.getElementsByTagName("content")[0];

                if (textElem && contentElem) {
                    const title = textElem.textContent?.trim();
                    const href = contentElem.getAttribute("src");

                    if (title && href) {
                        entries.push({ title, href });
                    }
                }
            }
        } catch (e) {
            console.warn("[EpubService] Failed to parse toc.ncx:", e);
        }
        return entries;
    },

    /**
     * Legacy method for backward compatibility
     * @deprecated Use parseEpubStructured instead
     */
    async parseEpub(buffer: Buffer): Promise<{ title: string, text: string }> {
        const result = await this.parseEpubStructured(buffer);
        return {
            title: result.title,
            text: result.fullText
        };
    }
};
