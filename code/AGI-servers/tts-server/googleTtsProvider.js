const textToSpeech = require('@google-cloud/text-to-speech');
const fs = require('fs');
const util = require('util');

class GoogleTtsProvider {
    constructor() {
        // Creates a client.
        // It will automatically use the GOOGLE_APPLICATION_CREDENTIALS environment variable
        // if it is set, or default credentials.
        this.client = new textToSpeech.TextToSpeechClient();
    }

    /**
     * Converts given text to audio and saves it to the specified file path.
     * @param {string} text - The text to synthesize.
     * @param {string} outputPath - The full file path where the WAV audio should be saved.
     * @returns {Promise<void>}
     */
    async synthesize(text, outputPath) {
        try {
            const request = {
                input: { text: text },
                // Select the language and voice
                voice: { languageCode: 'en-US', name: 'en-US-Standard-A' },
                // Select the type of audio encoding. 
                // Asterisk typically needs LINEAR16 at 8000Hz for standard phone calls.
                audioConfig: { 
                    audioEncoding: 'LINEAR16',
                    sampleRateHertz: 8000
                },
            };

            // Performs the text-to-speech request
            const [response] = await this.client.synthesizeSpeech(request);
            
            // Write the binary audio content to a local file
            const writeFile = util.promisify(fs.writeFile);
            await writeFile(outputPath, response.audioContent, 'binary');
            
            console.log(`[GoogleTtsProvider] Successfully synthesized audio to ${outputPath}`);
        } catch (error) {
            console.error('[GoogleTtsProvider] Error synthesizing text:', error);
            throw error;
        }
    }
}

module.exports = GoogleTtsProvider;
