require('dotenv').config();
const AGIServer = require('ding-dong');
const { v4: uuidv4 } = require('uuid');

const BotGrpcClient = require('./botGrpcClient');
const TTSService = require('./ttsService');

const AGI_PORT = process.env.AGI_PORT || 8081;

// Initialize clients
const botClient = new BotGrpcClient('localhost:50051'); // Ensure your bot gRPC server runs here
const ttsService = new TTSService();

const handleCall = async (context) => {
    try {
        console.log("[AGI Server] Incoming connection from Asterisk.");

        // 1. Wait for Asterisk to send all channel variables
        await context.onEvent('variables');
        
        // 2. Answer the call
        await context.answer();
        console.log("[AGI Server] Call answered.");

        // Generate a unique session ID for this call
        const sessionId = uuidv4();

        // 3. Retrieve the STT result stored in Asterisk context variable
        const sttResult = await context.getVariable('stt_result');
        const userText = sttResult || "Hello, I am calling you.";
        
        console.log(`[AGI Server] Retrieved text from dialplan: "${userText}"`);

        // 4. Pass the text to the bot using gRPC
        console.log(`[AGI Server] Sending text to bot...`);
        
        let botResponseText = "";
        try {
            const responseStream = botClient.getResponse(userText, sessionId);
            for await (const chunk of responseStream) {
                botResponseText += chunk;
            }
            console.log(`[AGI Server] Bot replied: "${botResponseText}"`);
        } catch (grpcErr) {
            console.error("[AGI Server] Bot gRPC call failed. Using fallback response.");
            // If gRPC isn't running, provide a fallback response so the call doesn't drop
            botResponseText = "I'm sorry, I am currently unable to reach the bot service.";
        }

        // 5. Convert the bot's response to speech
        console.log(`[AGI Server] Generating TTS audio...`);
        const ttsAudioPath = await ttsService.synthesize(botResponseText);

        // 6. Play the audio from the AGI
        console.log(`[AGI Server] Streaming audio to caller: ${ttsAudioPath}`);
        // context.streamFile expects the file path without the .wav extension
        await context.streamFile(ttsAudioPath);

        // Optional: delete the file after playing to save space
        // const fs = require('fs');
        // if (fs.existsSync(`${ttsAudioPath}.wav`)) fs.unlinkSync(`${ttsAudioPath}.wav`);

        // 7. Hang up the call
        await context.end();
        console.log("[AGI Server] Call ended gracefully.");

    } catch (err) {
        console.error("[AGI Server] Error during AGI execution:", err);
        try {
            await context.end();
        } catch (e) {
            // Ignore errors while forcing disconnect
        }
    }
};

// Create and start the AGI server
const agiServer = new AGIServer(handleCall);

agiServer.start(AGI_PORT);
console.log(`[AGI Server] Listening for AGI connections on port ${AGI_PORT}...`);
