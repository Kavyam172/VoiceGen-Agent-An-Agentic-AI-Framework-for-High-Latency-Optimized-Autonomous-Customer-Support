const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');

const PROTO_PATH = path.join(__dirname, 'proto', 'bot.proto');

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true
});

const botProto = grpc.loadPackageDefinition(packageDefinition).bot;

class BotGrpcClient {
    constructor(host = 'localhost:50051') {
        // Create the gRPC client connecting to the specified host
        this.client = new botProto.BotService(host, grpc.credentials.createInsecure());
    }

    /**
     * Send text to the bot and get a response in chunks.
     * @param {string} text - The transcribed text from the user.
     * @param {string} sessionId - A unique session ID for context.
     * @yields {string} - The bot's reply text chunks.
     */
    async *getResponse(text, sessionId) {
        const request = { text, session_id: sessionId };
        console.log(`[BotGrpcClient] Sending text to bot: "${text}"`);

        const call = this.client.GetResponse(request);

        try {
            for await (const responseChunk of call) {
                if (responseChunk.text) {
                    yield responseChunk.text;
                }
            }
            console.log('[BotGrpcClient] Finished receiving response chunks.');
        } catch (err) {
            console.error('[BotGrpcClient] Error communicating with bot stream:', err.message);
            throw err;
        }
    }
}

module.exports = BotGrpcClient;
