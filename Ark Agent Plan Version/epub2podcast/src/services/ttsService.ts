import { GoogleGenAI, Modality } from '@google/genai';
import { ELEVENLABS_CONFIG, MINIMAX_CONFIG, DEFAULT_TTS_PROVIDER, TTSProviderType, TTS_MODEL, SAMPLE_RATE } from '../constants.js';
import dotenv from 'dotenv';

dotenv.config();

const GEMINI_API_KEY = process.env.GEMINI_API_KEY || '';

export const ttsService = {
    async synthesizeSegment(text: string, speaker: 'Male' | 'Female', provider: TTSProviderType = DEFAULT_TTS_PROVIDER): Promise<{ buffer: Buffer, charCount: number }> {
        console.log(`[TTSService] Synthesizing segment for ${speaker} using ${provider}...`);

        // Ark Agent Plan 专用：优先使用原生火山引擎 TTS 工具
        // 与 Seedream/Seedance 共享技术栈，无需额外 API Key
        if (provider === 'volcengine' || process.env.AGENT_PLAN_NATIVE_TTS === 'true') {
            console.log('[TTSService] Using Ark Agent Plan native Volcengine TTS...');
            try {
                return { buffer: await this.synthesizeVolcengineNative(text, speaker), charCount: text.length };
            } catch (error) {
                console.warn('[TTSService] Native TTS failed, falling back to direct API call:', error);
                return { buffer: await this.synthesizeVolcengine(text, speaker), charCount: text.length };
            }
        }

        try {
            switch (provider) {
                case 'elevenlabs':
                    return { buffer: await this.synthesizeElevenLabs(text, speaker), charCount: text.length };
                case 'minimax':
                    return { buffer: await this.synthesizeMinimax(text, speaker), charCount: text.length };
                case 'volcengine':
                    return { buffer: await this.synthesizeVolcengine(text, speaker), charCount: text.length };
                case 'google':
                    return { buffer: await this.synthesizeGemini(text, speaker), charCount: text.length };
                default:
                    console.warn(`[TTSService] Unknown provider '${provider}'. Falling back to Volcengine.`);
                    return { buffer: await this.synthesizeVolcengine(text, speaker), charCount: text.length };
            }
        } catch (error) {
            console.error(`[TTSService] Provider ${provider} failed:`, error);
            // Fallback to Volcengine for Ark Agent Plan
            if (provider !== 'volcengine') {
                console.log("[TTSService] Falling back to Volcengine TTS...");
                return { buffer: await this.synthesizeVolcengine(text, speaker), charCount: text.length };
            }
            throw error;
        }
    },

    async synthesizeElevenLabs(text: string, speaker: 'Male' | 'Female'): Promise<Buffer> {
        const voiceId = speaker === 'Female' ? ELEVENLABS_CONFIG.voiceIdFemale : ELEVENLABS_CONFIG.voiceIdMale;
        const apiKey = ELEVENLABS_CONFIG.apiKey;

        if (!apiKey || !voiceId) throw new Error("ElevenLabs API Key or Voice ID is missing");

        const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'xi-api-key': apiKey
            },
            body: JSON.stringify({
                text,
                model_id: "eleven_v3", // Use v3 as requested
                voice_settings: { stability: 0.5, similarity_boost: 0.75 }
            }),
            signal: AbortSignal.timeout(120000) // 120s timeout
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`ElevenLabs API Error: ${response.status} - ${errorText}`);
        }

        const arrayBuffer = await response.arrayBuffer();
        return Buffer.from(arrayBuffer);
    },

    async synthesizeMinimax(text: string, speaker: 'Male' | 'Female'): Promise<Buffer> {
        const bearerToken = MINIMAX_CONFIG.bearerToken;
        const voiceId = speaker === 'Male' ? MINIMAX_CONFIG.voiceIdMale : MINIMAX_CONFIG.voiceIdFemale;

        if (!bearerToken) throw new Error("Minimax Bearer Token is missing");

        const url = 'https://api.minimaxi.com/v1/t2a_v2';

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${bearerToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: MINIMAX_CONFIG.modelId,
                text,
                stream: false,
                voice_setting: {
                    voice_id: voiceId,
                    speed: 1.0,
                    vol: 1.0,
                    pitch: 0
                },
                audio_setting: {
                    sample_rate: 32000,
                    bitrate: 128000,
                    format: "mp3",
                    channel: 1
                },
                subtitle_enable: false
            }),
            signal: AbortSignal.timeout(120000) // 120s timeout
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Minimax API Error: ${response.status} - ${errorText}`);
        }

        const data = await response.json() as any;
        if (data.base_resp && data.base_resp.status_code !== 0) {
            throw new Error(`Minimax API Error: ${data.base_resp.status_msg}`);
        }

        const audioDataStr = data.data?.audio;
        if (!audioDataStr) throw new Error("No audio data received from Minimax");

        // Handle Hex or Base64
        if (/^[0-9A-Fa-f]+$/.test(audioDataStr)) {
            return Buffer.from(audioDataStr, 'hex');
        } else {
            return Buffer.from(audioDataStr, 'base64');
        }
    },

    async synthesizeGemini(text: string, speaker: 'Male' | 'Female'): Promise<Buffer> {
        if (!GEMINI_API_KEY) throw new Error("GEMINI_API_KEY is missing");

        const ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });
        const voiceName = speaker === 'Male' ? 'Puck' : 'Aoede';

        const timeoutPromise = new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error("Gemini TTS timed out after 60s")), 60000)
        );

        const response = await Promise.race([
            ai.models.generateContent({
                model: TTS_MODEL,
                contents: [{ parts: [{ text }] }],
                config: {
                    responseModalities: [Modality.AUDIO],
                    speechConfig: {
                        voiceConfig: { prebuiltVoiceConfig: { voiceName } }
                    }
                }
            }),
            timeoutPromise
        ]);

        const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
        if (!base64Audio) throw new Error("Gemini TTS returned empty data");

        return Buffer.from(base64Audio, 'base64');
    },

    // Ark Agent Plan 专用：使用原生火山引擎 TTS 工具调用
    // 与 Seedream/Seedance 共享认证体系，无需单独配置 API Key
    async synthesizeVolcengineNative(text: string, speaker: 'Male' | 'Female'): Promise<Buffer> {
        const { VOLCENGINE_CONFIG } = await import('../constants.js');
        const voiceId = speaker === 'Male' ? VOLCENGINE_CONFIG.voiceIdMale : VOLCENGINE_CONFIG.voiceIdFemale;
        
        console.log(`[Volcengine TTS Native] Using voice: ${voiceId}`);
        
        // 方式1：通过 Agent Plan 原生工具调用
        // 实际调用由 Agent 运行时处理，这里返回占位符
        // 完整实现需要集成到 OpenClaw 工具调用框架
        throw new Error(
            "Native Volcengine TTS requires Agent Plan tool integration. " +
            "Please ensure the 'byted-volcengine-tts' tool is available in your Agent Plan. " +
            "Falling back to direct API call..."
        );
    },

    async synthesizeVolcengine(text: string, speaker: 'Male' | 'Female'): Promise<Buffer> {
        const { VOLCENGINE_CONFIG } = await import('../constants.js'); // Import here to avoid circular dep if any
        const accessToken = VOLCENGINE_CONFIG.accessToken;
        const appId = VOLCENGINE_CONFIG.appId;
        const voiceId = speaker === 'Male' ? VOLCENGINE_CONFIG.voiceIdMale : VOLCENGINE_CONFIG.voiceIdFemale;

        if (!accessToken || !appId) {
            throw new Error(
                "Volcengine Access Token or App ID is missing. " +
                "Please configure VOLCENGINE_ACCESS_TOKEN and VOLCENGINE_TTS_APP_ID environment variables. " +
                "These are shared with your Seedream/Seedance credentials in Ark Agent Plan."
            );
        }

        const url = 'https://openspeech.bytedance.com/api/v1/tts';
        const reqId = crypto.randomUUID();

        const payload = {
            app: { appid: appId, token: accessToken, cluster: 'volcano_tts' },
            user: { uid: 'user_1' },
            audio: {
                voice_type: voiceId,
                encoding: 'mp3',
                speed_ratio: 1.0,
                volume_ratio: 1.0,
                pitch_ratio: 1.0,
                sample_rate: SAMPLE_RATE
            },
            request: {
                reqid: reqId,
                text: text,
                operation: 'query',
                with_frontend: 1,
                frontend_type: 'unitTson',
                // resource_id should be in request, not audio!
                ...(VOLCENGINE_CONFIG.resourceId ? { resource_id: VOLCENGINE_CONFIG.resourceId } : {})
            }
        };

        console.log('[Volcengine TTS] Request payload:', JSON.stringify(payload, null, 2));

        console.log('[Volcengine TTS] Request payload:', JSON.stringify(payload, null, 2));

        // Retry logic for 504/502 errors
        let retries = 3;
        let lastError: any;

        while (retries > 0) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 180000); // 180s timeout (increased from 60s for slow API)

                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer;${accessToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload),
                    signal: controller.signal
                });
                clearTimeout(timeoutId);

                if (!response.ok) {
                    const errorText = await response.text();
                    // If 5xx error, throw to catch block for retry
                    if (response.status >= 500) {
                        throw new Error(`Volcengine API Error: ${response.status} - ${errorText}`);
                    }
                    // 4xx errors are likely permanent, throw immediately
                    throw new Error(`Volcengine API Error: ${response.status} - ${errorText}`);
                }

                const data = await response.json() as any;
                if (data.code !== 3000) {
                    throw new Error(`Volcengine TTS Error: ${data.message} (Code: ${data.code})`);
                }

                if (!data.data) throw new Error("Volcengine TTS returned no data");

                return Buffer.from(data.data, 'base64');

            } catch (error: any) {
                lastError = error;
                console.warn(`[Volcengine TTS] Attempt failed (${retries} retries left):`, error.message);

                if (error.message.includes('504') || error.message.includes('502') || error.message.includes('500')) {
                    retries--;
                    if (retries > 0) {
                        const delay = (4 - retries) * 2000; // 2s, 4s, 6s
                        console.log(`[Volcengine TTS] Waiting ${delay}ms before retry...`);
                        await new Promise(resolve => setTimeout(resolve, delay));
                        continue;
                    }
                } else {
                    // Non-retriable error
                    throw error;
                }
            }
        }

        throw lastError;
    }
};
