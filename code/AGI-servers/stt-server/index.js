require('dotenv').config();
const WebSocket = require('ws');
const { randomUUID } = require('crypto');
const EventEmitter = require('events');
const GeminiProvider = require('./geminiProvider');

// --- Configuration ---
const CONFIG = {
    AEAP_PORT: process.env.AEAP_PORT || 9099,
};

// --- AEAP WebSocket Server for Speech-to-Text ---
class AEAPServer {
    constructor(port) {
        this.wss = new WebSocket.Server({ port });
        this.wss.on('connection', this.handleConnection.bind(this));
        console.log(`[AEAP Server] Listening for Asterisk WebSocket connections on port ${port}`);
    }

    handleConnection(ws) {
        const sessionId = randomUUID();
        console.log(`[AEAP Server] New connection established. Session: ${sessionId}`);
        
        const sttService = new GeminiProvider();
        sttService.connect();

        // Listen for results from the STT engine and send back to Asterisk via AEAP set request
        sttService.on('result', (result) => {
            if (ws.readyState === WebSocket.OPEN) {
                const message = {
                    request: "set",
                    id: randomUUID(),
                    params: {
                        results: [
                            {
                                text: result.text,
                                score: result.score
                            }
                        ]
                    }
                };
                ws.send(JSON.stringify(message));
                console.log(`[AEAP Server] Sent transcription result to Asterisk. Session: ${sessionId}`);
            }
        });

        ws.on('message', (message, isBinary) => {
            if (isBinary) {
                // Pass incoming audio frames to the STT provider
                sttService.processAudio(message);
            } else {
                this.handleControlMessage(ws, message, sessionId);
            }
        });

        ws.on('close', () => {
            console.log(`[AEAP Server] Connection closed. Session: ${sessionId}`);
            sttService.close();
        });

        ws.on('error', (err) => {
            console.error(`[AEAP Server] WebSocket error on session ${sessionId}:`, err);
        });
    }

    handleControlMessage(ws, message, sessionId) {
        try {
            const msg = JSON.parse(message);
            console.log(`[AEAP Server] Received control message [${msg.request || msg.response}] - Session: ${sessionId}`);

            if (msg.request === "setup" || msg.request === "set") {
                // Acknowledge setup/set requests and negotiate codecs
                const response = {
                    response: msg.request,
                    id: msg.id,
                    codecs: msg.codecs ? [msg.codecs[0]] : undefined, // Select the preferred codec
                    params: msg.params || {}
                };
                ws.send(JSON.stringify(response));
            } else if (msg.request === "get") {
                const response = {
                    response: msg.request,
                    id: msg.id,
                    params: {}
                };
                ws.send(JSON.stringify(response));
            }
        } catch (err) {
            console.error(`[AEAP Server] Failed to parse control message on session ${sessionId}:`, err);
        }
    }
}

// --- Application Bootstrap ---
function bootstrap() {
    console.log("Starting Asterisk Application Servers...");
    
    // Start AEAP WebSocket Server for STT
    new AEAPServer(CONFIG.AEAP_PORT);
}

// Run the application
bootstrap();
