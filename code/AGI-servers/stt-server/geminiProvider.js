const WebSocket = require('ws');
const EventEmitter = require('events');

class GeminiProvider extends EventEmitter {
    constructor(apiKey) {
        super();
        this.apiKey = apiKey || process.env.GEMINI_API_KEY;
        this.ws = null;
        this.setupDone = false;
        
        // Use the Gemini Multimodal Live API endpoint
        this.url = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key=${this.apiKey}`;
    }

    connect() {
        if (!this.apiKey) {
            this.emit('error', new Error('GEMINI_API_KEY is not defined. Cannot connect to Gemini API.'));
            return;
        }

        console.log('[GeminiProvider] Connecting to Gemini Live API...');
        this.ws = new WebSocket(this.url);

        this.ws.on('open', () => {
            console.log('[GeminiProvider] WebSocket connected. Sending setup message...');
            
            // Initial configuration for Gemini Live API
            // The model supports real-time audio streaming
            const setupMessage = {
                setup: {
                    model: "models/gemini-2.0-flash-exp",
                    generationConfig: {
                        responseModalities: ["TEXT"], // We just want text transcriptions (STT)
                    }
                }
            };
            this.ws.send(JSON.stringify(setupMessage));
        });

        this.ws.on('message', (data) => {
            try {
                const response = JSON.parse(data);
                
                // 1. Setup complete response
                if (response.setupComplete) {
                    this.setupDone = true;
                    console.log('[GeminiProvider] Setup complete. Ready to receive audio.');
                    this.emit('ready');
                    return;
                }

                // 2. Real-time text/model response
                if (response.serverContent && response.serverContent.modelTurn) {
                    const parts = response.serverContent.modelTurn.parts;
                    let textResult = "";
                    
                    for (const part of parts) {
                        if (part.text) {
                            textResult += part.text;
                        }
                    }

                    if (textResult.trim() && part.generationComplete) {
                        console.log(`[GeminiProvider] Recognized: "${textResult}"`);
                        this.emit('result', { text: textResult.trim(), score: 100 });
                        textResult = "";
                    }
                }
            } catch (err) {
                console.error('[GeminiProvider] Error parsing response from Gemini:', err);
            }
        });

        this.ws.on('close', () => {
            console.log('[GeminiProvider] Disconnected from Gemini Live API.');
            this.setupDone = false;
            this.emit('close');
        });

        this.ws.on('error', (err) => {
            console.error('[GeminiProvider] WebSocket error:', err);
            this.emit('error', err);
        });
    }

    /**
     * Process audio chunk received from Asterisk and send it to Gemini
     * @param {Buffer} audioBuffer 
     */
    processAudio(audioBuffer) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN || !this.setupDone) {
            return;
        }

        // The Gemini Multimodal Live API expects audio as base64-encoded PCM
        // Default expected format for Asterisk should ideally be 16kHz PCM (slin16)
        // Ensure that Asterisk is configured to send slin16 in aeap.conf
        const base64Audio = audioBuffer.toString('base64');

        const message = {
            realtimeInput: {
                mediaChunks: [{
                    mimeType: "audio/pcm;rate=16000",
                    data: base64Audio
                }]
            }
        };

        this.ws.send(JSON.stringify(message));
    }

    close() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

module.exports = GeminiProvider;
