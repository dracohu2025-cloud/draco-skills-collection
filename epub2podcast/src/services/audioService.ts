import ffmpeg from 'fluent-ffmpeg';
import fs from 'fs';
import path from 'path';
import os from 'os';
import { v4 as uuidv4 } from 'uuid';
import { execSync } from 'child_process';
import { SAMPLE_RATE } from '../constants.js';

// Auto-detect ffmpeg/ffprobe paths based on platform
function getFfmpegPath(): string {
    // Check common paths in order of preference
    const possiblePaths = [
        '/usr/bin/ffmpeg',           // Linux standard
        '/usr/local/bin/ffmpeg',     // Linux/macOS manual install
        '/opt/homebrew/bin/ffmpeg',  // macOS Homebrew (Apple Silicon)
        '/usr/local/opt/ffmpeg/bin/ffmpeg', // macOS Homebrew (Intel)
    ];

    for (const p of possiblePaths) {
        if (fs.existsSync(p)) {
            return p;
        }
    }

    // Fallback: try to find via which command
    try {
        const result = execSync('which ffmpeg', { encoding: 'utf-8' }).trim();
        if (result) return result;
    } catch {
        // Ignore errors
    }

    // Last resort: assume it's in PATH
    return 'ffmpeg';
}

function getFfprobePath(): string {
    // Check common paths in order of preference
    const possiblePaths = [
        '/usr/bin/ffprobe',           // Linux standard
        '/usr/local/bin/ffprobe',     // Linux/macOS manual install
        '/opt/homebrew/bin/ffprobe',  // macOS Homebrew (Apple Silicon)
        '/usr/local/opt/ffmpeg/bin/ffprobe', // macOS Homebrew (Intel)
    ];

    for (const p of possiblePaths) {
        if (fs.existsSync(p)) {
            return p;
        }
    }

    // Fallback: try to find via which command
    try {
        const result = execSync('which ffprobe', { encoding: 'utf-8' }).trim();
        if (result) return result;
    } catch {
        // Ignore errors
    }

    // Last resort: assume it's in PATH
    return 'ffprobe';
}

// Configure ffmpeg paths (auto-detect based on platform)
const ffmpegPath = getFfmpegPath();
const ffprobePath = getFfprobePath();
console.log(`[AudioService] Using ffmpeg: ${ffmpegPath}`);
console.log(`[AudioService] Using ffprobe: ${ffprobePath}`);
ffmpeg.setFfmpegPath(ffmpegPath);
ffmpeg.setFfprobePath(ffprobePath);

export const audioService = {
    /**
     * Get accurate audio duration using FFprobe
     */
    async getAudioDuration(buffer: Buffer): Promise<number> {
        const tempDir = os.tmpdir();
        const tempFilePath = path.join(tempDir, `${uuidv4()}_probe.mp3`);

        try {
            // Write buffer to temp file
            fs.writeFileSync(tempFilePath, buffer);

            return await new Promise<number>((resolve, reject) => {
                ffmpeg.ffprobe(tempFilePath, (err, metadata) => {
                    if (err) {
                        console.warn('[AudioService] FFprobe failed, attempting fallback duration calculation:', err.message);

                        // Fallback: Estimate from file size and bitrate
                        try {
                            const stats = fs.statSync(tempFilePath);
                            const fileSize = stats.size;
                            const buffer = fs.readFileSync(tempFilePath);

                            // Check for MP3 Sync Word (FFE0-FFFF)
                            // We look for the first frame header
                            // Header is 4 bytes: AAAAAAAA AAABBCCD EEEEFFGH IIJJKLMM
                            // Sync: 11 bits set (FFE0)

                            if (buffer.length > 4 && buffer[0] === 0xFF && (buffer[1] & 0xE0) === 0xE0) {
                                // Parse Bitrate (EEEE)
                                const version = (buffer[1] >> 3) & 0x03; // 10=MPEG2, 11=MPEG1
                                const layer = (buffer[1] >> 1) & 0x03;   // 01=Layer3
                                const bitrateIdx = (buffer[2] >> 4) & 0x0F;

                                let bitrate = 0;
                                // MPEG-2 Layer III Bitrates (kbps)
                                const mpeg2L3Bitrates = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0];
                                // MPEG-1 Layer III Bitrates (kbps)
                                const mpeg1L3Bitrates = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0];

                                if (version === 2 && layer === 1) { // MPEG-2 Layer III
                                    bitrate = mpeg2L3Bitrates[bitrateIdx] * 1000;
                                } else if (version === 3 && layer === 1) { // MPEG-1 Layer III
                                    bitrate = mpeg1L3Bitrates[bitrateIdx] * 1000;
                                }

                                if (bitrate > 0) {
                                    const duration = (fileSize * 8) / bitrate;
                                    console.log(`[AudioService] Fallback duration calculated: ${duration}s (Bitrate: ${bitrate})`);
                                    resolve(duration);
                                    return;
                                }
                            }

                            // If we can't parse MP3 header, use simple estimation
                            const simpleEstimate = fileSize / 16000; // 128kbps assumption
                            console.warn(`[AudioService] Using simple estimation: ${simpleEstimate.toFixed(3)}s`);
                            resolve(simpleEstimate);
                        } catch (fallbackErr) {
                            console.error('[AudioService] Fallback calculation failed:', fallbackErr);
                            // Last resort: use simple file size estimation
                            const lastResort = buffer.length / 16000;
                            console.warn(`[AudioService] Last resort estimation: ${lastResort.toFixed(3)}s`);
                            resolve(lastResort);
                        }
                        return;
                    }

                    const duration = metadata.format.duration;
                    if (typeof duration === 'number' && duration > 0) {
                        resolve(duration);
                    } else {
                        reject(new Error('Invalid duration from FFprobe'));
                    }
                });
            });
        } finally {
            // Cleanup temp file
            try {
                if (fs.existsSync(tempFilePath)) {
                    fs.unlinkSync(tempFilePath);
                }
            } catch (e) {
                console.warn('[AudioService] Failed to cleanup temp file:', e);
            }
        }
    },

    async mergeAudio(buffers: Buffer[]): Promise<Buffer> {
        if (buffers.length === 0) return Buffer.alloc(0);

        const tempDir = os.tmpdir();
        const filePaths: string[] = [];
        const outputFilePath = path.join(tempDir, `${uuidv4()}_output.mp3`);

        try {
            // 1. Write buffers to temp files and re-encode to ensure valid format
            for (let i = 0; i < buffers.length; i++) {
                const buffer = buffers[i];
                const rawFilePath = path.join(tempDir, `${uuidv4()}_raw.mp3`);
                const encodedFilePath = path.join(tempDir, `${uuidv4()}.mp3`);

                try {
                    // Write raw buffer
                    fs.writeFileSync(rawFilePath, buffer);

                    // Re-encode with FFmpeg to fix format issues
                    await new Promise<void>((resolve, reject) => {
                        ffmpeg(rawFilePath)
                            .audioCodec('libmp3lame')
                            .audioBitrate('192k')
                            .audioChannels(1)
                            .audioFrequency(SAMPLE_RATE)
                            .on('error', (err) => {
                                console.warn(`[AudioService] Failed to re-encode segment ${i}, using original: ${err.message}`);
                                // If re-encoding fails, use original buffer
                                fs.writeFileSync(encodedFilePath, buffer);
                                resolve();
                            })
                            .on('end', () => {
                                console.log(`[AudioService] Re-encoded segment ${i}`);
                                resolve();
                            })
                            .save(encodedFilePath);
                    });

                    filePaths.push(encodedFilePath);

                    // Clean up raw file
                    if (fs.existsSync(rawFilePath)) fs.unlinkSync(rawFilePath);

                } catch (e) {
                    console.warn(`[AudioService] Error processing segment ${i}, skipping: ${e}`);
                    // Clean up
                    if (fs.existsSync(rawFilePath)) fs.unlinkSync(rawFilePath);
                    if (fs.existsSync(encodedFilePath)) fs.unlinkSync(encodedFilePath);
                }
            }

            // 2. Use FFmpeg to concat
            await new Promise<void>((resolve, reject) => {
                const command = ffmpeg();

                filePaths.forEach(fp => {
                    command.input(fp);
                });

                command
                    .on('error', (err) => {
                        console.error('[AudioService] FFmpeg error:', err);
                        reject(err);
                    })
                    .on('end', () => {
                        console.log('[AudioService] Merging finished');
                        resolve();
                    })
                    .mergeToFile(outputFilePath, tempDir);
            });

            // 3. Read output
            const mergedBuffer = fs.readFileSync(outputFilePath);
            return mergedBuffer;

        } catch (error) {
            console.error('[AudioService] Merge failed:', error);
            throw error;
        } finally {
            // 4. Cleanup
            try {
                filePaths.forEach(fp => {
                    if (fs.existsSync(fp)) fs.unlinkSync(fp);
                });
                if (fs.existsSync(outputFilePath)) fs.unlinkSync(outputFilePath);
            } catch (cleanupError) {
                console.warn('[AudioService] Cleanup warning:', cleanupError);
            }
        }
    },

    /**
     * Repair audio buffer by re-encoding it.
     * Useful when FFprobe fails to read the file header.
     */
    async repairAudio(buffer: Buffer): Promise<Buffer> {
        const tempDir = os.tmpdir();
        const inputPath = path.join(tempDir, `${uuidv4()}_bad.mp3`);
        const outputPath = path.join(tempDir, `${uuidv4()}_fixed.mp3`);

        try {
            fs.writeFileSync(inputPath, buffer);

            await new Promise<void>((resolve, reject) => {
                ffmpeg(inputPath)
                    .outputOptions('-c:a libmp3lame') // Re-encode to standard MP3
                    .save(outputPath)
                    .on('end', () => resolve())
                    .on('error', (err) => {
                        console.error('[AudioService] Repair failed:', err);
                        reject(err);
                    });
            });

            return fs.readFileSync(outputPath);
        } finally {
            try {
                if (fs.existsSync(inputPath)) fs.unlinkSync(inputPath);
                if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath);
            } catch (e) {
                console.warn('[AudioService] Failed to cleanup temp repair files:', e);
            }
        }
    }
};
