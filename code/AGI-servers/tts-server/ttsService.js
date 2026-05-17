const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const GoogleTtsProvider = require('./googleTtsProvider');

class TTSService {
    constructor(outputDir = '/tmp/asterisk_tts') {
        this.outputDir = outputDir;
        
        // Ensure the output directory exists
        if (!fs.existsSync(this.outputDir)) {
            fs.mkdirSync(this.outputDir, { recursive: true });
        }
        
        this.ttsProvider = new GoogleTtsProvider();
    }

    /**
     * Convert text to speech and save as a WAV file.
     * @param {string} text - The text to synthesize.
     * @returns {Promise<string>} - The path to the audio file WITHOUT the extension (required by Asterisk streamFile).
     */
    async synthesize(text) {
        try {
            const fileId = uuidv4();
            const filePath = path.join(this.outputDir, fileId);
            const fullFilePath = `${filePath}.wav`;

            console.log(`[TTSService] Synthesizing audio for text: "${text}"`);
            
            // Use the Google TTS Provider to synthesize and save the audio
            await this.ttsProvider.synthesize(text, fullFilePath);
            
            console.log(`[TTSService] Audio saved to ${fullFilePath}`);
            
            // Asterisk's streamFile expects the file path WITHOUT the .wav extension
            return filePath;
        } catch (error) {
            console.error('[TTSService] TTS Synthesis failed:', error);
            throw error;
        }
    }
}

module.exports = TTSService;
